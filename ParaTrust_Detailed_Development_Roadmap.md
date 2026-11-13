# ParaTrust --- Detailed Stage-by-Stage Development Roadmap

**Project type:** Agentic Climate Insurance Intelligence & Financial
Risk Platform\
**Primary users:** Insurance companies, banks acting as
distribution/payment partners, farmers, and auditors\
**Development approach:** Build and validate one stage at a time,
integrating each completed stage into the working application.

------------------------------------------------------------------------

## 1. Project Overview

ParaTrust is a platform that helps insurers investigate climate-related
insurance events and make transparent, evidence-based parametric
insurance settlements. It combines a farmer-facing experience with an
advanced insurer/bank-facing operations platform.

The platform will:

1.  Register farmers, farms, insurance policies, and verified payment
    details.
2.  Display the insured geographical area on an interactive satellite
    map.
3.  Monitor simulated rainfall, water levels, storms, and flood events.
4.  Detect faulty or suspicious sensor readings without automatically
    rejecting genuine localised weather events.
5.  Estimate rainfall and flood risk at individual farm level, including
    uncertainty.
6.  Use four cooperating AI agents to investigate events and claims.
7.  Calculate policy-based claim recommendations using a deterministic
    financial engine.
8.  Support authorised human review and payment approval.
9.  Communicate claim progress and payment status to farmers.
10. Maintain auditable records and financial reports.

### 1.1 Product positioning

**ParaTrust is a B2B2C Agentic InsurTech Platform.**

-   **B2B:** Insurers and financial partners use the operational
    platform, policy tools, risk information, and claim workflows.
-   **B2C:** Farmers use a simple interface to register, view their farm
    and policy information, track claims, receive notifications, and
    raise disputes.
-   **Core innovation:** AI agents investigate uncertain evidence and
    recommend actions, while deterministic policy rules, financial
    controls, and authorised human approvals govern settlement.

### 1.2 Important role distinction

The insurer is responsible for insurance coverage decisions and claim
authorisation. A bank may act as a distribution partner, lender,
account-verification provider, or payment-service partner depending on
the business arrangement. ParaTrust should not imply that every bank is
itself the insurer.

For the hackathon prototype, all money movement must be simulated. Do
not connect the prototype to real payment rails or move real funds.

------------------------------------------------------------------------

## 2. Users and Their Interfaces

### 2.1 Farmer interface

The farmer experience should be simple and mobile-friendly. It should
support:

-   Registration and login.
-   Farmer profile and contact details.
-   Farm location and boundary.
-   Crop and land-area information.
-   Insurance policy details.
-   Bank-account details and verification status.
-   Satellite map centred on the farmer's farm.
-   Weather and flood alerts.
-   Claim status and claim history.
-   Approved compensation and payment status.
-   Settlement explanation.
-   Dispute or support request.

Farmers should not need to upload extensive evidence for every
parametric claim. The platform should use available sensor, satellite,
and weather evidence automatically where possible.

### 2.2 Bank and insurer interface

The advanced operations dashboard should support:

-   Role-based access.
-   Farmer, farm, and policy search.
-   District-wide satellite map.
-   Insured-farm and sensor overlays.
-   Active weather and flood events.
-   Sensor reliability and investigation alerts.
-   Farm-level risk and uncertainty.
-   AI-agent investigation traces.
-   Claims awaiting review.
-   Approve, hold, or reject actions, subject to permissions.
-   Payout exposure and budget monitoring.
-   Payment simulation and reconciliation.
-   Audit history and reports.

### 2.3 Auditor interface

The auditor should be able to:

-   Search for a claim.
-   View the evidence used in the decision.
-   Inspect agent actions and handoffs.
-   View policy calculations and approvals.
-   Review payment history.
-   Verify the audit chain.
-   Replay a decision using stored inputs and the relevant policy/model
    versions.

------------------------------------------------------------------------

## 3. Overall Development Sequence

  -----------------------------------------------------------------------
  Stage                   Name                    Main outcome
  ----------------------- ----------------------- -----------------------
  1                       Website foundation and  Working application
                          user login              shell and role-based
                                                  access

  2                       Farmer and policy       Registered farmers,
                          management              farms, policies, and
                                                  payment details

  3                       Satellite map and       Interactive map with
                          geographic monitoring   farm boundaries and
                                                  geographic layers

  4                       Weather and flood       Reproducible weather
                          simulation              events and changing map
                                                  overlays

  5                       Sensor fault detection  Fault classification
                                                  and sensor trust scores

  6                       Farm-level risk         Farm-level rainfall
                          assessment              estimates, risk, and
                                                  uncertainty

  7                       Four AI agents          Visible investigation
                                                  workflow with tools and
                                                  handoffs

  8                       Claim calculation and   Policy-based claim
                          approval                recommendations and
                                                  human approval

  9                       Bank/insurer dashboard  Claim operations and
                          and payment system      simulated settlement

  10                      Farmer communication    Claim tracking,
                                                  notifications, and
                                                  disputes

  11                      Audit and financial     Traceability, duplicate
                          intelligence            prevention, and
                                                  financial reporting

  12                      Integration and final   End-to-end tested
                          demonstration           hackathon prototype
  -----------------------------------------------------------------------

**Build rule:** Complete the acceptance test for a stage before treating
it as complete. Later stages may use clearly labelled mock data until
their dependencies are implemented.

