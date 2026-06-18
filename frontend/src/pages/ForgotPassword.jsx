import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { EnvelopeSimple, PaperPlaneTilt, KeyReturn } from "@phosphor-icons/react";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [devLink, setDevLink] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post("/auth/forgot-password", { email });
      setSent(true);
      if (r.data.dev_reset_link) setDevLink(r.data.dev_reset_link);
      toast.success("If that email exists, a reset link has been sent.");
    } catch (err) {
      const detail = err?.response?.data?.detail || "Could not send reset link";
      toast.error(detail);
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-md mx-auto px-6 pt-16 pb-20">
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-full border border-[#FFBA08]/40 items-center justify-center mb-4 bg-[#FFBA08]/10">
            <KeyReturn size={28} weight="duotone" className="text-[#FFBA08]" />
          </div>
          <div className="tactical-label text-[#FFBA08] mb-2">// CREDENTIAL RECOVERY</div>
          <h1 className="font-display text-3xl font-black tracking-tighter">Recover your access</h1>
          <p className="text-sm text-zinc-400 mt-2">Enter the email on your account. We'll send a reset link valid for 2 hours.</p>
        </div>

        {sent ? (
          <div className="surface rounded-md p-7 text-center space-y-4" data-testid="forgot-success">
            <PaperPlaneTilt size={36} weight="duotone" className="text-[#10B981] mx-auto" />
            <h2 className="font-display text-xl font-bold">Check your inbox</h2>
            <p className="text-sm text-zinc-400">
              If an account exists for <span className="text-white">{email}</span>, a reset link has been delivered.
            </p>
            {devLink && (
              <div className="surface-elev rounded p-4 text-left">
                <div className="tactical-label text-[#FFBA08] mb-2">// DEV MODE — no email service configured</div>
                <p className="text-xs text-zinc-400 mb-2">Use this link directly:</p>
                <a href={devLink} className="text-xs text-[#E63946] break-all underline" data-testid="dev-reset-link">{devLink}</a>
              </div>
            )}
            <Link to="/auth" className="btn-outline inline-block">← Back to Recruitment Center</Link>
          </div>
        ) : (
          <form onSubmit={submit} className="surface rounded-md p-7 space-y-4" data-testid="forgot-form">
            <div>
              <label className="tactical-label flex items-center gap-1.5 mb-2">
                <EnvelopeSimple size={12} /> Account email
              </label>
              <input
                type="email" required
                value={email} onChange={e => setEmail(e.target.value)}
                placeholder="operator@frontline.com"
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                data-testid="forgot-input-email"
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full" data-testid="forgot-submit">
              {loading ? "Sending…" : "Send reset link"}
            </button>
            <Link to="/auth" className="block text-center text-sm text-zinc-400 hover:text-white mt-1" data-testid="forgot-back">
              ← Back to Recruitment Center
            </Link>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
