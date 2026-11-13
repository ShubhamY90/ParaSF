import { useAuth } from "../../hooks/useAuth";

const cards = [
  { icon: "🌾", title: "My Farm", desc: "Farm location, area, and crop details", badge: "Stage 2" },
  { icon: "📋", title: "My Policy", desc: "Insurance coverage and trigger conditions", badge: "Stage 2" },
  { icon: "🗺️", title: "Satellite Map", desc: "Live satellite view centred on your farm", badge: "Stage 3" },
  { icon: "🌧️", title: "Weather Alerts", desc: "Real-time rainfall and flood events", badge: "Stage 4" },
  { icon: "💰", title: "Claims", desc: "Claim status and payment history", badge: "Stage 8" },
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
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {cards.map((c) => (
          <div key={c.title} className="bg-navy-800 border border-navy-700 rounded-xl p-5 space-y-2 opacity-80">
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
