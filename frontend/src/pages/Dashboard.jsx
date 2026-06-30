import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../components/Navbar";
import TacticalGameMap from "../components/TacticalGameMap";
import CypherIntroBriefing from "../components/CypherIntroBriefing";
import HolographicGridFloor from "../components/HolographicGridFloor";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ChatCircleText, Target, BookOpen, ListChecks, ArrowRight, MapTrifold,
  Compass, GraduationCap, X, Brain, ShieldStar, Sparkle,
  CastleTurret, BuildingApartment, Fire, FlowerLotus, Mosque, Columns, Crown,
  Feather, ComputerTower, MoonStars, Skull,
  CreditCard, Tag,
} from "@phosphor-icons/react";
import { TUTORIALS } from "../data/tutorials";
import commandCenterBg from "../assets/command-center-bg-v1.jpg";
// LAYER 1 ART — cinematic War Room scene (AI-generated to match reference).
// Layers 2+ will mount text, briefings, panels, beacons on top of this scene.
import warRoomScene from "../assets/war-room-scene-v3-1.jpg";

/* === Per-game iconography === */
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

/* ===========================================================================
   Personalized Briefing — first-time vs returning, typewriter on each line.
   =========================================================================== */
const PersonalizedBriefing = ({ onboarding, onContinue, onPickNew }) => {
  const isFirstTime = onboarding?.first_time !== false;
  const name = (onboarding?.username || "Commander").toUpperCase();

  const firstTimeLines = [
    `> CYPHERAI ONLINE · WELCOME TO THE COMMAND CENTER, ${name}.`,
    `> Tactical Ally is your AI strategy companion across 11 active battle theaters.`,
    `> Your mission: dominate the meta. Our method: drop a screenshot of your account → CYPHERAI analyzes your roster, resources, and current play state, then issues a personalized Deep Dive plan.`,
    `> Stack follow-up Building Blocks to refine your strategy as you advance.`,
    `> Pick where you want to go below. The mission begins now.`,
  ];

  const last = onboarding?.last_activity;
  const lastLabel = last?.label || "your last campaign";
  const returningLines = [
    `> CYPHERAI ONLINE · WELCOME BACK, ${name}.`,
    last
      ? `> Last campaign on record: ${lastLabel}.`
      : `> Your war archive is ready.`,
    `> Pick your next move:`,
  ];

  const lines = isFirstTime ? firstTimeLines : returningLines;
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [done, setDone] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (done) return;
    if (lineIdx >= lines.length) { setDone(true); return; }
    const cur = lines[lineIdx];
    if (charIdx < cur.length) {
      timerRef.current = setTimeout(() => setCharIdx(c => c + 1), 16);
    } else {
      timerRef.current = setTimeout(() => { setLineIdx(i => i + 1); setCharIdx(0); }, 220);
    }
    return () => clearTimeout(timerRef.current);
  }, [charIdx, lineIdx, done, lines]);

  return (
    <div className="cc-panel relative p-7 sm:p-9 overflow-hidden" data-testid="briefing-panel">
      <div className="cc-scanline absolute inset-0" />
      <div className="tactical-label cc-neon-text mb-4">
        // INCOMING TRANSMISSION · {isFirstTime ? "FIRST CONTACT" : "RETURNING OPERATOR"}
      </div>
      <div className="font-mono-tactical text-[13px] sm:text-sm leading-relaxed cc-neon-text whitespace-pre-wrap min-h-[160px]" data-testid="briefing-text">
        {lines.slice(0, lineIdx).map((l, i) => <div key={i} className="mb-1.5">{l}</div>)}
        {lineIdx < lines.length && (
          <div className="mb-1.5">
            {lines[lineIdx].slice(0, charIdx)}
            <span className="cc-cursor">&nbsp;</span>
          </div>
        )}
        {done && <span className="cc-cursor">&nbsp;</span>}
      </div>

      {/* Returning user CTAs — only show after typewriter finishes */}
      {done && !isFirstTime && last && (
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="mt-6 flex flex-col sm:flex-row gap-3"
          data-testid="briefing-returning-ctas"
        >
          <button onClick={() => onContinue(last)} className="btn-primary flex-1" data-testid="briefing-continue">
            Pick up where you left off
          </button>
          <button onClick={onPickNew} className="btn-outline flex-1" data-testid="briefing-pick-new">
            Build a different strategy
          </button>
        </motion.div>
      )}
    </div>
  );
};

/* ===========================================================================
   Central Hub — 5 clickable mission stations.
   =========================================================================== */
