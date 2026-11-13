# ParaTrust

Agentic climate insurance intelligence & financial risk platform (B2B2C). All payments are **simulated**. Full plan: [docs/ROADMAP.md](docs/ROADMAP.md).

## Structure

```
backend/    FastAPI service
  app/api         HTTP routes
  app/core        config, security
  app/db          engine, sessions, migrations helpers
  app/models      SQLAlchemy models
  app/schemas     Pydantic schemas
  app/services    identity, policy, geospatial, simulation, claims, payments, notifications, audit
  app/ml          sensor_fault (LightGBM), spatial_estimation (GP/Kriging)
  app/agents      LangGraph workflow + tools (4 agents)
  tests/ scripts/ data/
frontend/   React + TypeScript + Vite (+ MapLibre)
  src/features    auth, farmer, insurer, auditor, map, simulation, claims, agents, disputes
data/       seeds + GeoJSON for the demo district
docs/       roadmap and per-stage notes (docs/stages/)
```

## Run (Stage 1)

**Backend:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_users.py      # seed 4 test accounts
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend && npm install && npm run dev
```

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | Landing page |
| http://localhost:5173/login | Sign in |
| http://localhost:5173/register | Farmer registration |
| http://localhost:8000/api/health | Backend health check |
| http://localhost:8000/docs | FastAPI interactive docs |

**Test accounts** (after seeding):

| Role | Email | Password |
|------|-------|----------|
| Farmer | farmer@paratrust.dev | farmer123 |
| Insurer | insurer@paratrust.dev | insurer123 |
| Auditor | auditor@paratrust.dev | auditor123 |
| Admin | admin@paratrust.dev | admin123 |

**Run tests:**
```bash
cd backend && .venv/bin/pytest tests/ -v
```

## Stages

| Stage | Name | Status |
|-------|------|--------|
| 1 | Website foundation & user login | ✅ Complete |
| 2 | Farmer & policy management | ⬜ Next |
| 3 | Satellite map & geographic monitoring | ⬜ Pending |
| 4–12 | … | ⬜ Pending |

Full plan: [docs/ROADMAP.md](docs/ROADMAP.md) · Stage notes: [docs/stages/](docs/stages/)
