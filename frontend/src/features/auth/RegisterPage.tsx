import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { UserRole } from "../../api/auth";

const AVAILABLE_ROLES: { value: UserRole; label: string; desc: string }[] = [
  { value: "farmer", label: "🌾 Farmer", desc: "Insured farms, alerts & claim payouts" },
  { value: "insurer", label: "🏦 Insurer", desc: "Policies, operations map & risk" },
  { value: "auditor", label: "📋 Auditor", desc: "Sensor health & audit records" },
  { value: "admin", label: "⚙️ Admin", desc: "Platform admin & configuration" },
];

export default function RegisterPage() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role: "farmer" as UserRole });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      const role = await login(form.email, form.password);
      navigate(`/${role}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  const selectedRoleObj = AVAILABLE_ROLES.find((r) => r.value === form.role);

  return (
    <div className="flex items-center justify-center min-h-[80vh] px-4 py-8">
      <div className="w-full max-w-lg bg-navy-800 rounded-2xl p-8 border border-navy-700 space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-2xl font-bold text-white">Create your account</h2>
          <p className="text-gray-400 text-sm">Join ParaTrust platform</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Role selector */}
          <div className="space-y-1.5">
            <label className="block text-sm text-gray-300 font-medium">Select Role</label>
            <div className="grid grid-cols-2 gap-2">
              {AVAILABLE_ROLES.map((r) => (
                <button
                  type="button"
                  key={r.value}
                  onClick={() => setForm((f) => ({ ...f, role: r.value }))}
                  className={`p-2.5 rounded-xl border text-left transition flex flex-col gap-0.5 ${
                    form.role === r.value
                      ? "border-brand-green bg-green-950/50 text-white ring-1 ring-brand-green"
                      : "border-navy-600 bg-navy-700/60 text-gray-300 hover:border-navy-500"
                  }`}
                >
                  <span className="text-sm font-semibold">{r.label}</span>
                  <span className="text-[11px] text-gray-400 leading-tight">{r.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Full Name</label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              className="w-full px-4 py-2.5 bg-navy-700 border border-navy-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand-green transition"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Email</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              className="w-full px-4 py-2.5 bg-navy-700 border border-navy-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand-green transition"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Password</label>
            <input
              type="password"
              required
              minLength={6}
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              className="w-full px-4 py-2.5 bg-navy-700 border border-navy-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand-green transition"
              placeholder="At least 6 characters"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-brand-green text-navy font-bold rounded-lg hover:bg-green-400 disabled:opacity-60 transition"
          >
            {loading ? "Creating account…" : `Create ${selectedRoleObj?.label.split(" ")[1] || "Account"}`}
          </button>
        </form>

        <div className="text-center text-sm text-gray-400">
          Already have an account?{" "}
          <Link to="/login" className="text-brand-green hover:underline">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
