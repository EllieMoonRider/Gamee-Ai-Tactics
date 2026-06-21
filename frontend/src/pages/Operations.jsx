import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ShieldStar, Plus, Users, ArrowRight, Lock, CheckCircle, KeyReturn,
} from "@phosphor-icons/react";

const Operations = () => {
  const { user } = useAuth();
  const nav = useNavigate();
  const [quota, setQuota] = useState(null);
  const [alliances, setAlliances] = useState([]);
  const [games, setGames] = useState([]);
  const [creating, setCreating] = useState(false);
  const [joining, setJoining] = useState(false);

  // Create form
  const [name, setName] = useState("");
  const [gameSlug, setGameSlug] = useState("");
  const [description, setDescription] = useState("");
  // Join form
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/billing/quota").then(r => setQuota(r.data));
    api.get("/games").then(r => setGames(r.data));
    api.get("/alliances/mine").then(r => setAlliances(r.data)).catch(() => {});
  }, []);

  const hasAccess = quota?.subscription_active && quota?.toc_active;

  const submitCreate = async (e) => {
    e.preventDefault();
    if (!name.trim() || !gameSlug) return toast.error("Name and game required");
    setBusy(true);
    try {
      const { data } = await api.post("/alliances", { name: name.trim(), game_slug: gameSlug, description });
      toast.success("Alliance forged");
      nav(`/operations/${data.id}`);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Could not create";
      if (err?.response?.status === 402) {
        toast.error(detail, { action: { label: "View Pricing", onClick: () => nav("/pricing") }, duration: 8000 });
      } else toast.error(detail);
    } finally { setBusy(false); }
  };

  const submitJoin = async (e) => {
    e.preventDefault();
    if (!code.trim()) return;
    setBusy(true);
    try {
      const { data } = await api.post("/alliances/join", { code: code.trim().toUpperCase() });
      toast.success(`Joined ${data.name}`);
      nav(`/operations/${data.id}`);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Could not join";
      if (err?.response?.status === 402) {
        toast.error(detail, { action: { label: "View Pricing", onClick: () => nav("/pricing") }, duration: 8000 });
      } else toast.error(detail);
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="tactical-label text-[#E63946] mb-2">// TACTICAL OPERATIONS CENTER</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter flex items-center gap-3">
            <ShieldStar size={42} weight="duotone" className="text-[#FFBA08]" />
            Alliance HQ
          </h1>
          <p className="text-zinc-400 mt-3 max-w-2xl">
            Create or join a per-game alliance room. Chat with your alliance, share Deep Dive analyses & Builds, post battle reports, and ask CypherAI questions <strong className="text-white">unlimited</strong> — in-room and game-specific.
          </p>
        </motion.div>

        {!hasAccess && (
          <div className="surface rounded-md p-6 border border-[#FFBA08]/30" data-testid="toc-locked">
            <div className="flex items-start gap-4 flex-wrap">
              <Lock size={28} weight="duotone" className="text-[#FFBA08] flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <h2 className="font-display font-bold text-lg">Operations Center add-on required</h2>
                <p className="text-sm text-zinc-400 mt-1">
                  Pro ($4.99/mo) + Tactical Operations Center add-on ($0.99/mo) = <strong className="text-[#FFBA08]">$5.99/mo total</strong>.
                  Unlock alliance chat, shared analyses, and unlimited in-room CypherAI questions.
                </p>
              </div>
              <Link to="/pricing" className="btn-primary" data-testid="toc-upgrade-cta">Unlock — $5.99/mo</Link>
            </div>
          </div>
        )}

        {/* Create + Join forms */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Create */}
          <div className="surface rounded-md">
            <button
              onClick={() => setCreating(c => !c)}
              className="w-full flex items-center gap-3 p-5 text-left"
              data-testid="toggle-create-alliance"
            >
              <div className="w-10 h-10 rounded bg-[#E63946]/10 border border-[#E63946]/30 flex items-center justify-center">
                <Plus size={20} weight="bold" className="text-[#E63946]" />
              </div>
              <div className="flex-1">
                <div className="font-display font-bold">Create an alliance</div>
                <div className="text-xs text-zinc-500">You'll get a join code to share with members</div>
              </div>
              <ArrowRight size={16} className={`text-zinc-500 transition ${creating ? "rotate-90" : ""}`} />
            </button>
            {creating && (
              <form onSubmit={submitCreate} className="border-t border-white/5 p-5 space-y-3" data-testid="create-alliance-form">
                <div>
                  <label className="tactical-label block mb-1.5">Alliance name</label>
                  <input value={name} onChange={e => setName(e.target.value)} className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" placeholder="Iron Wolves" required data-testid="alliance-name" />
                </div>
                <div>
                  <label className="tactical-label block mb-1.5">Game</label>
                  <select value={gameSlug} onChange={e => setGameSlug(e.target.value)} className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" required data-testid="alliance-game">
                    <option value="">— pick a game —</option>
                    {games.map(g => <option key={g.slug} value={g.slug}>{g.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="tactical-label block mb-1.5">Description (optional)</label>
                  <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2} className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" placeholder="F2P friendly · KvK focused" data-testid="alliance-description" />
                </div>
                <button type="submit" disabled={busy} className="btn-primary w-full" data-testid="alliance-create-submit">
                  {busy ? "Creating…" : "Forge alliance"}
                </button>
              </form>
            )}
          </div>

          {/* Join */}
          <div className="surface rounded-md">
            <button
              onClick={() => setJoining(j => !j)}
              className="w-full flex items-center gap-3 p-5 text-left"
              data-testid="toggle-join-alliance"
            >
              <div className="w-10 h-10 rounded bg-[#FFBA08]/10 border border-[#FFBA08]/30 flex items-center justify-center">
                <KeyReturn size={20} weight="bold" className="text-[#FFBA08]" />
              </div>
              <div className="flex-1">
                <div className="font-display font-bold">Join with a code</div>
                <div className="text-xs text-zinc-500">Paste the 6-char invite from your alliance</div>
              </div>
              <ArrowRight size={16} className={`text-zinc-500 transition ${joining ? "rotate-90" : ""}`} />
            </button>
            {joining && (
              <form onSubmit={submitJoin} className="border-t border-white/5 p-5 space-y-3" data-testid="join-alliance-form">
                <div>
                  <label className="tactical-label block mb-1.5">Alliance code</label>
                  <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} maxLength={6} className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-base font-mono-tactical tracking-widest text-center uppercase" placeholder="A1B2C3" required data-testid="alliance-join-code" />
                </div>
                <button type="submit" disabled={busy} className="btn-outline w-full" data-testid="alliance-join-submit">
                  {busy ? "Joining…" : "Join alliance"}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* My alliances */}
        <div>
          <div className="tactical-label text-zinc-500 mb-3">// YOUR ALLIANCES · {alliances.length}</div>
          {alliances.length === 0 ? (
            <div className="surface rounded-md p-10 text-center">
              <Users size={36} className="mx-auto text-zinc-600 mb-3" />
              <p className="text-sm text-zinc-500">No alliances yet. Create or join one above.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="alliance-list">
              {alliances.map(a => {
                const game = games.find(g => g.slug === a.game_slug);
                return (
                  <Link key={a.id} to={`/operations/${a.id}`} className="surface rounded-md p-5 block hover:-translate-y-1 transition group" data-testid={`alliance-card-${a.id}`}>
                    <div className="flex items-start justify-between mb-2">
                      <span className="tag-chip" style={{ color: game?.color, borderColor: (game?.color || "#888") + "40" }}>{game?.name || a.game_slug}</span>
                      <span className="font-mono-tactical text-xs text-zinc-500">{a.code}</span>
                    </div>
                    <h3 className="font-display text-xl font-bold tracking-tight">{a.name}</h3>
                    {a.description && <p className="text-xs text-zinc-400 mt-1.5 line-clamp-2">{a.description}</p>}
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/5">
                      <span className="text-xs text-zinc-500 flex items-center gap-1"><Users size={12} /> {a.member_count} member{a.member_count !== 1 ? "s" : ""}</span>
                      <ArrowRight size={14} className="text-zinc-500 group-hover:text-[#E63946] transition" />
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Operations;
