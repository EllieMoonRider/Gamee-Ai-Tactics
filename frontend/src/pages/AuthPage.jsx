import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import { IdentificationBadge, Lock, EnvelopeSimple, Eye, EyeSlash, Sparkle } from "@phosphor-icons/react";
import BrandLogo from "../components/BrandLogo";
import MilitaryBolt from "../components/MilitaryBolt";
import DiamondPlatePattern from "../components/DiamondPlatePattern";

const AuthPage = () => {
  const [params] = useSearchParams();
  const refFromUrl = params.get("ref") || "";
  const [mode, setMode] = useState(refFromUrl ? "register" : "login");
  // `identifier` accepts EITHER an email or a username (codename).
  const [identifier, setIdentifier] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [username, setUsername] = useState("");
  const [referralCode, setReferralCode] = useState(refFromUrl);
  const [showPw, setShowPw] = useState(false);
  const [showConfirmPw, setShowConfirmPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const nav = useNavigate();

  const isRegister = mode === "register";

  const submit = async (e) => {
    e.preventDefault();
    if (isRegister && password !== confirmPassword) {
      toast.error("Passwords don't match.");
      return;
    }
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password, username, referralCode || undefined);
      } else {
        await login(identifier, password);
      }
      toast.success(isRegister ? "Recruitment complete. Allied tactician deployed." : "Welcome back, commander.");
      nav("/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="recruit-page min-h-screen relative overflow-x-hidden flex items-start sm:items-center justify-center py-4 px-4">
      {/* Atmospheric dark/smoke background */}
      <div className="absolute inset-0 -z-10 pointer-events-none">
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(255,107,0,0.08) 0%, rgba(10,10,10,0) 55%), radial-gradient(ellipse at 50% 100%, rgba(230,57,70,0.07) 0%, rgba(10,10,10,0) 60%), #050505"
        }} />
      </div>

      {/* RECRUITMENT PLATE — industrial diamond-plate rectangle */}
      <div className={`recruit-card relative w-full max-w-[420px] mx-auto ${isRegister ? "is-enlist" : "is-login"}`} data-testid="recruit-banner">
        <div className="recruit-card-body relative">
          {/* Real industrial diamond-plate background */}
          <DiamondPlatePattern className="recruit-plate-bg" />

          {/* OTS military bolts in the four corners */}
          <div className="recruit-bolt tl" aria-hidden="true"><MilitaryBolt size={36} testid="ots-bolt-tl" /></div>
          <div className="recruit-bolt tr" aria-hidden="true"><MilitaryBolt size={36} testid="ots-bolt-tr" /></div>
          <div className="recruit-bolt bl" aria-hidden="true"><MilitaryBolt size={36} testid="ots-bolt-bl" /></div>
          <div className="recruit-bolt br" aria-hidden="true"><MilitaryBolt size={36} testid="ots-bolt-br" /></div>

          <div className="recruit-card-inner relative">
            {/* BRAND LOGO — smaller on enlistment */}
            <div className="flex justify-center mb-3 relative">
              <BrandLogo size={isRegister ? 150 : 210} className="recruit-logo" testid="recruit-brand-logo" />
            </div>

            {/* TITLE — single word, centered.
                Login: RECRUITMENT      Register: ENLISTMENT */}
            <div className="text-center mb-1">
              <h1
                className="text-3xl sm:text-4xl font-black tracking-[0.18em]"
                style={{
                  fontFamily: "Orbitron, sans-serif",
                  color: "#FF6B00",
                  textShadow: "0 0 10px rgba(255,107,0,0.65), 0 0 22px rgba(255,107,0,0.3)",
                }}
                data-testid="recruit-title"
              >
                {isRegister ? "ENLISTMENT" : "RECRUITMENT"}
              </h1>
            </div>

            {/* Divider with neon tick */}
            <div className="flex items-center gap-2 my-4">
              <div className="flex-1 h-px bg-[#FF6B00]/30" />
              <div className="w-1.5 h-1.5 rotate-45 bg-[#FF6B00]" />
              <div className="flex-1 h-px bg-[#FF6B00]/30" />
            </div>

            {/* FORM */}
            <form onSubmit={submit} className="space-y-3" data-testid="auth-form">
              {isRegister && (
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
                  {isRegister ? "EMAIL" : "EMAIL / USERNAME"}
                </label>
                {isRegister ? (
                  <input
                    type="email" required
                    placeholder="recruit@frontline.com"
                    className="recruit-input w-full text-sm"
                    value={email} onChange={e => setEmail(e.target.value)}
                    data-testid="auth-input-email"
                  />
                ) : (
                  <input
                    type="text" required
                    placeholder="recruit@frontline.com  •  or  •  IronCommander"
                    className="recruit-input w-full text-sm"
                    value={identifier} onChange={e => setIdentifier(e.target.value)}
                    autoComplete="username"
                    data-testid="auth-input-identifier"
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
                    className="absolute inset-y-0 right-2 z-10 flex items-center text-zinc-500 hover:text-[#FF6B00]"
                    aria-label={showPw ? "Hide password" : "Show password"}
                    data-testid="auth-toggle-show-password"
                  >
                    {showPw ? <EyeSlash size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {!isRegister && (
                  <div className="mt-1.5 text-right">
                    <Link to="/forgot-password" className="text-[11px] font-mono-tactical tracking-wider text-zinc-500 hover:text-[#FF6B00]" data-testid="auth-forgot-link">
                      FORGOT PASSWORD?
                    </Link>
                  </div>
                )}
              </div>

              {/* Confirm Password — register mode only */}
              {isRegister && (
                <div>
                  <label className="font-mono-tactical text-[10px] tracking-[0.25em] text-[#FF6B00] flex items-center gap-1.5 mb-1.5">
                    <Lock size={11} weight="bold" /> CONFIRM PASSWORD
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPw ? "text" : "password"} required minLength={6}
                      placeholder="Re-enter password"
                      className="recruit-input w-full pr-10 text-sm"
                      value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                      data-testid="auth-input-confirm-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPw(s => !s)}
                      className="absolute inset-y-0 right-2 z-10 flex items-center text-zinc-500 hover:text-[#FF6B00]"
                      aria-label={showConfirmPw ? "Hide password" : "Show password"}
                      data-testid="auth-toggle-show-confirm-password"
                    >
                      {showConfirmPw ? <EyeSlash size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  {confirmPassword && password !== confirmPassword && (
                    <p className="text-[11px] text-red-400 mt-1 font-mono-tactical tracking-wider">PASSWORDS DO NOT MATCH</p>
                  )}
                </div>
              )}

              {isRegister && (
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
                {loading ? "PROCESSING…" : isRegister ? "ENLIST" : "JOIN"}
              </button>

              <button
                type="button"
                onClick={() => setMode(isRegister ? "login" : "register")}
                className="w-full text-[11px] font-mono-tactical tracking-[0.25em] text-zinc-500 hover:text-[#FF6B00] mt-1"
                data-testid="auth-toggle-mode"
              >
                {isRegister
                  ? "ALREADY ENLISTED? · JOIN →"
                  : "NEW RECRUIT? · ENLIST →"}
              </button>
            </form>
          </div>
        </div>

        {/* Footer text below plate */}
        <p className="text-center mt-5 text-[11px] font-mono-tactical tracking-[0.2em] text-zinc-600">
          UNOFFICIAL STRATEGY COMPANION · 37GAMES UNAFFILIATED
          <br/>
          <Link to="/cypher" className="inline-block mt-2 text-[#FF6B00]/70 hover:text-[#FF6B00]" data-testid="recruit-about-cypher">ABOUT CYPHERAI</Link>
        </p>
      </div>
    </div>
  );
};

export default AuthPage;
