/**
 * React hook that manages Stage 5 sensor fault-detection state for the active
 * simulation run.
 *
 * Responsibilities:
 *   - Run fault classification at the current tick (POST /classify).
 *   - Hold the resulting trust map + annotated sensor GeoJSON for the map.
 *   - Lazily load the model evaluation (per-class metrics) on first request.
 *   - Clear state when the run changes so stale trust data is never shown.
 *
 * The hook is intentionally decoupled from the simulation hook: the caller
 * passes the active run id / tick when invoking ``classify``.
 */
import { useState, useEffect, useCallback } from "react";
import {
  SensorTrustMap,
  ModelEvaluation,
  classifySensors,
  getSensorTrustGeo,
  getTrustScores,
  getModelEvaluation,
} from "../api/sensors";

export interface UseSensorTrustReturn {
  /** Latest classified trust map (from classify or reload). */
  trustMap: SensorTrustMap | null;
  /** Sensor GeoJSON annotated with trust score / fault class for the map. */
  trustGeojson: GeoJSON.FeatureCollection | null;
  /** Per-class precision/recall/F1 + confusion matrix (loaded on demand). */
  modelEval: ModelEvaluation | null;
  /** True while a classification request is in flight. */
  classifying: boolean;
  /** True while trust/geojson is being (re)loaded (e.g. on reconnect). */
  loading: boolean;
  /** True while the model evaluation is being fetched. */
  evalLoading: boolean;
  error: string | null;
  /** Run fault detection at the given tick and persist the result. */
  classify: (runId: number, tick: number) => Promise<void>;
  /** Load the most recently persisted trust scores for a run (no recompute). */
  loadTrust: (runId: number) => Promise<void>;
  /** Load the model evaluation report (cached in state after first call). */
  loadModelEvaluation: () => Promise<void>;
  /** Drop all trust state (e.g. when the run is reset / recreated). */
  clear: () => void;
}

export function useSensorTrust(): UseSensorTrustReturn {
  const [trustMap, setTrustMap] = useState<SensorTrustMap | null>(null);
  const [trustGeojson, setTrustGeojson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [modelEval, setModelEval] = useState<ModelEvaluation | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classify = useCallback(async (runId: number, tick: number) => {
    setClassifying(true);
    setError(null);
    try {
      const map = await classifySensors(runId, tick);
      setTrustMap(map);
      // Refresh the annotated GeoJSON so the map reflects the new scores.
      const geo = await getSensorTrustGeo(runId);
      setTrustGeojson(geo);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Fault detection failed");
    } finally {
      setClassifying(false);
    }
  }, []);

  const loadTrust = useCallback(async (runId: number) => {
    setLoading(true);
    setError(null);
    try {
      const [map, geo] = await Promise.all([
        getTrustScores(runId),
        getSensorTrustGeo(runId),
      ]);
      setTrustMap(map);
      setTrustGeojson(geo);
    } catch (e: unknown) {
      // 404 is expected before any classification has run — treat as "no data".
      const msg = e instanceof Error ? e.message : "Failed to load trust scores";
      if (!/not found|no trust scores/i.test(msg)) {
        setError(msg);
      }
      setTrustMap(null);
      setTrustGeojson(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadModelEvaluation = useCallback(async () => {
    if (modelEval || evalLoading) return;
    setEvalLoading(true);
    try {
      const ev = await getModelEvaluation();
      setModelEval(ev);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load model evaluation");
    } finally {
      setEvalLoading(false);
    }
  }, [modelEval, evalLoading]);

  const clear = useCallback(() => {
    setTrustMap(null);
    setTrustGeojson(null);
    setError(null);
  }, []);

  // Reset state on unmount to avoid leaking trust data across sessions.
  useEffect(() => () => clear(), [clear]);

  return {
    trustMap,
    trustGeojson,
    modelEval,
    classifying,
    loading,
    evalLoading,
    error,
    classify,
    loadTrust,
    loadModelEvaluation,
    clear,
  };
}
