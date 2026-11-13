/**
 * Simulation control panel: scenario selector, play/pause/reset/step,
 * tick progress bar, and a live gauge-reading summary table.
 */
import { ScenarioInfo, SimulationRun, SimulationSnapshot, GaugeReading } from "../../api/simulation";
import { UseSimulationReturn } from "../../hooks/useSimulation";
import type { UseSensorTrustReturn } from "../../hooks/useSensorTrust";
import SensorTrustPanel from "../sensors/SensorTrustPanel";

interface Props {
  sim: UseSimulationReturn;
  /** Whether the panel is collapsed (map-only view). */
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  /** Stage 5 — sensor fault-detection state. When provided, a Sensor Health
   *  control section is rendered at the bottom of the sidebar. */
  sensorTrust?: UseSensorTrustReturn;
  onSensorSelect?: (sensorId: string) => void;
}

export default function SimulationControls({ sim, collapsed, onToggleCollapse, sensorTrust, onSensorSelect }: Props) {
  const { scenarios, selectedPreset, setSelectedPreset, run, snapshot, status, error, startNew, control } = sim;

  const pct = run ? Math.round((run.current_tick / Math.max(run.total_ticks - 1, 1)) * 100) : 0;
  const isRunning = status === "running";
  const isComplete = status === "complete";

  return (
    <div className="flex flex-col bg-navy-800 border-l border-navy-700 w-80 flex-shrink-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-navy-700 bg-navy-700/50">
        <div className="flex items-center gap-2">
          <span className="text-base">🌪️</span>
          <span className="text-sm font-semibold text-white">Simulation</span>
          <StatusPill status={status} />
        </div>
        {onToggleCollapse && (
          <button onClick={onToggleCollapse} className="text-gray-400 hover:text-white text-sm transition">
            {collapsed ? "▶" : "◀"}
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Error */}
        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-3 py-2 text-xs">{error}</div>
        )}

        {/* Scenario selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Scenario</label>
          <select
            className="w-full bg-navy-900 border border-navy-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-brand-blue"
            value={selectedPreset}
            onChange={e => setSelectedPreset(e.target.value as any)}
            disabled={isRunning}
          >
            {scenarios.map(s => (
              <option key={s.preset} value={s.preset}>{s.label}</option>
            ))}
          </select>
          {scenarios.find(s => s.preset === selectedPreset) && (
            <p className="text-xs text-gray-500">
              {scenarios.find(s => s.preset === selectedPreset)!.description}
            </p>
          )}
        </div>

        {/* Controls */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={startNew}
            disabled={status === "loading" || isRunning}
            className="flex-1 bg-brand-blue text-white text-xs font-semibold px-3 py-2 rounded-lg hover:opacity-90 disabled:opacity-40 transition"
          >
            {run ? "New Sim" : "Start Sim"}
          </button>
          {run && (
            <>
              <button
                onClick={() => control(isRunning ? "pause" : "start")}
                disabled={isComplete || status === "loading"}
                className="flex-1 bg-navy-700 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-navy-600 disabled:opacity-40 transition"
              >
                {isRunning ? "⏸ Pause" : "▶ Play"}
              </button>
              <button
                onClick={() => control("step")}
                disabled={isRunning || isComplete}
                className="bg-navy-700 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-navy-600 disabled:opacity-40 transition"
              >
                ⏭ Step
              </button>
              <button
                onClick={() => control("reset")}
                className="bg-navy-700 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-navy-600 transition"
              >
                ↺ Reset
              </button>
            </>
          )}
        </div>

        {/* Progress bar */}
        {run && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Hour {run.current_tick} of {run.total_ticks - 1}</span>
              <span>{pct}%</span>
            </div>
            <div className="w-full bg-navy-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full bg-brand-blue transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}

        {/* Flood alert */}
        {snapshot?.flood_active && (
          <div className="bg-red-900/40 border border-red-700 rounded-lg px-3 py-2 flex items-center gap-2">
            <span className="text-lg">🌊</span>
            <div>
              <p className="text-red-300 text-xs font-semibold">Flood Event Active</p>
              <p className="text-red-400 text-xs">
                Intensity: {Math.round(snapshot.flood_intensity * 100)}% ·{" "}
                <span className="italic">Simulated overlay</span>
              </p>
            </div>
          </div>
        )}

        {/* Storm cell */}
        {snapshot && snapshot.storm_cells.length > 0 && (
          <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg px-3 py-2 flex items-center gap-2">
            <span className="text-lg">⛈</span>
            <div>
              <p className="text-yellow-300 text-xs font-semibold">Storm Cell Active</p>
              <p className="text-yellow-500 text-xs">
                Peak {snapshot.storm_cells[0].peak_mm_hr.toFixed(1)} mm/hr ·{" "}
                <span className="italic">Simulated</span>
              </p>
            </div>
          </div>
        )}

        {/* Gauge readings table */}
        {snapshot && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Gauge Readings — Tick {snapshot.tick}
            </p>
            <div className="bg-navy-900 rounded-lg overflow-hidden border border-navy-700">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-navy-700 text-gray-500">
                    <th className="px-2 py-1.5 text-left font-medium">ID</th>
                    <th className="px-2 py-1.5 text-left font-medium">Type</th>
                    <th className="px-2 py-1.5 text-right font-medium">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshot.gauge_readings.map(r => (
                    <GaugeRow key={r.sensor_id} reading={r} />
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-600 italic">All readings are simulated demo data.</p>
          </div>
        )}

        {/* Stage 5 — Sensor fault detection & trust scoring */}
        {sensorTrust && (
          <SensorTrustPanel
            runId={run?.id ?? null}
            tick={run?.current_tick ?? 0}
            sensorTrust={sensorTrust}
            onSensorSelect={onSensorSelect}
          />
        )}
      </div>
    </div>
  );
}

function GaugeRow({ reading }: { reading: GaugeReading }) {
  const isRain = reading.sensor_type === "rainfall";
  const high = isRain ? reading.value > 50 : reading.value > 230;
  return (
    <tr className={`border-b border-navy-800 ${reading.is_faulty ? "bg-red-900/20" : ""}`}>
      <td className="px-2 py-1 font-mono text-gray-300">
        {reading.sensor_id}
        {reading.is_faulty && <span className="ml-1 text-red-400">⚠</span>}
      </td>
      <td className="px-2 py-1 text-gray-500 capitalize">
        {isRain ? "🌧" : "💧"} {reading.sensor_type.replace("_", " ")}
      </td>
      <td className={`px-2 py-1 text-right font-mono ${high ? "text-red-400 font-semibold" : "text-gray-300"}`}>
        {reading.value.toFixed(1)} {reading.unit}
      </td>
    </tr>
  );
}

function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    idle:     "bg-navy-700 text-gray-400",
    loading:  "bg-yellow-900/50 text-yellow-300",
    paused:   "bg-navy-700 text-gray-300",
    running:  "bg-green-900/50 text-green-300 animate-pulse",
    complete: "bg-blue-900/50 text-blue-300",
    error:    "bg-red-900/50 text-red-300",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border border-transparent capitalize ${styles[status] ?? styles.idle}`}>
      {status}
    </span>
  );
}
