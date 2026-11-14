"""Stage 6 — Farm-Level Risk Assessment service.

Architecture
------------
1. ``assess_farms()`` — main entry point called by the API.
   • Reads all sensor readings + trust scores for the requested tick.
   • Builds a trust-weighted Gaussian Process regression over the sensor
     locations (lat/lng → rainfall).
   • Evaluates the GP at each farm's centroid to produce:
       - estimated_rainfall_mm  (posterior mean, mm/hr)
       - uncertainty_mm         (posterior std dev)
       - lower_ci / upper_ci    (10th / 90th percentiles)
   • Converts the rainfall estimate into a risk category.
   • Derives a flood_risk_score from water-level gauge readings.
   • Returns FarmRiskResult dataclasses — one per farm.

2. ``categorise_risk()`` — deterministic rule that maps (rainfall_mm, uncertainty)
   → risk_category string.

3. ``derive_flood_risk()`` — simple normalised score from water-level gauge values.

Design rules (from roadmap)
---------------------------
- Trust-weighted: sensors with low trust scores contribute less to the GP.
  We achieve this by scaling observation noise inversely with trust:
  low-trust sensors are treated as noisier.
- genuine_localised_cell is NOT discarded — its trust base is 0.90, so it
  still contributes meaningfully.
- Uncertainty is *reported*, not hidden.
- If fewer than 2 trusted sensors are available the farm receives
  'insufficient_evidence' rather than a spurious estimate.
- All estimates carry a model_version tag for reproducibility.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

from app.services.simulation import GaugeReading, ScenarioPreset, WeatherSimulator
from app.services.geo import generate_farms, generate_sensors
from app.models.sensor import SensorTrustScore

MODEL_VERSION = "gp-v1"

# Risk thresholds (mm/hr)
_THRESHOLDS = {
    "low":      (0.0,  10.0),
    "moderate": (10.0, 25.0),
    "high":     (25.0, 60.0),
    "extreme":  (60.0, float("inf")),
}

# Minimum number of trusted (trust ≥ 0.3) sensors needed for a valid estimate.
_MIN_TRUSTED_SENSORS = 2


@dataclass
class FarmRiskResult:
    farm_id: str
    tick: int
    run_id: int

    estimated_rainfall_mm: float | None
    uncertainty_mm: float | None
    lower_ci: float | None
    upper_ci: float | None

    risk_category: str           # low | moderate | high | extreme | insufficient_evidence
    flood_risk_score: float | None  # 0.0–1.0

    supporting_sensors: list[str] = field(default_factory=list)
    evidence_note: str = ""
    model_version: str = MODEL_VERSION


# ─── Risk categorisation ─────────────────────────────────────────────────────

def categorise_risk(rainfall_mm: float | None, uncertainty_mm: float | None) -> str:
    if rainfall_mm is None:
        return "insufficient_evidence"
    # If uncertainty is very high relative to the estimate, bump up one category.
    uncertainty_factor = (uncertainty_mm or 0.0) / max(rainfall_mm, 1.0)
    for cat, (lo, hi) in _THRESHOLDS.items():
        if lo <= rainfall_mm < hi:
            # Upgrade if highly uncertain
            if uncertainty_factor > 1.5 and cat == "moderate":
                return "high"
            if uncertainty_factor > 1.5 and cat == "low":
                return "moderate"
            return cat
    return "extreme"


# ─── Flood risk from water-level gauges ──────────────────────────────────────

def derive_flood_risk(water_level_readings: list[GaugeReading]) -> float | None:
    """Normalise water-level readings to a 0–1 flood risk score.

    Uses a simple sigmoid centred around 300 cm (action level).
    Returns None when there are no water-level gauges.
    """
    if not water_level_readings:
        return None
    vals = [r.value for r in water_level_readings]
    mean_wl = float(np.mean(vals))
    # Sigmoid: 0 at 0 cm, 0.5 at 300 cm, ~1.0 at 600 cm
    score = 1.0 / (1.0 + math.exp(-(mean_wl - 300.0) / 80.0))
    return round(score, 3)


# ─── Trust-weighted GP estimation ────────────────────────────────────────────

def _build_noise_alpha(trust_scores: list[float]) -> np.ndarray:
    """Higher trust → lower noise (alpha) in the GP.

    trust=1.0 → alpha=0.1 (very reliable)
    trust=0.5 → alpha=1.0
    trust=0.1 → alpha=5.0 (very noisy)
    """
    alphas = []
    for t in trust_scores:
        t = max(0.05, min(1.0, t))
        alphas.append(0.1 / t)
    return np.array(alphas)


def _fit_gp(
    locs: np.ndarray,     # shape (n, 2) — [lat, lng]
    values: np.ndarray,   # shape (n,)
    noise_alphas: np.ndarray,  # per-observation noise
) -> GaussianProcessRegressor:
    """Fit a GP with RBF + WhiteKernel. The per-observation noise is
    approximated by using the mean noise as the GP's alpha parameter.
    scikit-learn's GP supports only scalar alpha, so we weight by noise."""
    # Scale coordinates to [0, 1] range for numerical stability.
    kernel = RBF(length_scale=0.1, length_scale_bounds=(1e-3, 1.0)) + WhiteKernel(
        noise_level=float(np.mean(noise_alphas)), noise_level_bounds=(1e-5, 10.0)
    )
    gp = GaussianProcessRegressor(
        kernel=kernel,
        alpha=noise_alphas,
        n_restarts_optimizer=3,
        normalize_y=True,
        random_state=42,
    )
    gp.fit(locs, values)
    return gp


