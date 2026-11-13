import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../shared/PageLayout";
import { searchFarmers, FarmerSummary } from "../../api/stage2";

export default function FarmerRegistryPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [farmers, setFarmers] = useState<FarmerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((q: string) => {
    setLoading(true);
    setError(null);
    searchFarmers(q || undefined)
      .then(setFarmers)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load farmers"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(""); }, [load]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    load(query);
  }

  return (
    <PageLayout title="Farmer Registry" subtitle="Search and manage registered farmers" backTo="/insurer">
      <form onSubmit={handleSearch} className="flex gap-3 max-w-md">
        <input
          className="flex-1 bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-brand-blue"
          placeholder="Search by name, email, or district…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          className="bg-brand-blue text-white font-semibold px-4 py-2 rounded-lg hover:opacity-90 transition text-sm"
        >
          Search
        </button>
      </form>

      {loading && <p className="text-gray-400">Loading…</p>}
      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      {!loading && !error && farmers.length === 0 && (
        <div className="bg-navy-800 border border-navy-700 rounded-xl p-8 text-center text-gray-400">
          No farmers found{query ? ` for "${query}"` : ""}.
        </div>
      )}

      {!loading && farmers.length > 0 && (
        <div className="bg-navy-800 border border-navy-700 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-700 text-gray-400 text-left">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">District</th>
                <th className="px-4 py-3 font-medium text-center">Farms</th>
                <th className="px-4 py-3 font-medium text-center">Policies</th>
              </tr>
            </thead>
            <tbody>
              {farmers.map((f, i) => (
                <tr
                  key={f.id}
                  className={`border-b border-navy-700/50 hover:bg-navy-700/40 cursor-pointer transition ${i === farmers.length - 1 ? "border-b-0" : ""}`}
                  onClick={() => navigate(`/insurer/farmers/${f.id}`)}
                >
                  <td className="px-4 py-3 text-white font-medium">{f.full_name}</td>
                  <td className="px-4 py-3 text-gray-300">{f.email}</td>
                  <td className="px-4 py-3 text-gray-300">{f.district ?? "—"}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="bg-navy-700 text-gray-300 px-2 py-0.5 rounded-full text-xs">{f.farm_count}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="bg-navy-700 text-gray-300 px-2 py-0.5 rounded-full text-xs">{f.policy_count}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageLayout>
  );
}
