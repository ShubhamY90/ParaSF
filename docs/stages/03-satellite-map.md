# Stage 03: Satellite Map and Geographic Monitoring

Status: Completed ✅

## Summary of Implementation

### Backend

- **Geospatial service** (`app/services/geo.py`):
  - Demo district: *Kashi-Ganga Demo District*, centred on Varanasi (25.335 N, 82.965 E).
  - District boundary polygon (8-node irregular ring, closed, clearly labelled simulated).
  - Bounding box (`DEMO_DISTRICT_BBOX`) used for fast in-district filtering of farms.
  - `generate_sensors(seed)` — deterministic from `settings.simulation_seed`; produces 12 rainfall gauges (random within bbox) and 8 water-level gauges (positioned along the river path).
  - `generate_water_features()` — the Ganga river as a LineString (8 nodes, south-easterly reach through Varanasi) plus 3 simulated water bodies as rectangular polygons.
  - `farm_geometry()` — builds a closed square polygon from a farm centroid + area when no stored `boundary_geojson` exists; uses stored geometry verbatim when present; returns `None` for farms with no coordinates (they are omitted from the map layer).
  - `in_district()` — bounding-box point test for insurer district filtering.

- **GeoJSON schemas** (`app/schemas/geo.py`):
  - `FarmMapDetail` — rich farm record for the detail panel with explicit `None` placeholders for `estimated_rainfall_mm`, `risk_category`, and `claim_status` (Stages 6 and 8), plus `stage_notes` strings.
  - `CropBrief`, `PolicyBrief` — compact summaries for the panel.

- **API endpoints** (`app/api/geo.py`) — all under `/api/geo`:
  - `GET /district` — demo district boundary as a single GeoJSON Feature.
  - `GET /sensors` — 20 gauge markers (12 rainfall + 8 water-level) as a FeatureCollection.
  - `GET /water` — river + 3 water bodies as a FeatureCollection.
  - `GET /farms` — role-aware farm polygons:
    - **Farmer**: own farms only, labelled "Your farm", `is_own: true`.
    - **Insurer / auditor / admin**: all in-district farms, privacy-safe labels (first name + last initial).
    - Farms with no GPS coordinates are omitted.
  - `GET /farms/{farm_id}` — rich detail record for the panel; farmers 403 on others' farms.

- **Seed script** (`scripts/seed_geo.py`):
  - 5 demo farmers (`*.geo@paratrust.dev`) with 2–3 farms each (~13 farms total), all within the demo district bbox, deterministic from `simulation_seed = 42`.

- **Tests** (`tests/test_stage3.py`) — 11 tests, all passing:
  - District polygon is closed, has `bbox`, is labelled `simulated`.
  - 12 rainfall + 8 water-level gauges, all `simulated: true`.
  - River is a LineString; water bodies are Polygons; all `simulated: true`.
  - Farmer sees only own farms, `is_own: true`, `farmer_label: "Your farm"`.
  - Insurer sees only in-district farms with privacy-safe labels; out-of-district farms absent.
  - Farm with no coordinates absent from the layer.
  - Stored `boundary_geojson` is preserved exactly (coordinates unchanged).
  - Generated polygon ring is closed (first == last coordinate).
  - Detail panel contains correct crop, explicit stage-6/8 placeholders, `policy_status`.
  - Farmer 403 on another farmer's detail; farmer 200 on own farm detail.

### Frontend

- **API client** (`src/api/geo.ts`) — typed async wrappers for all 5 geo endpoints.

- **`MapView` component** (`src/features/map/MapView.tsx`):
  - MapLibre GL JS with ESRI World Imagery satellite basemap (no API key required; compact attribution shown).
  - "Basemap imagery may be several weeks old. Coloured overlays are simulated." notice displayed persistently in the top-left corner.
  - Layers: district boundary (dashed blue), farm polygons (green for active-policy/own, grey otherwise), rainfall gauges (purple circles), water-level gauges (sky-blue circles), river (cyan line), water bodies (cyan fill).
  - Layer controls panel (bottom-right): toggle each layer on/off independently with coloured checkbox indicators.
  - Map legend panel (bottom-left): colour key with explicit simulated labels for all overlay types.
  - Farm-ID search (top-centre): flies to the farm on the map and opens the detail panel.
  - Farm click → opens `FarmDetailPanel` with identity, crop, policy, sum insured, and explicit "not yet available" placeholders for risk (Stage 6) and claims (Stage 8).
  - Sensor hover → popup showing sensor name, type, and status.
  - `centreOnFarm` prop: map initialises centred on a specific farm centroid at zoom 14 (farmer view).
  - `initialSelectedFarmId` prop: auto-opens the detail panel on load.
  - `layerVisibility` prop: override which layers start visible.

- **`OperationsMapPage`** (`src/features/insurer/OperationsMapPage.tsx`):
  - Full-viewport map for insurer / auditor / admin.
  - Shows all in-district farms, all sensor types, rivers, water bodies, and the district boundary.
  - Breadcrumb back to insurer dashboard.

- **`MyFarmMapPage`** (`src/features/farmer/MyFarmMapPage.tsx`):
  - Full-viewport map for farmer, centred on their primary farm.
  - District boundary layer hidden by default (less relevant for single-farm view).
  - Detail panel auto-opens for farmers with exactly one farm.
  - Graceful empty state with a link to register a farm.

- **Routes** (`src/app/routes.tsx`):
  - `/farmer/map` → `MyFarmMapPage` (farmer only).
  - `/insurer/map` → `OperationsMapPage` (insurer + auditor + admin).

- **Dashboard activation**:
  - `FarmerDashboard.tsx`: "Satellite Map" card activated and linked to `/farmer/map`.
  - `InsurerDashboard.tsx`: "Operations Map" card activated and linked to `/insurer/map`; removed from upcoming-stages section.

## Acceptance criteria — all met

- [x] The map loads the chosen demo district (Kashi-Ganga, Varanasi area).
- [x] Farm boundaries align with the selected map area (all seed farms within the district bbox).
- [x] Clicking a farm opens the correct farm record in the detail panel.
- [x] Layers can be toggled on/off independently.
- [x] The interface clearly distinguishes basemap imagery from simulated overlays (persistent notice + legend labels).

## Next: Stage 4 — Weather and Flood Simulation
