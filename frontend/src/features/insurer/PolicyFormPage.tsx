import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import PageLayout from "../shared/PageLayout";
import {
  createPolicy,
  searchFarmers,
  getFarmerDetail,
  FarmerSummary,
  FarmOut,
  PolicyCreate,
} from "../../api/stage2";

const STATUSES = ["active", "expired", "cancelled"];

function generatePolicyNumber(): string {
  const year = new Date().getFullYear();
  const rand = Math.floor(10000 + Math.random() * 90000);
  return `PT-${year}-${rand}`;
}

export default function PolicyFormPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedFarmerId = searchParams.get("farmerId");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [policyNumber, setPolicyNumber] = useState(generatePolicyNumber());
  const [farmers, setFarmers] = useState<FarmerSummary[]>([]);
  const [selectedFarmerId, setSelectedFarmerId] = useState<number | "">(
    preselectedFarmerId ? parseInt(preselectedFarmerId, 10) : ""
  );
  const [farmerSearch, setFarmerSearch] = useState("");
  const [farms, setFarms] = useState<FarmOut[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<number | "">("");

  const [coverageStart, setCoverageStart] = useState("");
  const [coverageEnd, setCoverageEnd] = useState("");
  const [sumInsured, setSumInsured] = useState("");
  const [rainfallTrigger, setRainfallTrigger] = useState("");
  const [rainfallMax, setRainfallMax] = useState("");
  const [floodTrigger, setFloodTrigger] = useState("");
  const [payoutLimit, setPayoutLimit] = useState("");
  const [status, setStatus] = useState("active");

  // Load farmers list
  useEffect(() => {
    searchFarmers(farmerSearch || undefined).then(setFarmers).catch(() => {});
  }, [farmerSearch]);

  // Load farms when farmer changes
  useEffect(() => {
    if (!selectedFarmerId) { setFarms([]); setSelectedFarmId(""); return; }
    getFarmerDetail(selectedFarmerId as number)
      .then((detail) => { setFarms(detail.farms ?? []); })
      .catch(() => { setFarms([]); });
  }, [selectedFarmerId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!selectedFarmerId) { setError("Select a farmer"); return; }
    if (!selectedFarmId) { setError("Select a farm"); return; }
    if (!coverageStart || !coverageEnd) { setError("Coverage dates are required"); return; }
    if (!sumInsured || isNaN(parseFloat(sumInsured))) { setError("Sum insured is required"); return; }

    setSaving(true);
    try {
      const payload: PolicyCreate = {
        policy_number: policyNumber.trim(),
        farm_id: selectedFarmId as number,
        farmer_profile_id: selectedFarmerId as number,
        coverage_start: coverageStart,
        coverage_end: coverageEnd,
        sum_insured: parseFloat(sumInsured),
        status,
        ...(rainfallTrigger ? { rainfall_trigger_mm: parseFloat(rainfallTrigger) } : {}),
        ...(rainfallMax ? { rainfall_max_payout_mm: parseFloat(rainfallMax) } : {}),
        ...(floodTrigger ? { flood_trigger_level: parseFloat(floodTrigger) } : {}),
        ...(payoutLimit ? { payout_limit: parseFloat(payoutLimit) } : {}),
      };
      await createPolicy(payload);
      navigate("/insurer/policies");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create policy");
    } finally {
      setSaving(false);
    }
  }

  const inputCls =
    "w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-brand-blue";

  return (
    <PageLayout title="Create Policy" subtitle="Issue a new insurance policy" backTo="/insurer/policies">
      <form onSubmit={handleSubmit} className="bg-navy-800 border border-navy-700 rounded-xl p-6 space-y-6 max-w-2xl">
        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
        )}

        {/* Policy Number */}
        <div className="space-y-1">
          <label className="text-sm text-gray-400">Policy Number *</label>
          <div className="flex gap-2">
            <input className={inputCls} value={policyNumber} onChange={(e) => setPolicyNumber(e.target.value)} required />
            <button
              type="button"
              onClick={() => setPolicyNumber(generatePolicyNumber())}
              className="text-xs bg-navy-700 text-gray-300 px-3 rounded-lg hover:bg-navy-600 transition whitespace-nowrap"
            >
              Regenerate
            </button>
          </div>
        </div>

        {/* Farmer */}
        <div className="space-y-1">
          <label className="text-sm text-gray-400">Farmer *</label>
          <input
            className={inputCls}
            placeholder="Search farmer by name or email…"
            value={farmerSearch}
            onChange={(e) => setFarmerSearch(e.target.value)}
          />
          <select
            className={inputCls}
            value={selectedFarmerId}
            onChange={(e) => setSelectedFarmerId(e.target.value ? parseInt(e.target.value, 10) : "")}
            required
          >
            <option value="">— Select farmer —</option>
            {farmers.map((f) => (
              <option key={f.id} value={f.id}>{f.full_name} ({f.email})</option>
            ))}
          </select>
        </div>

        {/* Farm */}
        <div className="space-y-1">
          <label className="text-sm text-gray-400">Farm *</label>
          <select
            className={inputCls}
            value={selectedFarmId}
            onChange={(e) => setSelectedFarmId(e.target.value ? parseInt(e.target.value, 10) : "")}
            disabled={!selectedFarmerId || farms.length === 0}
            required
          >
            <option value="">— Select farm —</option>
            {farms.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
          {selectedFarmerId && farms.length === 0 && (
            <p className="text-xs text-yellow-500">No farms found for this farmer.</p>
          )}
        </div>

        {/* Coverage dates */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Coverage Start *</label>
            <input className={inputCls} type="date" value={coverageStart} onChange={(e) => setCoverageStart(e.target.value)} required />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Coverage End *</label>
            <input className={inputCls} type="date" value={coverageEnd} onChange={(e) => setCoverageEnd(e.target.value)} required />
          </div>
        </div>

        {/* Financial */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Sum Insured (₹) *</label>
            <input className={inputCls} type="number" min="0" step="1000" placeholder="e.g. 100000" value={sumInsured} onChange={(e) => setSumInsured(e.target.value)} required />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Payout Limit (₹)</label>
            <input className={inputCls} type="number" min="0" step="1000" placeholder="optional cap" value={payoutLimit} onChange={(e) => setPayoutLimit(e.target.value)} />
          </div>
        </div>

        {/* Triggers */}
        <fieldset className="space-y-4">
          <legend className="text-brand-blue font-semibold text-sm uppercase tracking-wider">Trigger Conditions</legend>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm text-gray-400">Rainfall Trigger (mm)</label>
              <input className={inputCls} type="number" min="0" step="1" placeholder="Payout begins above this" value={rainfallTrigger} onChange={(e) => setRainfallTrigger(e.target.value)} />
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-400">Rainfall Max Payout (mm)</label>
              <input className={inputCls} type="number" min="0" step="1" placeholder="Full payout at this rainfall" value={rainfallMax} onChange={(e) => setRainfallMax(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1 max-w-xs">
            <label className="text-sm text-gray-400">Flood Trigger Level (m)</label>
            <input className={inputCls} type="number" min="0" step="0.1" placeholder="optional" value={floodTrigger} onChange={(e) => setFloodTrigger(e.target.value)} />
          </div>
        </fieldset>

        {/* Status */}
        <div className="space-y-1">
          <label className="text-sm text-gray-400">Status</label>
          <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-brand-blue text-white font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
        >
          {saving ? "Creating…" : "Create Policy"}
        </button>
      </form>
    </PageLayout>
  );
}
