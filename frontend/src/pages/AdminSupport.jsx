import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { ShieldStar, ArrowLeft, Lock, CheckCircle, Clock, ChatCircleText, EnvelopeSimple } from "@phosphor-icons/react";

const STATUS_STYLES = {
  open:         { color: "#E63946", label: "OPEN",        icon: Lock },
  in_progress:  { color: "#FFBA08", label: "IN PROGRESS", icon: Clock },
  resolved:     { color: "#10B981", label: "RESOLVED",    icon: CheckCircle },
};

const AdminSupport = () => {
  const nav = useNavigate();
  const [authorized, setAuthorized] = useState(null); // null=checking, false=denied, true=ok
  const [data, setData] = useState({ tickets: [], counts: { open: 0, in_progress: 0, resolved: 0 } });
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(null);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/support/admin/check").then(r => {
      setAuthorized(!!r.data.is_admin);
      if (r.data.is_admin) refresh();
    }).catch(() => setAuthorized(false));
  }, []);

  const refresh = async (statusFilter = filter) => {
    const url = statusFilter ? `/support/admin/tickets?status_filter=${statusFilter}` : "/support/admin/tickets";
    const { data: out } = await api.get(url);
    setData(out);
  };

  useEffect(() => { if (authorized) refresh(filter); /* eslint-disable-next-line */ }, [filter]);

  const openTicket = async (tid) => {
    const { data: t } = await api.get(`/support/tickets/${tid}`);
    setSelected(t);
    setReply("");
  };

  const submitReply = async () => {
    if (reply.trim().length < 1) return;
    setBusy(true);
    try {
      await api.post(`/support/admin/tickets/${selected.id}/reply`, { message: reply.trim() });
      toast.success("Reply sent");
      setReply("");
      await openTicket(selected.id);
      await refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not send reply");
    } finally { setBusy(false); }
  };

  const setStatus = async (status) => {
    setBusy(true);
    try {
      await api.patch(`/support/admin/tickets/${selected.id}/status`, { status });
      toast.success(`Marked ${status}`);
      await openTicket(selected.id);
      await refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not update status");
    } finally { setBusy(false); }
  };

  if (authorized === null) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="max-w-5xl mx-auto px-6 py-10"><div className="h-16 shimmer rounded" /></div>
      </div>
    );
  }

  if (authorized === false) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="max-w-md mx-auto px-6 py-20 text-center">
          <ShieldStar size={48} weight="duotone" className="text-[#E63946] mx-auto mb-3" />
          <h1 className="font-display text-2xl font-bold">Restricted</h1>
          <p className="text-sm text-zinc-400 mt-2">This page is for support admins only.</p>
          <button onClick={() => nav("/dashboard")} className="btn-outline mt-5">Back to Command Center</button>
        </div>
      </div>
    );
  }

  // Detail view
  if (selected) {
    const st = STATUS_STYLES[selected.status] || STATUS_STYLES.open;
    const StIcon = st.icon;
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="max-w-3xl mx-auto px-6 py-10 space-y-5">
          <button onClick={() => { setSelected(null); refresh(); }} className="btn-outline !py-1.5 !px-3 text-xs" data-testid="admin-back-list">
            <ArrowLeft size={14} /> Back to inbox
          </button>

          <div className="surface rounded-md p-6">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div className="min-w-0 flex-1">
                <div className="tactical-label text-zinc-500 mb-1">// #{selected.id.slice(0,8)} · {selected.category.toUpperCase()}</div>
                <h2 className="font-display text-2xl font-bold tracking-tight" data-testid="admin-ticket-subject">{selected.subject}</h2>
                <div className="text-sm text-zinc-400 mt-1">{selected.name} · <a href={`mailto:${selected.email}`} className="text-[#FFBA08] hover:underline">{selected.email}</a></div>
              </div>
              <div className="flex items-center gap-1.5 font-mono-tactical text-xs px-2.5 py-1.5 rounded border" style={{ color: st.color, borderColor: `${st.color}50` }}>
                <StIcon size={14} weight="duotone" /> {st.label}
              </div>
            </div>

            <div className="mt-4 p-4 bg-[#0c0c0c] border border-white/5 rounded text-sm whitespace-pre-wrap text-zinc-200 leading-relaxed" data-testid="admin-ticket-message">{selected.message}</div>

            {/* Status actions */}
            <div className="mt-4 flex gap-2 flex-wrap">
              {["open", "in_progress", "resolved"].filter(s => s !== selected.status).map(s => (
                <button key={s} disabled={busy} onClick={() => setStatus(s)} className="btn-outline !py-1.5 !px-3 text-xs" data-testid={`admin-set-${s}`}>Mark {s.replace("_", " ")}</button>
              ))}
            </div>
          </div>

          {/* Conversation thread */}
          {selected.responses?.length > 0 && (
            <div className="space-y-3" data-testid="admin-thread">
              {selected.responses.map(r => (
                <div key={r.id} className={`surface rounded-md p-4 ${r.from_admin ? "ring-1 ring-[#10B981]/30" : ""}`}>
                  <div className="tactical-label mb-2" style={{ color: r.from_admin ? "#10B981" : "#FFBA08" }}>
                    // {r.from_admin ? `STAFF · ${r.admin_username || ""}` : "USER"} · {new Date(r.created_at).toLocaleString()}
                  </div>
                  <div className="text-sm whitespace-pre-wrap text-zinc-200 leading-relaxed">{r.message}</div>
                </div>
              ))}
            </div>
          )}

          {/* Reply box */}
          <div className="surface rounded-md p-5">
            <div className="tactical-label text-[#10B981] mb-2">// REPLY</div>
            <textarea
              value={reply} onChange={e => setReply(e.target.value)} rows={6}
              placeholder="Write your reply to the user. They'll receive this via email."
              className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm font-sans leading-relaxed"
              data-testid="admin-reply-input"
            />
            <button onClick={submitReply} disabled={busy || reply.trim().length < 1} className="btn-primary w-full mt-3" data-testid="admin-reply-send">
              {busy ? "Sending…" : "Send reply via email"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // List view
  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-5">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <div className="tactical-label text-[#10B981] mb-1">// SUPPORT ADMIN</div>
            <h1 className="font-display text-3xl font-black tracking-tighter flex items-center gap-2">
              <ChatCircleText size={28} weight="duotone" className="text-[#10B981]" /> Support Inbox
            </h1>
          </div>
          <div className="flex gap-2">
            {["", "open", "in_progress", "resolved"].map(s => (
              <button key={s || "all"} onClick={() => setFilter(s)} className={`px-3 py-1.5 rounded text-xs font-mono-tactical tracking-wide border ${filter === s ? "bg-white/10 border-white/30" : "border-white/10 text-zinc-400 hover:border-white/30"}`} data-testid={`admin-filter-${s || "all"}`}>
                {(s || "all").toUpperCase()}{s ? ` · ${data.counts[s] || 0}` : ""}
              </button>
            ))}
          </div>
        </div>

        {/* Counts */}
        <div className="grid grid-cols-3 gap-3">
          {(["open", "in_progress", "resolved"]).map(s => {
            const st = STATUS_STYLES[s];
            return (
              <div key={s} className="surface rounded p-4" data-testid={`admin-count-${s}`}>
                <div className="tactical-label mb-1" style={{ color: st.color }}>// {st.label}</div>
                <div className="font-display text-3xl font-black">{data.counts[s] || 0}</div>
              </div>
            );
          })}
        </div>

        {/* Tickets list */}
        <div className="space-y-2" data-testid="admin-tickets-list">
          {data.tickets.length === 0 && (
            <div className="surface rounded-md p-8 text-center text-zinc-500 text-sm">
              <EnvelopeSimple size={32} weight="duotone" className="mx-auto mb-2 opacity-50" />
              No tickets yet. The inbox is quiet.
            </div>
          )}
          {data.tickets.map(t => {
            const st = STATUS_STYLES[t.status] || STATUS_STYLES.open;
            return (
              <button
                key={t.id} onClick={() => openTicket(t.id)}
                className="w-full text-left surface rounded-md p-4 hover:ring-1 hover:ring-[#FFBA08]/40 transition"
                data-testid={`admin-ticket-${t.id.slice(0,8)}`}
              >
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="tactical-label" style={{ color: st.color }}>{st.label}</span>
                      <span className="tactical-label text-zinc-500">· {t.category.toUpperCase()}</span>
                      <span className="tactical-label text-zinc-600">· #{t.id.slice(0,8)}</span>
                    </div>
                    <div className="font-display font-bold text-base truncate">{t.subject}</div>
                    <div className="text-xs text-zinc-400 mt-1">{t.name} · {t.email}</div>
                    <div className="text-xs text-zinc-500 mt-1 line-clamp-2">{t.message.slice(0,200)}</div>
                  </div>
                  <div className="text-[10px] font-mono-tactical text-zinc-500 whitespace-nowrap">
                    {new Date(t.created_at).toLocaleDateString()}<br/>
                    {t.responses?.length ? `${t.responses.length} reply${t.responses.length > 1 ? "s" : ""}` : "no replies"}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AdminSupport;
