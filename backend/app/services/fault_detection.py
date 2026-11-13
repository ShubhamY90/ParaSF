"""Stage 5 — Sensor Fault Detection & Trust Scoring.

Architecture
------------
1. ``generate_training_data()``  — synthetic labelled time-series for all six
   condition classes (normal, spike, stuck, drift, dead,
   genuine_localised_cell).  Deterministic from a fixed seed.

2. ``build_features()``  — per-reading feature vector:
   • own value & z-score within the sensor's rolling window
   • rate-of-change (1-tick delta, abs delta)
   • neighbour comparison (mean, max, ratio vs closest 3 sensors)
   • stuck-value flag (last N readings identical within tolerance)
   • missing / zero flag
   • temporal position (tick ratio within the scenario)

3. ``train_model()``  — LightGBM multi-class classifier trained on the
   synthetic data.  Returns (model, label_encoder, feature_names).
   The model is cached as a module-level singleton so it is trained once
   per process.

4. ``classify_readings()``  — takes a list of GaugeReading + neighbour
   context, returns SensorClassification dataclass per sensor.

5. ``compute_trust_score()``  — maps (class, confidence) → 0.0–1.0 trust.

Important design rule (from the roadmap)
-----------------------------------------
An outlier is *suspicious*, not automatically false.  The classifier may
flag a reading; that flag is input to the investigation agents in Stage 7.
The original reading is always preserved.  ``genuine_localised_cell`` is a
valid class, not a fault.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix

from app.services.simulation import GaugeReading, ScenarioPreset, WeatherSimulator

# ─── Constants ────────────────────────────────────────────────────────────────

FAULT_CLASSES = ["normal", "spike", "stuck", "drift", "dead", "genuine_localised_cell"]

# Trust weights per class: genuine_localised_cell treated as normal (trustworthy).
_CLASS_TRUST_BASE = {
    "normal":                1.0,
    "genuine_localised_cell": 0.90,  # slightly uncertain — investigate before discarding
    "drift":                 0.55,
    "stuck":                 0.30,
    "spike":                 0.20,
    "dead":                  0.10,
}

TRAIN_SEED = 7919   # separate from simulation seed

# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class SensorClassification:
    sensor_id: str
    sensor_type: str
    predicted_class: str
    confidence: float          # max class probability
    trust_score: float         # 0.0 – 1.0
    class_probabilities: dict[str, float]
    is_flagged: bool           # True for any non-normal, non-genuine class
    investigation_note: str
    simulated: bool = True


# ─── Synthetic training data generation ──────────────────────────────────────

def _generate_series(
    rng: random.Random,
    n_ticks: int,
    base: float,
    noise_std: float,
    condition: str,
    n_neighbours: int = 5,
) -> list[dict]:
    """Generate a list of feature-dicts for one sensor under one condition."""
    rows: list[dict] = []
    values: list[float] = []
    neighbour_means: list[float] = []

    # Stuck value chosen once at a mid-series tick.
    stuck_start = rng.randint(n_ticks // 4, n_ticks // 2)
    stuck_val   = base + rng.gauss(0, noise_std)
    drift_slope = rng.choice([0.8, 1.2, -0.6])  # mm/hr per tick

    # Localised peak tick range.
    local_start = n_ticks // 3
    local_end   = local_start + max(3, n_ticks // 6)

    for t in range(n_ticks):
        if condition == "normal":
            v = max(0.0, base + rng.gauss(0, noise_std))
            n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))
        elif condition == "spike":
            v = base + rng.gauss(0, noise_std)
            if t == n_ticks // 2:
                v += rng.uniform(150, 250)   # large sudden spike
            n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))
        elif condition == "stuck":
            v = stuck_val if t >= stuck_start else max(0.0, base + rng.gauss(0, noise_std))
            n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))
        elif condition == "drift":
            v = max(0.0, base + drift_slope * (t - n_ticks // 3) + rng.gauss(0, noise_std * 0.5))
            n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))
        elif condition == "dead":
            v = 0.0 if t >= n_ticks // 3 else max(0.0, base + rng.gauss(0, noise_std))
            n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))
        elif condition == "genuine_localised_cell":
            # One sensor sees a real intense local cell; neighbours stay low.
            if local_start <= t <= local_end:
                v = rng.uniform(80, 180)
                n_mean = rng.uniform(1, 8)   # neighbours stay low — key discriminator
            else:
                v = max(0.0, base + rng.gauss(0, noise_std))
                n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))
        else:
            v = max(0.0, base + rng.gauss(0, noise_std))
            n_mean = max(0.0, base + rng.gauss(0, noise_std * 0.8))

        values.append(v)
        neighbour_means.append(n_mean)

    # Build feature rows.
    window = 5
    for t in range(n_ticks):
        window_vals = values[max(0, t - window + 1): t + 1]
        w_mean = float(np.mean(window_vals))
        w_std  = float(np.std(window_vals)) + 1e-6

        delta1  = values[t] - values[t - 1] if t > 0 else 0.0
        delta3  = values[t] - values[max(0, t - 3)]
        abs_d1  = abs(delta1)

        stuck_flag = int(len(window_vals) >= 3 and np.std(window_vals[-3:]) < 0.05)

        ratio_to_neighbour = values[t] / (neighbour_means[t] + 1e-6)
        diff_to_neighbour  = values[t] - neighbour_means[t]

        rows.append({
            "value":               values[t],
            "z_score":             (values[t] - w_mean) / w_std,
            "delta1":              delta1,
            "delta3":              delta3,
            "abs_delta1":          abs_d1,
            "rolling_mean":        w_mean,
            "rolling_std":         w_std,
            "ratio_to_neighbour":  ratio_to_neighbour,
            "diff_to_neighbour":   diff_to_neighbour,
            "neighbour_mean":      neighbour_means[t],
            "stuck_flag":          stuck_flag,
            "is_zero":             int(values[t] < 0.01),
            "tick_ratio":          t / max(n_ticks - 1, 1),
            "label":               condition,
        })
    return rows


def generate_training_data(seed: int = TRAIN_SEED) -> pd.DataFrame:
    """Generate synthetic labelled sensor time-series data."""
    rng = random.Random(seed)
    all_rows: list[dict] = []

    # Generate multiple series per class to get a balanced dataset.
    n_series_per_class = 40
    n_ticks = 48

    for condition in FAULT_CLASSES:
        for _ in range(n_series_per_class):
            base  = rng.uniform(0.5, 15.0)
            noise = rng.uniform(0.3, 3.0)
            rows  = _generate_series(rng, n_ticks, base, noise, condition)
            all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    return df


# ─── Feature names ────────────────────────────────────────────────────────────

FEATURE_COLS = [
    "value", "z_score", "delta1", "delta3", "abs_delta1",
    "rolling_mean", "rolling_std", "ratio_to_neighbour",
    "diff_to_neighbour", "neighbour_mean", "stuck_flag",
    "is_zero", "tick_ratio",
]


# ─── Model training ───────────────────────────────────────────────────────────

@dataclass
class TrainedModel:
    model: LGBMClassifier
    label_encoder: LabelEncoder
    feature_names: list[str]
    class_report: str
    confusion: list[list[int]]


@lru_cache(maxsize=1)
def get_trained_model() -> TrainedModel:
    """Train and cache the LightGBM classifier (once per process)."""
    df = generate_training_data()
    X = df[FEATURE_COLS].values
    le = LabelEncoder()
    y = le.fit_transform(df["label"].values)

    model = LGBMClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        num_leaves=31,
        class_weight="balanced",
        random_state=TRAIN_SEED,
        verbose=-1,
    )
    model.fit(X, y)

    y_pred = model.predict(X)
    report = classification_report(y, y_pred, target_names=le.classes_, zero_division=0)
    cm = confusion_matrix(y, y_pred).tolist()

    return TrainedModel(
        model=model,
        label_encoder=le,
        feature_names=FEATURE_COLS,
        class_report=report,
        confusion=cm,
    )


# ─── Feature extraction from live readings ───────────────────────────────────

def _build_live_features(
    reading: GaugeReading,
    history: list[float],       # own recent values, oldest-first (up to 5)
    neighbour_vals: list[float], # concurrent readings from nearby sensors
) -> np.ndarray:
    window = history[-5:] if len(history) >= 5 else history
    w_arr  = np.array(window, dtype=float) if window else np.array([reading.value])
    w_mean = float(np.mean(w_arr))
    w_std  = float(np.std(w_arr)) + 1e-6

    delta1 = reading.value - history[-1] if len(history) >= 1 else 0.0
    delta3 = reading.value - history[-3] if len(history) >= 3 else 0.0

    n_arr     = np.array(neighbour_vals, dtype=float) if neighbour_vals else np.array([reading.value])
    n_mean    = float(np.mean(n_arr))
    ratio     = reading.value / (n_mean + 1e-6)
    diff      = reading.value - n_mean

    stuck = int(len(w_arr) >= 3 and float(np.std(w_arr[-3:])) < 0.05)

    return np.array([[
        reading.value,
        (reading.value - w_mean) / w_std,
        delta1, delta3, abs(delta1),
        w_mean, w_std,
        ratio, diff, n_mean,
        stuck,
        int(reading.value < 0.01),
        0.5,  # tick_ratio unknown for live; use mid-scenario default
    ]], dtype=float)


# ─── Trust score ──────────────────────────────────────────────────────────────

def compute_trust_score(predicted_class: str, confidence: float) -> float:
    """Map (predicted class, model confidence) → trust score 0.0–1.0.

    Higher confidence in a fault class → lower trust.
    genuine_localised_cell keeps near-normal trust so it is not discarded.
    """
    base = _CLASS_TRUST_BASE.get(predicted_class, 0.5)
    # Blend base trust with confidence: very confident fault prediction lowers trust further.
    if predicted_class in ("normal", "genuine_localised_cell"):
        # Confidence in a good class increases trust slightly.
        trust = base * (0.85 + 0.15 * confidence)
    else:
        # Confidence in a fault class decreases trust proportionally.
        trust = base * (1.0 - 0.4 * confidence) + (1.0 - base) * (1.0 - confidence) * 0.1
    return round(min(1.0, max(0.0, trust)), 3)


def _investigation_note(predicted_class: str, confidence: float, value: float) -> str:
    pct = int(confidence * 100)
    if predicted_class == "normal":
        return f"Reading within normal range (confidence {pct}%)."
    if predicted_class == "genuine_localised_cell":
        return (
            f"Outlier detected but consistent with a genuine localised storm cell "
            f"(confidence {pct}%). Neighbouring sensor comparison supports this. "
            f"Investigate before discarding."
        )
    if predicted_class == "spike":
        return (
            f"Sudden spike of {value:.1f} detected — likely sensor fault (confidence {pct}%). "
            f"Cross-check with neighbouring gauges and satellite evidence before rejecting."
        )
    if predicted_class == "stuck":
        return f"Sensor reporting a constant value — possible stuck fault (confidence {pct}%)."
    if predicted_class == "drift":
        return f"Gradual drift from baseline detected (confidence {pct}%). Recalibration may be needed."
    if predicted_class == "dead":
        return f"Sensor reporting zero or no signal — possible dead/offline fault (confidence {pct}%)."
    return f"Anomaly detected: {predicted_class} (confidence {pct}%)."


# ─── Main classification entry point ─────────────────────────────────────────

def classify_readings(
    readings: list[GaugeReading],
    history_map: dict[str, list[float]] | None = None,
) -> list[SensorClassification]:
    """Classify a list of GaugeReading objects from one simulation tick.

    ``history_map`` maps sensor_id → list of recent own values (up to 5 ticks).
    If not provided, single-tick features are used (less accurate for stuck/drift).

    Only rainfall gauges are classified for faults; water-level gauges receive
    a fixed 'normal' classification (fault model is trained on rainfall series).
    """
    tm = get_trained_model()
    results: list[SensorClassification] = []

    # Build neighbour map: for each rainfall gauge, find the 3 closest by index.
    rain_readings = [r for r in readings if r.sensor_type == "rainfall"]
    rain_vals     = {r.sensor_id: r.value for r in rain_readings}

    def _neighbours(sensor_id: str) -> list[float]:
        others = [v for sid, v in rain_vals.items() if sid != sensor_id]
        # Simple: take up to 3 closest-valued (index-adjacent) neighbours.
        return sorted(others, key=lambda v: abs(v - rain_vals.get(sensor_id, 0)))[:3]

    for r in readings:
        if r.sensor_type == "water_level":
            # Water-level gauges: trust based on simulated flood state only.
            results.append(SensorClassification(
                sensor_id=r.sensor_id,
                sensor_type=r.sensor_type,
                predicted_class="normal",
                confidence=1.0,
                trust_score=1.0,
                class_probabilities={c: (1.0 if c == "normal" else 0.0) for c in FAULT_CLASSES},
                is_flagged=False,
                investigation_note="Water-level gauge — fault detection not applied.",
            ))
            continue

        hist = (history_map or {}).get(r.sensor_id, [r.value])
        neighbours = _neighbours(r.sensor_id)
        X = _build_live_features(r, hist, neighbours)

        proba = tm.model.predict_proba(X)[0]
        class_idx = int(np.argmax(proba))
        predicted = tm.label_encoder.classes_[class_idx]
        confidence = float(proba[class_idx])

        proba_dict = {
            tm.label_encoder.classes_[i]: round(float(proba[i]), 4)
            for i in range(len(proba))
        }

        trust = compute_trust_score(predicted, confidence)
        is_flagged = predicted not in ("normal", "genuine_localised_cell")

        results.append(SensorClassification(
            sensor_id=r.sensor_id,
            sensor_type=r.sensor_type,
            predicted_class=predicted,
            confidence=round(confidence, 4),
            trust_score=trust,
            class_probabilities=proba_dict,
            is_flagged=is_flagged,
            investigation_note=_investigation_note(predicted, confidence, r.value),
        ))

    return results


# ─── Per-class evaluation helper ─────────────────────────────────────────────

def get_model_evaluation() -> dict[str, Any]:
    """Return per-class precision/recall/F1 and the confusion matrix.

    Used by the API to serve the evaluation report to the insurer UI.
    """
    tm = get_trained_model()
    return {
        "classes": FAULT_CLASSES,
        "classification_report": tm.class_report,
        "confusion_matrix": tm.confusion,
        "label_order": list(tm.label_encoder.classes_),
        "note": (
            "Evaluation on training data only — this is a prototype model. "
            "genuine_localised_cell is a valid weather condition, not a sensor fault."
        ),
    }
