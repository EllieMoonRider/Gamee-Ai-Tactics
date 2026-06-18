import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  MapTrifold, ChatCircleText, Target, ListChecks, ArrowLeft, Trash, CalendarBlank,
} from "@phosphor-icons/react";
import { toast } from "sonner";

const GameTag = ({ slug, games }) => {
  const g = games.find(x => x.slug === slug);
  return g ? (
    <Link to={`/game/${slug}`} className="tag-chip hover:border-white/30" style={{ color: g.color, borderColor: g.color + "40" }}>
      {g.name}
    </Link>
  ) : <span className="tag-chip">{slug}</span>;
};

const WarRoom = () => {
  const { user } = useAuth();
  const [games, setGames] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [builds, setBuilds] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    const [gs, ss, bs, ts] = await Promise.all([
      api.get("/games").then(r => r.data),
      api.get("/chat/sessions").then(r => r.data),
      api.get("/builds").then(r => r.data),
      api.get("/tasks").then(r => r.data),
    ]);
    setGames(gs); setSessions(ss); setBuilds(bs); setTasks(ts);
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  const deleteSession = async (id) => {
    await api.delete(`/chat/sessions/${id}`);
    setSessions(s => s.filter(x => x.id !== id));
    toast.success("Chat removed");
  };
  const deleteBuild = async (id) => {
    await api.delete(`/builds/${id}`);
    setBuilds(b => b.filter(x => x.id !== id));
    toast.success("Build removed");
  };
  const toggleTask = async (t) => {
    await api.patch(`/tasks/${t.id}`, { completed: !t.completed });
    refresh();
  };

  const openTasks = tasks.filter(t => !t.completed);
  const doneTasks = tasks.filter(t => t.completed);

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white" data-testid="back-to-command-center">
          <ArrowLeft size={16} /> Command Center
        </Link>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="tactical-label text-[#E63946] mb-3">// PERSONAL WAR ROOM</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter flex items-center gap-3">
            <MapTrifold size={42} weight="duotone" className="text-[#FFBA08]" />
            {user?.username}'s War Room
          </h1>
          <p className="text-zinc-400 mt-3 max-w-2xl">Every campaign, build, and objective you've logged across the 10 supported titles. Tactical archive — at a glance.</p>
        </motion.div>

        {/* Stat strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/5 border border-white/5 rounded">
          {[
            { l: "Chats", v: sessions.length, c: "#E63946" },
            { l: "Builds", v: builds.length, c: "#FFBA08" },
            { l: "Open tasks", v: openTasks.length, c: "#10B981" },
            { l: "Completed", v: doneTasks.length, c: "#A1A1AA" },
          ].map(s => (
            <div key={s.l} className="bg-[#0A0A0A] p-6">
              <div className="tactical-label mb-2" style={{ color: s.c }}>{s.l}</div>
              <div className="font-display text-3xl font-black">{s.v}</div>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="surface p-10 rounded-md text-center text-zinc-500 font-mono-tactical text-sm">LOADING WAR ROOM…</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Chats column */}
            <section className="surface rounded-md p-5" data-testid="war-room-chats">
              <div className="flex items-center gap-2 mb-4">
                <ChatCircleText size={20} weight="duotone" className="text-[#E63946]" />
                <h2 className="font-display font-bold tracking-tight">AI Chat sessions</h2>
                <span className="ml-auto tactical-label">{sessions.length}</span>
              </div>
              {sessions.length === 0 ? (
                <p className="text-sm text-zinc-500">No chats yet. Start one from a game page.</p>
              ) : (
                <ul className="space-y-2 max-h-[55vh] overflow-y-auto">
                  {sessions.map(s => (
                    <li key={s.id} className="surface-elev rounded p-3 flex items-start gap-2 group">
                      <div className="flex-1 min-w-0">
                        <Link to={`/game/${s.game_slug}`} className="text-sm hover:underline truncate block" data-testid={`war-chat-${s.id}`}>{s.title}</Link>
                        <div className="flex items-center gap-2 mt-1.5">
                          <GameTag slug={s.game_slug} games={games} />
                          <span className="text-[10px] font-mono-tactical text-zinc-500 flex items-center gap-1">
                            <CalendarBlank size={10} /> {new Date(s.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <button onClick={() => deleteSession(s.id)} className="text-zinc-500 hover:text-[#E63946] opacity-0 group-hover:opacity-100" data-testid={`war-chat-delete-${s.id}`}>
                        <Trash size={14} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Builds column */}
            <section className="surface rounded-md p-5" data-testid="war-room-builds">
              <div className="flex items-center gap-2 mb-4">
                <Target size={20} weight="duotone" className="text-[#FFBA08]" />
                <h2 className="font-display font-bold tracking-tight">Saved Builds</h2>
                <span className="ml-auto tactical-label">{builds.length}</span>
              </div>
              {builds.length === 0 ? (
                <p className="text-sm text-zinc-500">No builds saved yet. Generate one via the Optimizer.</p>
              ) : (
                <ul className="space-y-2 max-h-[55vh] overflow-y-auto">
                  {builds.map(b => (
                    <li key={b.id} className="surface-elev rounded p-3 group">
                      <div className="flex items-start gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-semibold">{b.title}</div>
                          {b.team?.length > 0 && (
                            <div className="text-xs text-zinc-400 mt-1 font-mono-tactical truncate">{b.team.join(" · ")}</div>
                          )}
                          <div className="mt-1.5"><GameTag slug={b.game_slug} games={games} /></div>
                        </div>
                        <button onClick={() => deleteBuild(b.id)} className="text-zinc-500 hover:text-[#E63946] opacity-0 group-hover:opacity-100" data-testid={`war-build-delete-${b.id}`}>
                          <Trash size={14} />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Tasks column */}
            <section className="surface rounded-md p-5" data-testid="war-room-tasks">
              <div className="flex items-center gap-2 mb-4">
                <ListChecks size={20} weight="duotone" className="text-[#10B981]" />
                <h2 className="font-display font-bold tracking-tight">Mission Tasks</h2>
                <span className="ml-auto tactical-label">{openTasks.length} OPEN</span>
              </div>
              {tasks.length === 0 ? (
                <p className="text-sm text-zinc-500">No tasks logged. Add some from any game's Planner tab.</p>
              ) : (
                <ul className="space-y-2 max-h-[55vh] overflow-y-auto">
                  {tasks.map(t => {
                    const colors = { high: "#E63946", med: "#FFBA08", low: "#10B981" };
                    return (
                      <li key={t.id} className="surface-elev rounded p-3 flex items-center gap-3" data-testid={`war-task-${t.id}`}>
                        <button onClick={() => toggleTask(t)}
                          className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center ${t.completed ? "bg-[#10B981] border-[#10B981]" : "border-white/20"}`}
                          data-testid={`war-task-toggle-${t.id}`}
                        >
                          {t.completed && <span className="text-[10px] font-bold">✓</span>}
                        </button>
                        <div className="flex-1 min-w-0">
                          <div className={`text-sm ${t.completed ? "line-through text-zinc-500" : ""}`}>{t.title}</div>
                          <div className="mt-1"><GameTag slug={t.game_slug} games={games} /></div>
                        </div>
                        <span className="tag-chip" style={{ color: colors[t.priority], borderColor: colors[t.priority] + "40" }}>{t.priority.toUpperCase()}</span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

          </div>
        )}
      </div>
    </div>
  );
};

export default WarRoom;
