import { apiFetch } from "./client";

// ─── Types ────────────────────────────────────────────────────────────────────

export type ScenarioPreset =
  | "normal"
  | "broad_rain"
  | "severe_flood"
  | "localised"
  | "faulty_sensor";

export interface ScenarioInfo {
  preset: ScenarioPreset;
  label: string;
  description: string;
  total_ticks: number;
}

export interface SimulationRun {
  id: number;
  scenario: ScenarioPreset;
  seed: number;
  current_tick: number;
  total_ticks: number;
  status: "paused" | "running" | "complete" | "reset";
  created_at: string;
  updated_at: string;
}

export interface GaugeReading {
  sensor_id: string;
  sensor_type: "rainfall" | "water_level";
  lat: number;
  lng: number;
  value: number;
  unit: string;
  tick: number;
  simulated: boolean;
  is_faulty: boolean;
  fault_type: string | null;
}

export interface StormCell {
  lat: number;
  lng: number;
  peak_mm_hr: number;
  radius_deg: number;
}

export interface SimulationSnapshot {
  run_id: number;
  scenario: ScenarioPreset;
  tick: number;
  total_ticks: number;
  simulated_hour: number;
  status: string;
  gauge_readings: GaugeReading[];
  storm_cells: StormCell[];
  flood_active: boolean;
  flood_intensity: number;
  rainfall_geojson: GeoJSON.FeatureCollection;
  flood_geojson: GeoJSON.Feature | null;
  water_geojson: GeoJSON.FeatureCollection;
  simulated: boolean;
}

// ─── REST API ─────────────────────────────────────────────────────────────────

export async function listScenarios(): Promise<ScenarioInfo[]> {
  return apiFetch<ScenarioInfo[]>("/simulation/scenarios");
}

export async function createRun(scenario: ScenarioPreset, seed?: number): Promise<SimulationRun> {
  return apiFetch<SimulationRun>("/simulation/runs", {
    method: "POST",
    body: { scenario, ...(seed !== undefined ? { seed } : {}) },
  });
}

export async function listRuns(): Promise<SimulationRun[]> {
  return apiFetch<SimulationRun[]>("/simulation/runs");
}

export async function getRun(runId: number): Promise<SimulationRun> {
  return apiFetch<SimulationRun>(`/simulation/runs/${runId}`);
}

export type ControlAction = "start" | "pause" | "reset" | "step";

export async function controlRun(runId: number, action: ControlAction): Promise<SimulationRun> {
  return apiFetch<SimulationRun>(`/simulation/runs/${runId}/control`, {
    method: "POST",
    body: { action },
  });
}

export async function getSnapshot(runId: number): Promise<SimulationSnapshot> {
  return apiFetch<SimulationSnapshot>(`/simulation/runs/${runId}/snapshot`);
}

// ─── SSE stream ───────────────────────────────────────────────────────────────

/**
 * Open an SSE connection to the simulation stream endpoint.
 * Returns a cleanup function to close the EventSource.
 *
 * ``onSnapshot`` is called each time a full snapshot arrives.
 * ``onHeartbeat`` is called on lightweight heartbeat events.
 * ``onError`` is called on connection errors.
 */
export function openSimulationStream(
  runId: number,
  token: string,
  onSnapshot: (snap: SimulationSnapshot) => void,
  onHeartbeat: (data: { status: string; tick: number; total_ticks: number }) => void,
  onError?: (err: Event) => void,
): () => void {
  // SSE with Bearer auth — the standard EventSource API doesn't support custom
  // headers, so we append the token as a query param (backend reads from URL).
  // A production system should use a short-lived SSE ticket instead.
  const url = `/api/simulation/runs/${runId}/stream?token=${encodeURIComponent(token)}`;
  const es = new EventSource(url);

  es.addEventListener("snapshot", (e: MessageEvent) => {
    try {
      onSnapshot(JSON.parse(e.data) as SimulationSnapshot);
    } catch { /* ignore parse errors */ }
  });

  es.addEventListener("heartbeat", (e: MessageEvent) => {
    try {
      onHeartbeat(JSON.parse(e.data));
    } catch { /* ignore */ }
  });

  if (onError) es.onerror = onError;

  return () => es.close();
}
