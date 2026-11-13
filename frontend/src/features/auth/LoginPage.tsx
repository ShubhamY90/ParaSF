import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const DEMO_ACCOUNTS = [
  { label: "🌾 Farmer", email: "farmer@paratrust.dev", pass: "farmer123" },
  { label: "🏦 Insurer", email: "insurer@paratrust.dev", pass: "insurer123" },
  { label: "📋 Auditor", email: "auditor@paratrust.dev", pass: "auditor123" },
  { label: "⚙️ Admin", email: "admin@paratrust.dev", pass: "admin123" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(eMail: string, pass: string) {
    setError("");
    setLoading(true);
    try {
      const role = await login(eMail, pass);
      navigate(`/${role}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await handleLogin(email, password);
  }

  return (
    <div className="flex items-center justify-center min-h-[80vh] px-4 py-8">
      <div className="w-full max-w-md bg-navy-800 rounded-2xl p-8 border border-navy-700 space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-2xl font-bold text-white">Welcome back</h2>
          <p className="text-gray-400 text-sm">Sign in to your ParaTrust account</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Quick Demo Login */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold text-center">
            One-Click Demo Sign In (Firebase)
          </p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                disabled={loading}
                onClick={() => {
                  setEmail(acc.email);
                  setPassword(acc.pass);
                  handleLogin(acc.email, acc.pass);
                }}
                className="px-3 py-2 text-xs rounded-lg bg-navy-700 hover:bg-navy-600 border border-navy-600 text-gray-200 hover:text-white transition font-medium flex items-center justify-center gap-1.5"
              >
                <span>{acc.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-navy-700"></div>
          <span className="flex-shrink mx-3 text-gray-500 text-xs uppercase">or with credentials</span>
          <div className="flex-grow border-t border-navy-700"></div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 bg-navy-700 border border-navy-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand-green transition"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1.5">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-navy-700 border border-navy-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-brand-green transition"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-brand-green text-navy font-bold rounded-lg hover:bg-green-400 disabled:opacity-60 transition"
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <div className="text-center text-sm text-gray-400">
          Don't have an account?{" "}
          <Link to="/register" className="text-brand-green hover:underline">Register here</Link>
        </div>
      </div>
    </div>
  );
}
