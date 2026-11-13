import { useState, useEffect } from "react";
import PageLayout from "../shared/PageLayout";
import { getMyProfile, upsertMyProfile, FarmerProfileOut } from "../../api/stage2";
import { useAuth } from "../../hooks/useAuth";

export default function FarmerProfilePage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [district, setDistrict] = useState("");
  const [state, setState] = useState("");

  useEffect(() => {
    getMyProfile()
      .then((p: FarmerProfileOut) => {
        setPhone(p.phone ?? "");
        setAddress(p.address ?? "");
        setDistrict(p.district ?? "");
        setState(p.state ?? "");
      })
      .catch(() => {
        // No profile yet — form stays empty
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setSaving(true);
    try {
      await upsertMyProfile({ phone, address, district, state });
      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  const inputCls =
    "w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-brand-blue";

  return (
    <PageLayout title="My Profile" subtitle="Update your personal details" backTo="/farmer">
      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : (
        <form onSubmit={handleSubmit} className="bg-navy-800 border border-navy-700 rounded-xl p-6 space-y-5 max-w-lg">
          {success && (
            <div className="bg-green-900/40 border border-green-700 text-green-300 rounded-lg px-4 py-3 text-sm">
              ✅ Profile saved successfully!
            </div>
          )}
          {error && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          {/* Full name — read-only */}
          <div className="space-y-1">
            <label className="text-sm text-gray-400">Full Name</label>
            <input
              className={`${inputCls} opacity-60 cursor-not-allowed`}
              value={user?.full_name ?? ""}
              readOnly
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Phone Number</label>
            <input
              className={inputCls}
              placeholder="+91 98765 43210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Address</label>
            <textarea
              className={inputCls}
              rows={3}
              placeholder="Village / Town, Taluka"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm text-gray-400">District</label>
              <input
                className={inputCls}
                placeholder="e.g. Nashik"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-400">State</label>
              <input
                className={inputCls}
                placeholder="e.g. Maharashtra"
                value={state}
                onChange={(e) => setState(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full bg-brand-blue text-white font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
          >
            {saving ? "Saving…" : "Save Profile"}
          </button>
        </form>
      )}
    </PageLayout>
  );
}
