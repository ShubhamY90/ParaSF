# Stage 01: Foundation — Website & User Login

**Status: ✅ Complete**

## What was built

### Backend (`backend/app/`)
| File | Purpose |
|------|---------|
| `db/engine.py` | SQLAlchemy engine, `Base`, `SessionLocal`, `get_db` dependency |
| `models/user.py` | `User` model + `UserRole` enum (farmer / insurer / auditor / admin) |
| `schemas/auth.py` | Pydantic schemas: `UserCreate`, `UserOut`, `LoginRequest`, `TokenResponse` |
| `core/security.py` | bcrypt hashing, JWT creation/verification, `get_current_user` dependency |
| `api/auth.py` | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| `main.py` | Updated: auto-creates tables on startup, mounts auth router |
| `scripts/seed_users.py` | Seeds 4 test accounts (one per role) |
| `tests/test_auth.py` | 6 tests — all passing |

### Frontend (`frontend/src/`)
| File/Folder | Purpose |
|-------------|---------|
| `tailwind.config.js` | Navy + brand-green/blue design tokens |
| `index.css` | Tailwind directives + dark navy base |
| `api/client.ts` | Fetch wrapper with Bearer token injection |
| `api/auth.ts` | Typed register / login / me API calls |
| `contexts/AuthContext.tsx` | Global auth state: user, token, login, logout, register |
| `hooks/useAuth.ts` | Convenience hook |
| `app/App.tsx` | BrowserRouter + AuthProvider + Navbar + AppRoutes |
| `app/routes.tsx` | All routes with role-based ProtectedRoute guards |
| `features/landing/LandingPage.tsx` | Professional InsurTech landing page |
| `features/auth/LoginPage.tsx` | Login form with error state + test account hints |
| `features/auth/RegisterPage.tsx` | Registration form with auto-login |
| `features/farmer/FarmerDashboard.tsx` | Dashboard shell with stage-labelled cards |
| `features/insurer/InsurerDashboard.tsx` | Dashboard shell with stage-labelled cards |
| `features/auditor/AuditorDashboard.tsx` | Dashboard shell with stage-labelled cards |
| `features/admin/AdminDashboard.tsx` | Admin placeholder panel |
| `features/shared/Navbar.tsx` | Logo, user badge, role pill, logout |
| `features/shared/ProtectedRoute.tsx` | Redirect to /login or /access-denied |
| `features/shared/AccessDenied.tsx` | 403 page |
| `features/shared/NotFound.tsx` | 404 page |
| `features/shared/LoadingSpinner.tsx` | Animated spinner |

## Test accounts (seed with `python scripts/seed_users.py`)
| Role | Email | Password |
|------|-------|----------|
| Farmer | farmer@paratrust.dev | farmer123 |
| Insurer | insurer@paratrust.dev | insurer123 |
| Auditor | auditor@paratrust.dev | auditor123 |
| Admin | admin@paratrust.dev | admin123 |

## Acceptance criteria — all met
- [x] Each role can sign in using a test account
- [x] Each role is routed to the correct dashboard (`/farmer`, `/insurer`, `/auditor`, `/admin`)
- [x] A user cannot access another role's protected pages by changing the URL
- [x] Invalid credentials produce a clear error message
- [x] The application can be started from documented setup instructions (see README)

## Next: Stage 2 — Farmer Registration and Policy Management
