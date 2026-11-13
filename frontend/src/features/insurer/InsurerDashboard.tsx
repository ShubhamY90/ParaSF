import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const activeCards = [
  {
    icon: "👥",
    title: "Farmer Registry",
    desc: "Search, inspect, and manage registered farmers and their farms",
    to: "/insurer/farmers",
    badge: "Active",
  },
  {
    icon: "📋",
    title: "Policy Management",
    desc: "Create, assign, filter, and track parametric insurance policies",
    to: "/insurer/policies",
    badge: "Active",
  },
  {
    icon: "🗺️",
    title: "Operations Map",
    desc: "District-wide satellite map with farm boundaries and sensor overlays",
    to: "/insurer/map",
    badge: "Active",
  },
  {
    icon: "📡",
    title: "Sensor Health",
    desc: "Detect faulty sensor readings, score sensor trust, and investigate flags",
    to: "/insurer/map",
    badge: "Stage 5",
  },
];

const upcomingCards = [
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
        <p className="text-gray-400 mt-1">
          Logged in as {user?.full_name ?? user?.email} ·{" "}
          <span className="uppercase text-brand-blue font-semibold">{user?.role}</span>
        </p>
      </div>

      {/* Active Stage 2 Features */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-brand-blue mb-4">
          Farmer & Policy Operations
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {activeCards.map((c) => (
            <Link
              key={c.title}
              to={c.to}
              className="bg-navy-800 border border-navy-700 hover:border-brand-blue rounded-xl p-5 space-y-2 transition block group"
            >
              <div className="flex items-start justify-between">
                <span className="text-3xl group-hover:scale-110 transition-transform">{c.icon}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/50 text-green-300 border border-green-700">
                  {c.badge}
                </span>
              </div>
              <h3 className="font-semibold text-white group-hover:text-brand-blue transition-colors text-base">
                {c.title}
              </h3>
              <p className="text-sm text-gray-400">{c.desc}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Upcoming Stages */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-4">
          Upcoming Capabilities
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {upcomingCards.map((c) => (
            <div
              key={c.title}
              className="bg-navy-800/50 border border-navy-700/50 rounded-xl p-5 space-y-2 opacity-60"
            >
              <div className="flex items-start justify-between">
                <span className="text-2xl">{c.icon}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700 text-gray-400">
                  {c.badge}
                </span>
              </div>
              <h3 className="font-semibold text-gray-300 text-sm">{c.title}</h3>
              <p className="text-xs text-gray-500">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
