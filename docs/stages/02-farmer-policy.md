# Stage 02: Farmer Registration and Policy Management

Status: Completed ✅

## Summary of Implementation

### Backend
- **Data Models** (`app/models/stage2.py`):
  - `FarmerProfile` (`farmer_profiles` table): 1:1 with User, stores phone, address, district, state.
  - `Farm` (`farms` table): Area in hectares, latitude/longitude, GeoJSON boundary support.
  - `Crop` (`crops` table): Crop type, season (kharif/rabi/zaid), cultivated area.
  - `InsurancePolicy` (`insurance_policies` table): Policy number, coverage period, sum insured, rainfall trigger mm, max payout mm, flood trigger, payout limit, status.
  - `PolicyRule` (`policy_rules` table): Rule name and JSON value structure.
  - `BankAccountReference` (`bank_account_references` table): Account holder name, masked account number (`****1234`), bank name, IFSC, verification status.
- **Pydantic Schemas** (`app/schemas/stage2.py`):
  - Complete Create / Update / Out schemas for all models.
  - `FarmerSummary` and `FarmerDetail` response models for insurer and admin consoles.
- **API Endpoints**:
  - `/api/farmers/profile` (GET / POST)
  - `/api/farmers/farms` (GET / POST)
  - `/api/farmers/farms/{id}` (GET)
  - `/api/farmers/farms/{id}/crops` (POST)
  - `/api/farmers/bank-account` (GET / POST)
  - `/api/policies/` (GET / POST)
  - `/api/policies/{id}` (GET / PATCH)
  - `/api/policies/farmer/{farmer_profile_id}` (GET)
  - `/api/admin/farmers/` (GET with `?search=` and `?q=`)
  - `/api/admin/farmers/{id}` (GET)
- **Role-based Security** (`app/core/deps.py`):
  - Strict farmer data isolation (farmers can only view/edit their own profiles, farms, and policies).
  - Insurer / Admin permission enforcement for policy creation and cross-farmer registry.
- **Security & Direct Bcrypt**:
  - Replaced legacy passlib wrapper with direct bcrypt to avoid Python 3.14 / bcrypt 5.0+ 72-byte init bug.
- **Automated Tests** (`tests/test_stage2.py`):
  - Profile, farm, crop, and masked bank account submission tests.
  - Cross-farmer policy isolation verification (Farmer 2 cannot read Farmer 1's policy).
  - Role enforcement test (Farmer cannot create policies).
- **Seeded Demo Accounts** (`scripts/seed_users.py`):
  - 3 demo farmers: `farmer.rajan@paratrust.demo`, `farmer.meena@paratrust.demo`, `farmer.suresh@paratrust.demo`.
  - Farms, crops, active policies, and verified bank accounts pre-populated.

### Frontend
- **API Client** (`src/api/stage2.ts`):
  - Fully typed async functions covering all farmer and insurer endpoints.
- **Farmer Experience**:
  - `FarmerProfilePage.tsx`: Personal details, district, state form.
  - `FarmRegistrationPage.tsx`: Interactive farm & crop onboarding with validation.
  - `MyFarmsPage.tsx`: Farm cards with area, GPS coordinates, and crop badges.
  - `MyPolicyPage.tsx`: Policy cards displaying coverage window, sum insured, and rainfall trigger conditions.
  - `BankAccountPage.tsx`: Payout account submission with bank-grade masking (`****1234`) and simulated instant verification.
- **Insurer & Operations Experience**:
  - `FarmerRegistryPage.tsx`: Real-time search by farmer name, email, or district with farm & policy counters.
  - `FarmerDetailPage.tsx`: Deep-dive profile view displaying all linked farms, crops, and active policies, plus quick policy creation CTA.
  - `PolicyListPage.tsx`: Policy portfolio with status filters (`active`, `expired`, `cancelled`) and date filters.
  - `PolicyFormPage.tsx`: Form for creating/issuing parametric policies with auto-generated policy IDs, trigger mm limits, and sum insured.
- **Layout & Navigation**:
  - `PageLayout.tsx`: Shared breadcrumbs and headers.
  - `routes.tsx`: Protected routes wired for all new farmer and insurer views.
  - `FarmerDashboard.tsx` & `InsurerDashboard.tsx`: Stage 2 feature cards activated and linked.
