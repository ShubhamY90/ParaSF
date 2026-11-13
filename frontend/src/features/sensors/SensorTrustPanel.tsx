/**
 * Stage 5 — Sensor Health control panel.
 *
 * Rendered inside the operations-map sidebar. Lets the insurer:
 *   - Run fault detection on the active simulation run at the current tick.
 *   - See a summary (gauges classified, flagged, average trust).
 *   - Drill into each flagged sensor (click → focuses it on the map).
 *   - Inspect the model evaluation (per-class precision/recall/F1 +
 *     confusion matrix) with the key note that a genuine localised cell is
 *     a valid weather condition, not a sensor fault.
 */
import { useState } from "react";
import type { UseSensorTrustReturn } from "../../hooks/useSensorTrust";
import type { ModelEvaluation, SensorClassification } from "../../api/sensors";

const CLASS_LABEL: Record<string, string> = {
  normal: "Normal",
  spike: "Spike",
  stuck: "Stuck",
  drift: "Drift",
  dead: "Dead / offline",
  genuine_localised_cell: "Genuine localised cell",
};

const CLASS_COLOUR: Record<string, string> = {
  normal: "bg-green-900/50 text-green-300 border-green-700",
  genuine_localised_cell: "bg-blue-900/50 text-blue-300 border-blue-700",
  spike: "bg-red-900/50 text-red-300 border-red-700",
  stuck: "bg-orange-900/50 text-orange-300 border-orange-700",
  drift: "bg-amber-900/50 text-amber-300 border-amber-700",
  dead: "bg-gray-700 text-gray-300 border-gray-600",
};

interface Props {
  runId: number | null;
  tick: number;
  sensorTrust: UseSensorTrustReturn;
  /** Focus a sensor on the map / open its investigation panel. */
  onSensorSelect?: (sensorId: string) => void;
}

