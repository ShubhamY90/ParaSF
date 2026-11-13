import { useAuth } from "../../hooks/useAuth";

const cards = [
  { icon: "👥", title: "Farmer Registry", desc: "Search and manage registered farmers and policies", badge: "Stage 2" },
  { icon: "🗺️", title: "Operations Map", desc: "District-wide satellite map with farm and sensor overlays", badge: "Stage 3" },
  { icon: "🌪️", title: "Weather Events", desc: "Active weather events and storm tracking", badge: "Stage 4" },
  { icon: "📡", title: "Sensor Health", desc: "Fault detection and sensor trust scores", badge: "Stage 5" },
  { icon: "⚠️", title: "Risk Assessment", desc: "Farm-level rainfall risk and uncertainty", badge: "Stage 6" },
  { icon: "🤖", title: "AI Agents", desc: "Investigation workflow and agent traces", badge: "Stage 7" },
  { icon: "✅", title: "Claims Queue", desc: "Review and approve claim recommendations", badge: "Stage 8" },
  { icon: "💳", title: "Payments", desc: "Simulated payment processing and reconciliation", badge: "Stage 9" },
];

export default function InsurerDashboard() {
  const { user } = useAuth();
  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">
          Operations Dashboard 🏦
        </h1>
        <p className="text-gray-400 mt-1">Logged in as {user?.full_name ?? user?.email} · <span className="uppercase text-brand-blue">{user?.role}</span></p>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div key={c.title} className="bg-navy-800 border border-navy-700 rounded-xl p-5 space-y-2 opacity-80">
            <div className="flex items-start justify-between">
              <span className="text-2xl">{c.icon}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700 text-gray-400">{c.badge}</span>
            </div>
            <h3 className="font-semibold text-white text-sm">{c.title}</h3>
            <p className="text-xs text-gray-400">{c.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
