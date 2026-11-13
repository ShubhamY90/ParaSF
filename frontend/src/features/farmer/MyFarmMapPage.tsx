/**
 * Stage 3 — My Farm Map (farmer)
 *
 * Shows the farmer's own registered farm(s) on a satellite map, centred on
 * the farm centroid. Sensor and water layers are visible for geographic
 * context. The detail panel opens automatically for farmers with a single farm.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyFarms, FarmOut } from "../../api/stage2";
import MapView from "../map/MapView";

export default function MyFarmMapPage() {
  const [farms, setFarms] = useState<FarmOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyFarms()
      .then(setFarms)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load farms"))
      .finally(() => setLoading(false));
  }, []);

  // Pick the first farm with coordinates to centre the map.
  const primaryFarm = farms.find(f => f.latitude != null && f.longitude != null);
  const centreOnFarm = primaryFarm
    ? { lat: primaryFarm.latitude!, lng: primaryFarm.longitude!, zoom: 14 }
    : null;

  // Auto-open detail panel when there's exactly one farm.
  const autoOpenId = farms.length === 1 && primaryFarm ? primaryFarm.id : null;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Page header */}
      <div className="flex items-center justify-between px-6 py-3 bg-navy-800 border-b border-navy-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/farmer" className="text-sm text-brand-blue hover:underline">← Dashboard</Link>
          <span className="text-gray-600">|</span>
          <h1 className="text-white font-semibold text-sm">My Farm Map</h1>
          <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/50 text-green-300 border border-green-700">
            Stage 3 Active
          </span>
        </div>
        <p className="text-xs text-gray-500 hidden sm:block">
          Satellite view of your registered farm · Simulated sensors and boundaries
        </p>
      </div>

      {/* Loading / error states before map initialises */}
      {loading && (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          Loading your farm data…
        </div>
      )}
      {!loading && error && (
        <div className="flex-1 flex items-center justify-center">
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-5 py-4 text-sm max-w-sm text-center">
            {error}
            <div className="mt-3">
              <Link to="/farmer/farms/new" className="text-brand-blue hover:underline text-xs">
                Register a farm →
              </Link>
            </div>
          </div>
        </div>
      )}
      {!loading && !error && farms.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="bg-navy-800 border border-navy-700 rounded-xl p-10 text-center space-y-3 max-w-sm">
            <p className="text-4xl">🗺️</p>
            <p className="text-white font-semibold">No farms registered yet</p>
            <p className="text-gray-400 text-sm">Register a farm with GPS coordinates to view it on the satellite map.</p>
            <Link
              to="/farmer/farms/new"
              className="inline-block mt-2 bg-brand-blue text-white font-semibold px-5 py-2 rounded-lg hover:opacity-90 transition text-sm"
            >
              Register Your Farm
            </Link>
          </div>
        </div>
      )}

      {/* Map — shown once we have farm data (even with no GPS coordinates, the
          map still shows the district so the farmer can orient themselves). */}
      {!loading && !error && farms.length > 0 && (
        <div className="flex-1 overflow-hidden">
          <MapView
            height="100%"
            centreOnFarm={centreOnFarm}
            initialSelectedFarmId={autoOpenId}
            layerVisibility={{ district: false }}
          />
        </div>
      )}
    </div>
  );
}