------------------------------------------------------------------------

# 4. Detailed Stage-by-Stage Plan

## Stage 1 --- Website Foundation and User Login

### Objective

Create the initial ParaTrust website, establish the application
structure, and provide separate entry points for farmers,
insurers/banks, and auditors.

### Work items

1.  Create the frontend project.
2.  Set up the backend service.
3.  Configure the database connection.
4.  Create the ParaTrust landing page and navigation.
5.  Build login and registration screens.
6.  Define user roles:
    -   Farmer
    -   Insurer/Bank Operator
    -   Auditor
    -   Platform Administrator
7.  Implement role-based routing and protected pages.
8.  Create basic dashboard shells for each role.
9.  Add form validation and error states.
10. Add a consistent visual design system.

### Suggested screens

-   Landing page.
-   Login.
-   Farmer registration.
-   Role-specific dashboard placeholders.
-   Access-denied and not-found pages.

### Suggested technologies

-   Frontend: React, TypeScript, Vite.
-   Styling: Tailwind CSS or an equivalent component system.
-   Backend: Python FastAPI.
-   Initial database: SQLite for rapid local development; PostgreSQL for
    a more production-like setup.
-   Authentication: secure password hashing and server-side session or
    token validation.

### Deliverables

-   Running frontend.
-   Running backend.
-   Database connection.
-   Role-aware login.
-   Three dashboard shells.

### Acceptance criteria

-   Each role can sign in using a test account.
-   Each role is routed to the correct dashboard.
-   A user cannot access another role's protected pages merely by
    changing a URL.
-   Invalid credentials produce a clear error.
-   The application can be started from documented setup instructions.

### Dependency

None. This is the first stage.

------------------------------------------------------------------------

## Stage 2 --- Farmer Registration and Policy Management

### Objective

Create the core records that connect a farmer, a farm, an insurance
policy, and a payment destination.

### Farmer-side work

1.  Create farmer profile form.
2.  Capture name and contact details.
3.  Capture farm location.
4.  Capture farm area and crop details.
5.  Store farm coordinates or a geographic boundary.
6.  Display the farmer's profile and registered farms.
7.  Provide a policy summary.

### Insurer-side work

1.  Create policy-management page.
2.  Register or assign a policy to a farmer and farm.
3.  Store policy number and coverage period.
4.  Store sum insured.
5.  Store rainfall or flood trigger conditions.
6.  Store payout limits and policy status.
7.  Search and filter farmers and policies.

### Bank-detail work

-   Capture the account details required by the prototype.
-   Store verification status separately from the account details.
-   Use mock verification for the hackathon.
-   Never display full account numbers in ordinary dashboard views.
-   Do not store real credentials, PINs, or OTPs.

### Suggested data entities

-   `User`
-   `FarmerProfile`
-   `Farm`
-   `Crop`
-   `InsurancePolicy`
-   `PolicyRule`
-   `BankAccountReference`

### Deliverables

-   Farmer registration.
-   Farm registration.
-   Policy creation and assignment.
-   Policy summary.
-   Mock bank-account verification status.

### Acceptance criteria

-   An insurer operator can create a policy for a registered farmer.
-   A farmer can see only their own farm and policy information.
-   The insurer can search for a farmer and view associated policies.
-   Policy parameters are stored in the database, not hardcoded into the
    frontend.

### Dependency

Stage 1.

------------------------------------------------------------------------

## Stage 3 --- Satellite Map and Geographic Monitoring

### Objective

Make the geographical area visible and interactive. The satellite map
should be a central part of the insurer's operations dashboard and a
useful local view for farmers.

### Map technology

-   MapLibre GL JS for the interactive map.
-   A suitable satellite imagery tile provider or permitted satellite
    basemap.
-   GeoJSON for farm boundaries and geographic features.
-   Python geospatial libraries such as GeoPandas for backend processing
    where needed.

### Map layers

1.  Satellite basemap.
2.  District or simulation boundary.
3.  Farm boundary polygons.
4.  Farm identifiers and selection markers.
5.  Rainfall-gauge locations.
6.  Water-level gauge locations.
7.  Rivers and water bodies.
8.  Flood-affected area overlay.
9.  Rainfall-intensity overlay.
10. Sensor status overlay.

### Interactions

-   Zoom and pan.
-   Switch map layers on and off.
-   Search for a farm ID.
-   Click a farm to open its detail panel.
-   Display farmer, crop, policy, and insured amount where the viewer
    has permission.
-   Filter by risk category or claim status.
-   Show a map legend.
-   Centre the farmer view on their own registered farm.

### Farm detail panel

The selected farm panel should display:

-   Farm ID.
-   Farmer name or privacy-safe identifier.
-   Crop.
-   Farm area.
-   Policy status.
-   Sum insured.
-   Latest estimated rainfall, once Stage 6 is available.
-   Risk category, once Stage 6 is available.
-   Claim status, once Stage 8 is available.

Before those later stages exist, show clear placeholders such as "Risk
assessment not yet available."

### Satellite imagery limitations

A satellite basemap is not automatically a live satellite feed. Imagery
may be several days or weeks old, depending on the provider and
acquisition conditions. Cloud cover, revisit frequency, licensing, and
tile availability affect what can be displayed.

For the hackathon:

-   Start with a satellite basemap and simulated farm/flood layers.
-   Label simulated overlays clearly.
-   Add actual satellite-derived evidence only if data access and
    processing are reliable.
