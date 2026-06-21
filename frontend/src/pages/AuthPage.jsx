import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import { IdentificationBadge, Lock, EnvelopeSimple, Eye, EyeSlash, Sparkle } from "@phosphor-icons/react";
import iconImg from "../assets/tactical-ally-icon.png";

const AuthPage = () => {
  const [params] = useSearchParams();
  const refFromUrl = params.get("ref") || "";
  const [mode, setMode] = useState(refFromUrl ? "register" : "login");
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
      if (mode === "login") await login(email, password);
      else await register(email, password, username, referralCode || undefined);
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

      {/* WAR BANNER */}
      <div className="war-banner relative w-full max-w-[420px] mx-auto" data-testid="recruit-banner">
        {/* Rope hangers at the top */}
        <div className="flex justify-between px-8 mb-[-2px] relative z-10">
          <div className="w-3 h-6 bg-gradient-to-b from-zinc-700 to-zinc-900 rounded-b-sm" />
          <div className="w-3 h-6 bg-gradient-to-b from-zinc-700 to-zinc-900 rounded-b-sm" />
        </div>

        {/* Crossbar / banner top rod */}
        <div className="h-2 mx-2 bg-gradient-to-r from-zinc-700 via-zinc-500 to-zinc-700 rounded-sm shadow-lg relative z-10" />

        {/* Banner body */}
        <div className="war-banner-body relative pt-9 px-7 pb-12">
          {/* Top fringe decorative SVG (above content) */}
          <svg viewBox="0 0 400 12" className="absolute top-2 left-0 right-0 w-full" preserveAspectRatio="none" style={{ height: 12 }}>
            <path d="M0 0 L400 0 L400 4 Q380 12 360 4 Q340 12 320 4 Q300 12 280 4 Q260 12 240 4 Q220 12 200 4 Q180 12 160 4 Q140 12 120 4 Q100 12 80 4 Q60 12 40 4 Q20 12 0 4 Z" fill="#FF6B00" opacity="0.18" />
          </svg>

          {/* INSIGNIA — circular crest with dragon icon */}
          <div className="flex justify-center mb-5 relative">
            <div className="relative">
              <div className="w-24 h-24 rounded-full overflow-hidden border-2 border-[#FF6B00]/60 shadow-[0_0_24px_rgba(255,107,0,0.45)]">
                <img src={iconImg} alt="Tactical Ally Insignia" className="w-full h-full object-cover" data-testid="recruit-insignia" />
              </div>
              {/* Crossing swords behind the crest */}
              <svg viewBox="0 0 200 120" className="absolute -inset-x-12 top-1/2 -translate-y-1/2 -z-10 pointer-events-none" style={{ width: "calc(100% + 6rem)" }}>
                <g stroke="#FF6B00" strokeWidth="1.5" opacity="0.5" fill="none" strokeLinecap="round">
                  <line x1="14" y1="100" x2="186" y2="20" />
                  <line x1="186" y1="100" x2="14" y2="20" />
                  <line x1="8" y1="106" x2="22" y2="92" strokeWidth="3" />
                  <line x1="192" y1="106" x2="178" y2="92" strokeWidth="3" />
                </g>
              </svg>
            </div>
          </div>

          {/* TITLE */}
          <div className="text-center mb-2" style={{ fontFamily: "Orbitron, sans-serif" }}>
            <div className="font-mono-tactical text-[10px] tracking-[0.4em] text-[#FF6B00] mb-2">// RECRUITMENT CENTER</div>
            <h1
              className="text-3xl font-black tracking-widest"
              style={{
                fontFamily: "Orbitron, sans-serif",
                color: "#FF6B00",
                textShadow: "0 0 10px rgba(255,107,0,0.65), 0 0 22px rgba(255,107,0,0.3)",
              }}
            >
              {mode === "login" ? "ENTER THE WAR ROOM" : "ENLIST"}
            </h1>
            <p className="text-xs text-zinc-400 mt-2 max-w-xs mx-auto leading-relaxed">
              {mode === "login"
                ? "Authenticate to advance to the Command Center."
                : "Stake your codename. Take the oath. Join the alliance."}
            </p>
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
                  <IdentificationBadge size={11} weight="bold" /> CODENAME
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
                <EnvelopeSimple size={11} weight="bold" /> EMAIL{mode === "register" && " · RECOVERY KEY"}
              </label>
              <input
                type="email" required
                placeholder="operator@frontline.com"
                className="recruit-input w-full text-sm"
                value={email} onChange={e => setEmail(e.target.value)}
                data-testid="auth-input-email"
              />
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
              {loading ? "PROCESSING…" : mode === "login" ? "TAKE THE FIELD" : "SWEAR THE OATH"}
            </button>

            <button
              type="button"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              className="w-full text-[11px] font-mono-tactical tracking-[0.25em] text-zinc-500 hover:text-[#FF6B00] mt-1"
              data-testid="auth-toggle-mode"
            >
              {mode === "login"
                ? "NEW OPERATOR? · ENLIST →"
                : "ALREADY ENLISTED? · AUTHENTICATE →"}
            </button>
          </form>

          {/* Banner bottom fringe — pointed cloth tails */}
          <svg viewBox="0 0 400 40" className="absolute bottom-[-39px] left-0 right-0 w-full" preserveAspectRatio="none" style={{ height: 40 }}>
            <polygon points="0,0 400,0 400,4 380,38 360,4 340,38 320,4 300,38 280,4 260,38 240,4 220,38 200,4 180,38 160,4 140,38 120,4 100,38 80,4 60,38 40,4 20,38 0,4" fill="var(--banner-fill)" stroke="rgba(255,107,0,0.45)" strokeWidth="1" />
          </svg>
        </div>

        {/* Footer text below banner */}
        <p className="text-center mt-16 text-[11px] font-mono-tactical tracking-[0.2em] text-zinc-600">
          UNOFFICIAL STRATEGY COMPANION · 37GAMES UNAFFILIATED
          <br/>
          <Link to="/cypher" className="inline-block mt-3 mr-4 text-[#FF6B00]/70 hover:text-[#FF6B00]" data-testid="recruit-about-cypher">ABOUT CYPHERAI</Link>
          <Link to="/" className="inline-block mt-3 text-zinc-500 hover:text-[#FF6B00]">← BACK TO HOME</Link>
        </p>
      </div>
    </div>
  );
};

export default AuthPage;
