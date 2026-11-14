/**
 * Stage 6 — Farm Risk Panel.
 *
 * Rendered in the insurer operations-map sidebar. Lets the insurer:
 *   - Run the GP spatial risk estimation for the active run + tick.
 *   - See a summary (category counts) with coloured badges.
 *   - View per-farm details when a farm is selected on the map.
 *
 * Design rules from the roadmap:
 *   - Uncertainty is displayed alongside the estimate, never hidden.
 *   - The panel clearly labels all data as simulated.
 *   - Risk colours must NOT imply a confirmed physical flood boundary.
 */
import { useState } from "react";
import type { UseRiskReturn } from "../../hooks/useRisk";
import type { FarmRiskEstimate, RiskCategory, RiskSummary } from "../../api/risk";

// ─── Visual constants ─────────────────────────────────────────────────────────

const CAT_LABEL: Record<RiskCategory, string> = {
  low:                   "Low",
  moderate:              "Moderate",
  high:                  "High",
  extreme:               "Extreme",
  insufficient_evidence: "Insufficient evidence",
};

const CAT_BADGE: Record<RiskCategory, string> = {
  low:                   "bg-green-900/50 text-green-300 border-green-700",
  moderate:              "bg-yellow-900/50 text-yellow-300 border-yellow-700",
  high:                  "bg-orange-900/50 text-orange-300 border-orange-700",
  extreme:               "bg-red-900/50 text-red-300 border-red-700",
  insufficient_evidence: "bg-slate-700 text-slate-300 border-slate-600",
};

// ─── Props ────────────────────────────────────────────────────────────────────

interface Props {
  runId: number | null;
  tick: number;
  risk: UseRiskReturn;
  /** Currently selected farm ID from the map. */
  selectedFarmId: string | null;
}

// ─── Main panel ──────────────────────────────────────────────────────────────

export default function FarmRiskPanel({ runId, tick, risk, selectedFarmId }: Props) {
  const { riskLayer, assessing, error, assess } = risk;
  const [showDetail, setShowDetail] = useState(false);

  const selectedFarm: FarmRiskEstimate | null =
    selectedFarmId && riskLayer
      ? riskLayer.farms.find((f) => f.farm_id === selectedFarmId) ?? null
      : null;

  async function handleAssess() {
    if (runId == null) return;
    await assess(runId, tick);
    if (selectedFarmId) setShowDetail(true);
  }

  return (
    <div className="border-t border-navy-700 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-base">🌧️</span>
        <span className="text-sm font-semibold text-white">Farm Risk Assessment</span>
        <span className="text-xs px-1.5 py-0.5 rounded bg-orange-900/50 text-orange-300 border border-orange-700">
          Stage 6
        </span>
      </div>

      {/* Run button */}
      <div className="space-y-1.5">
        <button
          onClick={handleAssess}
          disabled={runId == null || assessing}
          className="w-full bg-brand-blue text-white text-xs font-semibold px-3 py-2 rounded-lg hover:opacity-90 disabled:opacity-40 transition"
        >
          {assessing ? "Estimating…" : "📊 Run Risk Assessment"}
        </button>
        <p className="text-xs text-gray-500">
          GP spatial estimate at tick {tick}
          {runId == null ? " — start a simulation first" : ""}. Uncertainty is shown.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-3 py-2 text-xs">
          {error}
        </div>
      )}

      {/* Summary */}
      {riskLayer ? (
        <RiskSummaryCard summary={riskLayer.summary} tick={riskLayer.tick} />
      ) : (
        <div className="bg-navy-900/50 rounded-lg border border-navy-700/50 p-3 text-center">
          <p className="text-xs text-gray-500">
            No risk layer yet. Run assessment to score all farms.
          </p>
        </div>
      )}

      {/* Selected farm detail */}
      {selectedFarm && (
        <FarmRiskDetail farm={selectedFarm} />
      )}
      {selectedFarmId && riskLayer && !selectedFarm && (
        <p className="text-xs text-gray-500 italic">
          Farm {selectedFarmId} not found in current risk layer. Run assessment to include it.
        </p>
      )}

      <p className="text-xs text-gray-600 italic">
        Simulated GP estimate · not a confirmed physical flood boundary.
      </p>
    </div>
  );
}

