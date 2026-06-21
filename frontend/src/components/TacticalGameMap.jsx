import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import {
  CastleTurret, BuildingApartment, Fire, FlowerLotus, Mosque, Columns, Crown,
  Feather, ComputerTower, MoonStars, Skull, X, Lock, CheckCircle,
  ArrowRight, Star, Crosshair, ShieldStar,
} from "@phosphor-icons/react";
import { api } from "../lib/api";

const GAME_ICONS = {
  "puzzles-conquest":            CastleTurret,
  "puzzles-survival":            BuildingApartment,
  "legend-rise-mythic-heroes":   Fire,
  "soul-land-reloaded":          FlowerLotus,
  "days-of-empire":              Mosque,
  "era-of-conquest":             Columns,
  "infinity-kingdom":            Crown,
  "league-of-angels":            Feather,
  "wartune":                     ComputerTower,
  "dynasty-origins-conquest":    MoonStars,
  "puzzles-chaos":               Skull,
};

/* Positions on the 3D map floor — distributed so the eye reads them as scattered
   battlefields, with depth cues (further-away pieces shrink via CSS perspective). */
const MAP_POSITIONS = {
  "puzzles-conquest":            { left: "15%",  top: "18%",  scale: 0.85 },
  "puzzles-survival":            { left: "42%",  top: "10%",  scale: 0.80 },
  "legend-rise-mythic-heroes":   { left: "70%",  top: "16%",  scale: 0.86 },
  "soul-land-reloaded":          { left: "10%",  top: "44%",  scale: 0.95 },
  "days-of-empire":              { left: "38%",  top: "38%",  scale: 0.92 },
  "era-of-conquest":             { left: "64%",  top: "42%",  scale: 0.94 },
  "infinity-kingdom":            { left: "88%",  top: "36%",  scale: 0.88 },
  "league-of-angels":            { left: "22%",  top: "72%",  scale: 1.05 },
  "wartune":                     { left: "50%",  top: "78%",  scale: 1.08 },
  "dynasty-origins-conquest":    { left: "78%",  top: "70%",  scale: 1.04 },
  "puzzles-chaos":               { left: "92%",  top: "60%",  scale: 0.96 },
};

/* === Hovering radar disc above the map === */
const HoveringRadar = () => (
  <div className="map-radar" aria-hidden="true">
    <svg viewBox="0 0 220 220" width="100%" height="100%">
      <defs>
        <radialGradient id="rdrFill" cx="50%" cy="50%" r="50%">
          <stop offset="0%"  stopColor="rgba(0,255,128,0.18)" />
          <stop offset="60%" stopColor="rgba(0,255,128,0.04)" />
          <stop offset="100%" stopColor="rgba(0,255,128,0.0)" />
        </radialGradient>
        <linearGradient id="rdrSweep" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%"  stopColor="rgba(0,255,128,0.0)" />
          <stop offset="100%" stopColor="rgba(0,255,128,0.55)" />
        </linearGradient>
      </defs>
      <circle cx="110" cy="110" r="100" fill="url(#rdrFill)" />
      <circle cx="110" cy="110" r="100" fill="none" stroke="#00FF80" strokeWidth="1"  opacity="0.7" />
      <circle cx="110" cy="110" r="70"  fill="none" stroke="#00FF80" strokeWidth="0.8" opacity="0.45" />
      <circle cx="110" cy="110" r="40"  fill="none" stroke="#00FF80" strokeWidth="0.8" opacity="0.35" />
      <line x1="10"  y1="110" x2="210" y2="110" stroke="#00FF80" strokeWidth="0.5" opacity="0.35" />
      <line x1="110" y1="10"  x2="110" y2="210" stroke="#00FF80" strokeWidth="0.5" opacity="0.35" />
      {/* sweep */}
      <g style={{ transformOrigin: "110px 110px", animation: "mapRadarSweep 4s linear infinite" }}>
        <path d="M 110 110 L 110 10 A 100 100 0 0 1 200 65 Z" fill="url(#rdrSweep)" />
      </g>
      {/* center pulse */}
      <circle cx="110" cy="110" r="3" fill="#00FF80" />
      <circle cx="110" cy="110" r="8" fill="none" stroke="#00FF80" strokeWidth="0.7"
              style={{ transformOrigin: "110px 110px", animation: "mapRadarPing 2.2s ease-out infinite" }} />
    </svg>
  </div>
);