const HUB_STATIONS = [
  { id: "pricing",  label: "Pricing & Plans",   desc: "Pro, top-ups, alliance chat seats.",      icon: CreditCard,  to: "/pricing"  },
  { id: "tutorial", label: "Tutorial",          desc: "2-minute walkthroughs to get oriented.",   icon: GraduationCap, to: "tutorial" },
  { id: "war-room", label: "Personal War Room", desc: "Your cross-game campaign archive.",        icon: MapTrifold,  to: "/war-room" },
  { id: "referral", label: "Referrals",         desc: "Share your sigil. Earn bonus baselines.",  icon: Tag,         to: "/referral" },
  { id: "scouts",   label: "Tactical Scouts",   desc: "Earn free Deep Dives the F2P way.",        icon: Sparkle,     to: "/scouts"   },
  { id: "cypher",   label: "About CypherAI",    desc: "Who CypherAI is. The name, the mission.",  icon: ShieldStar,  to: "/cypher"   },
];

const CentralHub = ({ onPickTutorial }) => (
  <div data-testid="central-hub">
    <div className="tactical-label cc-neon-text mb-3">// CENTRAL HUB · 6 STATIONS</div>
    <h2 className="font-display text-2xl font-bold tracking-tight mb-4 flex items-center gap-2">
      <Compass size={22} weight="duotone" className="cc-neon-text" /> Where to, Commander?
    </h2>
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {HUB_STATIONS.map((s, i) => {
        const Icon = s.icon;
        const inner = (
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            className="cc-panel cc-tile p-4 sm:p-5 h-full group hover:-translate-y-1 transition cursor-pointer text-center"
            data-testid={`hub-station-${s.id}`}
          >
            <span className="cc-tile-corner tl" />
            <span className="cc-tile-corner tr" />
            <span className="cc-tile-corner bl" />
            <span className="cc-tile-corner br" />
            <div className="w-14 h-14 mx-auto mb-3 rounded-full border border-[#FF6B00]/40 flex items-center justify-center"
                 style={{ background: "radial-gradient(circle at center, rgba(255,107,0,0.18), rgba(255,107,0,0))" }}>
              <Icon size={28} weight="duotone" className="cc-neon-text" />
            </div>
            <h3 className="font-display text-sm font-bold tracking-tight leading-tight cc-neon-text">{s.label}</h3>
            <p className="text-[11px] text-zinc-400 mt-1.5 leading-snug">{s.desc}</p>
            <div className="mt-3 inline-flex items-center gap-1 text-[10px] font-mono-tactical text-zinc-500 group-hover:text-[#FF6B00] transition tracking-widest">
              OPEN <ArrowRight size={10} weight="bold" />
            </div>
          </motion.div>
        );
        if (s.to === "tutorial") {
          return <button key={s.id} onClick={onPickTutorial} className="contents">{inner}</button>;
        }
        return <Link key={s.id} to={s.to} className="contents">{inner}</Link>;
      })}
    </div>
  </div>
);

/* ===========================================================================
   Tutorial dropdown (modal)
   =========================================================================== */
