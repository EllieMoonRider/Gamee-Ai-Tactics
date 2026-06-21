import { useEffect, useState } from "react";
import { DownloadSimple, X } from "@phosphor-icons/react";

/**
 * InstallPwaPrompt
 * Listens for the browser's beforeinstallprompt event (Chrome/Edge/Android) and shows a
 * dismissible bottom-right banner that lets users install Tactical Ally to their home screen.
 *
 * iOS Safari doesn't fire this event — instead, we detect iOS and show a separate hint with
 * the "Share → Add to Home Screen" instructions.
 *
 * Stored dismissal in localStorage so we don't annoy returning users.
 */
const InstallPwaPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [iosHint, setIosHint] = useState(false);

  useEffect(() => {
    if (localStorage.getItem("pwa-install-dismissed") === "1") return;
    if (window.matchMedia("(display-mode: standalone)").matches) return; // already installed

    const onBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowPrompt(true);
    };
    window.addEventListener("beforeinstallprompt", onBeforeInstall);

    // iOS detection (Safari doesn't fire beforeinstallprompt)
    const ua = window.navigator.userAgent;
    const isIos = /iPhone|iPad|iPod/i.test(ua) && !/CriOS|FxiOS/i.test(ua);
    if (isIos) {
      // Delay a bit so we don't spam first paint
      const t = setTimeout(() => setIosHint(true), 5000);
      return () => { clearTimeout(t); window.removeEventListener("beforeinstallprompt", onBeforeInstall); };
    }
    return () => window.removeEventListener("beforeinstallprompt", onBeforeInstall);
  }, []);

  const dismiss = () => {
    localStorage.setItem("pwa-install-dismissed", "1");
    setShowPrompt(false);
    setIosHint(false);
  };

  const install = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") localStorage.setItem("pwa-install-dismissed", "1");
    setShowPrompt(false);
    setDeferredPrompt(null);
  };

  if (!showPrompt && !iosHint) return null;

  return (
    <div
      className="fixed bottom-4 right-4 left-4 sm:left-auto sm:max-w-sm z-[150] bg-[#080a08] border border-[#39FF14]/40 rounded-md p-4 shadow-2xl"
      style={{ boxShadow: "0 0 24px rgba(57,255,20,0.18)" }}
      data-testid="pwa-install-prompt"
    >
      <button
        onClick={dismiss}
        className="absolute top-2 right-2 text-zinc-500 hover:text-white"
        aria-label="Dismiss"
        data-testid="pwa-install-dismiss"
      >
        <X size={16} />
      </button>
      <div className="flex items-start gap-3 pr-6">
        <div className="w-10 h-10 rounded-md bg-[#39FF14]/10 border border-[#39FF14]/40 flex items-center justify-center flex-shrink-0">
          <DownloadSimple size={20} weight="duotone" style={{ color: "#39FF14" }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono-tactical text-[10px] tracking-[0.25em]" style={{ color: "#39FF14" }}>// INSTALL APP</div>
          <h4 className="font-display font-bold text-sm mt-0.5">Get Tactical Ally as an app</h4>
          {iosHint ? (
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
              Tap <strong className="text-white">Share</strong> → <strong className="text-white">Add to Home Screen</strong>. Opens in landscape, full-screen.
            </p>
          ) : (
            <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
              One-tap install. Launches in landscape, full-screen, with your home-screen icon.
            </p>
          )}
          {!iosHint && (
            <button
              onClick={install}
              className="btn-primary !py-1.5 !px-3 text-xs mt-3"
              style={{ background: "#39FF14", color: "#0a0a0a" }}
              data-testid="pwa-install-btn"
            >
              Install now
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default InstallPwaPrompt;
