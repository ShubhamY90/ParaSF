import { apiFetch } from "./client";

// ─── Types ────────────────────────────────────────────────────────────────────

/** The six sensor-condition classes recognised by the fault-detection model. */
export type FaultClass =
  | "normal"
  | "spike"
  | "stuck"
  | "drift"
  | "dead"
  | "genuine_localised_cell";

export interface SensorClassification {
  sensor_id: string;
  sensor_type: "rainfall" | "water_level";
  predicted_class: FaultClass;
  confidence: number;
  trust_score: number;
  class_probabilities: Record<string, number>;
  is_flagged: boolean;
  investigation_note: string;
  simulated: boolean;
}

/** Response from POST /classify and GET /trust/{run_id}. */
export interface SensorTrustMap {
  run_id: number;
  tick: number;
  scores: Record<string, number>;
  flagged: string[];
  classifications: SensorClassification[];
  simulated: boolean;
}

/** Per-tick persisted trust record (sensor history). */
export interface SensorTrustScoreRecord {
  id: number;
  run_id: number;
  sensor_id: string;
  sensor_type: string;
  tick: number;
  raw_value: number;
  unit: string;
  predicted_class: FaultClass;
  confidence: number;
  trust_score: number;
  is_flagged: boolean;
  investigation_note: string;
  created_at: string;
}

export interface ModelEvaluation {
  classes: string[];
  classification_report: string;
  confusion_matrix: number[][];
  label_order: string[];
  note: string;
}

// ─── REST API ─────────────────────────────────────────────────────────────────

/** Per-class precision/recall/F1 + confusion matrix for the fault model. */
export async function getModelEvaluation(): Promise<ModelEvaluation> {
  return apiFetch<ModelEvaluation>("/sensors/model/evaluation");
}

/**
 * Run fault classification on every rainfall gauge at the given tick and
 * persist the results. Idempotent per (run_id, tick).
 */
export async function classifySensors(
  runId: number,
  tick?: number,
): Promise<SensorTrustMap> {
  return apiFetch<SensorTrustMap>("/sensors/classify", {
    method: "POST",
    body: { run_id: runId, ...(tick !== undefined ? { tick } : {}) },
  });
}

/** Most recently persisted trust scores for a run (latest tick with data). */
export async function getTrustScores(runId: number): Promise<SensorTrustMap> {
  return apiFetch<SensorTrustMap>(`/sensors/trust/${runId}`);
}

/** Per-tick trust-score history for a single sensor. */
export async function getSensorHistory(
  runId: number,
  sensorId: string,
): Promise<SensorTrustScoreRecord[]> {
  return apiFetch<SensorTrustScoreRecord[]>(
    `/sensors/trust/${runId}/${encodeURIComponent(sensorId)}`,
  );
}

/**
 * GeoJSON FeatureCollection of all sensors annotated with the latest trust
 * score and fault class for the run. Unclassified sensors fall back to
 * trust_score=1.0 / predicted_class="normal".
 */
export async function getSensorTrustGeo(
  runId: number,
): Promise<GeoJSON.FeatureCollection> {
  return apiFetch<GeoJSON.FeatureCollection>(`/sensors/geojson/${runId}`);
}
