/**
 * React hook that manages Stage 6 farm-level risk state.
 *
 * Responsibilities:
 *   - Run GP spatial estimation (POST /risk/assess).
 *   - Hold the resulting risk layer + annotated farm GeoJSON.
 *   - Load previously persisted risk on reconnect.
 *   - Clear state when the simulation run changes.
 */
import { useState, useCallback, useEffect } from "react";
import {
  RiskLayer,
  assessRisk,
  getRiskLayer,
  getRiskGeoJSON,
} from "../api/risk";

export interface UseRiskReturn {
  riskLayer: RiskLayer | null;
  riskGeojson: GeoJSON.FeatureCollection | null;
  assessing: boolean;
  loading: boolean;
  error: string | null;
  assess: (runId: number, tick: number) => Promise<void>;
  loadRisk: (runId: number) => Promise<void>;
  clear: () => void;
}

export function useRisk(): UseRiskReturn {
  const [riskLayer,  setRiskLayer]  = useState<RiskLayer | null>(null);
  const [riskGeojson, setRiskGeojson] = useState<GeoJSON.FeatureCollection | null>(null);
  const [assessing,  setAssessing]  = useState(false);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  const assess = useCallback(async (runId: number, tick: number) => {
    setAssessing(true);
    setError(null);
    try {
      const layer = await assessRisk(runId, tick);
      setRiskLayer(layer);
      const geo = await getRiskGeoJSON(runId);
      setRiskGeojson(geo);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Risk assessment failed");
    } finally {
      setAssessing(false);
    }
  }, []);

  const loadRisk = useCallback(async (runId: number) => {
    setLoading(true);
    setError(null);
    try {
      const [layer, geo] = await Promise.all([
        getRiskLayer(runId),
        getRiskGeoJSON(runId),
      ]);
      setRiskLayer(layer);
      setRiskGeojson(geo);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to load risk layer";
      if (!/not found/i.test(msg)) setError(msg);
      setRiskLayer(null);
      setRiskGeojson(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setRiskLayer(null);
    setRiskGeojson(null);
    setError(null);
  }, []);

  useEffect(() => () => clear(), [clear]);

  return { riskLayer, riskGeojson, assessing, loading, error, assess, loadRisk, clear };
}

