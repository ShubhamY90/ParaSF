# Stage 04: Weather & Flood Simulation

Status: Completed ✅

## Summary of Implementation

### Backend

- **Simulation engine** (`app/services/simulation.py`):
  - Fully deterministic from `settings.simulation_seed`; same (preset, seed) always produces the same output — `snapshot(tick)` is a pure function.
  - Five scenario presets: `normal`, `broad_rain`, `severe_flood`, `localised`, `faulty_sensor`.
  - `WeatherSimulator` class: generates a storm-cell path across the district, interpolates cell position per tick, computes per-gauge rainfall (Gaussian decay from storm centre + background noise) and water-level readings.
  - `SEVERE_FLOOD` activates a flood polygon that expands from a river-corridor buffer as intensity rises (ticks 20–90% of total), then recedes.
  - `FAULTY_SENSOR` injects a +180 mm/hr spike into one randomly-chosen rainfall gauge between ticks 30–50% of total.
  - `LOCALISED` uses a narrow radius (0.04°) storm cell so only nearby gauges read high — most stay at background levels.
  - GeoJSON builders: `rainfall_intensity_geojson`, `flood_area_geojson`, `water_levels_geojson` — all features carry `simulated: true` and an explanatory `note` property.

- **ORM model** (`app/models/simulation.py`): `SimulationRun` — scenario, seed, `current_tick`, `total_ticks`, `status` (paused/running/complete).

- **Pydantic schemas** (`app/schemas/simulation.py`): `ScenarioInfo`, `SimulationRunOut`, `SimulationRunCreate`, `TickControl`, `SnapshotOut`.

- **API endpoints** (`app/api/simulation.py`) — all under `/api/simulation`:
  - `GET /scenarios` — catalogue of 5 presets with labels, descriptions, tick counts.
  - `POST /runs` — create a run (insurer/admin only).
  - `GET /runs` — list runs (all authenticated roles).
  - `GET /runs/{id}` — get run metadata.
  - `POST /runs/{id}/control` — `start | pause | reset | step` (insurer/admin only).
  - `GET /runs/{id}/snapshot` — full snapshot at current tick with GeoJSON overlays.
  - `GET /runs/{id}/stream` — SSE endpoint; advances tick at 1.5 s/tick while running; heartbeat when paused/complete; accepts JWT as Bearer header or `?token=` query param for browser `EventSource` compatibility.

- **Tests** (`tests/test_stage4.py`) — 14 tests, all passing:
  - Scenarios catalogue lists all 5 presets.
  - Insurer can create a run; farmer cannot.
  - Farmer can list/read runs.
  - `start → running`, `pause → paused`, `step → tick+1`, `reset → tick 0 + paused`.
  - Invalid action returns 400.
  - Snapshot has correct structure and `simulated: true`.
  - Gauge readings differ between tick 0 and tick 12 (simulation advances).
  - Same seed produces identical snapshots (reproducibility).
  - `SEVERE_FLOOD`: flood polygon present in mid-scenario, ring closed, `simulated: true`, `note` contains "not a verified".
  - `NORMAL`: no flood active at any tick.
  - `FAULTY_SENSOR`: spike injected with `is_faulty: true`, `fault_type: "spike"`, value > 100.
  - `LOCALISED`: fewer than half the gauges read > 30 mm/hr at peak tick.
  - Rainfall GeoJSON carries `simulated: true` on collection and all features.

### Frontend

- **API client** (`src/api/simulation.ts`) — typed wrappers for all 6 REST endpoints plus `openSimulationStream()` which opens an `EventSource` and routes `snapshot` / `heartbeat` SSE events.

- **`useSimulation` hook** (`src/hooks/useSimulation.ts`) — manages scenario selection, run lifecycle, SSE connection, snapshot state, and control actions. Cleans up the `EventSource` on unmount or run change.

- **`SimulationControls` panel** (`src/features/simulation/SimulationControls.tsx`):
  - Scenario dropdown with description text.
  - New Sim / Play / Pause / Step / Reset buttons; disabled states match run status.
  - Tick progress bar (0 → total_ticks − 1, percentage label).
  - Flood-event alert badge (animated pulse) when `flood_active`.
  - Storm-cell active badge when storm cells are present.
  - Live gauge-readings table: sensor ID, type icon, value with unit; faulty gauges highlighted red with ⚠ marker.
  - `Simulated demo data` disclaimer on the table.

- **`MapView` extensions** (`src/features/map/MapView.tsx`):
  - New `weatherSnapshot` prop; when provided, two new GeoJSON sources (`rainfall-overlay`, `flood-overlay`) are updated via `setData` on every snapshot change.
  - `rainfall-circles` layer: MapLibre circle layer with radius and colour interpolated from `rainfall_mm_hr` (light blue → deep red).
  - `flood-fill` + `flood-line` layers: red semi-transparent fill with dashed outline.
  - Two new layer toggles: "Rainfall intensity (sim)" and "Flood area (sim)".
  - Legend updated with both new overlay entries.
  - `LayerVisibility` interface extended with `rainfall_overlay` and `flood_overlay`.

- **`OperationsMapPage`** updated: imports `useSimulation`, passes `weatherSnapshot` to `MapView`, renders `SimulationControls` in a collapsible right sidebar. Header shows a live "🌊 Flood Event" badge when active.

- **Dashboard cleanup**: "Weather Events (Stage 4)" card removed from both insurer and farmer upcoming sections (now active via the Operations Map).

## Acceptance criteria — all met

- [x] A user can start and reset a scenario.
- [x] Gauge readings change over simulation time.
- [x] A flood scenario changes the affected-area overlay on the map.
- [x] The same seed reproduces the same scenario.
- [x] The frontend clearly identifies simulated weather data (labels on all GeoJSON features, notes on the controls panel).

## Next: Stage 5 — Sensor Fault Detection and Trust Scoring
