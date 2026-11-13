import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const roles = [
  {
    icon: "🌾",
    title: "For Farmers",
    desc: "Register your farm, track climate events, and receive transparent parametric payouts directly to your account.",
    color: "border-brand-green",
  },
  {
    icon: "🏦",
    title: "For Insurers & Banks",
    desc: "AI-assisted investigation, automated risk assessment, and policy-based claim calculation with full audit trails.",
    color: "border-brand-blue",
  },
  {
    icon: "📋",
    title: "For Auditors",
    desc: "Inspect every decision, replay agent actions, verify calculations, and validate the full chain of evidence.",
    color: "border-purple-400",
  },
];

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-5xl mx-auto px-6 py-16 space-y-20">
      {/* Hero */}
      <section className="text-center space-y-6">
        <div className="inline-block px-4 py-1.5 rounded-full bg-brand-green/10 text-brand-green text-sm font-medium border border-brand-green/30">
          Agentic Climate Insurance Platform
        </div>
        <h1 className="text-5xl font-extrabold leading-tight">
          Transparent Parametric
          <br />
          <span className="text-brand-green">Insurance Settlements</span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          ParaTrust uses AI agents, satellite data, and sensor networks to investigate climate events
          and provide evidence-based insurance payouts for farmers — automatically.
        </p>
        <div className="flex justify-center gap-4 pt-2">
          {user ? (
            <Link
              to={`/${user.role}`}
              className="px-8 py-3 bg-brand-green text-navy font-bold rounded-xl hover:bg-green-400 transition text-lg"
            >
              Go to Dashboard →
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="px-8 py-3 bg-brand-green text-navy font-bold rounded-xl hover:bg-green-400 transition text-lg"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-8 py-3 bg-navy-700 text-white font-semibold rounded-xl hover:bg-navy-600 border border-navy-600 transition text-lg"
              >
                Register as Farmer
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Role cards */}
      <section className="grid md:grid-cols-3 gap-6">
        {roles.map((r) => (
          <div
            key={r.title}
            className={`bg-navy-800 border ${r.color} rounded-2xl p-6 space-y-3 hover:scale-[1.02] transition-transform`}
          >
            <div className="text-4xl">{r.icon}</div>
            <h3 className="text-lg font-bold text-white">{r.title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{r.desc}</p>
          </div>
        ))}
      </section>

      {/* Stats / trust bar */}
      <section className="bg-navy-800 rounded-2xl p-8 grid grid-cols-2 md:grid-cols-4 gap-6 text-center border border-navy-700">
        {[
          { label: "Simulated Farms", value: "100+" },
          { label: "AI Agents", value: "4" },
          { label: "Weather Gauges", value: "12" },
          { label: "Full Audit Trail", value: "✓" },
        ].map((s) => (
          <div key={s.label}>
            <div className="text-3xl font-extrabold text-brand-green">{s.value}</div>
            <div className="text-gray-400 text-sm mt-1">{s.label}</div>
          </div>
        ))}
      </section>

      {/* Footer note */}
      <p className="text-center text-gray-600 text-xs">
        All payments in this platform are simulated. ParaTrust is a hackathon prototype.
      </p>
    </div>
  );
}
