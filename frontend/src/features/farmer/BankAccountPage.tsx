import { useState, useEffect } from "react";
import PageLayout from "../shared/PageLayout";
import { getBankAccount, submitBankAccount, BankAccountOut } from "../../api/stage2";

type VerificationStatus = "pending" | "verified" | "failed";

function VerificationBadge({ status }: { status: VerificationStatus }) {
  const map: Record<VerificationStatus, string> = {
    pending: "bg-yellow-900/50 text-yellow-300 border-yellow-700",
    verified: "bg-green-900/50 text-green-300 border-green-700",
    failed: "bg-red-900/50 text-red-300 border-red-700",
  };
  const icons: Record<VerificationStatus, string> = {
    pending: "⏳",
    verified: "✅",
    failed: "❌",
  };
  return (
    <span className={`text-sm px-3 py-1 rounded-full border font-medium ${map[status]}`}>
      {icons[status]} {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export default function BankAccountPage() {
  const [account, setAccount] = useState<BankAccountOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [holderName, setHolderName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [bankName, setBankName] = useState("");
  const [ifsc, setIfsc] = useState("");

  useEffect(() => {
    getBankAccount()
      .then(setAccount)
      .catch(() => { /* No account yet */ })
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (!holderName.trim()) { setError("Account holder name is required"); return; }
    if (!/^\d{12,16}$/.test(accountNumber)) {
      setError("Account number must be 12–16 digits");
      return;
    }
    if (!ifsc.trim()) { setError("IFSC code is required"); return; }

    setSaving(true);
    try {
      const result = await submitBankAccount({
        account_holder_name: holderName.trim(),
        account_number: accountNumber,
        bank_name: bankName.trim() || undefined,
        ifsc_code: ifsc.trim().toUpperCase(),
      });
      setAccount(result);
      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit bank account");
    } finally {
      setSaving(false);
    }
  }

  const inputCls =
    "w-full bg-navy-900 border border-navy-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-brand-blue";

  return (
    <PageLayout title="Bank Account" subtitle="Payment details for insurance payouts" backTo="/farmer">
      <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg px-4 py-3 text-yellow-300 text-sm max-w-lg">
        ⚠️ Your account number is used only for payment processing. We store only the last 4 digits.
      </div>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : account ? (
        // Show existing account
        <div className="bg-navy-800 border border-navy-700 rounded-xl p-6 space-y-4 max-w-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-semibold">Account on File</h2>
            <VerificationBadge status={account.verification_status as VerificationStatus} />
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500 text-xs">Account Holder</p>
              <p className="text-white">{account.account_holder_name}</p>
            </div>
            <div>
              <p className="text-gray-500 text-xs">Account Number</p>
              <p className="text-white font-mono">{account.masked_account_number}</p>
            </div>
            {account.bank_name && (
              <div>
                <p className="text-gray-500 text-xs">Bank</p>
                <p className="text-white">{account.bank_name}</p>
              </div>
            )}
            {account.ifsc_code && (
              <div>
                <p className="text-gray-500 text-xs">IFSC</p>
                <p className="text-white font-mono">{account.ifsc_code}</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        // Show submission form
        <form onSubmit={handleSubmit} className="bg-navy-800 border border-navy-700 rounded-xl p-6 space-y-5 max-w-lg">
          {success && (
            <div className="bg-green-900/40 border border-green-700 text-green-300 rounded-lg px-4 py-3 text-sm">
              ✅ Bank account submitted successfully!
            </div>
          )}
          {error && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
          )}

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Account Holder Name *</label>
            <input className={inputCls} placeholder="As on bank records" value={holderName} onChange={(e) => setHolderName(e.target.value)} required />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Account Number * (12–16 digits)</label>
            <input
              className={inputCls}
              type="text"
              inputMode="numeric"
              placeholder="Enter full account number"
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value.replace(/\D/g, ""))}
              maxLength={16}
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">Bank Name</label>
            <input className={inputCls} placeholder="e.g. State Bank of India" value={bankName} onChange={(e) => setBankName(e.target.value)} />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-gray-400">IFSC Code *</label>
            <input
              className={inputCls}
              placeholder="e.g. SBIN0001234"
              value={ifsc}
              onChange={(e) => setIfsc(e.target.value.toUpperCase())}
              maxLength={11}
              required
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full bg-brand-blue text-white font-semibold py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
          >
            {saving ? "Submitting…" : "Submit Bank Account"}
          </button>
        </form>
      )}
    </PageLayout>
  );
}
