import { useEffect, useState } from "react";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { CalendarBlank, Plus, Trash, Trophy, Brain, FlagBanner, Target, ListChecks, Star } from "@phosphor-icons/react";

const KIND_ICON = {
  deep_dive_created: { icon: Brain, color: "#E63946", label: "Deep Dive" },
  building_block_added: { icon: Brain, color: "#FFBA08", label: "Building Block" },
  battle_report_posted: { icon: FlagBanner, color: "#FFBA08", label: "Battle Report" },
  alliance_joined: { icon: Star, color: "#10B981", label: "Alliance" },
  optimizer_run: { icon: Target, color: "#10B981", label: "Optimizer" },
  build_saved: { icon: Target, color: "#FFBA08", label: "Build" },
  task_completed: { icon: ListChecks, color: "#10B981", label: "Task" },
  event_created: { icon: CalendarBlank, color: "#FFBA08", label: "Event" },
};

const Calendar = () => {
  const { user } = useAuth();
  const [games, setGames] = useState([]);
  const [events, setEvents] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [game, setGame] = useState("");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [desc, setDesc] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const [g, e, m] = await Promise.all([
      api.get("/games").then(r => r.data),
      api.get("/events").then(r => r.data),
      api.get("/milestones?limit=100").then(r => r.data),
    ]);
    setGames(g); setEvents(e); setMilestones(m);
  };
  useEffect(() => { refresh(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!title || !game || !startAt) return toast.error("Title, game, and start time required");
    setBusy(true);
    try {
      await api.post("/events", {
        game_slug: game, title, description: desc,
        start_at: new Date(startAt).toISOString(),
        end_at: endAt ? new Date(endAt).toISOString() : null,
        category: "general",
      });
      toast.success("Event scheduled");
      setTitle(""); setGame(""); setStartAt(""); setEndAt(""); setDesc("");
      setCreating(false);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not save");
    } finally { setBusy(false); }
  };

  const del = async (id) => {
    await api.delete(`/events/${id}`);
    refresh();
  };

  const upcoming = events.filter(e => new Date(e.start_at) >= new Date());
  const past = events.filter(e => new Date(e.start_at) < new Date());

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="tactical-label text-[#FFBA08] mb-2">// MISSION TIMELINE</div>
            <h1 className="font-display text-3xl font-black tracking-tighter flex items-center gap-3">
              <CalendarBlank size={32} weight="duotone" className="text-[#FFBA08]" /> {user?.username}'s Calendar
            </h1>
            <p className="text-sm text-zinc-400 mt-1 max-w-xl">Schedule events. Track milestones automatically. CyphrAI learns your rhythm to give better strategic advice.</p>
          </div>
          <button onClick={() => setCreating(c => !c)} className="btn-primary flex items-center gap-1.5" data-testid="cal-new-btn">
            <Plus size={14} weight="bold" /> {creating ? "Cancel" : "New event"}
          </button>
        </div>

        {creating && (
          <form onSubmit={submit} className="surface rounded-md p-5 grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="cal-form">
            <input value={title} onChange={e => setTitle(e.target.value)} required placeholder="Event title — KvK starts" className="md:col-span-2 bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="cal-title" />
            <select value={game} onChange={e => setGame(e.target.value)} required className="bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="cal-game">
              <option value="">— Game —</option>
              {games.map(g => <option key={g.slug} value={g.slug}>{g.name}</option>)}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <input type="datetime-local" value={startAt} onChange={e => setStartAt(e.target.value)} required className="bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="cal-start" />
              <input type="datetime-local" value={endAt} onChange={e => setEndAt(e.target.value)} className="bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="cal-end" />
            </div>
            <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={2} placeholder="Notes / strategy reminders" className="md:col-span-2 bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="cal-desc" />
            <button type="submit" disabled={busy} className="md:col-span-2 btn-primary" data-testid="cal-submit">{busy ? "Saving…" : "Schedule"}</button>
          </form>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5">
          {/* Events list */}
          <div className="space-y-2">
            <div className="tactical-label text-zinc-500 mb-1">// UPCOMING · {upcoming.length}</div>
            {upcoming.length === 0 ? (
              <div className="surface p-6 rounded text-center text-sm text-zinc-500">No upcoming events. Schedule your next mission.</div>
            ) : upcoming.map(ev => {
              const g = games.find(x => x.slug === ev.game_slug);
              return (
                <div key={ev.id} className="surface rounded p-4 flex items-start gap-3" data-testid={`cal-event-${ev.id}`}>
                  <div className="w-12 text-center">
                    <div className="font-display text-2xl font-black text-[#FFBA08]">{new Date(ev.start_at).getDate()}</div>
                    <div className="tactical-label text-zinc-500">{new Date(ev.start_at).toLocaleString("default", { month: "short" })}</div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-display font-bold">{ev.title}</div>
                    <div className="text-xs text-zinc-500 mt-0.5">{new Date(ev.start_at).toLocaleString()} · {g?.name || ev.game_slug}</div>
                    {ev.description && <p className="text-xs text-zinc-400 mt-1.5">{ev.description}</p>}
                  </div>
                  <button onClick={() => del(ev.id)} className="text-zinc-500 hover:text-[#E63946]" data-testid={`cal-delete-${ev.id}`}><Trash size={14} /></button>
                </div>
              );
            })}

            {past.length > 0 && (
              <>
                <div className="tactical-label text-zinc-500 mt-6 mb-1">// PAST · {past.length}</div>
                {past.slice(0, 10).map(ev => (
                  <div key={ev.id} className="surface rounded p-3 flex items-center gap-2 opacity-60">
                    <CalendarBlank size={14} className="text-zinc-500" />
                    <span className="text-sm">{ev.title}</span>
                    <span className="text-xs text-zinc-500 ml-auto">{new Date(ev.start_at).toLocaleDateString()}</span>
                  </div>
                ))}
              </>
            )}
          </div>

          {/* Milestone feed */}
          <aside className="surface rounded p-4" data-testid="milestone-feed">
            <div className="tactical-label text-[#10B981] mb-2 flex items-center gap-1"><Trophy size={12} /> // MILESTONES</div>
            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
              {milestones.length === 0 ? (
                <p className="text-xs text-zinc-500">CyphrAI is watching — your milestones will appear as you use the app.</p>
              ) : milestones.map(m => {
                const meta = KIND_ICON[m.kind] || { icon: Trophy, color: "#A1A1AA", label: m.kind };
                const Icon = meta.icon;
                return (
                  <div key={m.id} className="text-xs surface-elev p-2.5 rounded flex items-start gap-2">
                    <Icon size={12} weight="duotone" style={{ color: meta.color }} className="mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-zinc-300">{meta.label}</div>
                      <div className="text-[10px] text-zinc-500 font-mono-tactical">{new Date(m.created_at).toLocaleString()}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Calendar;
