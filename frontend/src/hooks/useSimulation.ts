/**
 * React hook that manages a simulation run: creates it, drives SSE,
 * exposes the latest snapshot, and provides control actions.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import {
  ScenarioPreset, ScenarioInfo, SimulationRun, SimulationSnapshot,
  listScenarios, createRun, controlRun, getSnapshot,
  openSimulationStream, ControlAction,
} from "../api/simulation";

export type SimStatus = "idle" | "loading" | "paused" | "running" | "complete" | "error";

export interface UseSimulationReturn {
  scenarios: ScenarioInfo[];
  selectedPreset: ScenarioPreset;
  setSelectedPreset: (p: ScenarioPreset) => void;
  run: SimulationRun | null;
  snapshot: SimulationSnapshot | null;
  status: SimStatus;
  error: string | null;
  /** Create a new run and open the SSE stream. */
  startNew: () => Promise<void>;
  /** Send a control action (start | pause | reset | step). */
  control: (action: ControlAction) => Promise<void>;
}

export function useSimulation(token: string | null): UseSimulationReturn {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<ScenarioPreset>("severe_flood");
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [snapshot, setSnapshot] = useState<SimulationSnapshot | null>(null);
  const [status, setStatus] = useState<SimStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  // Load scenario metadata once.
  useEffect(() => {
    listScenarios().then(setScenarios).catch(() => {});
  }, []);

  // Open / reopen SSE stream whenever run id or token changes.
  useEffect(() => {
    if (!run || !token) return;
    cleanupRef.current?.();

    const cleanup = openSimulationStream(
      run.id,
      token,
      (snap) => {
        setSnapshot(snap);
        setStatus(snap.status === "running" ? "running" : snap.status === "complete" ? "complete" : "paused");
      },
      (hb) => {
        setRun(prev => prev ? { ...prev, current_tick: hb.tick, status: hb.status as SimulationRun["status"] } : prev);
        setStatus(hb.status === "running" ? "running" : hb.status === "complete" ? "complete" : "paused");
      },
      () => setError("Stream connection lost. Reload to reconnect."),
    );
    cleanupRef.current = cleanup;
    return cleanup;
  }, [run?.id, token]); // eslint-disable-line react-hooks/exhaustive-deps

  const startNew = useCallback(async () => {
    if (!token) { setError("Not authenticated"); return; }
    setStatus("loading");
    setError(null);
    try {
      cleanupRef.current?.();
      const newRun = await createRun(selectedPreset);
      const snap = await getSnapshot(newRun.id);
      setRun(newRun);
      setSnapshot(snap);
      setStatus("paused");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create simulation");
      setStatus("error");
    }
  }, [token, selectedPreset]);

  const control = useCallback(async (action: ControlAction) => {
    if (!run) return;
    try {
      const updated = await controlRun(run.id, action);
      setRun(updated);
      if (action === "reset") {
        const snap = await getSnapshot(run.id);
        setSnapshot(snap);
        setStatus("paused");
      } else {
        setStatus(updated.status === "running" ? "running" : updated.status === "complete" ? "complete" : "paused");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Control action failed");
    }
  }, [run]);

  return { scenarios, selectedPreset, setSelectedPreset, run, snapshot, status, error, startNew, control };
}