/* === Identify / Claim modal for a selected piece === */
const PieceDetail = ({ game, isClaimed, isPro, slots, claimedCount, onClose, onClaim, onEnter, busy }) => {
  const Icon = GAME_ICONS[game.slug] || CastleTurret;
  const wouldExceed = !isClaimed && claimedCount >= slots;
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      onClick={onClose}
      data-testid="piece-detail-overlay"
    >
      <motion.div
        className="map-piece-detail relative w-full max-w-md"
        initial={{ scale: 0.92, opacity: 0, y: 8 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.94, opacity: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        onClick={(e) => e.stopPropagation()}
        data-testid={`piece-detail-${game.slug}`}
      >
        <button onClick={onClose} className="absolute top-3 right-3 text-zinc-500 hover:text-white" data-testid="piece-detail-close">
          <X size={20} />
        </button>

        {/* corner ticks */}
        <span className="cc-tile-corner tl" />
        <span className="cc-tile-corner tr" />
        <span className="cc-tile-corner bl" />
        <span className="cc-tile-corner br" />

        <div className="flex items-center gap-3 mb-2">
          <Crosshair size={14} weight="bold" className="map-green" />
          <div className="font-mono-tactical text-[10px] tracking-[0.3em] map-green">
            // FRIENDLY UNIT CONFIRMED
          </div>
        </div>

        <div className="flex items-start gap-4 mb-4">
          <div className="w-16 h-16 rounded-full border border-[#00FF80]/50 flex items-center justify-center shrink-0"
               style={{ background: "radial-gradient(circle at center, rgba(0,255,128,0.18), rgba(0,0,0,0))" }}>
            <Icon size={34} weight="duotone" className="map-green" />
          </div>
          <div className="min-w-0">
            <h3 className="font-display text-xl font-bold tracking-tight leading-tight">{game.name}</h3>
            <p className="text-[11px] uppercase tracking-widest font-mono-tactical text-zinc-500 mt-1">{game.genre}</p>
            {isClaimed && (
              <div className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-sm border border-[#00FF80]/40 bg-[#00FF80]/10">
                <Star size={10} weight="fill" className="map-green" />
                <span className="font-mono-tactical text-[10px] tracking-[0.2em] map-green">PRO THEATER · CLAIMED</span>
              </div>
            )}
          </div>
        </div>

        <p className="text-sm text-zinc-300 leading-relaxed mb-5">
          CypherAI is field-trained on <strong>{game.name}</strong>. Enter the war room to deploy chat, optimizers,
          guides, builds, and Deep Dive analysis specific to this title.
        </p>

        {/* Slot status line */}
        <div className="cc-panel-thin p-3 mb-4 flex items-center justify-between gap-3 flex-wrap">
          <div className="font-mono-tactical text-[10px] tracking-[0.25em] text-zinc-400">
            PRO SLOTS: <span className="map-green">{claimedCount}</span> / <span className="text-zinc-300">{slots || 0}</span>
          </div>
          {!isPro && (
            <span className="font-mono-tactical text-[10px] tracking-[0.25em] map-orange">
              SUBSCRIBE TO CLAIM
            </span>
          )}
          {isPro && wouldExceed && (
            <span className="font-mono-tactical text-[10px] tracking-[0.25em] map-orange">
              ADD A SLOT · $0.99 /MO
            </span>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            className="btn-primary flex-1 inline-flex items-center justify-center gap-2"
            onClick={onEnter}
            data-testid={`piece-enter-${game.slug}`}
          >
            ENTER WAR ROOM <ArrowRight size={14} weight="bold" />
          </button>
          {isPro ? (
            <button
              className={`flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded font-display font-bold tracking-wide transition ${
                isClaimed
                  ? "border border-zinc-700 text-zinc-300 hover:border-zinc-500"
                  : wouldExceed
                  ? "border border-[#FF6B00]/40 text-[#FF6B00] hover:bg-[#FF6B00]/10"
                  : "border border-[#00FF80]/50 text-[#00FF80] hover:bg-[#00FF80]/10"
              } ${busy ? "opacity-60 pointer-events-none" : ""}`}
              onClick={() => (wouldExceed ? (window.location.href = "/pricing") : onClaim())}
              data-testid={`piece-claim-${game.slug}`}
            >
              {isClaimed ? (
                <><X size={14} weight="bold" /> RELEASE THEATER</>
              ) : wouldExceed ? (
                <><Lock size={14} weight="bold" /> ADD SLOT $0.99</>
              ) : (
                <><CheckCircle size={14} weight="bold" /> CLAIM AS PRO</>
              )}
            </button>
          ) : (
            <a
              href="/pricing"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded font-display font-bold tracking-wide border border-[#FF6B00]/40 text-[#FF6B00] hover:bg-[#FF6B00]/10 transition"
              data-testid={`piece-subscribe-${game.slug}`}
            >
              <ShieldStar size={14} weight="bold" /> UPGRADE TO PRO
            </a>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

/* === Main Tactical Map === */
const TacticalGameMap = ({ games }) => {
  const nav = useNavigate();
  const [quota, setQuota] = useState(null);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get("/billing/quota").then(r => setQuota(r.data)).catch(() => {}); }, []);

  const proGames = useMemo(() => quota?.pro_games || [], [quota]);
  const slots    = quota?.pro_game_slots || 0;
  const isPro    = !!quota?.subscription_active;

  const claim = async () => {
    if (!selected) return;
    const slug = selected.slug;
    const next = proGames.includes(slug)
      ? proGames.filter(s => s !== slug)
      : [...proGames, slug];
    setBusy(true);
    try {
      const { data } = await api.post("/billing/pro-games", { games: next });
      setQuota(q => ({ ...(q || {}), pro_games: data.pro_games }));
      toast.success(proGames.includes(slug) ? `${selected.name} released.` : `${selected.name} claimed.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not update theaters.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="tactical-map" data-testid="tactical-map">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3 mb-4">
        <div>
          <div className="tactical-label map-green mb-1.5">// TACTICAL MAP · IDENTIFY YOUR BATTLEFIELDS</div>
          <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight">Pick your theaters</h2>
          <p className="text-sm text-zinc-400 mt-1">Tap a beacon to identify the title. Pro theaters get full CypherAI deployment.</p>
        </div>
        <div className="cc-panel-thin px-3 py-1.5 font-mono-tactical text-[10px] tracking-[0.25em] text-zinc-300" data-testid="map-slot-counter">
          PRO THEATERS · <span className="map-green">{proGames.length}</span> / <span className="text-zinc-400">{slots || 0}</span>
        </div>
      </div>

      {/* The 3D map viewport */}
      <div className="map-viewport" data-testid="map-viewport">
        {/* Hovering radar floats above */}
        <HoveringRadar />

        {/* Floor with grid + pieces */}
        <div className="map-perspective">
          <div className="map-floor">
            {/* Grid pattern */}
            <svg className="map-floor-grid" viewBox="0 0 1000 700" preserveAspectRatio="none" aria-hidden="true">
              <defs>
                <pattern id="map-grid-fine" width="50" height="50" patternUnits="userSpaceOnUse">
                  <path d="M50 0 L0 0 0 50" fill="none" stroke="#00FF80" strokeWidth="0.6" opacity="0.55" />
                </pattern>
                <pattern id="map-grid-coarse" width="200" height="200" patternUnits="userSpaceOnUse">
                  <path d="M200 0 L0 0 0 200" fill="none" stroke="#00FF80" strokeWidth="1.2" opacity="0.9" />
                </pattern>
                <radialGradient id="floor-vignette" cx="50%" cy="50%" r="55%">
                  <stop offset="0%"   stopColor="rgba(0,0,0,0)" />
                  <stop offset="100%" stopColor="rgba(0,0,0,0.85)" />
                </radialGradient>
              </defs>
              <rect width="1000" height="700" fill="#020806" />
              <rect width="1000" height="700" fill="url(#map-grid-fine)" />
              <rect width="1000" height="700" fill="url(#map-grid-coarse)" />
              <rect width="1000" height="700" fill="url(#floor-vignette)" />
              {/* faint concentric command rings */}
              <g fill="none" stroke="#00FF80" strokeWidth="1" opacity="0.18">
                <circle cx="500" cy="350" r="160" />
                <circle cx="500" cy="350" r="280" />
                <circle cx="500" cy="350" r="400" />
              </g>
            </svg>
          </div>
        </div>

        {/* Pieces — positioned in screen-space so they stay upright (counter-tilt would warp icons).
            The depth illusion comes from per-piece scale + brightness gradient. */}
        <div className="map-pieces-layer">
          {games.map((g, idx) => {
            const Icon = GAME_ICONS[g.slug] || CastleTurret;
            const pos = MAP_POSITIONS[g.slug] || { left: `${10 + (idx % 4) * 24}%`, top: `${20 + Math.floor(idx / 4) * 22}%`, scale: 1 };
            const claimed = proGames.includes(g.slug);
            return (
              <motion.button
                key={g.slug}
                className={`map-piece ${claimed ? "claimed" : ""}`}
                style={{ left: pos.left, top: pos.top, transform: `translate(-50%, -50%) scale(${pos.scale})` }}
                initial={{ opacity: 0, y: 14, scale: pos.scale * 0.85 }}
                animate={{ opacity: 1, y: 0, scale: pos.scale }}
                transition={{ delay: 0.05 * idx, duration: 0.5, ease: "easeOut" }}
                whileHover={{ scale: pos.scale * 1.08 }}
                whileTap={{ scale: pos.scale * 0.95 }}
                onClick={() => setSelected(g)}
                data-testid={`map-piece-${g.slug}`}
                aria-label={`Identify ${g.name}`}
              >
                <span className="map-piece-glow" />
                <span className="map-piece-ring" />
                <span className="map-piece-base" />
                <span className="map-piece-icon">
                  <Icon size={26} weight="duotone" />
                </span>
                <span className="map-piece-label">{g.name.split(":")[0]}</span>
                {claimed && (
                  <span className="map-piece-star" aria-hidden="true">
                    <Star size={12} weight="fill" />
                  </span>
                )}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Hint footer */}
      <div className="mt-3 flex items-center justify-between flex-wrap gap-2 text-[11px] font-mono-tactical tracking-[0.2em] text-zinc-500">
        <span>// {games.length} BATTLE THEATERS DETECTED</span>
        <span>TAP A BEACON TO IDENTIFY</span>
      </div>

      <AnimatePresence>
        {selected && (
          <PieceDetail
            game={selected}
            isClaimed={proGames.includes(selected.slug)}
            isPro={isPro}
            slots={slots}
            claimedCount={proGames.length}
            busy={busy}
            onClose={() => setSelected(null)}
            onClaim={claim}
            onEnter={() => nav(`/game/${selected.slug}`)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default TacticalGameMap;
