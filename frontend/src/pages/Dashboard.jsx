import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ChatCircleText, Target, BookOpen, ListChecks, ArrowRight, MapTrifold,
  Compass, GraduationCap, ArrowSquareOut, CaretDown, X, Brain,
} from "@phosphor-icons/react";
import { TUTORIALS } from "../data/tutorials";

/* === Briefing (Welcome panel) === */
const Briefing = ({ username }) => {
  const hour = new Date().getHours();
  const greet = hour < 5 ? "Late watch" : hour < 12 ? "Morning briefing" : hour < 17 ? "Afternoon briefing" : "Evening briefing";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="surface rounded-md p-7 lg:p-10 relative overflow-hidden"
      data-testid="briefing-panel"
    >
      <div className="absolute inset-0 -z-10 opacity-[0.08]">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>
      <div className="tactical-label text-[#E63946] mb-3">// {greet.toUpperCase()} — TRANSMISSION 01</div>
      <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
        Welcome to the Command Center,<br />
        <span className="text-[#FFBA08]">{username || "Operator"}</span>.
      </h1>
      <p className="text-zinc-400 mt-4 max-w-2xl leading-relaxed">
        Your war table is set. Below: tutorials, strategy access for all 10 supported 37Games titles, and a private War Room for your saved campaigns.
      </p>
    </motion.div>
  );
};

