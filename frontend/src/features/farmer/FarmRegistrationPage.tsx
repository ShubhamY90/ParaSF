import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../shared/PageLayout";
import { createFarm, addCrop } from "../../api/stage2";

const CROP_TYPES = ["wheat", "rice", "maize", "cotton", "sugarcane", "other"];
const SEASONS = ["kharif", "rabi", "zaid"];

export default function FarmRegistrationPage() {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [farmName, setFarmName] = useState("");
  const [area, setArea] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [cropType, setCropType] = useState("wheat");
  const [cropSeason, setCropSeason] = useState("kharif");
  const [cropArea, setCropArea] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!farmName.trim()) { setError("Farm name is required"); return; }
    setSaving(true);
    try {
      const farm = await createFarm({
        name: farmName.trim(),
        area_hectares: area ? parseFloat(area) : undefined,
        latitude: lat ? parseFloat(lat) : undefined,
        longitude: lng ? parseFloat(lng) : undefined,
      });
      await addCrop(farm.id, {
        crop_type: cropType,
        season: cropSeason,
        area_hectares: cropArea ? parseFloat(cropArea) : undefined,
      });
      navigate("/farmer/farms");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to register farm");
    } finally {
      setSaving(false);
    }
  }

  const inputCls =
    "w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-brand-blue";
  const selectCls = inputCls;

  return (
    <PageLayout title="Register a Farm" subtitle="Add your farm and primary crop details" backTo="/farmer/farms">
      <form onSubmit={handleSubmit} className="bg-navy-800 border border-navy-700 rounded-xl p-6 space-y-6 max-w-lg">
        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
        )}

        <fieldset className="space-y-4">
          <legend className="text-brand-blue font-semibold text-sm uppercase tracking-wider">Farm Details</legend>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Farm Name *</label>
            <input className={inputCls} placeholder="e.g. North Field" value={farmName} onChange={(e) => setFarmName(e.target.value)} required />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Total Area (hectares)</label>
            <input className={inputCls} type="number" step="0.01" min="0" placeholder="e.g. 2.5" value={area} onChange={(e) => setArea(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm text-gray-400">Latitude</label>
              <input className={inputCls} type="number" step="any" placeholder="e.g. 20.0059" value={lat} onChange={(e) => setLat(e.target.value)} />
              <p className="text-xs text-gray-500">Find on Google Maps</p>
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-400">Longitude</label>
              <input className={inputCls} type="number" step="any" placeholder="e.g. 73.7898" value={lng} onChange={(e) => setLng(e.target.value)} />
            </div>
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-brand-blue font-semibold text-sm uppercase tracking-wider">Crop Details</legend>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Crop Type *</label>
            <select className={selectCls} value={cropType} onChange={(e) => setCropType(e.target.value)} required>
              {CROP_TYPES.map((c) => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Crop Season *</label>
            <select className={selectCls} value={cropSeason} onChange={(e) => setCropSeason(e.target.value)} required>
              {SEASONS.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Crop Area (hectares)</label>
            <input className={inputCls} type="number" step="0.01" min="0" placeholder="e.g. 1.8" value={cropArea} onChange={(e) => setCropArea(e.target.value)} />
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-brand-blue text-white font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
        >
          {saving ? "Registering…" : "Register Farm"}
        </button>
      </form>
    </PageLayout>
  );
}
