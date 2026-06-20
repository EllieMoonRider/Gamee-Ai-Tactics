import { useEffect, useRef, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import Navbar from "../components/Navbar";
import { api, API } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ShieldStar, PaperPlaneTilt, Users, Copy, Brain, Target, Sparkle, ArrowLeft,
  UploadSimple, X, ChatCircleText, CheckCircle, SignOut, FlagBanner,
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

const MessageBubble = ({ m, isMine, currentUser }) => {
  if (m.type === "system") {
    return <div className="text-center text-xs text-zinc-500 italic py-1">{m.content}</div>;
  }
  if (m.type === "cyphr_a") {
    return (
      <div className="flex" data-testid={`msg-cyphr-a-${m.id}`}>
        <div className="max-w-[90%] surface-elev rounded-md p-3 border-l-2 border-[#10B981]">
          <div className="flex items-center gap-1.5 mb-1">
            <Brain size={12} weight="duotone" className="text-[#10B981]" />
            <span className="tactical-label text-[#10B981]">// CYPHRAI · {m.refs?.asked_by || "alliance"}</span>
          </div>
          <div className="text-sm markdown-output" dangerouslySetInnerHTML={{ __html: renderMd(m.content) }} />
        </div>
      </div>
    );
  }
  const bg = isMine ? "bg-[#E63946] text-white" : "surface-elev";
  return (
    <div className={`flex ${isMine ? "justify-end" : "justify-start"}`} data-testid={`msg-${m.type}-${m.id}`}>
      <div className={`max-w-[80%] rounded-md p-3 ${bg}`}>
        <div className={`tactical-label mb-1 opacity-70 ${isMine ? "text-white" : "text-[#FFBA08]"}`}>
          {m.username}{m.type === "cyphr_q" && " · asked CyphrAI"}
        </div>
        {m.type === "share_deepdive" && (
          <Link to={`/share/d/${m.refs?.share_token}`} target="_blank" rel="noreferrer" className={`block surface ${isMine ? "!bg-white/10 !border-white/20" : ""} rounded p-2.5 mb-2`}>
            <div className="flex items-center gap-2 text-xs">
              <Brain size={14} className={isMine ? "text-white" : "text-[#E63946]"} />
              <span className="font-display font-bold">{m.refs?.title || "Deep Dive"}</span>
            </div>
            <div className="text-[11px] opacity-70 mt-1">Deep Dive · {m.refs?.follow_ups || 0} building block{m.refs?.follow_ups === 1 ? "" : "s"} · click to view</div>
          </Link>
        )}
        {m.type === "share_build" && (
          <Link to={`/share/b/${m.refs?.share_token}`} target="_blank" rel="noreferrer" className={`block surface ${isMine ? "!bg-white/10 !border-white/20" : ""} rounded p-2.5 mb-2`}>
            <div className="flex items-center gap-2 text-xs">
              <Target size={14} className={isMine ? "text-white" : "text-[#FFBA08]"} />
              <span className="font-display font-bold">{m.refs?.title || "Build"}</span>
            </div>
            <div className="text-[11px] opacity-70 mt-1">Build · click to view</div>
          </Link>
        )}
        {m.type === "battle_report" && (
          <div className={`surface ${isMine ? "!bg-white/10 !border-white/20" : ""} rounded p-2.5 mb-2`}>
            <div className="flex items-center gap-2 text-xs">
              <FlagBanner size={14} className={isMine ? "text-white" : "text-[#FFBA08]"} />
              <span className="font-display font-bold">{m.refs?.title || "Battle Report"}</span>
              <span className="text-[10px] opacity-70 ml-auto">{m.refs?.shot_count || 0} shot{m.refs?.shot_count === 1 ? "" : "s"}</span>
            </div>
          </div>
        )}
        <div className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</div>
        <div className={`text-[10px] mt-1 opacity-50 ${isMine ? "" : "text-zinc-400"}`}>
          {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
};

const ShareModal = ({ open, onClose, alliance, onShared }) => {
  const [tab, setTab] = useState("deepdive");
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    if (!open) return;
    const url = tab === "deepdive" ? `/deep-dive?game_slug=${alliance.game_slug}` : `/builds?game_slug=${alliance.game_slug}`;
    api.get(url).then(r => setItems(r.data)).catch(() => setItems([]));
  }, [open, tab, alliance.game_slug]);

  const share = async (it) => {
    setBusy(it.id);
    try {
      const ep = tab === "deepdive" ? `/alliances/${alliance.id}/share-deepdive` : `/alliances/${alliance.id}/share-build`;
      await api.post(ep, { ref_id: it.id });
      toast.success(`${tab === "deepdive" ? "Deep Dive" : "Build"} shared`);
      onShared();
      onClose();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not share");
    } finally { setBusy(null); }
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose} data-testid="share-modal">
      <div className="surface-elev max-w-xl w-full rounded-md max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 border-b border-white/5 flex items-center justify-between">
          <div>
            <div className="tactical-label text-[#FFBA08] mb-1">// SHARE TO ALLIANCE</div>
            <h3 className="font-display text-xl font-bold">Pick from your archive</h3>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-white"><X size={18} /></button>
        </div>
        <div className="flex border-b border-white/5">
          {["deepdive", "build"].map(t => (
            <button key={t} onClick={() => setTab(t)} className={`flex-1 py-3 text-sm border-b-2 ${tab === t ? "border-[#E63946] text-white" : "border-transparent text-zinc-500 hover:text-white"}`} data-testid={`share-tab-${t}`}>
              {t === "deepdive" ? "Deep Dives" : "Builds"}
            </button>
          ))}
        </div>
        <div className="p-5 space-y-2">
          {items.length === 0 && <p className="text-sm text-zinc-500">Nothing matching this alliance's game in your archive.</p>}
          {items.map(it => (
            <button key={it.id} onClick={() => share(it)} disabled={busy === it.id} className="w-full surface rounded p-3 text-left hover:border-white/30 disabled:opacity-50" data-testid={`share-item-${it.id}`}>
              <div className="font-display font-bold text-sm">{it.title}</div>
              <div className="text-xs text-zinc-500 mt-1">{new Date(it.created_at).toLocaleDateString()}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

const BattleReportModal = ({ open, onClose, allianceId, onPosted }) => {
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!title.trim() || files.length === 0) return toast.error("Title and at least 1 screenshot required");
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("title", title); fd.append("notes", notes);
      files.forEach(f => fd.append("files", f));
      const r = await fetch(`${API}/alliances/${allianceId}/battle-reports`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      });
      if (!r.ok) throw new Error((await r.json())?.detail || "Failed");
      toast.success("Battle report posted");
      setTitle(""); setNotes(""); setFiles([]);
      onPosted();
      onClose();
    } catch (err) {
      toast.error(err.message);
    } finally { setBusy(false); }
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <form onSubmit={submit} className="surface-elev max-w-lg w-full rounded-md p-6 space-y-4" onClick={(e) => e.stopPropagation()} data-testid="battle-report-form">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-xl font-bold flex items-center gap-2"><FlagBanner size={20} className="text-[#FFBA08]" /> Battle Report</h3>
          <button type="button" onClick={onClose} className="text-zinc-500 hover:text-white"><X size={18} /></button>
        </div>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title — e.g. R5 vs Iron Crown rally" className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="br-title" required />
        <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Notes — what happened, lessons learned" rows={3} className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="br-notes" />
        <input ref={inputRef} type="file" multiple accept="image/*" onChange={(e) => setFiles(Array.from(e.target.files || []))} className="hidden" />
        <button type="button" onClick={() => inputRef.current?.click()} className="w-full border-2 border-dashed border-white/15 rounded p-5 text-sm text-zinc-400 hover:border-[#FFBA08]/40" data-testid="br-pick-files">
          <UploadSimple size={20} className="mx-auto mb-1.5 text-zinc-500" />
          {files.length === 0 ? "Add up to 6 screenshots" : `${files.length} file${files.length === 1 ? "" : "s"} ready`}
        </button>
        <button type="submit" disabled={busy} className="btn-primary w-full" data-testid="br-submit">
          {busy ? "Posting…" : "Post battle report"}
        </button>
      </form>
    </div>
  );
};

const OperationsRoom = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const [a, setA] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("text"); // "text" or "cyphr"
  const [busy, setBusy] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [brOpen, setBrOpen] = useState(false);
  const [showMembers, setShowMembers] = useState(false);
  const endRef = useRef(null);
  const pollRef = useRef(null);

  const refresh = async () => {
    try {
      const r = await api.get(`/alliances/${id}`);
      setA(r.data);
      const mr = await api.get(`/alliances/${id}/messages?limit=300`);
      setMessages(mr.data);
    } catch (err) {
      if (err?.response?.status === 403 || err?.response?.status === 404) {
        toast.error("You don't have access to this alliance.");
        nav("/operations");
      }
    }
  };

  useEffect(() => {
    refresh();
    pollRef.current = setInterval(async () => {
      if (!messages.length) return;
      const last = messages[messages.length - 1]?.created_at;
      try {
        const r = await api.get(`/alliances/${id}/messages?since=${encodeURIComponent(last)}`);
        if (r.data.length) {
          setMessages(prev => {
            const ids = new Set(prev.map(m => m.id));
            const fresh = r.data.filter(m => !ids.has(m.id));
            return fresh.length ? [...prev, ...fresh] : prev;
          });
        }
      } catch { /* ignore poll error */ }
    }, 3500);
    return () => clearInterval(pollRef.current);
    // eslint-disable-next-line
  }, [id, messages.length]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (e) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true); setInput("");
    try {
      if (mode === "cyphr") {
        const r = await api.post(`/alliances/${id}/ask-cyphr`, { question: text });
        setMessages(prev => [...prev, r.data.question, r.data.answer]);
      } else {
        const r = await api.post(`/alliances/${id}/messages`, { content: text });
        setMessages(prev => [...prev, r.data]);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Send failed");
      setInput(text);
    } finally { setBusy(false); }
  };

  const leave = async () => {
    if (!window.confirm("Leave this alliance?")) return;
    try {
      await api.post(`/alliances/${id}/leave`);
      toast.success("You left the alliance");
      nav("/operations");
    } catch { toast.error("Could not leave"); }
  };

  if (!a) return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="h-12 w-64 shimmer rounded mb-6" />
        <div className="h-96 shimmer rounded" />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-5">
        <Link to="/operations" className="text-sm text-zinc-400 hover:text-white inline-flex items-center gap-1.5" data-testid="back-to-operations"><ArrowLeft size={14} /> Operations Center</Link>

        {/* Header */}
        <div className="surface rounded-md p-6 flex items-start justify-between flex-wrap gap-4" data-testid="alliance-header">
          <div className="flex items-start gap-3">
            <ShieldStar size={36} weight="duotone" className="text-[#FFBA08]" />
            <div>
              <div className="tactical-label text-zinc-500">// {a.game_slug.toUpperCase()}</div>
              <h1 className="font-display text-3xl font-black tracking-tighter">{a.name}</h1>
              {a.description && <p className="text-sm text-zinc-400 mt-1">{a.description}</p>}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={() => { navigator.clipboard?.writeText(a.code); toast.success(`Code ${a.code} copied`); }} className="surface px-3 py-2 rounded text-xs font-mono-tactical tracking-widest flex items-center gap-1.5 hover:border-white/30" data-testid="alliance-code-copy">
              <Copy size={12} /> {a.code}
            </button>
            <button onClick={() => setShowMembers(s => !s)} className="surface px-3 py-2 rounded text-xs flex items-center gap-1.5 hover:border-white/30" data-testid="alliance-members-toggle">
              <Users size={12} /> {a.member_count}
            </button>
            <button onClick={leave} className="text-xs text-zinc-500 hover:text-[#E63946] px-2" data-testid="alliance-leave">
              <SignOut size={14} />
            </button>
          </div>
        </div>

        <AnimatePresence>
          {showMembers && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="surface rounded-md overflow-hidden" data-testid="alliance-members-list">
              <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-2">
                {a.members?.map(m => (
                  <div key={m.id} className="surface-elev rounded p-2 text-sm flex items-center gap-2">
                    <Users size={14} className="text-zinc-500" />
                    <span className="truncate">{m.username}</span>
                    {m.id === a.creator_id && <span className="tactical-label text-[#FFBA08] ml-auto">LEADER</span>}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Action bar */}
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={() => setShareOpen(true)} className="btn-outline !py-2 !px-3 text-xs flex items-center gap-1.5" data-testid="open-share">
            <Brain size={12} /> Share Deep Dive / Build
          </button>
          <button onClick={() => setBrOpen(true)} className="btn-outline !py-2 !px-3 text-xs flex items-center gap-1.5" data-testid="open-battle-report">
            <FlagBanner size={12} /> Post battle report
          </button>
        </div>

        {/* Chat */}
        <div className="surface rounded-md flex flex-col min-h-[55vh]" data-testid="alliance-chat">
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[60vh]">
            {messages.length === 0 ? (
              <div className="text-center text-zinc-500 mt-12">
                <ChatCircleText size={36} weight="duotone" className="text-[#E63946] mx-auto mb-2" />
                <p className="text-sm">No transmissions yet. Say hello.</p>
              </div>
            ) : messages.map(m => (
              <MessageBubble key={m.id} m={m} isMine={m.user_id === user?.id} currentUser={user} />
            ))}
            <div ref={endRef} />
          </div>

          <form onSubmit={send} className="border-t border-white/5 p-3">
            <div className="flex gap-2 mb-2">
              <button type="button" onClick={() => setMode("text")} className={`tactical-label px-2 py-1 rounded border ${mode === "text" ? "border-white/40 text-white" : "border-white/10 text-zinc-500 hover:text-white"}`} data-testid="mode-text">// CHAT</button>
              <button type="button" onClick={() => setMode("cyphr")} className={`tactical-label px-2 py-1 rounded border flex items-center gap-1 ${mode === "cyphr" ? "border-[#10B981]/60 text-[#10B981]" : "border-white/10 text-zinc-500 hover:text-[#10B981]"}`} data-testid="mode-cyphr">
                <Sparkle size={10} weight="fill" /> // ASK CYPHRAI
              </button>
            </div>
            <div className="flex gap-2">
              <input
                value={input} onChange={e => setInput(e.target.value)}
                placeholder={mode === "cyphr" ? "Ask CyphrAI a game-specific question…" : "Send a message to your alliance…"}
                className="flex-1 bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                disabled={busy} data-testid="alliance-input"
              />
              <button type="submit" disabled={busy || !input.trim()} className="btn-primary !py-2 !px-4 flex items-center gap-1" data-testid="alliance-send">
                <PaperPlaneTilt size={14} weight="bold" />
              </button>
            </div>
          </form>
        </div>
      </div>

      <ShareModal open={shareOpen} onClose={() => setShareOpen(false)} alliance={a} onShared={refresh} />
      <BattleReportModal open={brOpen} onClose={() => setBrOpen(false)} allianceId={id} onPosted={refresh} />
    </div>
  );
};

export default OperationsRoom;
