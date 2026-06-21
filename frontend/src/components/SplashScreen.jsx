import { useEffect, useState } from "react";
import bgImg from "../assets/command-center-bg-v1.jpg";

/**
 * SplashScreen — branded portrait-friendly intro for Tactical Ally.
 *
 * Shows on first session mount (gated by sessionStorage) for ~3.4s, then fades out.
 * "TACTICAL ALLY" curves around the top half; "CYPHRAI POWERED" curves around the bottom half.
 * The command-center backdrop (radar + dragon + knights) sits behind everything.
 * Tap-to-skip is enabled.
 */
const SplashScreen = ({ onDone }) => {
  const [phase, setPhase] = useState("intro"); // intro | fading | gone

  useEffect(() => {
    const t1 = setTimeout(() => setPhase("fading"), 3000);
    const t2 = setTimeout(() => onDone?.(), 3700);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onDone]);

  const skip = () => { setPhase("fading"); setTimeout(() => onDone?.(), 350); };

  return (
    <div
      className={`fixed inset-0 z-[400] bg-[#050505] flex items-center justify-center overflow-hidden cursor-pointer select-none transition-opacity duration-700 ${phase === "fading" ? "opacity-0" : "opacity-100"}`}
      onClick={skip}
      data-testid="splash-screen"
    >
      {/* Backdrop: radar + dragon + knights */}
      <img
        src={bgImg}
        alt=""
        aria-hidden
        className="absolute inset-0 w-full h-full object-cover splash-bg-anim"
        style={{ opacity: 0.55 }}
      />
      {/* Radial dim to push focus to center */}
      <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 0%, rgba(5,5,5,0.55) 60%, #050505 100%)" }} />
      {/* Scanlines */}
      <div className="absolute inset-0 cc-scanline" />

      {/* Center SVG with curved text + mini animated radar */}
      <svg
        viewBox="0 0 400 600"
        preserveAspectRatio="xMidYMid meet"
        className="relative w-[92vw] max-w-[420px] h-auto splash-fade-in"
        style={{ maxHeight: "92vh" }}
      >
        <defs>
          {/* Top curve — opens downward, arches upward like a banner */}
          <path id="topArc" d="M 40 230 Q 200 30 360 230" fill="none" />
          {/* Bottom curve — opens upward, arches downward */}
          <path id="bottomArc" d="M 40 400 Q 200 590 360 400" fill="none" />
          {/* Sweep gradient for radar */}
          <linearGradient id="splashSweep" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(57,255,20,0.8)" />
            <stop offset="100%" stopColor="rgba(57,255,20,0)" />
          </linearGradient>
          <radialGradient id="splashGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(57,255,20,0.4)" />
            <stop offset="60%" stopColor="rgba(57,255,20,0.08)" />
            <stop offset="100%" stopColor="rgba(57,255,20,0)" />
          </radialGradient>
        </defs>

        {/* Top curved title */}
        <text
          fontFamily="Orbitron, Rajdhani, sans-serif"
          fontWeight="900"
          fontSize="36"
          fill="#39FF14"
          letterSpacing="8"
          style={{ filter: "drop-shadow(0 0 6px rgba(57,255,20,0.85)) drop-shadow(0 0 18px rgba(57,255,20,0.45))" }}
        >
          <textPath href="#topArc" startOffset="50%" textAnchor="middle">
            TACTICAL ALLY
          </textPath>
        </text>

        {/* Center radar — concentric rings, crosshair, sweeping line, pulse */}
        <g transform="translate(200, 315)">
          {/* Outer rings */}
          {[110, 85, 60, 35].map((r, i) => (
            <circle key={i} cx="0" cy="0" r={r} fill="none" stroke="rgba(57,255,20,0.35)" strokeWidth="0.7" strokeDasharray={i === 0 ? "3 5" : "0"} />
          ))}
          {/* Crosshair */}
          <line x1="-115" y1="0" x2="115" y2="0" stroke="rgba(57,255,20,0.18)" strokeWidth="0.5" />
          <line x1="0" y1="-115" x2="0" y2="115" stroke="rgba(57,255,20,0.18)" strokeWidth="0.5" />
          {/* Soft inner glow */}
          <circle cx="0" cy="0" r="110" fill="url(#splashGlow)" />
          {/* Animated sweep */}
          <g className="splash-radar-sweep">
            <path d="M 0 0 L 0 -110 A 110 110 0 0 1 76 -76 Z" fill="url(#splashGlow)" />
            <line x1="0" y1="0" x2="0" y2="-110" stroke="url(#splashSweep)" strokeWidth="1.8" />
          </g>
          {/* Center dot + outward pulse */}
          <circle cx="0" cy="0" r="4" fill="#39FF14" />
          <circle cx="0" cy="0" r="6" fill="none" stroke="#39FF14" strokeWidth="1" className="splash-radar-pulse" />
          {/* Blips */}
          {[{a: 35, r: 0.55}, {a: 155, r: 0.42}, {a: 260, r: 0.6}, {a: 320, r: 0.32}].map((b, i) => {
            const x = Math.cos(b.a * Math.PI / 180) * (b.r * 100);
            const y = Math.sin(b.a * Math.PI / 180) * (b.r * 100);
            return (
              <g key={i}>
                <circle cx={x} cy={y} r="2.5" fill="#39FF14">
                  <animate attributeName="opacity" values="0.35;1;0.35" dur={`${1.4 + i * 0.4}s`} repeatCount="indefinite" />
                </circle>
              </g>
            );
          })}
        </g>

        {/* Bottom curved tagline */}
        <text
          fontFamily="Orbitron, Rajdhani, sans-serif"
          fontWeight="700"
          fontSize="18"
          fill="#39FF14"
          letterSpacing="6"
          style={{ filter: "drop-shadow(0 0 4px rgba(57,255,20,0.7))" }}
        >
          <textPath href="#bottomArc" startOffset="50%" textAnchor="middle">
            CYPHRAI POWERED
          </textPath>
        </text>
      </svg>

      {/* Skip hint at bottom */}
      <div className="absolute bottom-6 left-0 right-0 text-center font-mono-tactical text-[10px] tracking-[0.3em] text-zinc-600" data-testid="splash-skip-hint">
        TAP TO SKIP
      </div>
    </div>
  );
};

export default SplashScreen;
