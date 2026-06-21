import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { Lock, Eye, EyeSlash, ShieldCheck } from "@phosphor-icons/react";

const ResetPassword = () => {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    if (password.length < 6) return toast.error("Password must be at least 6 characters");
    if (password !== confirm) return toast.error("Passwords do not match");
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      setDone(true);
      toast.success("Password updated. Sign in with your new credentials.");
      setTimeout(() => nav("/auth"), 1800);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reset failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-md mx-auto px-6 pt-16 pb-20">
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-full border border-[#FF6B00]/40 items-center justify-center mb-4 bg-[#FF6B00]/10">
            <ShieldCheck size={28} weight="duotone" className="text-[#FF6B00]" />
          </div>
          <div className="tactical-label text-[#FF6B00] mb-2">// SECURE RESET</div>
          <h1 className="font-display text-3xl font-black tracking-tighter">Set a new password</h1>
          <p className="text-sm text-zinc-400 mt-2">Choose something you'll remember. Minimum 6 characters.</p>
        </div>

        {!token ? (
          <div className="surface rounded-md p-7 text-center" data-testid="reset-no-token">
            <p className="text-sm text-zinc-400">No reset token in the URL. Request a fresh link.</p>
            <Link to="/forgot-password" className="btn-outline inline-block mt-4">Request a new link</Link>
          </div>
        ) : done ? (
          <div className="surface rounded-md p-7 text-center space-y-3" data-testid="reset-done">
            <ShieldCheck size={36} weight="duotone" className="text-[#FFAA33] mx-auto" />
            <p className="text-sm">Password updated. Redirecting to sign-in…</p>
          </div>
        ) : (
          <form onSubmit={submit} className="surface rounded-md p-7 space-y-4" data-testid="reset-form">
            <div>
              <label className="tactical-label flex items-center gap-1.5 mb-2">
                <Lock size={12} /> New password
              </label>
              <div className="relative">
                <input
                  type={show ? "text" : "password"} required minLength={6}
                  value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm pr-10"
                  data-testid="reset-input-password"
                />
                <button type="button" onClick={() => setShow(s => !s)} className="absolute inset-y-0 right-2 flex items-center text-zinc-500 hover:text-white" data-testid="reset-toggle-show">
                  {show ? <EyeSlash size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div>
              <label className="tactical-label flex items-center gap-1.5 mb-2">
                <Lock size={12} /> Confirm new password
              </label>
              <input
                type={show ? "text" : "password"} required minLength={6}
                value={confirm} onChange={e => setConfirm(e.target.value)}
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                data-testid="reset-input-confirm"
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full" data-testid="reset-submit">
              {loading ? "Updating…" : "Update password"}
            </button>
            <Link to="/auth" className="block text-center text-sm text-zinc-400 hover:text-white mt-1">
              ← Back to Recruitment Center
            </Link>
          </form>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;