/* === Tutorial dropdown selector === */
const TutorialPanel = () => {
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const active = TUTORIALS.find(t => t.id === activeId);

  return (
    <div className="surface rounded-md p-6" data-testid="tutorial-panel">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
        <div>
          <div className="tactical-label text-zinc-500 mb-2">// 02 — ORIENTATION</div>
          <h2 className="font-display text-2xl font-bold tracking-tight flex items-center gap-2">
            <GraduationCap size={22} weight="duotone" className="text-[#10B981]" /> Walkthrough Tutorials
          </h2>
          <p className="text-sm text-zinc-400 mt-1">Pick a walkthrough to learn the platform in under 2 minutes.</p>
        </div>
      </div>

      {/* Custom dropdown */}
      <div className="relative">
        <button
          onClick={() => setOpen(o => !o)}
          className="w-full flex items-center justify-between bg-[#0c0c0c] border border-white/10 rounded px-4 py-3 text-sm hover:border-white/30 transition"
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
              className="absolute z-20 mt-2 w-full surface-elev rounded-md overflow-hidden shadow-2xl"
              data-testid="tutorial-dropdown-menu"
            >
              {TUTORIALS.map(t => (
                <button
                  key={t.id}
                  onClick={() => { setActiveId(t.id); setOpen(false); }}
                  className={`w-full flex items-center justify-between gap-2 px-4 py-3 text-left text-sm hover:bg-white/5 border-b border-white/5 last:border-0 ${activeId === t.id ? "bg-white/5" : ""}`}
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
          <span className="tactical-label">// {active.steps.length} STEPS · {active.duration}</span>
        </div>
      )}

      {/* Walkthrough modal */}
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
              className="surface-elev max-w-2xl w-full rounded-md p-7 max-h-[85vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="tactical-label text-[#FFBA08] mb-1">// {active.duration} WALKTHROUGH</div>
                  <h3 className="font-display text-2xl font-bold tracking-tight">{active.label}</h3>
                </div>
                <button onClick={() => setShowModal(false)} className="text-zinc-500 hover:text-white" data-testid="tutorial-modal-close">
                  <X size={20} />
                </button>
              </div>
              <ol className="space-y-4 mt-6">
                {active.steps.map((s, i) => (
                  <li key={i} className="flex gap-4">
                    <div className="font-mono-tactical text-2xl font-bold text-[#E63946] leading-none">{String(i + 1).padStart(2, "0")}</div>
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

/* === Path Cards (choose your action) === */
const PathCards = ({ navigate }) => {
  const paths = [
    { icon: Brain, label: "CyphrAI Deep Dive", desc: "Upload screenshots → AI baseline + building blocks.", action: "Pick a title below", color: "#E63946" },
    { icon: ChatCircleText, label: "Talk to CyphrAI", desc: "Streaming AI chat for any of the 10 titles.", action: "Pick a title below", color: "#FFBA08" },
    { icon: Target, label: "Run the Optimizer", desc: "Drop roster + objective → tactical plan.", action: "Pick a title below", color: "#10B981" },
    { icon: MapTrifold, label: "Enter the War Room", desc: "Your personal archive of campaigns, builds, tasks.", action: "Go to War Room →", color: "#FFFFFF", to: "/war-room", testId: "path-war-room" },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="path-cards">
      {paths.map((p) => {
        const Icon = p.icon;
        const inner = (
          <div className="surface rounded-md p-5 h-full group hover:-translate-y-1 transition cursor-pointer">
            <Icon size={28} weight="duotone" style={{ color: p.color }} className="mb-3" />
            <h3 className="font-display text-lg font-bold tracking-tight">{p.label}</h3>
            <p className="text-sm text-zinc-400 mt-1 mb-4">{p.desc}</p>
            <div className="tactical-label flex items-center gap-1" style={{ color: p.color }}>
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

/* === Game Grid (existing) === */
const GameGrid = ({ games }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="game-grid">
    {games.map((g, i) => (
      <motion.div key={g.slug} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
        <Link to={`/game/${g.slug}`} className="surface rounded-md overflow-hidden block group hover:-translate-y-1" data-testid={`game-card-${g.slug}`}>
          <div className="game-card-image aspect-[16/10] relative">
            <img src={g.image} alt={g.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
            <div className="absolute top-3 left-3 z-10">
              <span className="tag-chip" style={{ color: g.color, borderColor: g.color + "40" }}>{g.genre.split(" / ")[0]}</span>
            </div>
            <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
              <h3 className="font-display text-lg font-bold leading-tight">{g.name}</h3>
              <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{g.tagline}</p>
            </div>
          </div>
          <div className="px-4 py-3 flex items-center justify-between border-t border-white/5">
            <div className="flex items-center gap-3 text-zinc-500">
              <ChatCircleText size={16} /> <Target size={16} /> <BookOpen size={16} /> <ListChecks size={16} />
            </div>
            <ArrowRight size={16} className="text-zinc-500 group-hover:text-[#E63946] transition" />
          </div>
        </Link>
      </motion.div>
    ))}
  </div>
);

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
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        <Briefing username={user?.username} />

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 max-w-3xl">
          {[
            { l: "Open chats", v: stats.chats, c: "#E63946", testid: "stat-chats" },
            { l: "Saved builds", v: stats.builds, c: "#FFBA08", testid: "stat-builds" },
            { l: "Active tasks", v: stats.tasks, c: "#10B981", testid: "stat-tasks" },
          ].map(s => (
            <div key={s.l} className="surface p-5 rounded-md" data-testid={s.testid}>
              <div className="tactical-label mb-2" style={{ color: s.c }}>{s.l}</div>
              <div className="font-display text-4xl font-black">{s.v}</div>
            </div>
          ))}
        </div>

        <TutorialPanel />

        <div>
          <div className="tactical-label text-zinc-500 mb-3">// 03 — CHOOSE YOUR PATH</div>
          <h2 className="font-display text-2xl font-bold tracking-tight mb-5 flex items-center gap-2">
            <Compass size={22} weight="duotone" className="text-[#FFBA08]" /> What's the play?
          </h2>
          <PathCards navigate={nav} />
        </div>

        <div>
          <div className="tactical-label text-zinc-500 mb-3">// 04 — SUPPORTED ARSENAL</div>
          <h2 className="font-display text-2xl font-bold tracking-tight mb-5">Pick your title</h2>
          <GameGrid games={games} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
