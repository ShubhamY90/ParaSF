import { useState, useEffect } from "react";
import PageLayout from "../shared/PageLayout";
import { getMyFarms, listPolicies, FarmOut, PolicyOut } from "../../api/stage2";

type StatusKey = "active" | "expired" | "cancelled" | string;

function statusBadge(status: StatusKey) {
  const map: Record<string, string> = {
    active: "bg-green-900/50 text-green-300 border-green-700",
    expired: "bg-red-900/50 text-red-300 border-red-700",
    cancelled: "bg-gray-700 text-gray-400 border-gray-600",
  };
  const cls = map[status] ?? "bg-navy-700 text-gray-300 border-navy-600";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${cls}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function PolicyCard({ policy }: { policy: PolicyOut }) {
  return (
    <div className="bg-navy-800 border border-navy-700 rounded-xl p-5 space-y-3">
      <div className="flex items-start justify-between">
        <span className="font-mono text-brand-blue font-semibold">{policy.policy_number}</span>
        {statusBadge(policy.status)}
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
        <div>
          <p className="text-gray-500 text-xs">Coverage Start</p>
          <p className="text-white">{policy.coverage_start}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Coverage End</p>
          <p className="text-white">{policy.coverage_end}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Sum Insured</p>
          <p className="text-white">₹{policy.sum_insured.toLocaleString("en-IN")}</p>
        </div>
        {policy.payout_limit && (
          <div>
            <p className="text-gray-500 text-xs">Payout Cap</p>
            <p className="text-white">₹{policy.payout_limit.toLocaleString("en-IN")}</p>
          </div>
        )}
        {policy.rainfall_trigger_mm && (
          <div>
            <p className="text-gray-500 text-xs">Rainfall Trigger</p>
            <p className="text-white">{policy.rainfall_trigger_mm} mm</p>
          </div>
        )}
        {policy.rainfall_max_payout_mm && (
          <div>
            <p className="text-gray-500 text-xs">Max Payout Rainfall</p>
            <p className="text-white">{policy.rainfall_max_payout_mm} mm</p>
          </div>
        )}
        {policy.flood_trigger_level && (
          <div>
            <p className="text-gray-500 text-xs">Flood Trigger Level</p>
            <p className="text-white">{policy.flood_trigger_level} m</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MyPolicyPage() {
  const [farms, setFarms] = useState<FarmOut[]>([]);
  const [policies, setPolicies] = useState<PolicyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMyFarms(), listPolicies()])
      .then(([f, p]) => { setFarms(f); setPolicies(p); })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load data"))
      .finally(() => setLoading(false));
  }, []);

  const getPoliciesForFarm = (farmId: number) =>
    policies.filter((p) => p.farm_id === farmId);

  return (
    <PageLayout title="My Policy" subtitle="Insurance coverage for your farms" backTo="/farmer">
      {loading && <p className="text-gray-400">Loading…</p>}
      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      {!loading && !error && farms.length === 0 && (
        <div className="bg-navy-800 border border-navy-700 rounded-xl p-8 text-center space-y-2">
          <p className="text-3xl">📋</p>
          <p className="text-white font-semibold">No farms registered</p>
          <p className="text-gray-400 text-sm">Register a farm first before viewing policies.</p>
        </div>
      )}

      {!loading && farms.map((farm) => {
        const farmPolicies = getPoliciesForFarm(farm.id);
        return (
          <div key={farm.id} className="space-y-3">
            <h2 className="text-white font-semibold text-lg flex items-center gap-2">
              🌾 {farm.name}
            </h2>
            {farmPolicies.length === 0 ? (
              <div className="bg-navy-800 border border-navy-700 rounded-xl p-5 text-gray-400 text-sm">
                No policy assigned yet. Contact your insurer.
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {farmPolicies.map((p) => <PolicyCard key={p.id} policy={p} />)}
              </div>
            )}
          </div>
        );
      })}
    </PageLayout>
  );
}
