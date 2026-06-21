import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { DeviceMobile, ArrowsClockwise, X } from "@phosphor-icons/react";

/**
 * LandscapeOverlay
 * Shows a "rotate to landscape" overlay when:
 *  - user is on an authed route (NOT landing/auth/pricing/help — those stay flexible)
 *  - device viewport is narrow (mobile/tablet) AND orientation is portrait
 *  - user hasn't dismissed it this session
 */
const PUBLIC_PATHS = ["/", "/auth", "/pricing", "/help", "/forgot-password", "/reset-password", "/share", "/billing"];

const LandscapeOverlay = () => {
  const { pathname } = useLocation();
  const [isPortrait, setIsPortrait] = useState(false);
  const [isNarrow, setIsNarrow] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const checkPortrait = () => {
      setIsPortrait(window.matchMedia("(orientation: portrait)").matches);
      setIsNarrow(window.innerWidth < 900);
    };
    checkPortrait();
    window.addEventListener("resize", checkPortrait);
    window.addEventListener("orientationchange", checkPortrait);
    return () => {
      window.removeEventListener("resize", checkPortrait);
      window.removeEventListener("orientationchange", checkPortrait);
    };
  }, []);

  // Detect first public-path segment so dynamic routes still match e.g. /pricing/success
  const onPublicPath = PUBLIC_PATHS.some(p => p === "/" ? pathname === "/" : pathname.startsWith(p));

  if (onPublicPath) return null;
  if (!isPortrait || !isNarrow) return null;
  if (dismissed) return null;

  return (
    <div
      className="fixed inset-0 z-[200] bg-[#0a0a0a]/97 backdrop-blur-sm flex items-center justify-center p-6"
      data-testid="landscape-overlay"
    >
      <div className="max-w-sm text-center relative">
        <button
          onClick={() => setDismissed(true)}
          className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center"
          aria-label="Dismiss"
          data-testid="landscape-overlay-dismiss"
        >
          <X size={16} />
        </button>

        <div className="relative w-28 h-28 mx-auto mb-6">
          <DeviceMobile size={96} weight="duotone" className="cc-neon-text animate-pulse" style={{ color: "#39FF14" }} />
          <ArrowsClockwise size={32} weight="bold" className="absolute -right-2 -bottom-2 bg-[#0a0a0a] rounded-full p-1" style={{ color: "#39FF14", animation: "spin 2.4s ease-in-out infinite" }} />
        </div>

        <div className="font-mono-tactical text-xs tracking-[0.25em] mb-2" style={{ color: "#39FF14" }}>// ROTATE DEVICE</div>
        <h2 className="font-display text-2xl font-black tracking-tight mb-3">
          Tactical Ally is built for <span style={{ color: "#39FF14" }}>landscape</span>
        </h2>
        <p className="text-sm text-zinc-400 leading-relaxed mb-6">
          Your screens, radar, and battle theaters render full-cinematic when you turn your device sideways. Rotate now for the command-bridge experience.
        </p>
        <button
          onClick={() => setDismissed(true)}
          className="text-xs text-zinc-500 hover:text-zinc-300 underline"
          data-testid="landscape-overlay-continue"
        >
          Continue in portrait anyway
        </button>
      </div>
    </div>
  );
};

export default LandscapeOverlay;
