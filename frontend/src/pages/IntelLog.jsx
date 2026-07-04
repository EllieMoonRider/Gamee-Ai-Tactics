import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, ImageSquare, User, Archive } from "@phosphor-icons/react";
import "./IntelDrop.css";
import "./IntelLog.css";

const API = process.env.REACT_APP_BACKEND_URL;

const GAME_META = {
  "puzzles-conquest": { name: "Puzzles & Conquest", tag: "T-02" },
  "puzzles-survival": { name: "Puzzles & Survival", tag: "T-01" },
  "puzzles-chaos":    { name: "Puzzles & Chaos",    tag: "T-03" },
};

const CATEGORY_LABEL = {
  event: "Event",
  hero: "Hero",
  mechanic: "Mechanic",
  tip: "Tip",
  correction: "Correction",
  other: "Other",
};

export default function IntelLog() {
  const [data, setData] = useState(null);
  const [gameFilter, setGameFilter] = useState("all");

  useEffect(() => {
    const params = gameFilter !== "all" ? `?game_slug=${gameFilter}` : "";
    axios.get(`${API}/api/intel/log${params}`)
      .then(r => setData(r.data))
      .catch(() => setData({ entries: [], summary: {} }));
  }, [gameFilter]);

  if (!data) {
    return <div className="intel-drop"><div className="intel-shell"><p className="intel-loading">// SYNCING LOG…</p></div></div>;
  }

  const entries = data.entries || [];
  const summary = data.summary || {};

  return (
    <div className="intel-drop intel-log" data-testid="intel-log-page">
      <div className="intel-bg" aria-hidden="true" />
      <div className="intel-scanline" aria-hidden="true" />

      <div className="intel-shell">
        <div className="intel-header">
          <Link to="/intel-drop" className="intel-back" data-testid="log-back-drop">
            <ArrowLeft size={14} weight="bold" /> DROP MORE INTEL
          </Link>
          <span className="intel-header__stamp">// INTEL LOG · PUBLIC READ</span>
        </div>

        <h1 className="intel-log__title">Intel Log</h1>
        <p className="intel-log__desc">
          Running tally of intel already filed to CypherAI. Check here before submitting to
          avoid duplicates. Every entry has been reviewed and verified.
        </p>

        {/* Summary cards per game */}
        <div className="intel-log__summary">
          {Object.entries(GAME_META).map(([slug, meta]) => (
            <div key={slug} className="intel-log__stat">
              <span className="intel-corner tl" /><span className="intel-corner tr" />
              <span className="intel-corner bl" /><span className="intel-corner br" />
              <div className="intel-log__stat-tag">{meta.tag}</div>
              <div className="intel-log__stat-count">{summary[slug] || 0}</div>
              <div className="intel-log__stat-label">{meta.name}</div>
            </div>
          ))}
        </div>

        {/* Game filter pills */}
        <div className="intel-log__filters">
          {[["all", "ALL"], ["puzzles-conquest", "P&C"], ["puzzles-survival", "P&S"], ["puzzles-chaos", "P&Chaos"]].map(([slug, label]) => (
            <button
              key={slug}
              onClick={() => setGameFilter(slug)}
              className={`intel-log__pill ${gameFilter === slug ? "intel-log__pill--active" : ""}`}
              data-testid={`log-filter-${slug}`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Entries */}
        {entries.length === 0 ? (
          <div className="intel-log__empty">
            <Archive size={32} weight="duotone" />
            <p>No intel filed yet for this theater. Be the first!</p>
            <Link to="/intel-drop" className="intel-btn intel-btn--primary" style={{marginTop:"1rem"}}>
              DROP INTEL <span>▸</span>
            </Link>
          </div>
        ) : (
          <div className="intel-log__list" data-testid="intel-log-list">
            {entries.map(e => (
              <div key={e.reference} className="intel-log__entry" data-testid={`log-entry-${e.reference}`}>
                <span className="intel-corner tl" /><span className="intel-corner tr" />
                <span className="intel-corner bl" /><span className="intel-corner br" />
                <div className="intel-log__entry-top">
                  <span className="intel-log__entry-game">{GAME_META[e.game_slug]?.tag || e.game_slug}</span>
                  <span className="intel-log__entry-cat">{CATEGORY_LABEL[e.category] || e.category}</span>
                  {e.language && e.language !== "en" && (
                    <span className="intel-log__entry-lang">🌐 {e.language.toUpperCase()}</span>
                  )}
                </div>
                <div className="intel-log__entry-title">{e.title || "(no title)"}</div>
                <div className="intel-log__entry-meta">
                  <span><User size={11} weight="duotone" /> {e.contributor_name || "Anonymous"}</span>
                  {e.screenshot_count > 0 && (
                    <span><ImageSquare size={11} weight="duotone" /> {e.screenshot_count} screenshot{e.screenshot_count > 1 ? "s" : ""}</span>
                  )}
                  <span className="intel-log__entry-date">{new Date(e.submitted_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="intel-log__cta">
          Don&apos;t see your intel here?
          <Link to="/intel-drop">Drop it now →</Link>
        </div>
      </div>
    </div>
  );
}