-   Do not describe a simulated flood overlay as a verified satellite
    observation.

### Deliverables

-   Interactive satellite map.
-   Farm polygons.
-   Sensor markers.
-   Layer controls.
-   Farm-selection detail panel.
-   Map integration in insurer and farmer dashboards.

### Acceptance criteria

-   The map loads the chosen demo district.
-   Farm boundaries align with the selected map area.
-   Clicking a farm opens the correct farm record.
-   Layers can be toggled.
-   The interface clearly distinguishes basemap imagery from simulated
    overlays.

### Dependency

Stages 1 and 2. The map can initially use seeded demo farms.

------------------------------------------------------------------------

## Stage 4 --- Weather and Flood Simulation

### Objective

Create a repeatable simulation that produces weather and flood events
for the demonstration and downstream ML and claims modules.

### Initial simulation scope

Use a simulated district containing:

-   100 farms.
-   12 rainfall gauges.
-   A river and relevant water bodies.
-   Moving storm cells.
-   Rainfall readings over time.
-   Water-level readings.
-   Delayed satellite evidence as a separate evidence source.

### Work items

1.  Create a fixed-seed district generator.
2.  Generate farm and gauge coordinates.
3.  Generate normal rainfall patterns.
4.  Generate moving storm cells.
5.  Simulate rainfall at sensor locations.
6.  Simulate water-level changes.
7.  Generate flood-event scenarios.
8.  Add a simulation clock.
9.  Add start, pause, resume, and reset controls.
10. Publish updates to the frontend.
11. Display changing rainfall and flood overlays on the map.

### Required scenario presets

-   Normal weather.
-   Broad rainfall event.
-   Severe flood event.
-   Localised rainfall event.
-   Faulty-sensor event.

### Reproducibility

Every demo scenario should be reproducible from a fixed seed. Store the
seed and scenario configuration so that the same event can be replayed.

### Deliverables

-   District and weather generator.
-   Gauge readings.
-   Storm and flood scenarios.
-   Simulation controls.
-   Live map updates.

### Acceptance criteria

-   A user can start and reset a scenario.
-   Gauge readings change over simulation time.
-   A flood scenario changes the affected-area overlay.
-   The same seed reproduces the same scenario.
-   The frontend clearly identifies simulated weather data.

### Dependency

Stages 1--3.

------------------------------------------------------------------------

## Stage 5 --- Sensor Fault Detection and Trust Scoring

### Objective

Identify unreliable readings and assign a trust score to each sensor
without confusing a genuine localised weather event with a sensor fault.

### Sensor conditions

The model and simulation should distinguish:

-   `normal`
-   `spike`
-   `stuck`
-   `drift`
-   `dead`
-   `genuine_localised_cell`

The genuine localised rainfall condition is not a sensor fault. It must
be represented separately so that the system does not blindly discard a
valid local weather event.

### Work items

1.  Create labelled sensor time-series data.
2.  Generate normal and faulty sensor behaviour.
3.  Add temporal features.
4.  Add neighbouring-sensor comparison features.
5.  Add rate-of-change features.
6.  Add missing-data and stuck-value features.
7.  Train a LightGBM classifier.
8.  Evaluate each class separately.
9.  Calculate a sensor trust score.
10. Display fault alerts on the map.
11. Preserve the original readings and investigation history.

### Important investigation rule

An outlier is suspicious, not automatically false. For example, one
gauge reporting 180 mm while nearby gauges report much less should
trigger investigation. Satellite evidence, storm location, neighbouring
observations, and other local evidence should be considered before
deciding whether the reading is unreliable.

### Deliverables

-   Fault-injection generator.
-   Feature pipeline.
-   Trained classifier.
-   Per-class evaluation.
-   Sensor trust-score service.
-   Sensor investigation map markers.

### Acceptance criteria

-   The system detects the injected fault classes.
-   Class-wise precision, recall, and confusion matrix are available.
-   Genuine localised rainfall is not automatically classified as a
    faulty sensor.
-   The platform records why a sensor was flagged.
-   The original reading remains available for audit.

### Dependency

Stage 4.

------------------------------------------------------------------------

## Stage 6 --- Farm-Level Risk Assessment

### Objective

Estimate rainfall and flood risk for each farm using trusted evidence
and report uncertainty rather than presenting estimates as exact
measurements.

### Work items

1.  Read sensor locations and observations.
2.  Read sensor trust scores.
3.  Incorporate available satellite or other supporting evidence.
4.  Apply trust-weighted spatial estimation.
5.  Use Gaussian Process or Kriging-based estimation.
6.  Generate farm-level rainfall estimates.
7.  Calculate uncertainty or posterior intervals.
8.  Convert estimates into risk categories.
9.  Store the estimate and model version.
10. Display farm-level risk on the satellite map.

### Farm-level outputs

-   Estimated rainfall.
-   Estimated flood risk.
-   Confidence or uncertainty.
-   Main supporting sensors.
-   Evidence timestamp.
-   Model/version identifier.

### Map visualisation

-   Safe or lower-risk farms.
-   Farms requiring attention.
-   Higher-risk farms.
-   Uncertain estimates.
-   Sensor locations and trust indicators.

Use a clear legend and avoid implying that a colour category is a
confirmed physical flood boundary unless it is supported by the relevant
evidence.

### Deliverables