# ─── Main assessment entry point ─────────────────────────────────────────────

def assess_farms(
    run_id: int,
    tick: int,
    trust_rows: list[SensorTrustScore],
    sim: WeatherSimulator,
) -> list[FarmRiskResult]:
    """Produce a risk estimate for every farm in the district.

    Parameters
    ----------
    run_id:      Database run id (for embedding in results).
    tick:        Simulation tick to assess.
    trust_rows:  Persisted SensorTrustScore rows for this run (may span
                 multiple ticks — only the latest per sensor is used).
    sim:         Instantiated WeatherSimulator for the run's scenario/seed.
    """
    snapshot = sim.snapshot(tick)

    # Build a lookup: sensor_id → latest trust score.
    latest_trust: dict[str, float] = {}
    for row in sorted(trust_rows, key=lambda r: r.tick):
        latest_trust[row.sensor_id] = row.trust_score

    # Separate rainfall and water-level readings.
    rain_readings = [r for r in snapshot.gauge_readings if r.sensor_type == "rainfall"]
    wl_readings   = [r for r in snapshot.gauge_readings if r.sensor_type == "water_level"]

    # Flood risk (district-wide scalar derived from water-level gauges).
    flood_risk = derive_flood_risk(wl_readings)

    # Build GP training data from rainfall sensors that have trust scores.
    # Sensors with no trust score yet are given a conservative default of 0.5.
    locs_list:    list[list[float]] = []
    values_list:  list[float]       = []
    noise_list:   list[float]       = []
    sensor_ids:   list[str]         = []

    for r in rain_readings:
        trust = latest_trust.get(r.sensor_id, 0.5)
        if trust < 0.05:
            continue  # effectively dead sensor — exclude
        locs_list.append([r.lat, r.lng])
        values_list.append(r.value)
        noise_list.append(trust)
        sensor_ids.append(r.sensor_id)

    trusted_count = sum(1 for t in noise_list if t >= 0.3)

    farms = generate_farms()
    results: list[FarmRiskResult] = []

    if trusted_count < _MIN_TRUSTED_SENSORS:
        # Not enough trusted data — return 'insufficient_evidence' for all farms.
        for farm in farms:
            results.append(FarmRiskResult(
                farm_id=farm.id,
                tick=tick,
                run_id=run_id,
                estimated_rainfall_mm=None,
                uncertainty_mm=None,
                lower_ci=None,
                upper_ci=None,
                risk_category="insufficient_evidence",
                flood_risk_score=flood_risk,
                supporting_sensors=[],
                evidence_note=(
                    f"Only {trusted_count} trusted sensor(s) available at tick {tick}. "
                    "A minimum of 2 is required for spatial estimation."
                ),
            ))
        return results

    # Fit the GP.
    locs_arr   = np.array(locs_list)
    values_arr = np.array(values_list)
    noise_arr  = _build_noise_alpha(noise_list)

    try:
        gp = _fit_gp(locs_arr, values_arr, noise_arr)
    except Exception as exc:  # noqa: BLE001
        # GP fitting failure (e.g. singular matrix) — fall back to IDW.
        gp = None
        gp_error = str(exc)
    else:
        gp_error = None

    # Evaluate at each farm centroid.
    for farm in farms:
        farm_loc = np.array([[farm.latitude, farm.longitude]])

        if gp is not None:
            mean, std = gp.predict(farm_loc, return_std=True)
            est   = float(max(0.0, mean[0]))
            sigma = float(std[0])
        else:
            # Inverse-distance weighted fallback.
            dists = np.sqrt(
                (locs_arr[:, 0] - farm.latitude) ** 2
                + (locs_arr[:, 1] - farm.longitude) ** 2
            ) + 1e-9
            weights = (1.0 / dists) * np.array(noise_list)  # trust-weighted IDW
            weights /= weights.sum()
            est   = float(max(0.0, np.dot(weights, values_arr)))
            sigma = float(np.std(values_arr))  # rough uncertainty estimate

        # Identify the top-3 supporting sensors (closest by distance).
        dists_to_farm = np.sqrt(
            (locs_arr[:, 0] - farm.latitude) ** 2
            + (locs_arr[:, 1] - farm.longitude) ** 2
        )
        top3_idx = np.argsort(dists_to_farm)[:3].tolist()
        top_sensors = [sensor_ids[i] for i in top3_idx]

        # 10th / 90th percentile (assume Gaussian).
        NORM_10 = -1.282
        NORM_90 =  1.282
        lower = max(0.0, est + NORM_10 * sigma)
        upper = max(0.0, est + NORM_90 * sigma)

        risk = categorise_risk(est, sigma)
        note = (
            f"GP estimate from {len(sensor_ids)} sensors "
            f"({trusted_count} trusted). "
            f"Tick {tick}. Simulated data."
        )
        if gp_error:
            note = f"IDW fallback (GP error: {gp_error}). " + note

        results.append(FarmRiskResult(
            farm_id=farm.id,
            tick=tick,
            run_id=run_id,
            estimated_rainfall_mm=round(est, 2),
            uncertainty_mm=round(sigma, 2),
            lower_ci=round(lower, 2),
            upper_ci=round(upper, 2),
            risk_category=risk,
            flood_risk_score=flood_risk,
            supporting_sensors=top_sensors,
            evidence_note=note,
        ))

    return results

