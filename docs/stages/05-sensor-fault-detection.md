# Stage 05: sensor-fault-detection

Status: complete

Backend: `app/services/fault_detection.py` (LightGBM multi-class classifier over
synthetic labelled time-series, per-class evaluation, trust-score mapping),
`app/models/sensor.py` (persisted `SensorTrustScore` records — original reading
always preserved), `app/api/sensors.py` (model evaluation, classify, trust
history, annotated sensor GeoJSON). All six condition classes are represented,
including `genuine_localised_cell` which is treated as a valid weather event,
not a fault.

Frontend: `src/api/sensors.ts`, `src/hooks/useSensorTrust.ts`,
`src/features/sensors/SensorTrustPanel.tsx` (run detection, summary, flagged
list, model evaluation with confusion matrix), and
`SensorInvestigationPanel.tsx` (classification, probabilities, raw reading,
per-tick audit history). The operations map recolours gauges by trust score,
highlights flagged sensors, and opens the investigation panel on click.

Acceptance: `backend/tests/test_stage5.py` (13 tests) pass; frontend type-checks
and builds cleanly.

See ../ROADMAP.md for objectives, work items and acceptance criteria.