-   Spatial-estimation pipeline.
-   Farm-level estimates.
-   Uncertainty outputs.
-   Risk layer.
-   Farm risk detail panel.

### Acceptance criteria

-   Every farm in the simulation receives an estimate or an explicit
    "insufficient evidence" status.
-   The estimate uses trusted evidence.
-   Uncertainty is displayed alongside the estimate.
-   Changing sensor trust changes the spatial estimate where
    appropriate.
-   Results can be reproduced from stored inputs and model versions.

### Dependency

Stages 3, 4, and 5.

------------------------------------------------------------------------

## Stage 7 --- Four-Agent Investigation System

### Objective

Coordinate the investigation and claim workflow through four agents with
explicit responsibilities, tool calls, shared state, and human approval
checkpoints.

### Agent 1: Storm Intelligence Agent

Responsibilities:

-   Detect or receive a weather event.
-   Identify the event's time and geographical scope.
-   Identify potentially affected farms.
-   Summarise estimated exposure.
-   Pass event context to the Sensor Investigation Agent.

### Agent 2: Sensor Investigation Agent

Responsibilities:

-   Inspect readings from relevant gauges.
-   Compare neighbouring sensors.
-   Retrieve sensor classifications and trust scores.
-   Review available satellite evidence.
-   Distinguish suspicious readings from plausible localised rainfall.
-   Record findings and supporting evidence.
-   Pass verified or uncertain evidence to the Claims Resolution Agent.

### Agent 3: Claims Resolution Agent

Responsibilities:

-   Retrieve the relevant insurance policy.
-   Retrieve farm-level rainfall and risk estimates.
-   Apply the claim calculation service.
-   Propose a claim outcome such as `PAY`, `ADVANCE`, `HOLD`, or `NONE`.
-   Explain the recommendation and its evidence.
-   Pass the recommendation to the Compliance & Audit Agent.

### Agent 4: Compliance & Audit Agent

Responsibilities:

-   Check policy limits.
-   Check payout budget and exposure constraints.
-   Check for duplicate payments.
-   Check evidence completeness.
-   Check whether human approval is required.
-   Record the decision trace.
-   Pause for authorised human review when required.

### Orchestration

Use LangGraph or an equivalent explicit workflow orchestrator. Maintain
shared state containing:

-   Event ID.
-   Scenario ID.
-   Affected farm IDs.
-   Evidence references.
-   Sensor findings.
-   Farm-level estimates.
-   Policy references.
-   Claim recommendation.
-   Compliance findings.
-   Approval status.
-   Audit references.

### Safety and financial control

-   Agents must not directly authorise money movement.
-   LLMs may investigate, summarise, explain, and propose.
-   Deterministic code must calculate policy entitlement and enforce
    limits.
-   Consequential approvals must be performed by an authorised human or
    a separately approved deterministic process.
-   All tool calls and handoffs should be visible in the demo.
-   Provide an offline or LLM-unavailable fallback for critical
    deterministic operations.

### Deliverables

-   Four agent definitions.
-   Shared workflow state.
-   Agent tools.
-   Handoff logic.
-   Checkpoints.
-   Human approval pause.
-   Visible agent activity and trace panel.

### Acceptance criteria

-   All four agents execute their assigned tasks.
-   At least one real tool call is made by each relevant agent.
-   Shared state is updated across handoffs.
-   A case requiring approval pauses for human review.
-   An agent failure does not bypass financial controls.
-   The deterministic claim engine remains functional if the LLM is
    unavailable.

### Dependency

Stages 4, 5, and 6. Stage 2 policy records are also required for
claim-related tools.

------------------------------------------------------------------------

## Stage 8 --- Claim Calculation and Approval

### Objective

Calculate an insurance claim using stored policy rules and farm-level
evidence, then route the recommendation through the required approval
process.

### Work items

1.  Retrieve the policy assigned to the affected farm.
2.  Validate policy dates and eligibility.
3.  Retrieve the policy trigger and coverage parameters.
4.  Retrieve farm-level rainfall and uncertainty.
5.  Calculate graduated entitlement.
6.  Apply policy caps and cumulative payment checks.
7.  Apply confidence-aware settlement rules.
8.  Create a claim record.
9.  Route the claim for human approval when required.
10. Store approval, hold, or rejection reasons.

### Example graduated entitlement

Let:

-   \(S\) = sum insured.
-   (T\_{start}) = rainfall threshold at which payout begins.
-   (T\_{full}) = rainfall threshold at which the full eligible payout
    is reached.
-   (`\mu`{=tex}) = estimated rainfall at the farm.

A simple graduated score is:

\[ s(`\mu`{=tex})=`\operatorname{clip}`{=tex}`\left`{=tex}(
`\frac{\mu-T_{start}}{T_{full}-T_{start}}`{=tex},0,1 `\right`{=tex}) \]

The illustrative entitlement is:

\[ E=S`\times `{=tex}s(`\mu`{=tex}) \]

This is a prototype formula only. Actual policy wording, exclusions,
caps, waiting periods, and other contractual terms must determine the
production calculation.

### Confidence-aware settlement

The platform may recommend a bounded advance when evidence is
sufficiently trustworthy and a later settlement adjustment when
additional evidence arrives. The exact thresholds and rules must be
explicit, configurable, and tested. Do not allow uncertainty to silently
increase a payout.

### Claim statuses

Suggested statuses:

-   `CREATED`
-   `UNDER_INVESTIGATION`
-   `RECOMMENDED`
-   `AWAITING_APPROVAL`
-   `APPROVED`
-   `ON_HOLD`
-   `REJECTED`
-   `PAYMENT_PENDING`
-   `PAID`
-   `DISPUTED`

### Deliverables

-   Deterministic claim calculation service.
-   Claim records and statuses.
-   Approval screen.
-   Decision explanation.
-   Policy and evidence references.

### Acceptance criteria

-   The claim calculation is reproducible from policy and evidence
    inputs.
-   The sum insured and policy caps cannot be exceeded.
-   A claim cannot be paid twice.
-   A human reviewer can approve or hold a claim.
-   The system stores the reason for the decision.

### Dependency

Stages 2, 6, and 7.

------------------------------------------------------------------------

## Stage 9 --- Bank/Insurer Dashboard and Simulated Payment System

### Objective

Provide the insurer with an operational control centre and simulate the
settlement workflow to the farmer's registered account.

### Dashboard components

-   Total insured farms.
-   Active weather events.
-   Farms at elevated risk.
-   Claims under investigation.
-   Claims awaiting approval.
-   Approved claims.
-   Payments pending.
-   Completed simulated payments.
-   Total approved payout exposure.
-   Policy and event filters.

### Claim review page

Display:

-   Farmer and farm reference.
-   Policy details.
-   Satellite map location.
-   Event information.
-   Farm-level rainfall estimate.
-   Sensor trust and evidence summary.
-   AI-agent investigation trace.
-   Recommended claim amount.
-   Compliance checks.
-   Approval controls.

### Payment simulation

1.  Receive an approved claim.
2.  Create a payment instruction record.
3.  Validate the farmer's registered payment reference.
4.  Check the claim's payment status.
5.  Create a simulated transaction.
6.  Update the claim to `PAID` only after the simulated transaction
    succeeds.
7.  Store the transaction reference.
8.  Notify the farmer through Stage 10.

### Duplicate prevention

Use an idempotency key, for example:

`farm_id + event_id + policy_id`

The database should enforce a unique constraint or equivalent control
for the relevant settlement identity. Replaying the same event must not
create another payment.

### Important scope limitation

This stage uses simulated payments only. Real bank integration requires
authorised provider access, security review, compliance review, and an
agreed commercial arrangement.

### Deliverables

-   Insurer dashboard.
-   Claim review and approval page.
-   Payment instruction records.
-   Simulated payment service.
-   Reconciliation view.

### Acceptance criteria

-   Insurer operators can find and review claims.
-   Only authorised users can approve them.
-   Approved claims can be simulated as paid.
-   Duplicate payment attempts are blocked.
-   Payment and claim status remain consistent.

### Dependency

Stages 1, 2, and 8.

------------------------------------------------------------------------

## Stage 10 --- Farmer Communication and Claim Tracking

### Objective

Keep the farmer informed throughout the claim process through a clear,
accessible interface.

### Farmer dashboard

Show:

-   Registered farm and policy.
-   Satellite map of the farmer's farm.
-   Relevant weather alerts.
-   Active claim.
-   Claim status and timeline.
-   Recommended or approved amount, where appropriate.
-   Payment status.
-   Settlement explanation.
-   Claim history.

### Notifications

For the hackathon, implement in-app notifications and a simulated
SMS/WhatsApp notification panel. Real messaging integrations can be
added only after selecting and authorising a provider.

Example notification:

> ParaTrust: Your insured farm has been included in a flood-event
> investigation. Your claim is currently under review. You can view its
> progress in your ParaTrust account.

After approval:

> ParaTrust: Your claim has been approved for the illustrative amount
> shown in your account. Payment status: Processing.

After simulated settlement:

> ParaTrust: Your simulated payment has been marked as completed. Please
> check your claim details for the transaction reference.

### Dispute workflow

-   Farmer selects a claim.
-   Farmer chooses a reason.
-   Farmer adds an explanation or supporting document if available.
-   System creates a dispute record.
-   Insurer reviewer sees the dispute.
-   Resolution and reason are recorded.

### Accessibility considerations

-   Mobile-first layout.
-   Simple language.
-   Clear icons and status labels.
-   Avoid technical ML terminology in farmer-facing messages.
-   Consider multilingual support as a later enhancement.
-   Consider low-bandwidth access and SMS/IVR channels for future
    versions.

### Deliverables

-   Farmer claim dashboard.
-   Claim timeline.
-   In-app notification system.
-   Simulated SMS/WhatsApp messages.
-   Dispute submission and review record.

### Acceptance criteria

-   A farmer can view only their own claim information.
-   Claim status updates appear after insurer actions.
-   Payment notification appears only after the payment record reaches
    the completed state.
-   A farmer can submit a dispute.
-   The insurer can see the dispute and record a resolution.

### Dependency

Stages 1, 2, 8, and 9.

------------------------------------------------------------------------

## Stage 11 --- Audit and Financial Intelligence

### Objective

Make claim decisions traceable and give insurers a basic view of
financial exposure and settlement performance.

### Audit functionality

-   Record event creation.
-   Record source evidence references.
-   Record sensor investigation results.
-   Record model and policy versions.
-   Record farm-level estimates.
-   Record claim calculation inputs and outputs.
-   Record agent tool calls and handoffs.
-   Record human approvals and reasons.
-   Record payment instructions and transaction references.
-   Maintain a hash-chained audit trail.
-   Support deterministic decision replay where all required inputs and
    versions are retained.

