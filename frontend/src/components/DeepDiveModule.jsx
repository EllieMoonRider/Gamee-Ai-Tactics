import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { api, API } from "../lib/api";
import {
  Brain, UploadSimple, X, Plus, CaretRight, CaretDown, Trash, Stack, Sparkle, Image as ImageIcon,
  Share, LinkSimple, Compass, Lightning,
} from "@phosphor-icons/react";
import GuidedDeepDive from "./GuidedDeepDive";

const renderMd = (s) => (s || "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/^### (.+)$/gm, "<h3>$1</h3>")
  .replace(/^## (.+)$/gm, "<h2>$1</h2>")
  .replace(/^# (.+)$/gm, "<h1>$1</h1>")
  .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
  .replace(/^- (.+)$/gm, "<li>$1</li>")
  .replace(/(<li>.*?<\/li>(?:\n|$))+/gs, m => `<ul>${m}</ul>`)
  .replace(/\n/g, "<br />");

const UploadZone = ({ files, setFiles, max = 6 }) => {
  const inputRef = useRef(null);
  const onPick = (e) => {
    const incoming = Array.from(e.target.files || []).filter(f => f.type.startsWith("image/"));
    if (files.length + incoming.length > max) {
      toast.error(`Max ${max} screenshots`);
      return;
    }
    setFiles([...files, ...incoming]);
    e.target.value = "";
  };
  const remove = (i) => setFiles(files.filter((_, idx) => idx !== i));
  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="w-full border-2 border-dashed border-white/15 hover:border-[#FF6B00]/60 rounded-md p-8 text-center transition group"
        data-testid="deepdive-upload-zone"
      >
        <UploadSimple size={28} className="mx-auto text-zinc-500 group-hover:text-[#FF6B00] mb-2" />
        <div className="text-sm font-semibold">Drop game screenshots here</div>
        <div className="text-xs text-zinc-500 mt-1">PNG/JPG · up to {max} files · 6MB each</div>
      </button>
      <input ref={inputRef} type="file" multiple accept="image/*" onChange={onPick} className="hidden" data-testid="deepdive-file-input" />
      {files.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-3">
          {files.map((f, i) => (
            <div key={i} className="relative aspect-square surface-elev rounded overflow-hidden group">
              <img src={URL.createObjectURL(f)} alt="" className="w-full h-full object-cover" />
              <button type="button" onClick={() => remove(i)} className="absolute top-1 right-1 bg-black/70 rounded-full p-1 opacity-0 group-hover:opacity-100" data-testid={`deepdive-shot-remove-${i}`}>
                <X size={10} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const FollowUpBlock = ({ idx, block }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="surface-elev rounded-md" data-testid={`followup-block-${block.id}`}>
      <button onClick={() => setOpen(o => !o)} className="w-full flex items-center gap-3 px-4 py-3 text-left">
        <div className="w-8 h-8 rounded-full bg-[#FFBA08]/15 border border-[#FFBA08]/30 flex items-center justify-center font-mono-tactical text-xs font-bold text-[#FFBA08]">
          {String(idx + 1).padStart(2, "0")}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-display font-semibold text-sm">Building Block · {block.shot_count} shot{block.shot_count !== 1 ? "s" : ""}</div>
          <div className="text-xs text-zinc-500 font-mono-tactical">{new Date(block.created_at).toLocaleString()}</div>
        </div>
        {open ? <CaretDown size={14} /> : <CaretRight size={14} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="px-4 pb-4">
              {block.notes && <p className="text-xs text-zinc-500 italic mb-2">Notes: {block.notes}</p>}
              <div className="terminal-block markdown-output" dangerouslySetInnerHTML={{ __html: renderMd(block.analysis) }} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const DeepDiveDetail = ({ id, onBack, onDelete }) => {
  const [dd, setDd] = useState(null);
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [files, setFiles] = useState([]);
  const [notes, setNotes] = useState("");
  const [running, setRunning] = useState(false);
  const [shareUrl, setShareUrl] = useState(null);

  const refresh = () => api.get(`/deep-dive/${id}`).then(r => {
    setDd(r.data);
    if (r.data.share_token) setShareUrl(`${window.location.origin}/share/d/${r.data.share_token}`);
  });
  useEffect(() => { refresh(); }, [id]);

  const generateShare = async () => {
    try {
      const r = await api.post(`/deep-dive/${id}/share`);
      setShareUrl(r.data.url);
      navigator.clipboard?.writeText(r.data.url).catch(() => {});
      toast.success("Share link copied to clipboard");
    } catch { toast.error("Could not create share link"); }
  };
  const revokeShare = async () => {
    try {
      await api.delete(`/deep-dive/${id}/share`);
      setShareUrl(null);
      toast.success("Share link revoked");
    } catch { toast.error("Could not revoke"); }
  };

  const submitFollowUp = async (e) => {
    e.preventDefault();
    if (files.length === 0) return toast.error("Upload at least 1 screenshot");
    setRunning(true);
    try {
      const fd = new FormData();
      fd.append("notes", notes);
      files.forEach(f => fd.append("files", f));
      await fetch(`${API}/deep-dive/${id}/followup`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      }).then(async r => { if (!r.ok) throw new Error((await r.json())?.detail || "Failed"); });
      toast.success("Building block added");
      setFiles([]); setNotes(""); setShowFollowUp(false);
      refresh();
    } catch (err) {
      toast.error("CypherAI failed: " + err.message);
    } finally { setRunning(false); }
  };

  if (!dd) return <div className="surface p-10 rounded text-center text-zinc-500 font-mono-tactical text-sm">LOADING DEEP DIVE…</div>;

  return (
    <div className="space-y-5" data-testid="deepdive-detail">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <button onClick={onBack} className="text-sm text-zinc-400 hover:text-white" data-testid="deepdive-back">← Back to archive</button>
        <div className="flex items-center gap-2">
          {shareUrl ? (
            <>
              <button onClick={() => { navigator.clipboard?.writeText(shareUrl); toast.success("Link copied"); }}
                className="text-xs text-zinc-300 hover:text-white flex items-center gap-1 surface px-3 py-1.5 rounded" data-testid="deepdive-copy-share">
                <LinkSimple size={12} /> Copy share link
              </button>
              <button onClick={revokeShare} className="text-xs text-zinc-500 hover:text-[#FF6B00] flex items-center gap-1" data-testid="deepdive-revoke-share">
                Revoke
              </button>
            </>
          ) : (
            <button onClick={generateShare} className="text-xs text-zinc-300 hover:text-white flex items-center gap-1 surface px-3 py-1.5 rounded" data-testid="deepdive-share-btn">
              <Share size={12} /> Share read-only
            </button>
          )}
          <button onClick={() => onDelete(dd.id)} className="text-xs text-zinc-500 hover:text-[#FF6B00] flex items-center gap-1" data-testid="deepdive-delete">
            <Trash size={12} /> Delete
          </button>
        </div>
      </div>

      <div className="surface rounded-md p-6">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div className="tactical-label text-[#FF6B00] mb-2">// BASELINE · {new Date(dd.created_at).toLocaleDateString()}</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">{dd.title}</h2>
            {dd.baseline_notes && <p className="text-xs text-zinc-500 italic mt-1">Notes: {dd.baseline_notes}</p>}
          </div>
          <div className="tactical-label">{dd.follow_ups?.length || 0} BUILDING BLOCK{(dd.follow_ups?.length || 0) !== 1 ? "S" : ""}</div>
        </div>
        <div className="mt-5 terminal-block markdown-output" data-testid="deepdive-baseline-analysis"
             dangerouslySetInnerHTML={{ __html: renderMd(dd.baseline_analysis) }} />
      </div>

      {/* Building blocks chain */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Stack size={18} className="text-[#FFBA08]" />
          <h3 className="font-display font-bold tracking-tight">Building Blocks</h3>
          <button onClick={() => setShowFollowUp(s => !s)} className="ml-auto btn-outline !py-1.5 !px-3 text-xs flex items-center gap-1" data-testid="deepdive-add-followup">
            <Plus size={12} weight="bold" /> {showFollowUp ? "Cancel" : "Add building block"}
          </button>
        </div>
        <AnimatePresence>
          {showFollowUp && (
            <motion.form
              initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              onSubmit={submitFollowUp} className="surface rounded-md p-5 mb-4 space-y-4"
              data-testid="deepdive-followup-form"
            >
              <UploadZone files={files} setFiles={setFiles} />
              <input
                value={notes} onChange={e => setNotes(e.target.value)}
                placeholder="What did you change since baseline? (optional)"
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                data-testid="deepdive-followup-notes"
              />
              <button type="submit" disabled={running || files.length === 0} className="btn-primary w-full flex items-center justify-center gap-2" data-testid="deepdive-followup-submit">
                <Brain size={16} weight="bold" /> {running ? "CypherAI analyzing…" : "Add building block"}
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        {(dd.follow_ups?.length || 0) === 0 ? (
          <p className="text-sm text-zinc-500 surface p-5 rounded-md">No building blocks yet. Add one any time you make progress to track growth.</p>
        ) : (
          <div className="space-y-2">
            {dd.follow_ups.map((b, i) => <FollowUpBlock key={b.id} idx={i} block={b} />)}
          </div>
        )}
      </div>
    </div>
  );
};

const DeepDiveModule = ({ slug, gameName }) => {
  const [list, setList] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [creating, setCreating] = useState(false);
  const [mode, setMode] = useState("quick"); // "quick" | "guided"
  const [files, setFiles] = useState([]);
  const [title, setTitle] = useState("Account Baseline");
  const [notes, setNotes] = useState("");
  const [running, setRunning] = useState(false);

  const refresh = () => api.get(`/deep-dive?game_slug=${slug}`).then(r => setList(r.data));
  useEffect(() => { refresh(); setSelectedId(null); /* eslint-disable-next-line */ }, [slug]);

  const submitNew = async (e) => {
    e.preventDefault();
    if (files.length === 0) return toast.error("Upload at least 1 screenshot");
    setRunning(true);
    try {
      const fd = new FormData();
      fd.append("game_slug", slug);
      fd.append("title", title || "Account Baseline");
      fd.append("notes", notes);
      files.forEach(f => fd.append("files", f));
      const r = await fetch(`${API}/deep-dive`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      });
      if (!r.ok) {
        const detail = (await r.json())?.detail || "Failed";
        if (r.status === 402) {
          toast.error(detail, {
            action: { label: "View Pricing", onClick: () => window.location.assign("/pricing") },
            duration: 8000,
          });
          throw new Error("quota");
        }
        throw new Error(detail);
      }
      const data = await r.json();
      toast.success("CypherAI baseline complete");
      setFiles([]); setNotes(""); setTitle("Account Baseline"); setCreating(false);
      await refresh();
      setSelectedId(data.id);
    } catch (err) {
      if (err.message !== "quota") toast.error("CypherAI failed: " + err.message);
    } finally { setRunning(false); }
  };

  const onDelete = async (did) => {
    if (!window.confirm("Delete this deep dive and all its building blocks?")) return;
    await api.delete(`/deep-dive/${did}`);
    setSelectedId(null);
    refresh();
    toast.success("Deep dive removed");
  };

  if (selectedId) return <DeepDiveDetail id={selectedId} onBack={() => setSelectedId(null)} onDelete={onDelete} />;

  return (
    <div className="space-y-5">
      <div className="surface rounded-md p-6 flex items-start gap-4 flex-wrap" data-testid="deepdive-intro">
        <div className="w-12 h-12 rounded-md bg-[#FF6B00]/10 border border-[#FF6B00]/30 flex items-center justify-center flex-shrink-0">
          <Brain size={24} weight="duotone" className="text-[#FF6B00]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="tactical-label text-[#FF6B00] mb-1">// CYPHERAI · DEEP DIVE</div>
          <h2 className="font-display text-xl font-bold tracking-tight">Establish your {gameName} baseline</h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Upload screenshots of your account — heroes, HQ, formation, gear, alliance.
            CypherAI analyzes everything visible and produces a strategic baseline.
            Every time you make progress, drop new screenshots to add a <strong className="text-[#FFBA08]">building block</strong> — your tactical archive grows with you.
          </p>
        </div>
        <button onClick={() => setCreating(true)} className="btn-primary flex items-center gap-2" data-testid="deepdive-new-btn">
          <Plus size={16} weight="bold" /> New deep dive
        </button>
      </div>

      {/* Mode toggle */}
      <AnimatePresence>
        {creating && (
          <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} className="surface rounded-md p-2 flex items-center gap-1" data-testid="deepdive-mode-toggle">
            <button onClick={() => setMode("quick")} className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded text-xs transition ${mode === "quick" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-white"}`} data-testid="mode-quick">
              <Lightning size={12} weight={mode === "quick" ? "fill" : "regular"} /> Quick — upload everything at once
            </button>
            <button onClick={() => setMode("guided")} className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded text-xs transition ${mode === "guided" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-white"}`} data-testid="mode-guided">
              <Compass size={12} weight={mode === "guided" ? "fill" : "regular"} /> Guided — CypherAI walks you through it
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {creating && mode === "guided" && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} key="guided">
            <GuidedDeepDive
              slug={slug}
              gameName={gameName}
              onFinalized={async (ddId) => {
                setCreating(false);
                await refresh();
                setSelectedId(ddId);
              }}
            />
            <div className="mt-3 flex justify-end">
              <button onClick={() => { setCreating(false); }} className="text-xs text-zinc-400 hover:text-white">Cancel guided session</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {creating && mode === "quick" && (
          <motion.form
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
            onSubmit={submitNew} className="surface rounded-md p-6 space-y-4"
            data-testid="deepdive-new-form" key="quick"
          >
            <div>
              <label className="tactical-label block mb-2">Baseline title</label>
              <input
                value={title} onChange={e => setTitle(e.target.value)}
                placeholder="e.g. Pre-KvK Snapshot · June"
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                data-testid="deepdive-new-title"
              />
            </div>
            <UploadZone files={files} setFiles={setFiles} />
            <div>
              <label className="tactical-label block mb-2">Context for CypherAI (optional)</label>
              <textarea
                value={notes} onChange={e => setNotes(e.target.value)}
                rows={2}
                placeholder="e.g. F2P, focusing on cavalry, want to dominate Kingdom War"
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                data-testid="deepdive-new-notes"
              />
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => { setCreating(false); setFiles([]); }} className="btn-outline flex-1">Cancel</button>
              <button type="submit" disabled={running || files.length === 0} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="deepdive-new-submit">
                <Sparkle size={16} weight="bold" /> {running ? "CypherAI analyzing…" : "Run deep dive"}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Archive */}
      <div>
        <div className="tactical-label text-zinc-500 mb-3">// ARCHIVE · {list.length} ENTR{list.length === 1 ? "Y" : "IES"}</div>
        {list.length === 0 ? (
          <div className="surface rounded-md p-10 text-center">
            <ImageIcon size={36} className="mx-auto text-zinc-700 mb-3" />
            <p className="text-sm text-zinc-500">No deep dives yet. Run your first baseline above.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="deepdive-archive">
            {list.map(d => (
              <button
                key={d.id} onClick={() => setSelectedId(d.id)}
                className="surface rounded-md p-5 text-left hover:-translate-y-1 transition group"
                data-testid={`deepdive-card-${d.id}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="tactical-label text-[#FF6B00]">// {new Date(d.created_at).toLocaleDateString()}</span>
                  <span className="tactical-label text-[#FFBA08]">{d.followup_count || 0} BLOCK{d.followup_count === 1 ? "" : "S"}</span>
                </div>
                <h3 className="font-display font-bold text-base tracking-tight">{d.title}</h3>
                <p className="text-xs text-zinc-500 mt-2 line-clamp-2">{(d.baseline_analysis || "").replace(/[#*]/g, "").slice(0, 140)}…</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DeepDiveModule;
