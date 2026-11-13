import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import PageLayout from "../shared/PageLayout";
import { getFarmerDetail, FarmerDetail, FarmOut, PolicyOut } from "../../api/stage2";

function FarmCard({ farm }: { farm: FarmOut }) {
  const crop = farm.crops[0];
  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-4 space-y-2">
      <div className="flex justify-between items-start">
        <p className="text-white font-semibold">{farm.name}</p>
        {farm.area_hectares && (
          <span className="text-xs bg-navy-700 text-gray-400 px-2 py-0.5 rounded-full">{farm.area_hectares} ha</span>
        )}
      </div>
      {(farm.latitude || farm.longitude) && (
        <p className="text-xs text-gray-500">📍 {farm.latitude?.toFixed(5)}, {farm.longitude?.toFixed(5)}</p>
      )}
      {crop && (
        <p className="text-xs text-gray-400">🌱 {crop.crop_type}{crop.season ? ` · ${crop.season}` : ""}</p>
      )}
    </div>
  );
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    active: "bg-green-900/50 text-green-300 border-green-700",
    expired: "bg-red-900/50 text-red-300 border-red-700",
    cancelled: "bg-gray-700 text-gray-400 border-gray-600",
  };
  const cls = map[status] ?? "bg-navy-700 text-gray-300 border-navy-600";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${cls}`}>
      {status}
    </span>
  );
}

function PolicyCard({ policy }: { policy: PolicyOut }) {
  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-4 space-y-2">
      <div className="flex justify-between items-center">
        <span className="font-mono text-brand-blue text-sm">{policy.policy_number}</span>
        {statusBadge(policy.status)}
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-400">
        <p>Start: <span className="text-white">{policy.coverage_start}</span></p>
        <p>End: <span className="text-white">{policy.coverage_end}</span></p>
        <p>Sum Insured: <span className="text-white">₹{policy.sum_insured.toLocaleString("en-IN")}</span></p>
        {policy.rainfall_trigger_mm && <p>Trigger: <span className="text-white">{policy.rainfall_trigger_mm} mm</span></p>}
      </div>
    </div>
  );
}

export default function FarmerDetailPage() {
  const { profileId } = useParams<{ profileId: string }>();
  const [farmer, setFarmer] = useState<FarmerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!profileId) return;
    getFarmerDetail(parseInt(profileId, 10))
      .then(setFarmer)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load farmer"))
      .finally(() => setLoading(false));
  }, [profileId]);

  return (
    <PageLayout title="Farmer Detail" backTo="/insurer/farmers">
      {loading && <p className="text-gray-400">Loading…</p>}
      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      {!loading && farmer && (
        <div className="space-y-8">
          {/* Profile */}
          <div className="bg-navy-800 border border-navy-700 rounded-xl p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold text-white">{farmer.full_name}</h2>
                <p className="text-gray-400 text-sm">{farmer.email}</p>
              </div>
              <Link
                to={`/insurer/policies/new?farmerId=${farmer.id}`}
                className="bg-brand-blue text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition"
              >
                + Create Policy
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              {farmer.phone && (
                <div>
                  <p className="text-gray-500 text-xs">Phone</p>
                  <p className="text-white">{farmer.phone}</p>
                </div>
              )}
              {farmer.district && (
                <div>
                  <p className="text-gray-500 text-xs">District</p>
                  <p className="text-white">{farmer.district}</p>
                </div>
              )}
              {farmer.state && (
                <div>
                  <p className="text-gray-500 text-xs">State</p>
                  <p className="text-white">{farmer.state}</p>
                </div>
              )}
            </div>
          </div>

          {/* Farms */}
          <div className="space-y-3">
            <h3 className="text-white font-semibold text-lg">
              🌾 Farms <span className="text-gray-500 text-sm font-normal">({farmer.farms.length})</span>
            </h3>
            {farmer.farms.length === 0 ? (
              <p className="text-gray-400 text-sm">No farms registered.</p>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {farmer.farms.map((f) => <FarmCard key={f.id} farm={f} />)}
              </div>
            )}
          </div>

          {/* Policies */}
          <div className="space-y-3">
            <h3 className="text-white font-semibold text-lg">
              📋 Policies <span className="text-gray-500 text-sm font-normal">({farmer.policies.length})</span>
            </h3>
            {farmer.policies.length === 0 ? (
              <p className="text-gray-400 text-sm">No policies assigned yet.</p>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {farmer.policies.map((p) => <PolicyCard key={p.id} policy={p} />)}
              </div>
            )}
          </div>
        </div>
      )}
    </PageLayout>
  );
}