### Financial intelligence

Start with:

-   Total insured exposure.
-   Total recommended claims.
-   Total approved claims.
-   Total simulated paid claims.
-   Pending payout amount.
-   Payout budget utilisation.
-   Claims by event and geographical area.

Possible later extensions:

-   Portfolio exposure forecasting.
-   Monte Carlo catastrophe scenarios.
-   Liquidity and reserve forecasting.
-   Dynamic underwriting recommendations.
-   Advanced fraud-network analysis.

These are extensions and should not delay the core claim workflow.

### Fairness and model evaluation

Evaluate:

-   Basis-risk misses and overpayments.
-   False payouts blocked.
-   Genuine payouts delayed.
-   Results by farm size or smallholder status.
-   Results by distance from gauges.
-   Calibration and confidence reliability.
-   Payout budget compliance.
-   Sensor fault performance by class.

Use held-out scenarios and fixed random seeds. Clearly distinguish
generated results from targets or illustrative figures.

### Deliverables

-   Audit event records.
-   Hash verification.
-   Decision replay.
-   Financial summary dashboard.
-   Evaluation report.

### Acceptance criteria

-   An auditor can trace a claim from event to payment.
-   Audit-chain verification detects an altered record.
-   Decision replay reproduces the stored decision when inputs and
    versions are unchanged.
-   Financial totals reconcile with claim and payment records.
-   Evaluation results are generated from actual test runs, not
    hardcoded.

### Dependency

Stages 4--10, with the most important audit events added incrementally
from earlier stages.

------------------------------------------------------------------------

## Stage 12 --- Integration, Testing, and Final Demonstration

### Objective

Connect all modules into one reliable end-to-end prototype and prepare a
repeatable hackathon demonstration.

### Integration work

1.  Connect frontend to backend APIs.
2.  Connect the map to farm, sensor, and risk data.
3.  Connect simulation events to the agent workflow.
4.  Connect sensor trust to spatial estimation.
5.  Connect farm estimates to claim calculation.
6.  Connect agent recommendations to approval.
7.  Connect approval to simulated payment.
8.  Connect payment status to farmer notifications.
9.  Connect all important actions to the audit trail.
10. Test role permissions and error handling.

### Required end-to-end scenarios

#### Scenario A --- Faulty sensor

1.  Start a flood scenario.
2.  Inject a suspicious spike, such as a gauge reporting 180 mm while
    neighbouring gauges report much lower values.
3.  Show the suspicious gauge on the satellite map.
4.  Run the Sensor Investigation Agent.
5.  Show the fault classification and trust-score change.
6.  Recalculate farm-level rainfall using trusted evidence.
7.  Show the claim recommendation and approval checks.
8.  Confirm that an unreliable reading does not automatically create an
    unjustified payout.

#### Scenario B --- Genuine localised rainfall

1.  Start a localised rainfall scenario.
2.  Show coherent local evidence around the affected farm.
3.  Demonstrate that the system does not automatically reject the
    unusual reading.
4.  Show the farm-level estimate and uncertainty.
5.  Run the claim workflow.
6.  Recommend a justified bounded advance or claim according to the
    configured demo policy.
7.  Obtain the required approval.
8.  Show the simulated payment and farmer notification.

#### Scenario C --- Duplicate payment attempt

1.  Complete a simulated payment.
2.  Replay the same settlement request.
3.  Show that the idempotency control blocks a duplicate.
4.  Show the audit record explaining the result.

### Final demo acceptance checklist

-   [ ] Application starts from a clean setup.
-   [ ] Fixed-seed simulation can be reset.
-   [ ] Farmer, insurer, and auditor roles work.
-   [ ] Farmer and policy records are visible to authorised users.
-   [ ] Satellite map displays farm boundaries and sensor locations.
-   [ ] Weather and flood layers update during simulation.
-   [ ] Faulty sensor classes can be injected and detected.
-   [ ] Genuine localised rainfall is treated separately.
-   [ ] Farm-level estimate includes uncertainty.
-   [ ] Four agents execute and show handoffs.
-   [ ] Human approval pauses work where required.
-   [ ] Claim calculation respects policy limits.
-   [ ] Duplicate payment is prevented.
-   [ ] Farmer claim status updates.
-   [ ] Audit trail can be verified.
-   [ ] Demo can run without relying on live external services.

------------------------------------------------------------------------

# 5. Suggested Technical Architecture

``` text
                         PARATRUST WEBSITE
                                 |
                 React + TypeScript + MapLibre
                                 |
                  Role-Based User Experiences
             /                  |                 \
          Farmer            Insurer/Bank          Auditor
             \                  |                 /
                                 |
                           FastAPI Backend
                                 |
      -------------------------------------------------------
      |              |              |             |          |
   Identity       Policy        Geospatial     Simulation  Claims
   & Access       Service         Service        Engine    Service
      |              |              |             |          |
      -------------------------------------------------------
                                 |
                       Evidence and Risk Layer
                                 |
             ----------------------------------------
             |                  |                   |
        Sensor ML         Spatial Estimation    Satellite Data
        LightGBM          GP / Kriging           and GeoJSON
             |                  |                   |
             ----------------------------------------
                                 |
                       LangGraph Orchestration
                                 |
             ----------------------------------------
             |                  |                   |
          Storm             Sensor               Claims
       Intelligence       Investigation         Resolution
                                 |
                         Compliance & Audit
                                 |
                  Deterministic Policy Engine
                                 |
                    Human Approval Checkpoint
                                 |
                     Simulated Payment Ledger
                                 |
                    Farmer Notifications
                                 |
                       Audit and Reporting
```