// ─── Summary card ─────────────────────────────────────────────────────────────

function RiskSummaryCard({ summary, tick }: { summary: RiskSummary; tick: number }) {
  const cats: { key: RiskCategory; label: string }[] = [
    { key: "low",                   label: "Low" },
    { key: "moderate",              label: "Moderate" },
    { key: "high",                  label: "High" },
    { key: "extreme",               label: "Extreme" },
    { key: "insufficient_evidence", label: "Insuff." },
  ];

  return (
    <div className="bg-navy-900 rounded-lg border border-navy-700 p-3 space-y-2">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
        Risk Distribution · Tick {tick}
      </p>
      <div className="grid grid-cols-5 gap-1 text-center">
        {cats.map(({ key, label }) => (
          <div key={key}>
            <div
              className={`text-sm font-bold px-1 rounded border text-center ${CAT_BADGE[key]}`}
            >
              {summary[key]}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-600 italic">
        {summary.total_farms} farms assessed · simulated data.
      </p>
    </div>
  );
}

// ─── Farm detail card ────────────────────────────────────────────────────────

function FarmRiskDetail({ farm }: { farm: FarmRiskEstimate }) {
  const badgeCls = CAT_BADGE[farm.risk_category] ?? CAT_BADGE.insufficient_evidence;
  const label    = CAT_LABEL[farm.risk_category] ?? farm.risk_category;

  return (
    <div className="bg-navy-900 rounded-lg border border-navy-700 p-3 space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-gray-300">{farm.farm_id}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full border ${badgeCls}`}>
          {label}
        </span>
      </div>

      {farm.estimated_rainfall_mm !== null ? (
        <>
          {/* Rainfall estimate with CI */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
              Rainfall estimate
            </p>
            <div className="flex items-baseline gap-1">
              <span className="text-lg font-bold text-white">
                {farm.estimated_rainfall_mm.toFixed(1)}
              </span>
              <span className="text-xs text-gray-400">mm/hr</span>
              <span className="text-xs text-gray-500 ml-1">
                ± {farm.uncertainty_mm?.toFixed(1)} (1σ)
              </span>
            </div>
            <p className="text-xs text-gray-600 mt-0.5">
              80% CI: [{farm.lower_ci?.toFixed(1)}, {farm.upper_ci?.toFixed(1)}] mm/hr
            </p>
          </div>

          {/* Flood risk */}
          {farm.flood_risk_score !== null && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Flood risk</span>
              <FloodBar value={farm.flood_risk_score} />
            </div>
          )}

          {/* Supporting sensors */}
          {farm.supporting_sensors.length > 0 && (
            <div>
              <p className="text-xs text-gray-500">
                Primary sensors:{" "}
                <span className="font-mono text-gray-300">
                  {farm.supporting_sensors.join(", ")}
                </span>
              </p>
            </div>
          )}
        </>
      ) : (
        <p className="text-xs text-gray-500 italic">
          Insufficient evidence — fewer than 2 trusted sensors available.
        </p>
      )}

      <p className="text-xs text-gray-600 italic border-t border-navy-700 pt-1">
        {farm.evidence_note}
      </p>
    </div>
  );
}

// ─── Flood bar ────────────────────────────────────────────────────────────────

function FloodBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const colour =
    value >= 0.7 ? "bg-red-500" :
    value >= 0.4 ? "bg-orange-500" :
    "bg-green-500";

  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-navy-800 rounded-full overflow-hidden">
        <div className={`h-2 rounded-full ${colour}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-white w-9 text-right">{value.toFixed(2)}</span>
    </div>
  );
}

