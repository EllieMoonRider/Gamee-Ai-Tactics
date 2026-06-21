import { useEffect, useState } from "react";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ShieldStar, Plus, Trash, CheckCircle, Clock, X, ShieldWarning } from "@phosphor-icons/react";

const Seats = () => {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState(null);
  const [seats, setSeats] = useState([]);
  const [email, setEmail] = useState("");
  const [alliance, setAlliance] = useState("OTS");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const r = await api.get("/seats/admin-status");
    setIsAdmin(r.data.is_alliance_admin);
    if (r.data.is_alliance_admin) {
      const s = await api.get("/seats/mine");
      setSeats(s.data);
    }
  };
  useEffect(() => { refresh(); }, []);

  const grant = async (e) => {
    e.preventDefault();
    if (!email || !alliance) return;
    setBusy(true);
    try {
      await api.post("/seats", { email: email.toLowerCase(), alliance_name: alliance.toUpperCase(), note });
      toast.success(`Seat granted to ${email}`);
      setEmail(""); setNote("");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not grant");
    } finally { setBusy(false); }
  };

  const revoke = async (id) => {
    if (!window.confirm("Revoke this seat? The member will lose free Pro+TOC access.")) return;
    await api.delete(`/seats/${id}`);
    toast.success("Seat revoked");
    refresh();
  };

  if (isAdmin === null) return <div className="command-center min-h-screen"><Navbar /><div className="max-w-4xl mx-auto px-6 py-10"><div className="h-12 shimmer rounded" /></div></div>;

  if (!isAdmin) return (
    <div className="command-center min-h-screen"><Navbar />
      <div className="max-w-md mx-auto px-6 py-20 text-center">
        <ShieldWarning size={42} weight="duotone" className="text-zinc-500 mx-auto mb-3" />
        <h1 className="font-display text-2xl font-bold">Alliance admins only</h1>
        <p className="text-sm text-zinc-400 mt-2">Ask your R5 to add your email to the admin list (or hit them up for an invite seat instead).</p>
      </div>
    </div>
  );

  const active = seats.filter(s => s.status === "active").length;
  const pending = seats.filter(s => s.status === "pending").length;

  return (
    <div className="command-center min-h-screen">
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
        <div>
          <div className="tactical-label text-[#FFBA08] mb-2">// R5 ADMIN · ALLIANCE SEATS</div>
          <h1 className="font-display text-3xl font-black tracking-tighter flex items-center gap-3">
            <ShieldStar size={32} weight="duotone" className="text-[#FFBA08]" /> Seats Granted by {user?.username}
          </h1>
          <p className="text-zinc-400 mt-2 max-w-xl">Grant free <strong>Pro + Operations Center</strong> access to your alliance members. Each seat is email-locked & revocable. Max <strong>100 active seats</strong> (avg alliance: 60 active members).</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="surface rounded p-4"><div className="tactical-label text-[#FFAA33] mb-1">// ACTIVE</div><div className="font-display text-3xl font-black">{active}</div></div>
          <div className="surface rounded p-4"><div className="tactical-label text-[#FFBA08] mb-1">// PENDING</div><div className="font-display text-3xl font-black">{pending}</div></div>
          <div className="surface rounded p-4"><div className="tactical-label text-zinc-500 mb-1">// AVAILABLE</div><div className="font-display text-3xl font-black">{Math.max(0, 100 - active - pending)}</div></div>
        </div>

        {/* Grant form */}
        <form onSubmit={grant} className="surface rounded-md p-5 grid grid-cols-1 md:grid-cols-[1fr_120px_1fr_auto] gap-2" data-testid="seat-grant-form">
          <input value={email} onChange={e => setEmail(e.target.value)} type="email" required placeholder="member@email.com" className="bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="seat-email" />
          <input value={alliance} onChange={e => setAlliance(e.target.value.toUpperCase())} maxLength={10} placeholder="OTS" className="bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm font-mono-tactical text-center" data-testid="seat-alliance" />
          <input value={note} onChange={e => setNote(e.target.value)} placeholder="Note (optional)" className="bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm" data-testid="seat-note" />
          <button type="submit" disabled={busy} className="btn-primary !py-2 !px-4 flex items-center gap-1.5" data-testid="seat-grant-btn">
            <Plus size={14} weight="bold" /> Grant
          </button>
        </form>

        {/* Seats list */}
        <div className="space-y-2" data-testid="seats-list">
          {seats.length === 0 && <p className="surface p-6 rounded text-center text-sm text-zinc-500">No seats granted yet.</p>}
          {seats.map(s => (
            <div key={s.id} className="surface rounded p-3 flex items-center gap-3 flex-wrap" data-testid={`seat-${s.id}`}>
              {s.status === "active" && <CheckCircle size={16} weight="duotone" className="text-[#FFAA33]" />}
              {s.status === "pending" && <Clock size={16} className="text-[#FFBA08]" />}
              {s.status === "revoked" && <X size={16} className="text-[#FF6B00]" />}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold truncate">{s.email}</div>
                <div className="text-xs text-zinc-500">[{s.alliance_name}] · {s.note || "—"} · {new Date(s.created_at).toLocaleDateString()}</div>
              </div>
              <span className="tag-chip" style={{ color: s.status === "active" ? "#FFAA33" : s.status === "pending" ? "#FFBA08" : "#FF6B00" }}>{s.status.toUpperCase()}</span>
              {s.status !== "revoked" && (
                <button onClick={() => revoke(s.id)} className="text-zinc-500 hover:text-[#FF6B00]" data-testid={`seat-revoke-${s.id}`}>
                  <Trash size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Seats;
