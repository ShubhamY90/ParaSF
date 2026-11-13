import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const activeCards = [
  {
    icon: "👤",
    title: "My Profile",
    desc: "Update your personal and contact details",
    to: "/farmer/profile",
    badge: "Active",
  },
  {
    icon: "🌾",
    title: "My Farms",
    desc: "Register farms, coordinates, and crop details",
    to: "/farmer/farms",
    badge: "Active",
  },
  {
    icon: "📋",
    title: "My Policy",
    desc: "Insurance coverage, sum insured & trigger conditions",
    to: "/farmer/policy",
    badge: "Active",
  },
  {
    icon: "🏦",
    title: "Bank Account",
    desc: "Manage payout account details and verification",
    to: "/farmer/bank",
    badge: "Active",
  },
];

const upcomingCards = [
  { icon: "🗺️", title: "Satellite Map", desc: "Live satellite view centred on your farm", badge: "Stage 3" },
  { icon: "🌧️", title: "Weather Alerts", desc: "Real-time rainfall and flood events", badge: "Stage 4" },
  { icon: "💰", title: "Claims", desc: "Claim status, evidence & payment history", badge: "Stage 8" },
];

export default function FarmerDashboard() {
  const { user } = useAuth();
  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">
          Welcome, {user?.full_name ?? "Farmer"} 🌾
        </h1>
        <p className="text-gray-400 mt-1">Your ParaTrust farmer dashboard</p>
      </div>

      {/* Active Stage 2 Features */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-brand-blue mb-4">
          Farm & Policy Management
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
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
              <h3 className="font-semibold text-white group-hover:text-brand-blue transition-colors">
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
        <div className="grid sm:grid-cols-3 gap-5">
          {upcomingCards.map((c) => (
            <div
              key={c.title}
              className="bg-navy-800/50 border border-navy-700/50 rounded-xl p-5 space-y-2 opacity-60"
            >
              <div className="flex items-start justify-between">
                <span className="text-3xl">{c.icon}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-navy-700 text-gray-400">
                  {c.badge}
                </span>
              </div>
              <h3 className="font-semibold text-gray-300">{c.title}</h3>
              <p className="text-sm text-gray-500">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
