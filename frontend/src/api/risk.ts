import { apiFetch } from "./client";

// ─── Types ────────────────────────────────────────────────────────────────────

export type RiskCategory =
  | "low"
  | "moderate"
  | "high"
  | "extreme"
  | "insufficient_evidence";

export interface FarmRiskEstimate {
  farm_id: string;
  tick: number;
  run_id: number;
  estimated_rainfall_mm: number | null;
  uncertainty_mm: number | null;
  lower_ci: number | null;
  upper_ci: number | null;
  risk_category: RiskCategory;
  flood_risk_score: number | null;
  supporting_sensors: string[];
  evidence_note: string;
  model_version: string;
  simulated: boolean;
}

export interface RiskSummary {
  total_farms: number;
  low: number;
  moderate: number;
  high: number;
  extreme: number;
  insufficient_evidence: number;
}

export interface RiskLayer {
  run_id: number;
  tick: number;
  farms: FarmRiskEstimate[];
  summary: RiskSummary;
  simulated: boolean;
}

// ─── REST API ─────────────────────────────────────────────────────────────────

/** Run GP spatial estimation for all farms at the given tick and persist. */
export async function assessRisk(runId: number, tick?: number): Promise<RiskLayer> {
  return apiFetch<RiskLayer>("/risk/assess", {
    method: "POST",
    body: { run_id: runId, ...(tick !== undefined ? { tick } : {}) },
  });
}

/** Latest persisted risk layer for a run (all farms). */
export async function getRiskLayer(runId: number): Promise<RiskLayer> {
  return apiFetch<RiskLayer>(`/risk/${runId}`);
}

/** Per-tick risk estimate history for a single farm. */
export async function getFarmRiskHistory(
  runId: number,
  farmId: string,
): Promise<FarmRiskEstimate[]> {
  return apiFetch<FarmRiskEstimate[]>(`/risk/${runId}/${encodeURIComponent(farmId)}`);
}

/** GeoJSON FeatureCollection of farms coloured by risk category. */
export async function getRiskGeoJSON(runId: number): Promise<GeoJSON.FeatureCollection> {
  return apiFetch<GeoJSON.FeatureCollection>(`/risk/geojson/${runId}`);
}

