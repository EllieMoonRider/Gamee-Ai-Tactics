import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import { IdentificationBadge, Lock, EnvelopeSimple, Eye, EyeSlash, Sparkle } from "@phosphor-icons/react";
import BrandLogo from "../components/BrandLogo";

const AuthPage = () => {
  const [params] = useSearchParams();
  const refFromUrl = params.get("ref") || "";
  const [mode, setMode] = useState(refFromUrl ? "register" : "login");
  // `identifier` accepts EITHER an email or a username (codename).
  // The backend resolves which one it is.
  const [identifier, setIdentifier] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [referralCode, setReferralCode] = useState(refFromUrl);
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") {
        // Send the combined identifier as the `email` field — backend accepts either.
        await login(identifier, password);
      } else {
        await register(email, password, username, referralCode || undefined);
      }
      toast.success(mode === "login" ? "Welcome back, commander." : "Recruitment complete. Allied tactician deployed.");
      nav("/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="recruit-page min-h-screen relative overflow-x-hidden flex items-start sm:items-center justify-center py-6 px-4">
      {/* Atmospheric dark/smoke background */}
      <div className="absolute inset-0 -z-10 pointer-events-none">
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(255,107,0,0.08) 0%, rgba(10,10,10,0) 55%), radial-gradient(ellipse at 50% 100%, rgba(230,57,70,0.07) 0%, rgba(10,10,10,0) 60%), #050505"
        }} />
        {/* Faint grid */}
        <svg width="100%" height="100%" className="opacity-[0.04]">
          <defs>
            <pattern id="rec-grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="white" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#rec-grid)" />
        </svg>
      </div>

      {/* RECRUITMENT CARD — diamond-plate metal rectangle */}
      <div className="recruit-card relative w-full max-w-[420px] mx-auto" data-testid="recruit-banner">
        <div className="recruit-card-body relative px-7 py-9">

          {/* BRAND LOGO — full dragon + curved text mark, top center */}
          <div className="flex justify-center mb-5 relative">
            <BrandLogo size={210} className="recruit-logo" testid="recruit-brand-logo" />
          </div>

          {/* TITLE — Recruitment Center (no // prefix, no extra subtitle) */}
          <div className="text-center mb-1">
            <h1
              className="text-2xl sm:text-3xl font-black tracking-[0.18em]"
              style={{
                fontFamily: "Orbitron, sans-serif",
                color: "#FF6B00",
                textShadow: "0 0 10px rgba(255,107,0,0.65), 0 0 22px rgba(255,107,0,0.3)",
              }}
              data-testid="recruit-title"
            >
              RECRUITMENT CENTER
            </h1>
          </div>

          {/* Divider with neon ticks */}
          <div className="flex items-center gap-2 my-5">
            <div className="flex-1 h-px bg-[#FF6B00]/30" />
            <div className="w-1.5 h-1.5 rotate-45 bg-[#FF6B00]" />
            <div className="flex-1 h-px bg-[#FF6B00]/30" />
          </div>

          {/* FORM */}
          <form onSubmit={submit} className="space-y-3.5" data-testid="auth-form">
            {mode === "register" && (
              <div>
                <label className="font-mono-tactical text-[10px] tracking-[0.25em] text-[#FF6B00] flex items-center gap-1.5 mb-1.5">
                  <IdentificationBadge size={11} weight="bold" /> CODENAME · USERNAME
                </label>
                <input
                  className="recruit-input w-full text-sm"
                  placeholder="IronCommander"
                  value={username} onChange={e => setUsername(e.target.value)}
                  required minLength={2} maxLength={30}
                  data-testid="auth-input-username"
                />
              </div>
            )}

            <div>
              <label className="font-mono-tactical text-[10px] tracking-[0.25em] text-[#FF6B00] flex items-center gap-1.5 mb-1.5">
                <EnvelopeSimple size={11} weight="bold" />
                {mode === "login" ? "EMAIL / USERNAME" : "EMAIL · RECOVERY KEY"}
              </label>
              {mode === "login" ? (
                <input
                  type="text" required
                  placeholder="recruit@frontline.com  •  or  •  IronCommander"
                  className="recruit-input w-full text-sm"
                  value={identifier} onChange={e => setIdentifier(e.target.value)}
                  autoComplete="username"
                  data-testid="auth-input-identifier"
                />
              ) : (
                <input
                  type="email" required
                  placeholder="recruit@frontline.com"
                  className="recruit-input w-full text-sm"
                  value={email} onChange={e => setEmail(e.target.value)}
                  data-testid="auth-input-email"
                />
              )}
            </div>

            <div>
              <label className="font-mono-tactical text-[10px] tracking-[0.25em] text-[#FF6B00] flex items-center gap-1.5 mb-1.5">
                <Lock size={11} weight="bold" /> PASSWORD
              </label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"} required minLength={6}
                  placeholder="Min. 6 characters"
                  className="recruit-input w-full pr-10 text-sm"
                  value={password} onChange={e => setPassword(e.target.value)}
                  data-testid="auth-input-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  className="absolute inset-y-0 right-2 flex items-center text-zinc-500 hover:text-[#FF6B00]"
                  aria-label={showPw ? "Hide password" : "Show password"}
                  data-testid="auth-toggle-show-password"
                >
                  {showPw ? <EyeSlash size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {mode === "login" && (
                <div className="mt-1.5 text-right">
                  <Link to="/forgot-password" className="text-[11px] font-mono-tactical tracking-wider text-zinc-500 hover:text-[#FF6B00]" data-testid="auth-forgot-link">
                    FORGOT PASSWORD?
                  </Link>
                </div>
              )}
            </div>

            {mode === "register" && (
              <div>
                <label className="font-mono-tactical text-[10px] tracking-[0.25em] text-[#FF6B00] flex items-center gap-1.5 mb-1.5">
                  <Sparkle size={11} weight="bold" /> SIGIL <span className="text-zinc-600">· OPTIONAL</span>
                </label>
                <input
                  className="recruit-input w-full text-sm font-mono-tactical tracking-widest uppercase"
                  placeholder="TA-XXXXXX"
                  value={referralCode} onChange={e => setReferralCode(e.target.value.toUpperCase())}
                  maxLength={12}
                  data-testid="auth-input-referral"
                />
                {refFromUrl && <p className="text-[10px] text-[#FF6B00] mt-1.5">Sigil verified. Welcome bonus locked in: +1 Deep Dive.</p>}
              </div>
            )}

            <button
              type="submit" disabled={loading}
              className="recruit-cta w-full mt-2"
              data-testid="auth-submit-btn"
            >
              {loading ? "PROCESSING…" : mode === "login" ? "JOIN" : "SWEAR THE OATH"}
            </button>

            <button
              type="button"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              className="w-full text-[11px] font-mono-tactical tracking-[0.25em] text-zinc-500 hover:text-[#FF6B00] mt-1"
              data-testid="auth-toggle-mode"
            >
              {mode === "login"
                ? "NEW RECRUIT? · ENLIST →"
                : "ALREADY ENLISTED? · AUTHENTICATE →"}
            </button>
          </form>
        </div>

        {/* Footer text below card */}
        <p className="text-center mt-6 text-[11px] font-mono-tactical tracking-[0.2em] text-zinc-600">
          UNOFFICIAL STRATEGY COMPANION · 37GAMES UNAFFILIATED
          <br/>
          <Link to="/cypher" className="inline-block mt-3 mr-4 text-[#FF6B00]/70 hover:text-[#FF6B00]" data-testid="recruit-about-cypher">ABOUT CYPHERAI</Link>
        </p>
      </div>
    </div>
  );
};

export default AuthPage;