### Suggested stack

  Layer                 Suggested technology
  --------------------- ------------------------------------------
  Frontend              React, TypeScript, Vite
  Styling               Tailwind CSS
  Interactive map       MapLibre GL JS
  Map data              GeoJSON
  Backend               Python, FastAPI
  Database              PostgreSQL; SQLite for initial prototype
  Realtime updates      WebSockets
  ML classifier         LightGBM
  Spatial estimation    Gaussian Process / Kriging
  Agent orchestration   LangGraph
  Financial rules       Deterministic Python services
  Audit                 Append-only records and hash chain
  Charts                ECharts or equivalent

------------------------------------------------------------------------

# 6. Suggested Database Model

The following is a starting point, not a final production schema.

  -----------------------------------------------------------------------
  Entity                              Purpose
  ----------------------------------- -----------------------------------
  `users`                             Login identity and role

  `farmer_profiles`                   Farmer details

  `farms`                             Farm location, area, and boundary

  `crops`                             Crop information

  `insurance_policies`                Policy dates, coverage, and status

  `policy_rules`                      Trigger, payout, and cap parameters

  `bank_account_references`           Masked payment destination and
                                      verification state

  `sensors`                           Gauge location and metadata

  `sensor_readings`                   Original time-series observations

  `sensor_assessments`                Fault class, trust score, and
                                      reasons

  `weather_events`                    Event time, area, and scenario
                                      reference

  `satellite_evidence`                Imagery/evidence metadata and
                                      timestamps

  `farm_risk_estimates`               Farm estimate, uncertainty, and
                                      model version

  `claims`                            Claim status and calculated
                                      entitlement

  `claim_evidence`                    Evidence references used for a
                                      claim

  `agent_runs`                        Agent execution and handoff trace

  `approvals`                         Reviewer, decision, timestamp, and
                                      reason

  `payment_transactions`              Simulated payment instruction and
                                      status

  `disputes`                          Farmer disputes and resolution

  `audit_events`                      Append-only audit records
  -----------------------------------------------------------------------

### Data design principles

-   Store original sensor readings separately from corrected or
    interpreted values.
-   Store timestamps and source references for evidence.
-   Store model and policy versions used in each claim.
-   Use stable event and farm identifiers.
-   Use database constraints to prevent duplicate settlement.
-   Apply role-based access to farmer, policy, and payment information.
-   Keep sensitive payment details masked in user interfaces.

------------------------------------------------------------------------

# 7. Suggested Team Division

For a team of five:

  -----------------------------------------------------------------------
  Member                  Primary ownership       Supporting work
  ----------------------- ----------------------- -----------------------
  Member 1                Farmer UI and           Farmer claim tracking
                          onboarding              

  Member 2                Weather simulation and  Sensor reliability and
                          ML                      risk estimation

  Member 3                AI agents and LangGraph Agent tools, state,
                                                  handoffs, approval
                                                  pauses

  Member 4                Insurer dashboard and   Payment simulation and
                          claim engine            financial views

  Member 5                Backend, database,      Audit trail, API
                          integration             contracts, end-to-end
                                                  testing
  -----------------------------------------------------------------------

For a team of four, combine backend/integration with the insurer
dashboard or combine farmer UI with the map frontend, depending on team
strengths.

### Team coordination rules

-   Agree on API contracts and database identifiers before parallel
    development.
-   Use one shared Git repository.
-   Use feature branches and pull requests.
-   Maintain a seeded demo dataset.
-   Assign one person responsibility for integration.
-   Avoid separate teams inventing incompatible field names or status
    values.

------------------------------------------------------------------------

# 8. Suggested Four-Day Hackathon Schedule

This schedule assumes a focused prototype, not production readiness.

  -----------------------------------------------------------------------
  Day                     Main focus              Expected result
  ----------------------- ----------------------- -----------------------
  Day 1                   Stages 1--3             Login, farmer/policy
                                                  records, satellite map

  Day 2                   Stages 4--6             Simulation, sensor ML,
                                                  farm-level risk

  Day 3                   Stages 7--8             Four agents, claim
                                                  calculation, approval

  Day 4                   Stages 9--12            Insurer/farmer views,
                                                  simulated payments,
                                                  audit, integration,
                                                  demo
  -----------------------------------------------------------------------

### Day 1 --- Foundation and map

-   Freeze the scope and identifiers.
-   Set up frontend, backend, database, and repository.
-   Build role-based dashboards.
-   Create farmer and policy records.
-   Display seeded farms on the satellite map.

### Day 2 --- Simulation and intelligence

-   Build the fixed-seed district generator.
-   Add storms, gauges, rainfall, and water levels.
-   Add fault injection and LightGBM classification.
-   Calculate trust scores.
-   Produce farm-level estimates and map overlays.

### Day 3 --- Agents and claims

-   Build four agent workflows.
-   Connect agent tools to simulation, evidence, policy, and risk
    services.
