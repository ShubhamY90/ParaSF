/**
 * Stage 3 / 4 / 5 — Operations Map (insurer / auditor / admin)
 *
 * Shows all in-district farms with their boundaries, sensor locations,
 * rivers, and the demo district outline.
 *
 * Stage 4 adds: simulation control sidebar, live rainfall-intensity overlay,
 * and flood-affected-area overlay updated tick by tick.
 *
 * Stage 5 adds: sensor fault detection & trust scoring. Rainfall gauges are
 * recoloured by trust score, flagged sensors are highlighted, and clicking a
 * sensor opens an investigation panel with the classification, probabilities,
 * and per-tick audit history. An outlier is suspicious, not automatically
 * false — the original reading is always preserved.
 */
import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import MapView from "../map/MapView";
import SimulationControls from "../simulation/SimulationControls";
import SensorInvestigationPanel from "../sensors/SensorInvestigationPanel";
import { useSimulation } from "../../hooks/useSimulation";
import { useAuth } from "../../hooks/useAuth";
import { useSensorTrust } from "../../hooks/useSensorTrust";

export default function OperationsMapPage() {
  const { token } = useAuth();
  const sim = useSimulation(token);
  const sensorTrust = useSensorTrust();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedSensorId, setSelectedSensorId] = useState<string | null>(null);

  // Clear sensor-trust state + selection whenever the active run changes so we
  // never show stale trust data from a previous simulation.
  useEffect(() => {
    sensorTrust.clear();
    setSelectedSensorId(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sim.run?.id]);

  const handleSensorClick = useCallback((sensorId: string) => {
    setSelectedSensorId(sensorId);
  }, []);

  const handleSensorSelect = useCallback((sensorId: string) => {
    setSelectedSensorId(sensorId);
  }, []);

  // Resolve the selected sensor's classification + latest raw reading.
  const selectedClassification =
    selectedSensorId && sensorTrust.trustMap
      ? sensorTrust.trustMap.classifications.find((c) => c.sensor_id === selectedSensorId) ?? null
      : null;
  const selectedReading =
    selectedSensorId && sim.snapshot
      ? sim.snapshot.gauge_readings.find((r) => r.sensor_id === selectedSensorId) ?? null
      : null;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Page header */}
      <div className="flex items-center justify-between px-6 py-3 bg-navy-800 border-b border-navy-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/insurer" className="text-sm text-brand-blue hover:underline">← Dashboard</Link>
          <span className="text-gray-600">|</span>
          <h1 className="text-white font-semibold text-sm">Operations Map</h1>
          <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/50 text-green-300 border border-green-700">
            Stages 3–5 Active
          </span>
          {sim.snapshot?.flood_active && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/60 text-red-300 border border-red-700 animate-pulse">
              🌊 Flood Event
            </span>
          )}
          {sensorTrust.trustMap && sensorTrust.trustMap.flagged.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/60 text-red-300 border border-red-700">
              ⚠ {sensorTrust.trustMap.flagged.length} Sensor{sensorTrust.trustMap.flagged.length > 1 ? "s" : ""} Flagged
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <p className="text-xs text-gray-500 hidden sm:block">
            Kashi-Ganga Demo District · Basemap: ESRI World Imagery
          </p>
          <button
            onClick={() => setSidebarOpen(o => !o)}
            className="text-xs bg-navy-700 text-gray-300 hover:text-white px-3 py-1.5 rounded-lg border border-navy-600 transition"
          >
            {sidebarOpen ? "Hide Sim ◀" : "Show Sim ▶"}
          </button>
        </div>
      </div>

      {/* Main content: map + optional simulation sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="flex-1 overflow-hidden">
          <MapView
            height="100%"
            weatherSnapshot={sim.snapshot}
            sensorTrust={sensorTrust.trustGeojson}
            onSensorClick={handleSensorClick}
            layerVisibility={{
              rainfall_overlay: !!sim.snapshot,
              flood_overlay: !!sim.snapshot,
            }}
          />
        </div>

        {/* Simulation controls sidebar (includes Stage 5 sensor health) */}
        {sidebarOpen && (
          <SimulationControls
            sim={sim}
            collapsed={!sidebarOpen}
            onToggleCollapse={() => setSidebarOpen(o => !o)}
            sensorTrust={sensorTrust}
            onSensorSelect={handleSensorSelect}
          />
        )}
      </div>

      {/* Stage 5 — sensor investigation panel */}
      {selectedSensorId && (
        <SensorInvestigationPanel
          runId={sim.run?.id ?? null}
          sensor={selectedClassification}
          rawValue={selectedReading?.value ?? null}
          unit={selectedReading?.unit ?? null}
          onClose={() => setSelectedSensorId(null)}
        />
      )}
    </div>
  );
}