export default function SensorTrustPanel({ runId, tick, sensorTrust, onSensorSelect }: Props) {
  const { trustMap, modelEval, classifying, evalLoading, error, classify, loadModelEvaluation } =
    sensorTrust;
  const [showEval, setShowEval] = useState(false);

  const flagged: SensorClassification[] =
    trustMap?.classifications.filter((c) => c.is_flagged) ?? [];
  const rainCount = trustMap?.classifications.filter((c) => c.sensor_type === "rainfall").length ?? 0;
  const avgTrust =
    trustMap && trustMap.classifications.length > 0
      ? Math.round(
          (trustMap.classifications.reduce((s, c) => s + c.trust_score, 0) /
            trustMap.classifications.length) *
            100,
        ) / 100
      : null;

  async function handleRun() {
    if (runId == null) return;
    await classify(runId, tick);
  }

  async function toggleEval() {
    const next = !showEval;
    setShowEval(next);
    if (next && !modelEval) await loadModelEvaluation();
  }

  return (
    <div className="border-t border-navy-700 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">📡</span>
          <span className="text-sm font-semibold text-white">Sensor Health</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-blue-900/50 text-blue-300 border border-blue-700">
            Stage 5
          </span>
        </div>
      </div>

      {/* Run detection */}
      <div className="space-y-1.5">
        <button
          onClick={handleRun}
          disabled={runId == null || classifying}
          className="w-full bg-brand-blue text-white text-xs font-semibold px-3 py-2 rounded-lg hover:opacity-90 disabled:opacity-40 transition"
        >
          {classifying ? "Detecting…" : "🔍 Run Fault Detection"}
        </button>
        <p className="text-xs text-gray-500">
          Classifies every rainfall gauge at tick {tick}
          {runId == null ? " — start a simulation first" : ""}.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-3 py-2 text-xs">
          {error}
        </div>
      )}

      {/* Summary */}
      {trustMap ? (
        <div className="bg-navy-900 rounded-lg border border-navy-700 p-3 space-y-2">
          <div className="grid grid-cols-3 gap-2 text-center">
            <Stat label="Gauges" value={`${rainCount}`} />
            <Stat label="Flagged" value={`${flagged.length}`} accent={flagged.length > 0 ? "red" : undefined} />
            <Stat label="Avg trust" value={avgTrust != null ? avgTrust.toFixed(2) : "—"} />
          </div>
          <p className="text-xs text-gray-500 italic">
            Tick {trustMap.tick} · simulated classifications · original readings preserved.
          </p>
        </div>
      ) : (
        <div className="bg-navy-900/50 rounded-lg border border-navy-700/50 p-3 text-center">
          <p className="text-xs text-gray-500">
            No fault detection run yet. Run detection to score sensor trust.
          </p>
        </div>
      )}

      {/* Flagged sensors list */}
      {flagged.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
            Flagged Sensors ({flagged.length})
          </p>
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {flagged.map((c) => (
              <button
                key={c.sensor_id}
                onClick={() => onSensorSelect?.(c.sensor_id)}
                className="w-full text-left bg-navy-900 hover:bg-navy-700 border border-navy-700 hover:border-brand-blue rounded-lg px-2.5 py-2 transition group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-gray-200 group-hover:text-white">
                    {c.sensor_id}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded border capitalize ${CLASS_COLOUR[c.predicted_class] ?? "bg-navy-700 text-gray-300 border-navy-600"}`}>
                    {CLASS_LABEL[c.predicted_class] ?? c.predicted_class}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-500">
                    trust {c.trust_score.toFixed(2)} · conf {Math.round(c.confidence * 100)}%
                  </span>
                  {onSensorSelect && <span className="text-xs text-brand-blue opacity-0 group-hover:opacity-100">view →</span>}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Model evaluation */}
      <div className="space-y-1.5">
        <button
          onClick={toggleEval}
          className="w-full flex items-center justify-between bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-xs font-semibold text-gray-300 hover:text-white transition"
        >
          <span>📊 Model Evaluation</span>
          <span className="text-gray-500">{showEval ? "▲" : "▼"}</span>
        </button>
        {showEval && (
          <ModelEvaluationBody loading={evalLoading} modelEval={modelEval} />
        )}
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Stat({ label, value, accent }: { label: string; value: string; accent?: "red" }) {
  const colour = accent === "red" ? "text-red-300" : "text-white";
  return (
    <div>
      <div className={`text-lg font-bold ${colour}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

function ModelEvaluationBody({
  loading,
  modelEval,
}: {
  loading: boolean;
  modelEval: ModelEvaluation | null;
}) {
  if (loading && !modelEval) {
    return <div className="text-xs text-gray-500 px-1 py-2">Loading evaluation…</div>;
  }
  if (!modelEval) {
    return <div className="text-xs text-gray-500 px-1 py-2">Evaluation unavailable.</div>;
  }

  const labels = modelEval.label_order;

  return (
    <div className="space-y-2.5">
      {/* Key note */}
      <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg px-2.5 py-2">
        <p className="text-xs text-blue-200">
          {modelEval.note}
        </p>
      </div>

      {/* Per-class report */}
      <div>
        <p className="text-xs font-semibold text-gray-400 mb-1">Per-class precision / recall / F1</p>
        <pre className="text-xs text-gray-300 bg-navy-900 border border-navy-700 rounded-lg p-2 overflow-x-auto whitespace-pre">
{modelEval.classification_report}
        </pre>
      </div>

      {/* Confusion matrix */}
      <div>
        <p className="text-xs font-semibold text-gray-400 mb-1">
          Confusion matrix (rows = true class, cols = predicted)
        </p>
        <div className="overflow-x-auto">
          <table className="text-xs border-collapse">
            <thead>
              <tr>
                <th className="p-1 text-gray-500"></th>
                {labels.map((l) => (
                  <th key={l} className="p-1 text-gray-400 font-medium" title={CLASS_LABEL[l] ?? l}>
                    {l === "genuine_localised_cell" ? "GLC" : l.slice(0, 4)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {modelEval.confusion_matrix.map((row, i) => (
                <tr key={labels[i]}>
                  <td className="p-1 text-gray-400 font-medium text-right pr-2" title={CLASS_LABEL[labels[i]] ?? labels[i]}>
                    {labels[i] === "genuine_localised_cell" ? "GLC" : labels[i].slice(0, 4)}
                  </td>
                  {row.map((cell, j) => {
                    const max = Math.max(...row, 1);
                    const intensity = cell / max;
                    return (
                      <td
                        key={j}
                        className="p-1 text-center border border-navy-700/50"
                        style={{
                          backgroundColor: i === j
                            ? `rgba(34,197,94,${0.15 + intensity * 0.45})`
                            : cell > 0 ? `rgba(239,68,68,${0.1 + intensity * 0.4})` : "transparent",
                          color: cell > 0 ? "#e5e7eb" : "#64748b",
                        }}
                      >
                        {cell}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
