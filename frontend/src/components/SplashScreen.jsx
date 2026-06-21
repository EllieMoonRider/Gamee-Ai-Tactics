import { useEffect, useState } from "react";
import iconImg from "../assets/tactical-ally-icon.png";

/**
 * SplashScreen — 3-second cinematic intro using the actual app icon (dragon-centered)
 * with "TACTICAL ALLY" curving around the top half and "CYPHERAI STRATEGIES" curving
 * around the bottom half of the icon.
 *
 * Auto-fades after HOLD_MS. Tap to skip.
 */
const SplashScreen = ({ onDone }) => {
  const [phase, setPhase] = useState("intro"); // intro | fading
  const HOLD_MS = 3000;
  const FADE_MS = 700;

  useEffect(() => {
    const t1 = setTimeout(() => setPhase("fading"), HOLD_MS);
    const t2 = setTimeout(() => onDone?.(), HOLD_MS + FADE_MS);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onDone]);

  const skip = () => { setPhase("fading"); setTimeout(() => onDone?.(), 300); };

  return (
    <div
      className={`fixed inset-0 z-[400] bg-[#050505] flex items-center justify-center overflow-hidden cursor-pointer select-none transition-opacity ${phase === "fading" ? "opacity-0" : "opacity-100"}`}
      onClick={skip}
      style={{ transitionDuration: `${FADE_MS}ms` }}
      data-testid="splash-screen"
    >
      {/* Scanline overlay */}
      <div className="absolute inset-0 cc-scanline" />
      {/* Soft ambient green glow behind icon */}
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(circle at 50% 50%, rgba(57,255,20,0.10) 0%, rgba(57,255,20,0.02) 35%, rgba(5,5,5,0) 65%)",
        }}
      />

      {/* Center: SVG with the icon as centerpiece + curved text around it */}
      <svg
        viewBox="0 0 400 460"
        preserveAspectRatio="xMidYMid meet"
        className="relative w-[92vw] max-w-[420px] h-auto splash-fade-in"
        style={{ maxHeight: "92vh" }}
      >
        <defs>
          <clipPath id="iconClip">
            <circle cx="200" cy="230" r="120" />
          </clipPath>
          {/* Top text arc — opens DOWN, text reads left-to-right across the top of the icon */}
          <path id="splashTopArc" d="M 35 230 A 165 165 0 0 1 365 230" fill="none" />
          {/* Bottom text arc — opens UP, text reads left-to-right across the bottom of the icon */}
          <path id="splashBottomArc" d="M 35 230 A 165 165 0 0 0 365 230" fill="none" />
        </defs>

        {/* App icon (clipped to circle) */}
        <image
          href={iconImg}
          x="80" y="110" width="240" height="240"
          clipPath="url(#iconClip)"
          className="splash-icon-pop"
        />

        {/* Glow ring around the icon */}
        <circle
          cx="200" cy="230" r="122"
          fill="none"
          stroke="#39FF14"
          strokeWidth="1.5"
          opacity="0.7"
          style={{ filter: "drop-shadow(0 0 10px rgba(57,255,20,0.8))" }}
        />
        <circle
          cx="200" cy="230" r="135"
          fill="none"
          stroke="#39FF14"
          strokeWidth="0.5"
          opacity="0.35"
          strokeDasharray="4 6"
        />

        {/* TOP curved text — TACTICAL ALLY */}
        <text
          fontFamily="Orbitron, sans-serif"
          fontWeight="900"
          fontSize="26"
          fill="#39FF14"
          letterSpacing="4"
          style={{ filter: "drop-shadow(0 0 6px rgba(57,255,20,0.9)) drop-shadow(0 0 18px rgba(57,255,20,0.4))" }}
        >
          <textPath href="#splashTopArc" startOffset="50%" textAnchor="middle">
            TACTICAL ALLY
          </textPath>
        </text>

        {/* BOTTOM curved text — CYPHERAI STRATEGIES */}
        <text
          fontFamily="Orbitron, sans-serif"
          fontWeight="700"
          fontSize="18"
          fill="#39FF14"
          letterSpacing="3"
          style={{ filter: "drop-shadow(0 0 4px rgba(57,255,20,0.7))" }}
        >
          <textPath href="#splashBottomArc" startOffset="50%" textAnchor="middle">
            CYPHERAI STRATEGIES
          </textPath>
        </text>
      </svg>

      {/* Progress + skip */}
      <div className="absolute bottom-6 left-0 right-0 text-center font-mono-tactical text-[10px] tracking-[0.3em] text-zinc-600" data-testid="splash-skip-hint">
        TAP TO SKIP
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#39FF14]/10">
        <div
          className="h-full bg-[#39FF14]"
          style={{
            animation: `splashProgress ${HOLD_MS}ms linear forwards`,
            boxShadow: "0 0 8px rgba(57,255,20,0.7)",
          }}
        />
      </div>
    </div>
  );
};

export default SplashScreen;
