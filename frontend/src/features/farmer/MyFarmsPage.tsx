import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PageLayout from "../shared/PageLayout";
import { getMyFarms, FarmOut } from "../../api/stage2";

function FarmCard({ farm }: { farm: FarmOut }) {
  const crop = farm.crops[0];
  return (
    <div className="bg-navy-800 border border-navy-700 rounded-xl p-5 space-y-3">
      <div className="flex items-start justify-between">
        <h3 className="font-semibold text-white text-lg">{farm.name}</h3>
        <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700 text-gray-400">
          {farm.area_hectares ? `${farm.area_hectares} ha` : "Area TBD"}
        </span>
      </div>

      {(farm.latitude || farm.longitude) && (
        <p className="text-xs text-gray-500">
          📍 {farm.latitude?.toFixed(5)}, {farm.longitude?.toFixed(5)}
        </p>
      )}

      {crop ? (
        <div className="flex gap-2 flex-wrap">
          <span className="text-xs bg-navy-700 text-gray-300 px-2 py-0.5 rounded-full">
            🌱 {crop.crop_type}
          </span>
          {crop.season && (
            <span className="text-xs bg-navy-700 text-gray-300 px-2 py-0.5 rounded-full">
              {crop.season}
            </span>
          )}
          {crop.area_hectares && (
            <span className="text-xs bg-navy-700 text-gray-300 px-2 py-0.5 rounded-full">
              {crop.area_hectares} ha crop
            </span>
          )}
        </div>
      ) : (
        <p className="text-xs text-gray-500">No crop recorded</p>
      )}
    </div>
  );
}

export default function MyFarmsPage() {
  const [farms, setFarms] = useState<FarmOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyFarms()
      .then(setFarms)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load farms"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageLayout title="My Farms" subtitle="All registered farms" backTo="/farmer">
      <div className="flex justify-end">
        <Link
          to="/farmer/farms/new"
          className="bg-brand-blue text-white font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition text-sm"
        >
          + Add Farm
        </Link>
      </div>

      {loading && <p className="text-gray-400">Loading…</p>}
      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      {!loading && !error && farms.length === 0 && (
        <div className="bg-navy-800 border border-navy-700 rounded-xl p-10 text-center space-y-4">
          <p className="text-4xl">🌾</p>
          <p className="text-white font-semibold">No farms registered yet</p>
          <p className="text-gray-400 text-sm">Register your first farm to get started with ParaTrust coverage.</p>
          <Link
            to="/farmer/farms/new"
            className="inline-block mt-2 bg-brand-blue text-white font-semibold px-5 py-2 rounded-lg hover:opacity-90 transition text-sm"
          >
            Register Your First Farm
          </Link>
        </div>
      )}

      {!loading && farms.length > 0 && (
        <div className="grid sm:grid-cols-2 gap-4">
          {farms.map((farm) => <FarmCard key={farm.id} farm={farm} />)}
        </div>
      )}
    </PageLayout>
  );
}