-   Add deterministic claim calculation.
-   Add human approval.
-   Test both faulty-sensor and genuine-localised-rainfall scenarios.

### Day 4 --- Settlement and proof

-   Finish insurer and farmer views.
-   Add simulated payment.
-   Add notifications and dispute flow.
-   Add audit records and duplicate-payment checks.
-   Run end-to-end tests.
-   Prepare slides and backup demo.

------------------------------------------------------------------------

# 9. Prioritisation if Time Is Limited

Do not attempt to build every advanced feature at once.

### P0 --- Essential foundation

-   Working website and role-based login.
-   Farmer and policy records.
-   Satellite map with farms.
-   Reproducible weather simulation.
-   Sensor fault detection and trust.
-   Farm-level estimates.
-   Deterministic claim calculation.
-   Simulated payment ledger.

### P1 --- Core differentiation

-   Four agents with visible tool use and handoffs.
-   Human approval.
-   Faulty-sensor scenario.
-   Genuine localised-rainfall scenario.
-   Farmer and insurer claim views.
-   Basic audit trail.

### P2 --- Strong supporting features

-   Basis-Risk Lab.
-   Calibration and uncertainty evaluation.
-   Hash-chain verification and replay.
-   Portfolio exposure dashboard.
-   Basic financial reports.

### P3 --- Optional extensions

-   Dynamic underwriting recommendations.
-   Advanced fraud-network analysis.
-   Liquidity and reserve forecasting.
-   Real satellite-derived flood analysis.
-   Real messaging and banking integrations.

### Features not to cut

If time becomes very limited, preserve:

1.  Resettable simulation.
2.  Satellite map with farm boundaries.
3.  Sensor trust and fault detection.
4.  Farm-level risk estimate.
5.  Deterministic claim engine.
6.  Both signature scenarios.
7.  Visible agent trace.
8.  Human approval.
9.  Duplicate-payment protection.
10. Basic audit history.

------------------------------------------------------------------------

# 10. Final Demonstration Plan

Target duration: approximately 4 minutes and 30 seconds.

  -----------------------------------------------------------------------
  Time                                Demonstration
  ----------------------------------- -----------------------------------
  0:00--0:20                          Open insurer operations dashboard
                                      and satellite map

  0:20--0:55                          Start flood simulation and show
                                      affected farms

  0:55--1:15                          Inject a suspicious gauge spike

  1:15--2:05                          Show four agents investigating and
                                      handing off work

  2:05--2:25                          Reviewer approves sensor quarantine
                                      or the appropriate investigation
                                      action

  2:25--2:55                          Run genuine localised-rainfall
                                      scenario

  2:55--3:35                          Show farm-level estimates and
                                      basis-risk comparison

  3:35--4:10                          Show claim approval, simulated
                                      farmer payment, and auditor replay

  4:10--4:30                          Summarise prototype scope, metrics,
                                      and limitations
  -----------------------------------------------------------------------

### Suggested opening statement

"A single broken rain gauge can make an insurer pay the wrong
farmer---or deny the right one. ParaTrust uses AI agents to investigate
the evidence, while a transparent settlement engine ensures every payout
is justified and auditable."

### Suggested closing statement

"ParaTrust connects climate intelligence with financial accountability.
It helps insurers investigate uncertain weather evidence, estimate
farm-level risk, and coordinate fast, fair, and auditable parametric
insurance settlements."

------------------------------------------------------------------------

# 11. Key Risks and Controls

  -----------------------------------------------------------------------
  Risk                                Control
  ----------------------------------- -----------------------------------
  Satellite imagery is not current    Display acquisition time and
                                      distinguish basemap from event
                                      evidence

  Genuine localised rainfall is       Keep localised-cell as a separate
  mistaken for sensor failure         scenario/class and investigate
                                      multiple evidence sources

  LLM gives an incorrect payout       Use deterministic policy and
  amount                              financial services for calculations

  Duplicate claim payment             Enforce idempotency and database
                                      uniqueness

  Agent failure or LLM outage         Provide deterministic fallback for
                                      critical calculations and workflow
                                      steps

  Unclear farmer communication        Use simple status messages and
                                      explain settlement reasons

  Demo depends on external APIs       Keep seeded data, cached map assets
                                      where permitted, and an offline
                                      demo path

  Illustrative metrics appear real    Label mock values and report only
                                      measured test results as actual
                                      performance
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 12. Definition of Done

ParaTrust's hackathon prototype is ready when a judge can follow this
complete journey without manual database intervention:

1.  A farmer and policy exist in the platform.
2.  The farm appears on the satellite map.
3.  A reproducible weather event begins.
4.  Sensors report rainfall and water-level readings.
5.  The system investigates a suspicious sensor.
6.  The system distinguishes a genuine localised event from a sensor
    fault.
7.  The platform estimates risk at farm level and displays uncertainty.
8.  Four agents investigate the event and produce a recommendation.
9.  A deterministic claim engine calculates the eligible amount.
10. An authorised insurer reviewer approves or holds the claim.
11. The payment is simulated and recorded without duplication.
12. The farmer sees the updated claim and payment status.
13. An auditor can trace the decision and verify the audit record.

**Final development principle:** Build one reliable end-to-end insurance
journey before adding optional sophistication. ParaTrust's strongest
demonstration is not the number of AI features; it is the ability to
turn uncertain climate evidence into a transparent, controlled, and
auditable financial decision.
