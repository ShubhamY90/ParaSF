import { useAuth } from "../../hooks/useAuth";

const cards = [
  { icon: "🔍", title: "Search Claims", desc: "Find any claim by ID, farm, or date range", badge: "Stage 8" },
  { icon: "📄", title: "Evidence Inspector", desc: "View all evidence used in a decision", badge: "Stage 7" },
  { icon: "🤖", title: "Agent Trace", desc: "Inspect agent actions and handoffs step by step", badge: "Stage 7" },
  { icon: "🧮", title: "Policy Calculations", desc: "Review the deterministic calculation and approvals", badge: "Stage 8" },
  { icon: "💰", title: "Payment History", desc: "Full history of simulated payments and reconciliation", badge: "Stage 9" },
  { icon: "🔗", title: "Audit Chain", desc: "Verify the unbroken audit chain of every decision", badge: "Stage 11" },
];

export default function AuditorDashboard() {
  const { user } = useAuth();
  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Audit Console 📋</h1>
        <p className="text-gray-400 mt-1">Logged in as {user?.full_name ?? user?.email}</p>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {cards.map((c) => (
          <div key={c.title} className="bg-navy-800 border border-purple-900/50 rounded-xl p-5 space-y-2 opacity-80">
            <div className="flex items-start justify-between">
              <span className="text-3xl">{c.icon}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700 text-gray-400">{c.badge}</span>
            </div>
            <h3 className="font-semibold text-white">{c.title}</h3>
            <p className="text-sm text-gray-400">{c.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
