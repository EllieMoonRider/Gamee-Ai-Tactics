import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import Navbar from "../components/Navbar";
import { ShieldStar, IdentificationBadge, Lock, EnvelopeSimple, Eye, EyeSlash } from "@phosphor-icons/react";

const AuthPage = () => {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, username);
      toast.success(mode === "login" ? "Welcome back, commander." : "Recruitment complete. Allied tactician deployed.");
      nav("/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Recruitment Center background grid */}
      <div className="fixed inset-0 -z-10 opacity-[0.05] pointer-events-none">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="rec-grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="white" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#rec-grid)" />
        </svg>
      </div>

      <div className="max-w-md mx-auto px-6 pt-12 pb-20">
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-full border border-[#E63946]/40 items-center justify-center mb-4 bg-[#E63946]/10">
            <ShieldStar size={28} weight="duotone" className="text-[#E63946]" />
          </div>
          <div className="tactical-label text-[#FFBA08] mb-2">// RECRUITMENT CENTER</div>
          <h1 className="font-display text-3xl font-black tracking-tighter">
            {mode === "login" ? "Resume command" : "Enlist your Ally"}
          </h1>
          <p className="text-sm text-zinc-400 mt-2 max-w-xs mx-auto">
            {mode === "login"
              ? "Authenticate to enter the Command Center."
              : "Register an email + codename. Your codename is your in-game identity; your email is the recovery key."}
          </p>
        </div>

        <form onSubmit={submit} className="surface p-7 rounded-md space-y-4" data-testid="auth-form">
          {mode === "register" && (
            <div>
              <label className="tactical-label flex items-center gap-1.5 mb-2">
                <IdentificationBadge size={12} /> Codename / Username
              </label>
              <input
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                placeholder="e.g. IronCommander"
                value={username} onChange={e => setUsername(e.target.value)}
                required minLength={2} maxLength={30}
                data-testid="auth-input-username"
              />
              <p className="text-[11px] text-zinc-500 mt-1.5">This is the name your Tactical Ally addresses you by.</p>
            </div>
          )}
          <div>
            <label className="tactical-label flex items-center gap-1.5 mb-2">
              <EnvelopeSimple size={12} /> Email{mode === "register" && " · recovery"}
            </label>
            <input
              type="email" required
              placeholder="operator@frontline.com"
              className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
              value={email} onChange={e => setEmail(e.target.value)}
              data-testid="auth-input-email"
            />
            {mode === "register" && <p className="text-[11px] text-zinc-500 mt-1.5">Used to recover your codename if access is lost.</p>}
          </div>
          <div>
            <label className="tactical-label flex items-center gap-1.5 mb-2">
              <Lock size={12} /> Password
            </label>
            <div className="relative">
              <input
                type={showPw ? "text" : "password"} required minLength={6}
                placeholder="Min. 6 characters"
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 pr-10 text-sm"
                value={password} onChange={e => setPassword(e.target.value)}
                data-testid="auth-input-password"
              />
              <button
                type="button"
                onClick={() => setShowPw(s => !s)}
                className="absolute inset-y-0 right-2 flex items-center text-zinc-500 hover:text-white"
                aria-label={showPw ? "Hide password" : "Show password"}
                data-testid="auth-toggle-show-password"
              >
                {showPw ? <EyeSlash size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {mode === "login" && (
              <div className="mt-2 text-right">
                <Link to="/forgot-password" className="text-xs text-zinc-400 hover:text-[#FFBA08]" data-testid="auth-forgot-link">
                  Forgot password?
                </Link>
              </div>
            )}
          </div>
          <button
            type="submit" disabled={loading}
            className="btn-primary w-full mt-2" data-testid="auth-submit-btn"
          >
            {loading ? "Processing…" : mode === "login" ? "Authenticate" : "Enlist now"}
          </button>
          <button
            type="button"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            className="w-full text-sm text-zinc-400 hover:text-white mt-1"
            data-testid="auth-toggle-mode"
          >
            {mode === "login"
              ? "New operator? Enlist now →"
              : "Already enlisted? Authenticate →"}
          </button>
        </form>

        <p className="text-center mt-6 text-xs text-zinc-500">
          Tactical Ally is an unofficial strategy companion.
          <Link to="/" className="block text-zinc-400 hover:text-white mt-2">← Back to home</Link>
        </p>
      </div>
    </div>
  );
};

export default AuthPage;
