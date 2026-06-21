import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ChatCircleText, Target, BookOpen, ListChecks, ArrowRight, MapTrifold,
  Compass, GraduationCap, ArrowSquareOut, CaretDown, X, Brain, ShieldStar, FlagBanner,
  CastleTurret, BuildingApartment, Fire, FlowerLotus, Mosque, Columns, Crown,
  Feather, ComputerTower, MoonStars, Skull,
} from "@phosphor-icons/react";
import { TUTORIALS } from "../data/tutorials";
import commandCenterBg from "../assets/command-center-bg-v1.jpg";

/* === Per-game iconography (no all-castles — each title gets its motif) === */
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

/* === Typewriter Briefing (neon green, character-by-character) === */
const TypewriterBriefing = ({ username }) => {
  const lines = [
    `> CYPHR-AI ONLINE · OPERATOR ${(username || "COMMANDER").toUpperCase()}`,
    `> Tactical Ally is your AI strategy companion across 11 active battle theaters.`,
    `> Upload account screenshots → CyphrAI runs a personalized Deep Dive baseline tailored to your roster, resources, and play style.`,
    `> Stack Building Blocks as you advance — every follow-up sharpens your plan against the current meta.`,
    `> Free intel includes: CyphrAI Chat, Build Optimizer, 15+ curated Guides, Daily Planner. Pro unlocks Deep Dives and Alliance Operations.`,
    `> SELECT A THEATER BELOW TO BEGIN.`,
  ];

  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [done, setDone] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (done) return;
    if (lineIdx >= lines.length) { setDone(true); return; }
    const current = lines[lineIdx];
    if (charIdx < current.length) {
      timerRef.current = setTimeout(() => setCharIdx(c => c + 1), 18);
    } else {
      timerRef.current = setTimeout(() => { setLineIdx(i => i + 1); setCharIdx(0); }, 240);
    }
    return () => clearTimeout(timerRef.current);
  }, [charIdx, lineIdx, done, lines]);

  return (
    <div className="cc-panel relative p-7 sm:p-9 overflow-hidden" data-testid="briefing-panel">
      <div className="cc-scanline absolute inset-0" />
      <div className="tactical-label cc-neon-text mb-4">// INCOMING TRANSMISSION · 0001</div>
      <div className="font-mono-tactical text-[13px] sm:text-sm leading-relaxed cc-neon-text whitespace-pre-wrap" data-testid="briefing-text">
        {lines.slice(0, lineIdx).map((l, i) => <div key={i} className="mb-1.5">{l}</div>)}
        {lineIdx < lines.length && (
          <div className="mb-1.5">
            {lines[lineIdx].slice(0, charIdx)}
            <span className="cc-cursor">&nbsp;</span>
          </div>
        )}
        {done && <span className="cc-cursor">&nbsp;</span>}
      </div>
    </div>
  );
};

