/**
 * Stage 5 — Sensor investigation panel.
 *
 * Shown when an insurer clicks a sensor marker on the operations map. Displays
 * the classification result, trust score, full class-probability breakdown, the
 * preserved raw reading, and the per-tick trust history for that sensor so the
 * reason it was flagged is fully auditable.
 *
 * Design rules reflected here:
 *   - The original reading is always shown alongside the classification — a flag
 *     is advisory, it does not overwrite the measurement.
 *   - ``genuine_localised_cell`` is rendered as a valid weather condition, not a
 *     fault.
 */
import { useEffect, useState } from "react";
import type { SensorClassification, SensorTrustScoreRecord } from "../../api/sensors";
import { getSensorHistory } from "../../api/sensors";

const CLASS_LABEL: Record<string, string> = {
  normal: "Normal",
  spike: "Spike fault",
  stuck: "Stuck fault",
  drift: "Drift fault",
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
  sensor: SensorClassification | null;
  /** Raw reading value/unit at the classified tick (from the live snapshot). */
  rawValue: number | null;
  unit: string | null;
  onClose: () => void;
}

export default function SensorInvestigationPanel({ runId, sensor, rawValue, unit, onClose }: Props) {
  const [history, setHistory] = useState<SensorTrustScoreRecord[] | null>(null);
  const [histLoading, setHistLoading] = useState(false);

  // Load per-tick history when a sensor is opened.
  useEffect(() => {
    setHistory(null);
    if (!runId || !sensor) return;
    let cancelled = false;
    setHistLoading(true);
    getSensorHistory(runId, sensor.sensor_id)
      .then((rows) => { if (!cancelled) setHistory(rows); })
      .catch(() => { if (!cancelled) setHistory([]); })
      .finally(() => { if (!cancelled) setHistLoading(false); });
    return () => { cancelled = true; };
  }, [runId, sensor?.sensor_id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!sensor) return null;

  const probaEntries = Object.entries(sensor.class_probabilities)
    .sort((a, b) => b[1] - a[1]);

  return (
    <div className="absolute top-12 right-2 z-20 w-80 bg-navy-800/95 border border-navy-600 rounded-xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-navy-600 bg-navy-700/60">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white font-mono">{sensor.sensor_id}</span>
          <span className="text-xs text-gray-400 capitalize">{sensor.sensor_type.replace("_", " ")}</span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition text-lg leading-none">×</button>
      </div>

      <div className="p-4 space-y-3 max-h-[72vh] overflow-y-auto text-sm">
        {/* Classification + trust */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Classification</span>
          <span className={`text-xs px-2 py-0.5 rounded-full border ${CLASS_COLOUR[sensor.predicted_class] ?? "bg-navy-700 text-gray-300 border-navy-600"}`}>
            {CLASS_LABEL[sensor.predicted_class] ?? sensor.predicted_class}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400">Trust score</span>
          <TrustBar value={sensor.trust_score} flagged={sensor.is_flagged} />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400">Confidence</span>
          <span className="text-white">{Math.round(sensor.confidence * 100)}%</span>
        </div>

        {/* Raw reading — always preserved */}
        <div className="border-t border-navy-600 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Raw reading</span>
            <span className="text-white font-mono">
              {rawValue != null ? `${rawValue.toFixed(1)} ${unit ?? ""}` : "—"}
            </span>
          </div>
          <p className="text-xs text-gray-600 italic mt-0.5">
            Original reading preserved — the classification is advisory and does not overwrite it.
          </p>
        </div>

        {/* Investigation note */}
        <div className="border-t border-navy-600 pt-2">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
            Investigation note
          </p>
          <p className="text-xs text-gray-200 leading-relaxed">{sensor.investigation_note}</p>
        </div>

        {/* Class probability breakdown */}
        {probaEntries.length > 0 && (
          <div className="border-t border-navy-600 pt-2">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
              Class probabilities
            </p>
            <div className="space-y-1">
              {probaEntries.map(([cls, p]) => (
                <div key={cls} className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 w-32 truncate" title={CLASS_LABEL[cls] ?? cls}>
                    {CLASS_LABEL[cls] ?? cls}
                  </span>
                  <div className="flex-1 h-2 bg-navy-900 rounded-full overflow-hidden">
                    <div
                      className={`h-2 rounded-full ${cls === sensor.predicted_class ? "bg-brand-blue" : "bg-navy-600"}`}
                      style={{ width: `${Math.round(p * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-300 w-9 text-right">{(p * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Per-tick history (audit trail) */}
        <div className="border-t border-navy-600 pt-2">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">
            Trust history (this run)
          </p>
          {histLoading && <p className="text-xs text-gray-500">Loading…</p>}
          {!histLoading && history && history.length === 0 && (
            <p className="text-xs text-gray-600 italic">
              Only the current tick has been classified so far. Run detection at other ticks to build the history.
            </p>
          )}
          {!histLoading && history && history.length > 0 && (
            <div className="bg-navy-900 rounded-lg border border-navy-700 overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-navy-700 text-gray-500">
                    <th className="px-2 py-1.5 text-left font-medium">Tick</th>
                    <th className="px-2 py-1.5 text-right font-medium">Raw</th>
                    <th className="px-2 py-1.5 text-right font-medium">Trust</th>
                    <th className="px-2 py-1.5 text-left font-medium">Class</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((r) => (
                    <tr key={r.id} className={`border-b border-navy-800 ${r.is_flagged ? "bg-red-900/15" : ""}`}>
                      <td className="px-2 py-1 text-gray-300">{r.tick}</td>
                      <td className="px-2 py-1 text-right font-mono text-gray-300">
                        {r.raw_value.toFixed(1)}
                      </td>
                      <td className="px-2 py-1 text-right font-mono text-gray-300">{r.trust_score.toFixed(2)}</td>
                      <td className="px-2 py-1 text-gray-400 capitalize">
                        {r.predicted_class === "genuine_localised_cell" ? "GLC" : r.predicted_class}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <p className="text-xs text-gray-600 italic pt-1">
          Simulated classification · model trained on synthetic labelled data.
        </p>
      </div>
    </div>
  );
}

// ─── Trust bar ────────────────────────────────────────────────────────────────

function TrustBar({ value, flagged }: { value: number; flagged: boolean }) {
  const pct = Math.round(value * 100);
  const colour =
    value >= 0.7 ? "bg-green-500" :
    value >= 0.4 ? "bg-amber-500" :
    "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      {flagged && <span className="text-xs text-red-400">⚠</span>}
      <div className="w-20 h-2 bg-navy-900 rounded-full overflow-hidden">
        <div className={`h-2 rounded-full ${colour}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-white text-xs font-mono w-9 text-right">{value.toFixed(2)}</span>
    </div>
  );
}
