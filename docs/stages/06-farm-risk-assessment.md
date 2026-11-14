# Stage 06: farm-risk-assessment

Status: complete ✅

## Summary

Backend: `app/services/risk.py` (trust-weighted Gaussian Process regression over simulated sensor readings, IDW fallback, risk categorisation thresholds, flood risk score via sigmoid on water-level gauges), `app/models/risk.py` (`FarmRiskEstimate` table with per-tick idempotent upsert), `app/api/risk.py` (POST /api/risk/assess, GET /api/risk/{run_id}, GET /api/risk/{run_id}/{farm_id}, GET /api/risk/geojson/{run_id}).

Frontend: `src/api/risk.ts`, `src/hooks/useRisk.ts`, `src/features/risk/FarmRiskPanel.tsx` (run assessment button, category summary grid, per-farm detail card with rainfall estimate ± σ, 80% CI bar, flood risk bar, evidence note). Operations map shows risk GeoJSON overlay coloured by category; clicking a farm shows risk in the detail panel.

Bug fixed (post-stage): farm detail panel now finds the nearest simulated farm by lat/lng Euclidean distance (`_nearest_sim_farm_id` in `api/geo.py`) instead of guessing by integer DB ID.

See ../ROADMAP.md for objectives, work items, and acceptance criteria.
