import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api, API } from "../lib/api";
import {
  FlagBanner, Plus, UploadSimple, X, Brain, Sparkle, Trash, Share, ArrowLeft, Image as ImageIcon,
} from "@phosphor-icons/react";

const renderMd = (s) => (s || "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/^### (.+)$/gm, "<h3>$1</h3>")
  .replace(/^## (.+)$/gm, "<h2>$1</h2>")
  .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
  .replace(/^- (.+)$/gm, "<li>$1</li>")
  .replace(/(<li>.*?<\/li>(?:\n|$))+/gs, m => `<ul>${m}</ul>`)
  .replace(/\n/g, "<br />");

const UploadZone = ({ files, setFiles, max = 6 }) => {
  const inputRef = useRef(null);
  const onPick = (e) => {
    const arr = Array.from(e.target.files || []).filter(f => f.type.startsWith("image/"));
    if (files.length + arr.length > max) return toast.error(`Max ${max} screenshots`);
    setFiles([...files, ...arr]);
    e.target.value = "";
  };
  return (
    <>
      <button type="button" onClick={() => inputRef.current?.click()} className="w-full border-2 border-dashed border-white/15 hover:border-[#FFBA08]/60 rounded p-6 text-center transition" data-testid="br-upload-zone">
        <UploadSimple size={24} className="mx-auto text-zinc-500 mb-1.5" />
        <div className="text-sm font-semibold">Add battle screenshots</div>
        <div className="text-xs text-zinc-500">PNG / JPG · up to {max} · 6MB each</div>
      </button>
      <input ref={inputRef} type="file" multiple accept="image/*" onChange={onPick} className="hidden" />
      {files.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-2">
          {files.map((f, i) => (
            <div key={i} className="relative aspect-square surface-elev rounded overflow-hidden group">
              <img src={URL.createObjectURL(f)} alt="" className="w-full h-full object-cover" />
              <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="absolute top-1 right-1 bg-black/70 rounded-full p-1 opacity-0 group-hover:opacity-100">
                <X size={10} />
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export const BattleReportsList = () => {
  const [reports, setReports] = useState([]);
  const [games, setGames] = useState([]);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [gameSlug, setGameSlug] = useState("");
  const [files, setFiles] = useState([]);
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const refresh = () => api.get("/battle-reports").then(r => setReports(r.data));
  useEffect(() => {
    refresh();
    api.get("/games").then(r => setGames(r.data));
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !gameSlug || files.length === 0) return toast.error("Title, game, and at least 1 screenshot required");
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("title", title); fd.append("notes", notes); fd.append("game_slug", gameSlug);
      fd.append("auto_analyze", autoAnalyze ? "true" : "false");
      files.forEach(f => fd.append("files", f));
      const r = await fetch(`${API}/battle-reports`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      });
      if (!r.ok) throw new Error((await r.json())?.detail || "Failed");
      const data = await r.json();
      toast.success("Battle report saved");
      setTitle(""); setNotes(""); setFiles([]); setCreating(false);
      nav(`/battle-reports/${data.id}`);
    } catch (err) {
      toast.error(err.message);
    } finally { setBusy(false); }
  };

  return (
    <div className="command-center min-h-screen">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="tactical-label text-[#FFBA08] mb-2">// FIELD INTEL</div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tighter flex items-center gap-3">
              <FlagBanner size={32} weight="duotone" className="text-[#FFBA08]" /> Battle Reports
            </h1>
            <p className="text-sm text-zinc-400 mt-2 max-w-xl">Log engagements with screenshots & notes. Get an optional CypherAI quick-take. Share to your alliance with one click.</p>
          </div>
          <button onClick={() => setCreating(c => !c)} className="btn-primary flex items-center gap-1.5" data-testid="br-new-btn">
            <Plus size={14} weight="bold" /> {creating ? "Cancel" : "New report"}
          </button>
        </div>

        <AnimatePresence>
          {creating && (
            <motion.form initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
              onSubmit={submit} className="surface rounded-md p-5 space-y-3" data-testid="br-create-form">
              <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title — e.g. R5 vs Iron Crown rally win" className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="br-title" required />
              <select value={gameSlug} onChange={e => setGameSlug(e.target.value)} className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" required data-testid="br-game">
                <option value="">— Game —</option>
                {games.map(g => <option key={g.slug} value={g.slug}>{g.name}</option>)}
              </select>
              <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} placeholder="Notes — what happened, lessons learned" className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="br-notes" />
              <UploadZone files={files} setFiles={setFiles} />
              <label className="flex items-center gap-2 cursor-pointer p-2 surface-elev rounded hover:border-white/30" data-testid="br-auto-label">
                <input
                  type="checkbox"
                  checked={autoAnalyze}
                  onChange={(e) => setAutoAnalyze(e.target.checked)}
                  className="w-4 h-4 accent-[#FFAA33]"
                  data-testid="br-auto-checkbox"
                />
                <Brain size={14} weight="duotone" className="text-[#FFAA33]" />
                <span className="text-sm">Auto-run CypherAI Take after saving</span>
                <span className="tactical-label text-zinc-500 ml-auto">// COSTS 1 AI CALL</span>
              </label>
              <button type="submit" disabled={busy} className="btn-primary w-full" data-testid="br-submit">
                {busy ? (autoAnalyze ? "Saving + analyzing…" : "Saving…") : "Save battle report"}
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        {reports.length === 0 ? (
          <div className="surface rounded p-10 text-center">
            <ImageIcon size={32} className="mx-auto text-zinc-600 mb-2" />
            <p className="text-sm text-zinc-500">No battle reports yet. Log your first engagement above.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="br-list">
            {reports.map(r => {
              const g = games.find(x => x.slug === r.game_slug);
              return (
                <Link key={r.id} to={`/battle-reports/${r.id}`} className="surface rounded-md p-5 block hover:-translate-y-1 transition" data-testid={`br-card-${r.id}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="tag-chip" style={{ color: g?.color, borderColor: (g?.color || "#888") + "40" }}>{g?.name || r.game_slug}</span>
                    <span className="text-[10px] font-mono-tactical text-zinc-500">{new Date(r.created_at).toLocaleDateString()}</span>
                  </div>
                  <h3 className="font-display font-bold tracking-tight">{r.title}</h3>
                  {r.notes && <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{r.notes}</p>}
                  <div className="flex items-center justify-between mt-3 text-xs text-zinc-500">
                    <span>{(r.shots || []).length} shot{(r.shots || []).length !== 1 ? "s" : ""}</span>
                    {r.cyphr_take && <span className="flex items-center gap-1 text-[#FFAA33]"><Brain size={12} /> CypherAI take</span>}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export const BattleReportDetail = () => {
  const { id } = useParams();
  const nav = useNavigate();
  const [br, setBr] = useState(null);
  const [busy, setBusy] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [alliances, setAlliances] = useState([]);

  const refresh = () => api.get(`/battle-reports/${id}`).then(r => setBr(r.data)).catch(() => toast.error("Not found"));
  useEffect(() => { refresh(); }, [id]);

  const runAnalyze = async () => {
    setBusy(true);
    try {
      const r = await api.post(`/battle-reports/${id}/analyze`);
      setBr(b => ({ ...b, cyphr_take: r.data.cyphr_take }));
      toast.success(r.data.cached ? "Loaded cached take" : "CypherAI take generated");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Analyze failed");
    } finally { setBusy(false); }
  };

  const del = async () => {
    if (!window.confirm("Delete this battle report?")) return;
    await api.delete(`/battle-reports/${id}`);
    toast.success("Removed");
    nav("/battle-reports");
  };

  const openShare = async () => {
    try {
      const r = await api.get("/alliances/mine");
      const matching = r.data.filter(a => a.game_slug === br.game_slug);
      if (matching.length === 0) return toast.error("No alliance for this game. Create or join one in Operations Center.");
      setAlliances(matching);
      setShareOpen(true);
    } catch { toast.error("Could not load alliances"); }
  };

  const shareTo = async (aid) => {
    try {
      await api.post(`/alliances/${aid}/share-battle-report`, { ref_id: id });
      toast.success("Shared to alliance");
      setShareOpen(false);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not share");
    }
  };

  if (!br) return (
    <div className="command-center min-h-screen"><Navbar />
      <div className="max-w-4xl mx-auto px-6 py-10"><div className="h-12 w-64 shimmer rounded mb-6" /><div className="h-64 shimmer rounded" /></div>
    </div>
  );

  return (
    <div className="command-center min-h-screen">
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-5">
        <Link to="/battle-reports" className="text-sm text-zinc-400 hover:text-white inline-flex items-center gap-1.5" data-testid="back-to-reports"><ArrowLeft size={14} /> Battle Reports</Link>

        <div className="surface rounded-md p-6" data-testid="br-detail">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div className="tactical-label text-[#FFBA08] mb-2">// BATTLE REPORT · {new Date(br.created_at).toLocaleDateString()}</div>
              <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tighter">{br.title}</h1>
              {br.notes && <p className="text-sm text-zinc-400 mt-2 max-w-xl">{br.notes}</p>}
            </div>
            <div className="flex items-center gap-2">
              <button onClick={openShare} className="btn-outline !py-2 !px-3 text-xs flex items-center gap-1.5" data-testid="br-share">
                <Share size={12} /> Share to alliance
              </button>
              <button onClick={del} className="text-xs text-zinc-500 hover:text-[#FF6B00] flex items-center gap-1" data-testid="br-delete">
                <Trash size={12} /> Delete
              </button>
            </div>
          </div>

          {/* Screenshots */}
          {br.shots?.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-5">
              {br.shots.map((s, i) => (
                <div key={i} className="aspect-video surface-elev rounded overflow-hidden">
                  <img src={`${API}/deep-dive/shot/${s.file_id}`} alt="" className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* CypherAI take */}
        <div className="surface rounded-md p-6">
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <h2 className="font-display font-bold flex items-center gap-2">
              <Brain size={18} weight="duotone" className="text-[#FFAA33]" /> CypherAI Take
              <span className="tactical-label text-zinc-500 ml-2">// OPTIONAL</span>
            </h2>
            {!br.cyphr_take && (
              <button onClick={runAnalyze} disabled={busy} className="btn-primary !py-2 !px-4 text-xs flex items-center gap-1.5" data-testid="br-analyze">
                <Sparkle size={12} weight="fill" /> {busy ? "Analyzing…" : "Get CypherAI take"}
              </button>
            )}
          </div>
          {!br.cyphr_take ? (
            <p className="text-sm text-zinc-500">No take yet. Click to have CypherAI analyze your engagement — what worked, what didn't, what to do next time.</p>
          ) : (
            <div className="terminal-block markdown-output" data-testid="br-cyphr-take" dangerouslySetInnerHTML={{ __html: renderMd(br.cyphr_take) }} />
          )}
        </div>
      </div>

      {/* Share modal */}
      {shareOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShareOpen(false)}>
          <div className="surface-elev max-w-md w-full rounded-md p-6 space-y-3" onClick={(e) => e.stopPropagation()} data-testid="br-share-modal">
            <h3 className="font-display text-lg font-bold">Share to which alliance?</h3>
            {alliances.map(a => (
              <button key={a.id} onClick={() => shareTo(a.id)} className="w-full surface rounded p-3 text-left hover:border-white/30 flex items-center justify-between" data-testid={`br-share-${a.id}`}>
                <span>{a.name}</span>
                <span className="font-mono-tactical text-xs text-zinc-500">{a.code}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
