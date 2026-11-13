import { useAuth } from "../../hooks/useAuth";

export default function AdminDashboard() {
  const { user } = useAuth();
  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
      <h1 className="text-3xl font-bold text-white">Admin Panel ⚙️</h1>
      <p className="text-gray-400">Platform Administrator: {user?.full_name ?? user?.email}</p>
      <div className="bg-navy-800 border border-navy-700 rounded-xl p-6">
        <p className="text-gray-400 text-sm">
          Admin tools (user management, system config, seed controls) will be available in later stages.
        </p>
      </div>
    </div>
  );
}
