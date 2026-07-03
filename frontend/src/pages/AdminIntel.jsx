import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  ArrowLeft, CheckCircle, XCircle, Archive, Sparkle,
  Envelope, ImageSquare, Calendar as CalIcon, User, LinkSimple,
} from "@phosphor-icons/react";
import "./IntelDrop.css";
import "./AdminIntel.css";

const API = process.env.REACT_APP_BACKEND_URL;

const CATEGORY_LABEL = {
  event: "Event Guide",
  hero: "Hero / Team",
  mechanic: "Game Mechanic",
  tip: "Tip / Trick",
  correction: "Correction",
  other: "Other",
};

const GAME_LABEL = {
  "puzzles-conquest": "P&C",
  "puzzles-survival": "P&S",
  "puzzles-chaos":    "P&Chaos",
};

const STATUS_STYLE = {
  pending:  { color: "#FFBA08", label: "PENDING" },
  approved: { color: "#00FF80", label: "APPROVED" },
  rejected: { color: "#FF3366", label: "REJECTED" },
  filed:    { color: "#00BFFF", label: "FILED" },
};

export default function AdminIntel() {
  const { user, loading } = useAuth();
  const [allowed, setAllowed] = useState(null); // null=checking, true, false
  const [data, setData] = useState(null);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [gameFilter, setGameFilter] = useState("all");
  const [selected, setSelected] = useState(null);
  const [reviewNote, setReviewNote] = useState("");
  const [busy, setBusy] = useState(null);

  // Admin gate check
  useEffect(() => {
    if (loading) return;
    if (!user) { setAllowed(false); return; }
    api.get("/support/admin/check")
      .then(r => setAllowed(!!r.data?.is_admin))
      .catch(() => setAllowed(false));
  }, [user, loading]);

  const load = async () => {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status_filter", statusFilter);
    if (gameFilter && gameFilter !== "all") params.set("game_slug", gameFilter);
    try {
      const r = await api.get(`/intel/submissions?${params}`);
      setData(r.data);
    } catch (err) {
      toast.error("Failed to load intel queue");
    }
  };

  useEffect(() => {
    if (allowed) load();
  }, [allowed, statusFilter, gameFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const updateStatus = async (sid, newStatus) => {
    setBusy(sid);
    try {
      await api.patch(`/intel/submissions/${sid}`, {
        status: newStatus,
        review_notes: reviewNote || undefined,
      });
      toast.success(`Marked ${newStatus.toUpperCase()}`);
      setReviewNote("");
      setSelected(null);
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Update failed");
    } finally { setBusy(null); }
  };

  if (loading || allowed === null) {
    return <div className="intel-drop"><div className="intel-shell"><p className="intel-loading">// SYNCING TELEMETRY…</p></div></div>;
  }
  if (!allowed) {
    return (
      <div className="intel-drop">
        <div className="intel-shell">
          <p className="intel-forbidden">// ACCESS DENIED · ADMIN CLEARANCE REQUIRED</p>
          <Link to="/dashboard" className="intel-btn intel-btn--ghost" style={{ marginTop: "1rem" }}>
            RETURN TO COMMAND CENTER
          </Link>
        </div>
      </div>
    );
  }

  const submissions = data?.submissions || [];
  const counts = data?.counts || {};

  return (
    <div className="intel-drop admin-intel" data-testid="admin-intel-page">
      <div className="intel-bg" aria-hidden="true" />
      <div className="intel-scanline" aria-hidden="true" />

      <div className="intel-shell admin-intel__shell">
        {/* Header */}
        <div className="intel-header">
          <Link to="/dashboard" className="intel-back" data-testid="admin-back-dashboard">
            <ArrowLeft size={14} weight="bold" /> COMMAND CENTER
          </Link>
          <span className="intel-header__stamp">// INTEL REVIEW QUEUE · ADMIN CONSOLE</span>
        </div>

        <h1 className="admin-intel__title">
          <Sparkle size={22} weight="duotone" /> Intel Review Queue
        </h1>
        <p className="admin-intel__desc">
          Every intel submission from [OTS] Outlanders and allies lands here. Review, approve, mark
          as filed once you or Lt. Atlas has moved it into the live dossier.
        </p>

        {/* Stat counters */}
        <div className="admin-intel__stats" data-testid="admin-intel-counts">
          <StatCell label="PENDING" value={counts.pending || 0} color="#FFBA08" testid="stat-pending" />
          <StatCell label="APPROVED" value={counts.approved || 0} color="#00FF80" testid="stat-approved" />
          <StatCell label="FILED" value={counts.filed || 0} color="#00BFFF" testid="stat-filed" />
          <StatCell label="REJECTED" value={counts.rejected || 0} color="#FF3366" testid="stat-rejected" />
          <StatCell label="TOTAL" value={counts.total || 0} color="#cfffe1" testid="stat-total" />
        </div>

        {/* Filters */}
        <div className="admin-intel__filters">
          <div className="admin-intel__filter-group">
            <span className="admin-intel__filter-label">STATUS</span>
            <div className="admin-intel__filter-pills">
              {["pending", "approved", "filed", "rejected", "all"].map(s => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`admin-intel__pill ${statusFilter === s ? "admin-intel__pill--active" : ""}`}
                  data-testid={`filter-status-${s}`}
                >
                  {s.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div className="admin-intel__filter-group">
            <span className="admin-intel__filter-label">GAME</span>
            <div className="admin-intel__filter-pills">
              {["all", "puzzles-conquest", "puzzles-survival", "puzzles-chaos"].map(g => (
                <button
                  key={g}
                  onClick={() => setGameFilter(g)}
                  className={`admin-intel__pill ${gameFilter === g ? "admin-intel__pill--active" : ""}`}
                  data-testid={`filter-game-${g}`}
                >
                  {g === "all" ? "ALL" : GAME_LABEL[g]}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Submissions list */}
        <div className="admin-intel__list" data-testid="admin-intel-list">
          {submissions.length === 0 ? (
            <div className="admin-intel__empty">
              <Archive size={32} weight="duotone" />
              <p>No submissions match these filters.</p>
            </div>
          ) : submissions.map(s => (
            <div
              key={s.id}
              className={`admin-intel__card ${selected === s.id ? "admin-intel__card--open" : ""}`}
              data-testid={`intel-card-${s.reference}`}
            >
              <span className="intel-corner tl" /><span className="intel-corner tr" />
              <span className="intel-corner bl" /><span className="intel-corner br" />

              <div className="admin-intel__card-head">
                <div className="admin-intel__card-meta">
                  <span className="admin-intel__ref">{s.reference}</span>
                  <span
                    className="admin-intel__status"
                    style={{ color: STATUS_STYLE[s.status]?.color, borderColor: STATUS_STYLE[s.status]?.color }}
                  >
                    {STATUS_STYLE[s.status]?.label || s.status}
                  </span>
                  <span className="admin-intel__game">{GAME_LABEL[s.game_slug] || s.game_slug}</span>
                  <span className="admin-intel__category">{CATEGORY_LABEL[s.category] || s.category}</span>
                </div>
                <button
                  onClick={() => setSelected(selected === s.id ? null : s.id)}
                  className="admin-intel__toggle"
                  data-testid={`toggle-${s.reference}`}
                >
                  {selected === s.id ? "COLLAPSE" : "EXPAND"} ▸
                </button>
              </div>

              <div className="admin-intel__card-sub">
                <span><User size={12} weight="duotone" /> {s.contributor_name || "Anonymous"}{s.contributor_handle ? ` · ${s.contributor_handle}` : ""}</span>
                <span><CalIcon size={12} weight="duotone" /> {new Date(s.submitted_at).toLocaleString()}</span>
                {s.image_refs?.length > 0 && <span><ImageSquare size={12} weight="duotone" /> {s.image_refs.length} screenshot{s.image_refs.length > 1 ? "s" : ""}</span>}
                {s.source_url && <span><LinkSimple size={12} weight="duotone" /> source linked</span>}
              </div>

              {selected === s.id && (
                <div className="admin-intel__body" data-testid={`body-${s.reference}`}>
                  <div className="admin-intel__intel-text">{s.intel_text}</div>

                  {s.source_url && (
                    <div className="admin-intel__source">
                      <span className="admin-intel__body-label">SOURCE:</span>
                      <a href={s.source_url} target="_blank" rel="noreferrer noopener" className="admin-intel__source-link">
                        {s.source_url}
                      </a>
                    </div>
                  )}

                  {s.image_refs?.length > 0 && (
                    <div className="admin-intel__images">
                      {s.image_refs.map((ref) => (
                        <a
                          key={ref.file_id}
                          href={`${API}/api/intel/submissions/${s.id}/image/${ref.file_id}`}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="admin-intel__thumb"
                        >
                          <img
                            src={`${API}/api/intel/submissions/${s.id}/image/${ref.file_id}`}
                            alt={ref.name}
                            loading="lazy"
                          />
                        </a>
                      ))}
                    </div>
                  )}

                  {s.status === "pending" && (
                    <>
                      <textarea
                        value={reviewNote}
                        onChange={e => setReviewNote(e.target.value)}
                        placeholder="Optional review notes (why approved / rejected / edits made)…"
                        className="intel-textarea admin-intel__note"
                        rows={3}
                        data-testid={`note-${s.reference}`}
                      />
                      <div className="admin-intel__actions">
                        <button
                          onClick={() => updateStatus(s.id, "approved")}
                          disabled={busy === s.id}
                          className="intel-btn admin-intel__btn admin-intel__btn--approve"
                          data-testid={`approve-${s.reference}`}
                        >
                          <CheckCircle size={14} weight="bold" /> APPROVE
                        </button>
                        <button
                          onClick={() => updateStatus(s.id, "filed")}
                          disabled={busy === s.id}
                          className="intel-btn admin-intel__btn admin-intel__btn--filed"
                          data-testid={`file-${s.reference}`}
                        >
                          <Archive size={14} weight="bold" /> MARK FILED
                        </button>
                        <button
                          onClick={() => updateStatus(s.id, "rejected")}
                          disabled={busy === s.id}
                          className="intel-btn admin-intel__btn admin-intel__btn--reject"
                          data-testid={`reject-${s.reference}`}
                        >
                          <XCircle size={14} weight="bold" /> REJECT
                        </button>
                      </div>
                    </>
                  )}

                  {s.status !== "pending" && (
                    <div className="admin-intel__review-meta">
                      <span>Reviewed by <strong>{s.reviewer_email || "—"}</strong></span>
                      <span>on {s.reviewed_at ? new Date(s.reviewed_at).toLocaleString() : "—"}</span>
                      {s.review_notes && <div className="admin-intel__review-notes">📝 {s.review_notes}</div>}
                      {(s.status === "approved" || s.status === "rejected") && (
                        <div className="admin-intel__reopen">
                          <button
                            onClick={() => updateStatus(s.id, "pending")}
                            disabled={busy === s.id}
                            className="intel-btn intel-btn--ghost admin-intel__btn"
                          >
                            REOPEN
                          </button>
                          {s.status === "approved" && (
                            <button
                              onClick={() => updateStatus(s.id, "filed")}
                              disabled={busy === s.id}
                              className="intel-btn admin-intel__btn admin-intel__btn--filed"
                            >
                              <Archive size={14} weight="bold" /> MARK FILED
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Public portal link callout */}
        <div className="admin-intel__portal-cta">
          <Envelope size={16} weight="duotone" />
          Share the drop portal with your alliance:&nbsp;
          <Link to="/intel-drop" target="_blank" rel="noreferrer">/intel-drop</Link>
        </div>
      </div>
    </div>
  );
}

function StatCell({ label, value, color, testid }) {
  return (
    <div className="admin-intel__stat" style={{ borderColor: color }} data-testid={testid}>
      <span className="intel-corner tl" style={{ borderColor: color }} />
      <span className="intel-corner tr" style={{ borderColor: color }} />
      <span className="intel-corner bl" style={{ borderColor: color }} />
      <span className="intel-corner br" style={{ borderColor: color }} />
      <div className="admin-intel__stat-value" style={{ color }}>{value}</div>
      <div className="admin-intel__stat-label" style={{ color }}>{label}</div>
    </div>
  );
}
