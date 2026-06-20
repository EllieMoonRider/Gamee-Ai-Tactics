import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { api, API } from "../lib/api";
import {
  Brain, UploadSimple, X, ArrowRight, CheckCircle, SkipForward,
  Sparkle, PaperPlaneTilt, Lightning, ChatCircleText,
} from "@phosphor-icons/react";

const renderMd = (s) => (s || "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/^- (.+)$/gm, "<li>$1</li>")
  .replace(/(<li>.*?<\/li>(?:\n|$))+/gs, m => `<ul>${m}</ul>`)
  .replace(/\n/g, "<br />");

const GuidedDeepDive = ({ slug, gameName, onFinalized }) => {
  const [session, setSession] = useState(null);
  const [activeStepIdx, setActiveStepIdx] = useState(0);
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [askInput, setAskInput] = useState("");
  const [asking, setAsking] = useState(false);
  const [showFinalize, setShowFinalize] = useState(false);
  const [title, setTitle] = useState("Guided Baseline");
  const [notes, setNotes] = useState("");
  const fileInputRef = useRef(null);

  // Start a session immediately
  useEffect(() => {
    (async () => {
      try {
        const fd = new FormData();
        fd.append("game_slug", slug);
        const r = await fetch(`${API}/guided-dive/start`, {
          method: "POST",
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
          body: fd,
        });
        if (!r.ok) throw new Error("Couldn't start guided session");
        const data = await r.json();
        setSession(data);
      } catch (e) {
        toast.error(e.message);
      }
    })();
  }, [slug]);

  if (!session) return (
    <div className="surface rounded-md p-10 text-center text-zinc-500 font-mono-tactical text-sm">
      CYPHRAI IS PREPARING YOUR GUIDED PLAN…
    </div>
  );

  const steps = session.steps || [];
  const activeStep = steps[activeStepIdx];
  const uploaded = session.uploads?.[activeStep?.id] || [];
  const skipped = (session.skipped || []).includes(activeStep?.id);
  const completedCount = steps.filter(s => (session.uploads?.[s.id]?.length || 0) > 0).length;
  const totalCaptured = completedCount;
  const canFinalize = totalCaptured > 0;

  const pickFiles = (e) => {
    const arr = Array.from(e.target.files || []).filter(f => f.type.startsWith("image/"));
    if (arr.length === 0) return;
    if (arr.length > 6) return toast.error("Max 6 screenshots per step");
    setFiles(arr);
    e.target.value = "";
  };

  const uploadCurrent = async () => {
    if (!files.length) return toast.error("Pick at least 1 screenshot");
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("step_id", activeStep.id);
      files.forEach(f => fd.append("files", f));
      const r = await fetch(`${API}/guided-dive/${session.id}/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      });
      if (!r.ok) throw new Error((await r.json())?.detail || "Upload failed");
      const data = await r.json();
      setSession(data);
      setFiles([]);
      toast.success("Captured ✓");
      if (activeStepIdx < steps.length - 1) setActiveStepIdx(i => i + 1);
    } catch (e) {
      toast.error(e.message);
    } finally { setBusy(false); }
  };

  const skipStep = async () => {
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("step_id", activeStep.id);
      const r = await fetch(`${API}/guided-dive/${session.id}/skip`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      });
      const data = await r.json();
      setSession(data);
      setFiles([]);
      if (activeStepIdx < steps.length - 1) setActiveStepIdx(i => i + 1);
    } catch { toast.error("Skip failed"); }
    finally { setBusy(false); }
  };

  const ask = async (e) => {
    e?.preventDefault();
    const q = askInput.trim();
    if (!q) return;
    setAsking(true);
    try {
      const { data } = await api.post(`/guided-dive/${session.id}/ask`, { question: q });
      setSession(s => ({ ...s, qa: [...(s.qa || []), data] }));
      setAskInput("");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not ask CyphrAI");
    } finally { setAsking(false); }
  };

  const finalize = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/guided-dive/${session.id}/finalize`, { title, notes });
      toast.success("Deep Dive generated");
      onFinalized?.(data.deep_dive_id);
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail || "Finalize failed";
      if (status === 402) {
        toast.error(detail, { action: { label: "View Pricing", onClick: () => window.location.assign("/pricing") }, duration: 8000 });
      } else toast.error(detail);
    } finally { setBusy(false); }
  };

  return (
    <div className="space-y-5" data-testid="guided-dive">
      {/* Header w/ progress */}
      <div className="surface rounded-md p-5">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <div className="tactical-label text-[#10B981] mb-1">// CYPHRAI GUIDED MODE</div>
            <h2 className="font-display text-xl font-bold tracking-tight">{gameName} · step-by-step capture</h2>
            <p className="text-xs text-zinc-400 mt-1">CyphrAI tells you exactly what to screenshot. Ask anything mid-flow.</p>
          </div>
          <div className="text-right">
            <div className="tactical-label text-zinc-500">// PROGRESS</div>
            <div className="font-display text-2xl font-black">{completedCount}<span className="text-zinc-500 text-lg">/{steps.length}</span></div>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-7 gap-1.5">
          {steps.map((s, i) => {
            const done = (session.uploads?.[s.id]?.length || 0) > 0;
            const skip = (session.skipped || []).includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => setActiveStepIdx(i)}
                className={`h-1.5 rounded-sm transition ${done ? "bg-[#10B981]" : skip ? "bg-zinc-700" : i === activeStepIdx ? "bg-[#FFBA08]" : "bg-white/10"}`}
                title={s.title}
                data-testid={`guided-progress-${i}`}
              />
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-5">
        {/* Step card */}
        <div className="surface rounded-md p-6 space-y-4" data-testid="guided-step-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded bg-[#FFBA08]/10 border border-[#FFBA08]/30 flex items-center justify-center font-mono-tactical font-bold text-[#FFBA08]">
              {String(activeStepIdx + 1).padStart(2, "0")}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-display text-lg font-bold tracking-tight" data-testid="guided-step-title">{activeStep.title}</h3>
              <p className="text-sm text-zinc-400 mt-0.5">{activeStep.desc}</p>
            </div>
          </div>

          {/* State indicator */}
          {uploaded.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-[#10B981] surface-elev rounded p-2.5">
              <CheckCircle size={14} weight="duotone" /> {uploaded.length} screenshot{uploaded.length === 1 ? "" : "s"} captured. Pick again to replace.
            </div>
          )}
          {skipped && (
            <div className="flex items-center gap-2 text-xs text-zinc-500 surface-elev rounded p-2.5">
              <SkipForward size={14} /> Skipped — CyphrAI will note this in the analysis.
            </div>
          )}

          {/* File picker */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="w-full border-2 border-dashed border-white/15 hover:border-[#FFBA08]/60 rounded p-6 text-center transition"
            data-testid="guided-pick-files"
          >
            <UploadSimple size={24} className="mx-auto text-zinc-500 mb-1.5" />
            <div className="text-sm font-semibold">{files.length === 0 ? "Tap to add screenshots" : `${files.length} file${files.length === 1 ? "" : "s"} ready`}</div>
            <div className="text-xs text-zinc-500">Up to 6 · PNG / JPG / WebP</div>
          </button>
          <input ref={fileInputRef} type="file" multiple accept="image/*" onChange={pickFiles} className="hidden" />

          {files.length > 0 && (
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {files.map((f, i) => (
                <div key={i} className="aspect-square surface-elev rounded overflow-hidden relative group">
                  <img src={URL.createObjectURL(f)} alt="" className="w-full h-full object-cover" />
                  <button type="button" onClick={() => setFiles(files.filter((_, idx) => idx !== i))} className="absolute top-1 right-1 bg-black/70 rounded-full p-1 opacity-0 group-hover:opacity-100">
                    <X size={10} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={uploadCurrent} disabled={busy || !files.length} className="btn-primary flex-1 flex items-center justify-center gap-2" data-testid="guided-capture-btn">
              <CheckCircle size={14} weight="bold" /> {busy ? "Saving…" : uploaded.length > 0 ? "Re-capture" : "Capture this step"}
            </button>
            <button onClick={skipStep} disabled={busy} className="btn-outline !py-2 !px-3 text-xs flex items-center gap-1.5" data-testid="guided-skip-btn">
              <SkipForward size={12} /> Skip
            </button>
          </div>

          <div className="flex items-center justify-between text-xs text-zinc-500 pt-2 border-t border-white/5">
            <button onClick={() => setActiveStepIdx(i => Math.max(0, i - 1))} disabled={activeStepIdx === 0} className="hover:text-white disabled:opacity-30">← Previous</button>
            <span>Step {activeStepIdx + 1} of {steps.length}</span>
            <button onClick={() => setActiveStepIdx(i => Math.min(steps.length - 1, i + 1))} disabled={activeStepIdx === steps.length - 1} className="hover:text-white disabled:opacity-30">Next →</button>
          </div>
        </div>

        {/* Q&A sidebar */}
        <div className="surface rounded-md flex flex-col min-h-[400px]" data-testid="guided-qa">
          <div className="p-4 border-b border-white/5 flex items-center gap-2">
            <Brain size={16} weight="duotone" className="text-[#10B981]" />
            <div className="font-display font-bold text-sm">Ask CyphrAI</div>
            <span className="tactical-label text-zinc-500 ml-auto">// {gameName}</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[50vh]">
            {(session.qa || []).length === 0 ? (
              <div className="text-center text-zinc-500 text-xs py-8">
                <ChatCircleText size={28} className="mx-auto mb-2 text-zinc-700" />
                Ask anything mid-capture.<br />e.g. "Where do I find the gear screen?"
              </div>
            ) : (
              (session.qa || []).map(qa => (
                <div key={qa.id} className="space-y-1.5">
                  <div className="text-xs text-zinc-300 surface-elev p-2 rounded">{qa.q}</div>
                  <div className="text-xs markdown-output surface-elev p-2 rounded border-l-2 border-[#10B981]" dangerouslySetInnerHTML={{ __html: renderMd(qa.a) }} />
                </div>
              ))
            )}
          </div>
          <form onSubmit={ask} className="border-t border-white/5 p-3 flex gap-2">
            <input
              value={askInput} onChange={e => setAskInput(e.target.value)}
              placeholder="Quick question…"
              className="flex-1 bg-[#0c0c0c] border border-white/10 rounded px-2.5 py-2 text-xs"
              disabled={asking} data-testid="guided-ask-input"
            />
            <button type="submit" disabled={asking || !askInput.trim()} className="btn-primary !py-2 !px-3 text-xs" data-testid="guided-ask-send">
              <PaperPlaneTilt size={12} weight="bold" />
            </button>
          </form>
        </div>
      </div>

      {/* Finalize bar */}
      <div className="surface rounded-md p-5 flex items-center gap-3 flex-wrap" data-testid="guided-finalize-bar">
        <Lightning size={20} weight="duotone" className="text-[#E63946]" />
        <div className="flex-1 min-w-[200px]">
          <div className="font-display font-bold">Ready to generate your Deep Dive?</div>
          <div className="text-xs text-zinc-400">CyphrAI will analyze all <strong className="text-white">{totalCaptured}</strong> captured screen{totalCaptured === 1 ? "" : "s"} and produce a full baseline. <strong className="text-[#FFBA08]">Costs 1 baseline from your quota.</strong></div>
        </div>
        <button onClick={() => setShowFinalize(true)} disabled={!canFinalize} className="btn-primary" data-testid="guided-open-finalize">
          <Sparkle size={14} weight="fill" className="inline mr-1.5" /> Finalize ({totalCaptured})
        </button>
      </div>

      {/* Finalize modal */}
      <AnimatePresence>
        {showFinalize && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowFinalize(false)}
          >
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }}
              className="surface-elev max-w-md w-full rounded-md p-6 space-y-4"
              onClick={(e) => e.stopPropagation()}
              data-testid="guided-finalize-modal"
            >
              <h3 className="font-display text-xl font-bold">Finalize this Guided Deep Dive</h3>
              <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="guided-finalize-title" />
              <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} placeholder="Optional context for CyphrAI (e.g. F2P, focusing on KvK)" className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="guided-finalize-notes" />
              <div className="flex items-center gap-2 text-xs text-zinc-400 surface rounded p-2.5">
                <Lightning size={12} className="text-[#FFBA08]" /> This uses <strong className="text-[#FFBA08]">1 Deep Dive baseline</strong> from your quota.
              </div>
              <div className="flex gap-2">
                <button onClick={() => setShowFinalize(false)} className="btn-outline flex-1">Not yet</button>
                <button onClick={finalize} disabled={busy} className="btn-primary flex-1" data-testid="guided-finalize-confirm">
                  {busy ? "CyphrAI analyzing…" : "Generate Deep Dive"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default GuidedDeepDive;