/* === Animated Radar Widget === */
const RadarWidget = ({ stats, gamesCount }) => {
  // Static blip positions (deterministic so they don't dance on every render)
  const blips = [
    { angle: 32, r: 0.32 },
    { angle: 110, r: 0.55 },
    { angle: 198, r: 0.42 },
    { angle: 265, r: 0.65 },
    { angle: 340, r: 0.28 },
  ];
  return (
    <div className="cc-panel p-5 sm:p-6 flex items-center gap-6 flex-wrap" data-testid="radar-widget">
      <div className="relative" style={{ width: 200, height: 200 }}>
        <svg viewBox="0 0 200 200" width="200" height="200" className="cc-radar">
          <defs>
            <radialGradient id="rg" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(57,255,20,0.35)" />
              <stop offset="60%" stopColor="rgba(57,255,20,0.08)" />
              <stop offset="100%" stopColor="rgba(57,255,20,0)" />
            </radialGradient>
            <linearGradient id="sweep" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(57,255,20,0)" />
              <stop offset="100%" stopColor="rgba(57,255,20,0.8)" />
            </linearGradient>
          </defs>
          {/* outer rings */}
          {[95, 75, 55, 35].map((r, i) => (
            <circle key={i} cx="100" cy="100" r={r} fill="none" stroke="rgba(57,255,20,0.35)" strokeWidth="0.6" strokeDasharray={i === 0 ? "2 4" : "0"} />
          ))}
          {/* crosshair */}
          <line x1="100" y1="2" x2="100" y2="198" stroke="rgba(57,255,20,0.18)" strokeWidth="0.5" />
          <line x1="2" y1="100" x2="198" y2="100" stroke="rgba(57,255,20,0.18)" strokeWidth="0.5" />
          {/* radial divisions */}
          {[45, 135, 225, 315].map(a => {
            const x2 = 100 + Math.cos(a * Math.PI / 180) * 95;
            const y2 = 100 + Math.sin(a * Math.PI / 180) * 95;
            return <line key={a} x1="100" y1="100" x2={x2} y2={y2} stroke="rgba(57,255,20,0.12)" strokeWidth="0.5" />;
          })}
          {/* sweep */}
          <g className="cc-radar-sweep">
            <path d="M 100 100 L 100 5 A 95 95 0 0 1 165 35 Z" fill="url(#rg)" />
            <line x1="100" y1="100" x2="100" y2="5" stroke="url(#sweep)" strokeWidth="1.5" />
          </g>
          {/* center pulse */}
          <circle cx="100" cy="100" r="3" fill="#39FF14" />
          <circle cx="100" cy="100" r="8" fill="none" stroke="#39FF14" strokeWidth="0.8" className="cc-radar-pulse" />
          {/* blips */}
          {blips.map((b, i) => {
            const cx = 100 + Math.cos(b.angle * Math.PI / 180) * (b.r * 90);
            const cy = 100 + Math.sin(b.angle * Math.PI / 180) * (b.r * 90);
            return (
              <g key={i}>
                <circle cx={cx} cy={cy} r="2.5" fill="#39FF14">
                  <animate attributeName="opacity" values="0.3;1;0.3" dur={`${1.5 + i * 0.4}s`} repeatCount="indefinite" />
                </circle>
                <circle cx={cx} cy={cy} r="5" fill="none" stroke="#39FF14" strokeWidth="0.5" opacity="0.4" />
              </g>
            );
          })}
        </svg>
      </div>

      {/* Right-side scanner readouts (clean, minimal — NOT the chaotic mockup boxes) */}
      <div className="flex-1 min-w-[240px] space-y-3" data-testid="radar-readouts">
        <div className="tactical-label cc-neon-text">// TACTICAL SCAN · ALL CLEAR</div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <div className="tactical-label text-zinc-500">THEATERS</div>
            <div className="font-display text-2xl font-black cc-neon-text" data-testid="radar-stat-theaters">{gamesCount}</div>
          </div>
          <div>
            <div className="tactical-label text-zinc-500">OPEN CHATS</div>
            <div className="font-display text-2xl font-black cc-neon-text" data-testid="radar-stat-chats">{stats.chats}</div>
          </div>
          <div>
            <div className="tactical-label text-zinc-500">ACTIVE OBJ.</div>
            <div className="font-display text-2xl font-black cc-neon-text" data-testid="radar-stat-tasks">{stats.tasks}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

/* === Quota Widget (re-styled for command room theme) === */
const QuotaWidget = () => {
  const [q, setQ] = useState(null);
  useEffect(() => { api.get("/billing/quota").then(r => setQ(r.data)); }, []);
  if (!q) return null;
  const isPro = q.plan === "pro";
  return (
    <div className="cc-panel p-5 flex items-center gap-5 flex-wrap" data-testid="quota-widget">
      <div className="flex-1 min-w-[200px]">
        <div className="tactical-label cc-neon-text mb-1.5">
          // PLAN · {isPro ? "TACTICAL ALLY PRO" : "RECRUIT (FREE)"}
        </div>
        <div className="font-display text-2xl font-black">
          {q.total_baselines_available} <span className="text-zinc-500 text-sm font-medium">Deep Dive{q.total_baselines_available === 1 ? "" : "s"} available</span>
        </div>
        {isPro && q.subscription_period_end && (
          <p className="text-xs text-zinc-500 mt-1.5">
            Pro renews {new Date(q.subscription_period_end).toLocaleDateString()} · {q.period_baselines_remaining} from plan · {q.extra_baselines} top-up
          </p>
        )}
        {!isPro && (
          <p className="text-xs text-zinc-500 mt-1.5">Unlock 2 baselines / month with Pro, or earn free ones via Tactical Scouts.</p>
        )}
      </div>
      <Link to="/pricing" className={isPro ? "btn-outline" : "btn-primary"} data-testid="quota-cta">
        {isPro ? "Manage plan" : "Upgrade to Pro"}
      </Link>
    </div>
  );
};

/* === Tutorial dropdown selector (preserved, re-themed) === */
const TutorialPanel = () => {
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const active = TUTORIALS.find(t => t.id === activeId);

  return (
    <div className="cc-panel p-6" data-testid="tutorial-panel">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
        <div>
          <div className="tactical-label cc-neon-text mb-2">// ORIENTATION · WALKTHROUGHS</div>
          <h2 className="font-display text-2xl font-bold tracking-tight flex items-center gap-2">
            <GraduationCap size={22} weight="duotone" className="cc-neon-text" /> Pick a 2-min tutorial
          </h2>
        </div>
      </div>

      <div className="relative">
        <button
          onClick={() => setOpen(o => !o)}
          className="w-full flex items-center justify-between bg-[#050805] border border-[#39FF14]/30 rounded px-4 py-3 text-sm hover:border-[#39FF14]/70 transition"
          data-testid="tutorial-dropdown-trigger"
        >
          <span className={active ? "text-white" : "text-zinc-500"}>
            {active ? active.label : "Select a tutorial…"}
          </span>
          <CaretDown size={14} className={`transition ${open ? "rotate-180" : ""}`} />
        </button>
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
              className="absolute z-20 mt-2 w-full bg-[#050805] border border-[#39FF14]/30 rounded-md overflow-hidden shadow-2xl"
              data-testid="tutorial-dropdown-menu"
            >
              {TUTORIALS.map(t => (
                <button
                  key={t.id}
                  onClick={() => { setActiveId(t.id); setOpen(false); }}
                  className={`w-full flex items-center justify-between gap-2 px-4 py-3 text-left text-sm hover:bg-[#39FF14]/10 border-b border-[#39FF14]/10 last:border-0 ${activeId === t.id ? "bg-[#39FF14]/5" : ""}`}
                  data-testid={`tutorial-option-${t.id}`}
                >
                  <span>{t.label}</span>
                  <span className="tactical-label">{t.duration}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {active && (
        <div className="mt-5 flex items-center gap-3">
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2" data-testid="tutorial-start-btn">
            <ArrowSquareOut size={16} weight="bold" /> Start walkthrough
          </button>
          <span className="tactical-label cc-neon-text">// {active.steps.length} STEPS · {active.duration}</span>
        </div>
      )}

      <AnimatePresence>
        {showModal && active && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowModal(false)}
            data-testid="tutorial-modal"
          >
            <motion.div
              initial={{ scale: 0.95, y: 10 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 10 }}
              className="cc-panel max-w-2xl w-full p-7 max-h-[85vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="tactical-label cc-neon-text mb-1">// {active.duration} WALKTHROUGH</div>
                  <h3 className="font-display text-2xl font-bold tracking-tight">{active.label}</h3>
                </div>
                <button onClick={() => setShowModal(false)} className="text-zinc-500 hover:text-white" data-testid="tutorial-modal-close">
                  <X size={20} />
                </button>
              </div>
              <ol className="space-y-4 mt-6">
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
              <button onClick={() => setShowModal(false)} className="btn-primary w-full mt-6" data-testid="tutorial-modal-done">Got it, commander</button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/* === Path Cards (preserved, re-themed) === */
const PathCards = ({ navigate }) => {
  const paths = [
    { icon: Brain, label: "CyphrAI Deep Dive", desc: "Upload screenshots → AI baseline + building blocks.", action: "Pick a theater below" },
    { icon: ShieldStar, label: "Operations Center", desc: "Alliance chat, share Deep Dives, ask CyphrAI in-room.", action: "Open HQ →", to: "/operations", testId: "path-operations" },
    { icon: FlagBanner, label: "Battle Reports", desc: "Log engagements with screenshots + optional CyphrAI take.", action: "Open archive →", to: "/battle-reports", testId: "path-battle-reports" },
    { icon: MapTrifold, label: "Enter the War Room", desc: "Your personal archive of campaigns, builds, tasks.", action: "Go to War Room →", to: "/war-room", testId: "path-war-room" },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="path-cards">
      {paths.map((p) => {
        const Icon = p.icon;
        const inner = (
          <div className="cc-panel p-5 h-full group hover:-translate-y-1 transition cursor-pointer">
            <Icon size={28} weight="duotone" className="cc-neon-text mb-3" />
            <h3 className="font-display text-lg font-bold tracking-tight">{p.label}</h3>
            <p className="text-sm text-zinc-400 mt-1 mb-4">{p.desc}</p>
            <div className="tactical-label cc-neon-text flex items-center gap-1">
              {p.action} <ArrowRight size={12} weight="bold" />
            </div>
          </div>
        );
        return p.to
          ? <Link key={p.label} to={p.to} data-testid={p.testId}>{inner}</Link>
          : <div key={p.label}>{inner}</div>;
      })}
    </div>
  );
};

/* === Battle Theater Tiles (11 games, custom icons, glowing outpost style) === */
const BattleTheaters = ({ games }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 cc-grid-floor p-4 -m-4 rounded-md" data-testid="game-grid">
      {games.map((g, i) => {
        const Icon = GAME_ICONS[g.slug] || CastleTurret;
        return (
          <motion.div
            key={g.slug}
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
          >
            <Link
              to={`/game/${g.slug}`}
              className="cc-panel cc-tile p-5 h-full flex flex-col items-center text-center group hover:-translate-y-1 transition"
              data-testid={`game-card-${g.slug}`}
            >
              <span className="cc-tile-corner tl" />
              <span className="cc-tile-corner tr" />
              <span className="cc-tile-corner bl" />
              <span className="cc-tile-corner br" />
              <div className="w-16 h-16 rounded-full border border-[#39FF14]/40 flex items-center justify-center mb-3"
                   style={{ background: "radial-gradient(circle at center, rgba(57,255,20,0.18), rgba(57,255,20,0))" }}>
                <Icon size={32} weight="duotone" className="cc-neon-text" />
              </div>
              <h3 className="font-display text-sm font-bold tracking-tight leading-tight">{g.name}</h3>
              <p className="text-[10px] uppercase tracking-widest font-mono-tactical text-zinc-500 mt-1">{g.genre.split(" / ")[0]}</p>
              <div className="mt-3 flex items-center gap-2 text-zinc-600 group-hover:text-[#39FF14] transition">
                <ChatCircleText size={12} /> <Target size={12} /> <BookOpen size={12} /> <ListChecks size={12} />
              </div>
            </Link>
          </motion.div>
        );
      })}
    </div>
  );
};

/* === Main Dashboard (Command Center) === */
const Dashboard = () => {
  const { user } = useAuth();
  const nav = useNavigate();
  const [games, setGames] = useState([]);
  const [stats, setStats] = useState({ chats: 0, builds: 0, tasks: 0 });

  useEffect(() => {
    api.get("/games").then(r => setGames(r.data));
    Promise.all([
      api.get("/chat/sessions").then(r => r.data.length).catch(() => 0),
      api.get("/builds").then(r => r.data.length).catch(() => 0),
      api.get("/tasks").then(r => r.data.filter(t => !t.completed).length).catch(() => 0),
    ]).then(([chats, builds, tasks]) => setStats({ chats, builds, tasks }));
  }, []);

  return (
    <div className="command-center">
      <div className="cc-backdrop" style={{ backgroundImage: `url(${commandCenterBg})` }} />
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-8 relative z-10">
        {/* Header: Welcome */}
        <div>
          <div className="tactical-label cc-neon-text mb-2">// COMMAND CENTER</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
            Welcome to the Command Center,<br />
            <span className="cc-neon-text">{user?.username || "Commander"}</span>.
          </h1>
        </div>

        {/* Typewriter briefing */}
        <TypewriterBriefing username={user?.username} />

        {/* Tactical Radar + readouts */}
        <RadarWidget stats={stats} gamesCount={games.length || 11} />

        {/* Quota strip */}
        <QuotaWidget />

        {/* Battle Theaters (11 games) */}
        <div>
          <div className="tactical-label cc-neon-text mb-3">// BATTLE THEATERS · {games.length} ACTIVE</div>
          <h2 className="font-display text-2xl font-bold tracking-tight mb-4 flex items-center gap-2">
            <Compass size={22} weight="duotone" className="cc-neon-text" /> Select your theater
          </h2>
          <BattleTheaters games={games} />
        </div>

        {/* Path cards */}
        <div>
          <div className="tactical-label cc-neon-text mb-3">// OPERATIONS</div>
          <PathCards navigate={nav} />
        </div>

        {/* Tutorial panel */}
        <TutorialPanel />
      </div>
    </div>
  );
};

export default Dashboard;
