import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import { api, streamChat } from "../lib/api";
import {
  ChatCircleText, Target, BookOpen, ListChecks, ArrowLeft, PaperPlaneTilt, Plus,
  Trash, Check, Lightning, Sparkle,
} from "@phosphor-icons/react";

const TABS = [
  { key: "chat", label: "AI Chat", icon: ChatCircleText },
  { key: "optimizer", label: "Optimizer", icon: Target },
  { key: "guides", label: "Guides", icon: BookOpen },
  { key: "tasks", label: "Planner", icon: ListChecks },
];

/* ========================= CHAT MODULE ========================= */
const ChatModule = ({ slug, gameName }) => {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const endRef = useRef(null);

  const refreshSessions = async () => {
    const r = await api.get(`/chat/sessions?game_slug=${slug}`);
    setSessions(r.data);
    if (!activeId && r.data.length) setActiveId(r.data[0].id);
  };

  useEffect(() => { refreshSessions(); /* eslint-disable-next-line */ }, [slug]);

  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    api.get(`/chat/sessions/${activeId}/messages`).then(r => setMessages(r.data));
  }, [activeId]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const newSession = async () => {
    const r = await api.post("/chat/sessions", { game_slug: slug });
    setSessions(s => [r.data, ...s]);
    setActiveId(r.data.id);
    setMessages([]);
  };

  const deleteSession = async (id) => {
    await api.delete(`/chat/sessions/${id}`);
    setSessions(s => s.filter(x => x.id !== id));
    if (activeId === id) { setActiveId(null); setMessages([]); }
  };

  const send = async (e) => {
    e?.preventDefault();
    if (!input.trim() || streaming) return;
    let sid = activeId;
    if (!sid) {
      const r = await api.post("/chat/sessions", { game_slug: slug });
      setSessions(s => [r.data, ...s]);
      sid = r.data.id;
      setActiveId(sid);
    }
    const userText = input.trim();
    setInput("");
    const userMsg = { id: "u" + Date.now(), role: "user", content: userText };
    const aiMsg = { id: "a" + Date.now(), role: "assistant", content: "" };
    setMessages(m => [...m, userMsg, aiMsg]);
    setStreaming(true);
    await streamChat(
      sid, userText,
      (chunk) => setMessages(m => m.map(x => x.id === aiMsg.id ? { ...x, content: x.content + chunk } : x)),
      (err) => {
        setStreaming(false);
        if (err) toast.error("Stream error: " + err.message);
        refreshSessions();
      }
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-5">
      {/* Sessions sidebar */}
      <aside className="surface rounded-md p-4 h-fit lg:sticky lg:top-24">
        <button onClick={newSession} className="btn-primary w-full flex items-center justify-center gap-2 !py-2 mb-3" data-testid="chat-new-session">
          <Plus size={16} weight="bold" /> New chat
        </button>
        <div className="tactical-label text-zinc-500 mb-2">// History</div>
        <div className="space-y-1 max-h-[60vh] overflow-y-auto">
          {sessions.length === 0 && <p className="text-xs text-zinc-500 px-2 py-3">No sessions yet</p>}
          {sessions.map(s => (
            <div key={s.id} className={`flex items-center gap-1 group rounded ${activeId === s.id ? "bg-white/5" : "hover:bg-white/[0.03]"}`}>
              <button onClick={() => setActiveId(s.id)} className="flex-1 text-left px-3 py-2 text-sm truncate" data-testid={`chat-session-${s.id}`}>
                {s.title}
              </button>
              <button onClick={() => deleteSession(s.id)} className="px-2 opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-[#E63946]" data-testid={`chat-delete-${s.id}`}>
                <Trash size={14} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Chat panel */}
      <div className="surface rounded-md flex flex-col min-h-[60vh]">
        <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
          <div className="tactical-label">// {gameName} TACTICIAN</div>
          <Sparkle size={14} className="text-[#10B981]" />
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4 max-h-[60vh]" data-testid="chat-messages">
          {messages.length === 0 && (
            <div className="text-center text-zinc-500 mt-12">
              <ChatCircleText size={42} weight="duotone" className="text-[#E63946] mx-auto mb-3" />
              <p className="text-sm">Ask anything about {gameName}.</p>
              <p className="text-xs mt-2 opacity-70">Try: "Best F2P team for arena" or "How to prep for KvK"</p>
            </div>
          )}
          {messages.map(m => (
            <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-md px-4 py-3 ${m.role === "user" ? "bg-[#E63946] text-white" : "surface-elev"}`}>
                <div className="tactical-label mb-1 opacity-60" style={{ color: m.role === "user" ? "white" : "#FFBA08" }}>
                  {m.role === "user" ? "// YOU" : "// TACTICIAN"}
                </div>
                <div className={`text-sm whitespace-pre-wrap leading-relaxed ${m.role === "assistant" ? "markdown-output" : ""}`}>
                  {m.content || (streaming && m.role === "assistant" ? "thinking…" : "")}
                </div>
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
        <form onSubmit={send} className="border-t border-white/5 p-4 flex gap-2">
          <input
            value={input} onChange={e => setInput(e.target.value)}
            placeholder="Ask your tactician…"
            className="flex-1 bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
            disabled={streaming} data-testid="chat-input"
          />
          <button type="submit" disabled={streaming || !input.trim()} className="btn-primary !py-2 !px-4 flex items-center gap-1.5" data-testid="chat-send-btn">
            <PaperPlaneTilt size={16} weight="bold" /> Send
          </button>
        </form>
      </div>
    </div>
  );
};

/* ========================= OPTIMIZER MODULE ========================= */
const OptimizerModule = ({ slug }) => {
  const [objective, setObjective] = useState("");
  const [roster, setRoster] = useState("");
  const [resources, setResources] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");

  const run = async (e) => {
    e.preventDefault();
    if (!objective.trim()) return toast.error("Set an objective first");
    setLoading(true); setResult("");
    try {
      const r = await api.post("/optimizer", { game_slug: slug, objective, roster, resources });
      setResult(r.data.result);
    } catch (err) {
      toast.error("Optimizer failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <form onSubmit={run} className="surface rounded-md p-6 space-y-4" data-testid="optimizer-form">
        <div className="tactical-label text-zinc-500">// INPUT PARAMETERS</div>
        <div>
          <label className="tactical-label block mb-2">Objective</label>
          <input
            value={objective} onChange={e => setObjective(e.target.value)}
            placeholder="e.g. Win Kingdom War this weekend"
            className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
            data-testid="optimizer-objective"
          />
        </div>
        <div>
          <label className="tactical-label block mb-2">Current Roster</label>
          <textarea
            value={roster} onChange={e => setRoster(e.target.value)}
            placeholder="e.g. Athena lv60, Merlin lv55, Hua Mulan lv40"
            rows={3}
            className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm font-mono-tactical"
            data-testid="optimizer-roster"
          />
        </div>
        <div>
          <label className="tactical-label block mb-2">Resources Available</label>
          <textarea
            value={resources} onChange={e => setResources(e.target.value)}
            placeholder="e.g. 5k gems, 200 hero shards, 12h speedups"
            rows={2}
            className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm font-mono-tactical"
            data-testid="optimizer-resources"
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="optimizer-run">
          <Lightning size={16} weight="bold" /> {loading ? "Computing…" : "Run optimizer"}
        </button>
      </form>

      <div className="surface rounded-md p-6">
        <div className="tactical-label text-zinc-500 mb-3">// OPTIMIZER OUTPUT</div>
        {loading ? (
          <div className="space-y-3" data-testid="optimizer-loading">
            <div className="h-3 shimmer rounded" />
            <div className="h-3 shimmer rounded w-5/6" />
            <div className="h-3 shimmer rounded w-4/6" />
            <div className="h-3 shimmer rounded w-3/4" />
          </div>
        ) : result ? (
          <div className="terminal-block markdown-output" data-testid="optimizer-result"
               dangerouslySetInnerHTML={{ __html: renderMd(result) }} />
        ) : (
          <p className="text-sm text-zinc-500">Submit your parameters to receive a tactical plan.</p>
        )}
      </div>
    </div>
  );
};

// extremely tiny markdown renderer (bold + headings + newlines)
const renderMd = (s) => s
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/^### (.+)$/gm, "<h3>$1</h3>")
  .replace(/^## (.+)$/gm, "<h2>$1</h2>")
  .replace(/^# (.+)$/gm, "<h1>$1</h1>")
  .replace(/^- (.+)$/gm, "<li>$1</li>")
  .replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>")
  .replace(/\n/g, "<br />");

/* ========================= GUIDES MODULE ========================= */
const GuidesModule = ({ slug }) => {
  const [guides, setGuides] = useState([]);
  const [active, setActive] = useState(null);
  useEffect(() => {
    api.get(`/guides?game_slug=${slug}`).then(r => setGuides(r.data));
    setActive(null);
  }, [slug]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div className="space-y-3" data-testid="guides-list">
        {guides.length === 0 && <p className="text-sm text-zinc-500">No guides for this title yet.</p>}
        {guides.map(g => (
          <button
            key={g.id} onClick={() => setActive(g)}
            className={`surface w-full text-left p-5 rounded-md ${active?.id === g.id ? "border-[#E63946]/50" : ""}`}
            data-testid={`guide-${g.id}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="tag-chip" style={{ color: "#FFBA08", borderColor: "#FFBA0840" }}>{g.category}</span>
              <BookOpen size={14} className="text-zinc-500" />
            </div>
            <h3 className="font-display text-lg font-bold tracking-tight">{g.title}</h3>
            <p className="text-xs text-zinc-400 mt-1">{g.summary}</p>
          </button>
        ))}
      </div>
      <div className="surface rounded-md p-6 lg:sticky lg:top-24 h-fit">
        {active ? (
          <>
            <div className="tactical-label text-[#E63946] mb-2">// {active.category}</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">{active.title}</h2>
            <p className="text-sm text-zinc-400 mt-2 mb-5">{active.summary}</p>
            <div className="terminal-block">{active.content}</div>
          </>
        ) : (
          <p className="text-sm text-zinc-500">Select a guide to view its content.</p>
        )}
      </div>
    </div>
  );
};

/* ========================= TASKS MODULE ========================= */
const TasksModule = ({ slug }) => {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("med");

  const refresh = () => api.get(`/tasks?game_slug=${slug}`).then(r => setTasks(r.data));
  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, [slug]);

  const add = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    await api.post("/tasks", { game_slug: slug, title: title.trim(), priority });
    setTitle("");
    refresh();
  };

  const toggle = async (t) => {
    await api.patch(`/tasks/${t.id}`, { completed: !t.completed });
    refresh();
  };

  const remove = async (id) => {
    await api.delete(`/tasks/${id}`);
    refresh();
  };

  const colors = { high: "#E63946", med: "#FFBA08", low: "#10B981" };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-5">
      <div>
        <div className="tactical-label text-zinc-500 mb-3">// DAILY OBJECTIVES</div>
        <div className="space-y-2" data-testid="tasks-list">
          {tasks.length === 0 && <p className="text-sm text-zinc-500 surface p-5 rounded-md">No tasks yet. Add one to start tracking.</p>}
          {tasks.map(t => (
            <div key={t.id} className="surface rounded-md p-4 flex items-center gap-3 group" data-testid={`task-${t.id}`}>
              <button onClick={() => toggle(t)}
                className={`w-5 h-5 rounded border flex items-center justify-center transition ${t.completed ? "bg-[#10B981] border-[#10B981]" : "border-white/20 hover:border-white/60"}`}
                data-testid={`task-toggle-${t.id}`}>
                {t.completed && <Check size={12} weight="bold" />}
              </button>
              <div className="flex-1">
                <p className={`text-sm ${t.completed ? "line-through text-zinc-500" : ""}`}>{t.title}</p>
              </div>
              <span className="tag-chip" style={{ color: colors[t.priority], borderColor: colors[t.priority] + "40" }}>{t.priority.toUpperCase()}</span>
              <button onClick={() => remove(t.id)} className="text-zinc-500 hover:text-[#E63946] opacity-0 group-hover:opacity-100" data-testid={`task-delete-${t.id}`}>
                <Trash size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <form onSubmit={add} className="surface rounded-md p-6 h-fit space-y-4" data-testid="task-form">
        <div className="tactical-label text-zinc-500">// ADD TASK</div>
        <input
          value={title} onChange={e => setTitle(e.target.value)}
          placeholder="e.g. Donate to alliance"
          className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
          data-testid="task-input-title"
        />
        <div>
          <label className="tactical-label block mb-2">Priority</label>
          <div className="grid grid-cols-3 gap-2">
            {["low", "med", "high"].map(p => (
              <button key={p} type="button" onClick={() => setPriority(p)}
                className={`py-2 rounded text-xs font-mono-tactical uppercase tracking-wider border transition ${priority === p ? "border-white text-white" : "border-white/10 text-zinc-500 hover:border-white/30"}`}
                data-testid={`task-priority-${p}`}>{p}</button>
            ))}
          </div>
        </div>
        <button type="submit" className="btn-primary w-full" data-testid="task-add-btn">
          <Plus size={16} weight="bold" className="inline mr-1" /> Add objective
        </button>
      </form>
    </div>
  );
};

/* ========================= MAIN PAGE ========================= */
const GamePage = () => {
  const { slug } = useParams();
  const [game, setGame] = useState(null);
  const [tab, setTab] = useState("chat");

  useEffect(() => {
    api.get(`/games/${slug}`).then(r => setGame(r.data));
  }, [slug]);

  if (!game) return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="h-12 w-64 shimmer rounded mb-6" />
        <div className="h-48 shimmer rounded" />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Game header */}
      <section className="relative overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 -z-10">
          <img src={game.image} alt="" className="w-full h-full object-cover opacity-25" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#0A0A0A]/60 via-[#0A0A0A]/85 to-[#0A0A0A]" />
        </div>
        <div className="max-w-7xl mx-auto px-6 py-10">
          <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white mb-5" data-testid="back-to-dashboard">
            <ArrowLeft size={16} /> Dashboard
          </Link>
          <div className="flex items-start justify-between flex-wrap gap-4">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <div className="tactical-label mb-2" style={{ color: game.color }}>// {game.genre}</div>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">{game.name}</h1>
              <p className="text-zinc-400 mt-2 max-w-xl">{game.tagline}</p>
              <div className="flex flex-wrap gap-2 mt-4">
                {game.tags.map(t => <span key={t} className="tag-chip">{t}</span>)}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tabs */}
      <div className="border-b border-white/5 sticky top-[64px] glass-nav z-30">
        <div className="max-w-7xl mx-auto px-6 flex gap-1 overflow-x-auto">
          {TABS.map(t => {
            const Icon = t.icon;
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex items-center gap-2 px-4 py-3 text-sm border-b-2 transition whitespace-nowrap ${active ? "border-[#E63946] text-white" : "border-transparent text-zinc-500 hover:text-white"}`}
                data-testid={`tab-${t.key}`}
              >
                <Icon size={16} weight={active ? "duotone" : "regular"} /> {t.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {tab === "chat" && <ChatModule slug={slug} gameName={game.name} />}
        {tab === "optimizer" && <OptimizerModule slug={slug} />}
        {tab === "guides" && <GuidesModule slug={slug} />}
        {tab === "tasks" && <TasksModule slug={slug} />}
      </div>
    </div>
  );
};

export default GamePage;