const TutorialModal = ({ open, onClose }) => {
  const [activeId, setActiveId] = useState(null);
  const active = TUTORIALS.find(t => t.id === activeId);
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
          data-testid="tutorial-modal"
        >
          <motion.div
            initial={{ scale: 0.95, y: 10 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 10 }}
            className="cc-panel max-w-2xl w-full p-7 max-h-[88vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {!active ? (
              <>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="tactical-label cc-neon-text mb-1">// ORIENTATION</div>
                    <h3 className="font-display text-2xl font-bold tracking-tight">Pick a 2-minute walkthrough</h3>
                  </div>
                  <button onClick={onClose} className="text-zinc-500 hover:text-white" data-testid="tutorial-modal-close"><X size={20} /></button>
                </div>
                <div className="space-y-2" data-testid="tutorial-list">
                  {TUTORIALS.map(t => (
                    <button
                      key={t.id} onClick={() => setActiveId(t.id)}
                      className="w-full flex items-center justify-between gap-2 px-4 py-3 rounded text-left text-sm border border-[#FF6B00]/20 hover:bg-[#FF6B00]/10 hover:border-[#FF6B00]/50 transition"
                      data-testid={`tutorial-option-${t.id}`}
                    >
                      <span>{t.label}</span>
                      <span className="tactical-label cc-neon-text">{t.duration}</span>
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="tactical-label cc-neon-text mb-1">// {active.duration} WALKTHROUGH</div>
                    <h3 className="font-display text-2xl font-bold tracking-tight">{active.label}</h3>
                  </div>
                  <button onClick={() => setActiveId(null)} className="text-zinc-500 hover:text-white" data-testid="tutorial-modal-back">← Back</button>
                </div>
                <ol className="space-y-4 mt-4">
                  {active.steps.map((s, i) => (
                    <li key={i} className="flex gap-4">
                      <div className="font-mono-tactical text-2xl font-bold cc-neon-text leading-none">{String(i + 1).padStart(2, "0")}</div>
                      <div>
                        <h4 className="font-display font-bold text-base">{s.title}</h4>
                        <p className="text-sm text-zinc-400 mt-1 leading-relaxed">{s.body}</p>
                      </div>
                    </li>
                  ))}
                </ol>
                <button onClick={onClose} className="btn-primary w-full mt-6" data-testid="tutorial-modal-done">Got it, commander</button>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/* ===========================================================================
   Quota strip
   =========================================================================== */
const QuotaWidget = () => {
  const [q, setQ] = useState(null);
  useEffect(() => { api.get("/billing/quota").then(r => setQ(r.data)); }, []);
  if (!q) return null;
  const isPro = q.plan === "pro";
  return (
    <div className="cc-panel p-5 flex items-center gap-5 flex-wrap" data-testid="quota-widget">
      <div className="flex-1 min-w-[200px]">
        <div className="tactical-label cc-neon-text mb-1.5">// PLAN · {isPro ? "TACTICAL ALLY PRO" : "RECRUIT (FREE)"}</div>
        <div className="font-display text-2xl font-black">
          {q.total_baselines_available} <span className="text-zinc-500 text-sm font-medium">Deep Dive{q.total_baselines_available === 1 ? "" : "s"} available</span>
        </div>
        {isPro && q.subscription_period_end && <p className="text-xs text-zinc-500 mt-1.5">Pro renews {new Date(q.subscription_period_end).toLocaleDateString()}</p>}
        {!isPro && <p className="text-xs text-zinc-500 mt-1.5">Unlock 2 baselines / month with Pro, or earn free ones via Tactical Scouts.</p>}
      </div>
      <Link to="/pricing" className={isPro ? "btn-outline" : "btn-primary"} data-testid="quota-cta">
        {isPro ? "Manage plan" : "Upgrade to Pro"}
      </Link>
    </div>
  );
};

/* ===========================================================================
   Main Dashboard (Command Center)
   =========================================================================== */
const Dashboard = () => {
  const { user } = useAuth();
  const nav = useNavigate();
  const [games, setGames] = useState([]);
  const [onboarding, setOnboarding] = useState(null);
  const [tutorialOpen, setTutorialOpen] = useState(false);
  // CypherAI one-time first-sign-in briefing. Gated by localStorage so it
  // only plays once per device. /cypher page always shows the same words.
  const [showBriefing, setShowBriefing] = useState(
    () => typeof window !== "undefined" && localStorage.getItem("ta-cypher-intro-seen") !== "1"
  );

  // Attempt to lock landscape orientation (PWA / Android Chrome supports this; iOS Safari ignores)
  useEffect(() => {
    const lock = async () => {
      try {
        if (window.screen?.orientation?.lock) {
          await window.screen.orientation.lock("landscape");
        }
      } catch { /* unsupported — overlay handles it */ }
    };
    lock();
    return () => {
      try { window.screen?.orientation?.unlock?.(); } catch { /* noop */ }
    };
  }, []);

  useEffect(() => {
    api.get("/games").then(r => setGames(r.data));
    api.get("/user/onboarding").then(r => setOnboarding(r.data));
  }, []);

  const handleContinue = (last) => { if (last?.link) nav(last.link); };
  const handlePickNew = () => {
    document.querySelector('[data-testid="game-grid"]')?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="command-center min-h-screen relative overflow-hidden bg-black">
      {/* === LAYER 1 — Cinematic War Room scene only ===
          The AI-painted backdrop IS the design. No panels, no headers, no
          briefing rectangle, no central hub, no tactical map yet — those
          arrive in Layer 2+. Data hooks above (games, onboarding) stay wired
          so we can layer functionality on top without rebuilding logic. */}
      <Navbar />

      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url(${warRoomScene})`,
          backgroundSize: "cover",
          backgroundPosition: "center center",
          backgroundRepeat: "no-repeat",
        }}
        data-testid="war-room-scene"
      />

      {/* === LAYER 1.5 — Live holographic topographic grid floor ===
          Animated perspective grid + contour lines + scanning sweep,
          projected on the bottom portion of the scene. Pointer-events
          none — beacons (Layer 2) will mount on top and remain clickable. */}
      <HolographicGridFloor />

      {/* One-time CypherAI introduction — overlay only, plays once per device. */}
      <AnimatePresence>
        {showBriefing && <CypherIntroBriefing onDismiss={() => setShowBriefing(false)} />}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;
