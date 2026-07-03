import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import {
  Envelope, UploadSimple, Image as ImageIcon, X, ShieldCheck,
  ArrowLeft, CheckCircle, GameController, Info, Sparkle,
} from "@phosphor-icons/react";
import "./IntelDrop.css";

const API = process.env.REACT_APP_BACKEND_URL;

const GAMES = [
  { slug: "puzzles-conquest", name: "Puzzles & Conquest", tag: "T-02 · Primary Theater" },
  { slug: "puzzles-survival", name: "Puzzles & Survival", tag: "T-01 · Survival Theater" },
  { slug: "puzzles-chaos",    name: "Puzzles & Chaos",    tag: "T-03 · Chaos Theater" },
];

const CATEGORIES = [
  { key: "event",      label: "Event Guide",       help: "Ace Week, Get Week, Dragondom, Demon Incursion, etc." },
  { key: "hero",       label: "Hero / Team",       help: "Hero kits, ideal teams, tactical skill breakdowns" },
  { key: "mechanic",   label: "Game Mechanic",     help: "Combat math, formulas, hidden stats, unlocks" },
  { key: "tip",        label: "Tip / Trick",       help: "Exploits, efficiency plays, doctrine" },
  { key: "correction", label: "Correction to CypherAI", help: "CypherAI said X but the real answer is Y" },
  { key: "other",      label: "Other",             help: "Anything else you think we should know" },
];

const MAX_IMAGES = 5;
const MAX_BYTES = 5 * 1024 * 1024;

export default function IntelDrop() {
  const [game, setGame] = useState("puzzles-conquest");
  const [category, setCategory] = useState("event");
  const [text, setText] = useState("");
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [images, setImages] = useState([]); // { file, preview }
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null); // { reference, ... }

  const addFiles = (files) => {
    const arr = Array.from(files || []);
    const slots = MAX_IMAGES - images.length;
    if (slots <= 0) {
      toast.error(`Max ${MAX_IMAGES} screenshots`);
      return;
    }
    const accepted = [];
    for (const f of arr.slice(0, slots)) {
      if (!f.type.startsWith("image/")) {
        toast.error(`${f.name}: not an image`); continue;
      }
      if (f.size > MAX_BYTES) {
        toast.error(`${f.name}: exceeds 5MB`); continue;
      }
      accepted.push({ file: f, preview: URL.createObjectURL(f) });
    }
    if (accepted.length > 0) {
      const totalAfter = images.length + accepted.length;
      toast.success(
        accepted.length === 1
          ? `Screenshot attached — ${totalAfter} of ${MAX_IMAGES} total`
          : `${accepted.length} screenshots attached — ${totalAfter} of ${MAX_IMAGES} total`
      );
    }
    setImages(prev => [...prev, ...accepted]);
  };

  const removeImage = (idx) => {
    setImages(prev => {
      const clone = [...prev];
      URL.revokeObjectURL(clone[idx].preview);
      clone.splice(idx, 1);
      return clone;
    });
  };

  const submit = async (e) => {
    e.preventDefault();
    const hasText = text.trim().length >= 1;
    const hasImage = images.length > 0;
    // Accept ANY meaningful contribution: text alone, screenshot alone, or both.
    // Admin reviews everything before it reaches Cypher.
    if (!hasText && !hasImage) {
      toast.error("Please type your intel OR attach a screenshot before transmitting.");
      document.querySelector('[data-testid="intel-text"]')?.focus();
      return;
    }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("game_slug", game);
      fd.append("category", category);
      fd.append("intel_text", text.trim());
      if (name.trim())      fd.append("contributor_name", name.trim());
      if (handle.trim())    fd.append("contributor_handle", handle.trim());
      if (sourceUrl.trim()) fd.append("source_url", sourceUrl.trim());
      images.forEach(im => fd.append("images", im.file));
      const { data } = await axios.post(`${API}/api/intel/submit`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setDone(data);
      images.forEach(im => URL.revokeObjectURL(im.preview));
      setImages([]);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Transmission failed");
    } finally { setBusy(false); }
  };

  const resetForm = () => {
    setDone(null);
    setText(""); setName(""); setHandle(""); setSourceUrl("");
    setCategory("event"); setGame("puzzles-conquest");
  };

  const gameMeta = GAMES.find(g => g.slug === game);
  const catMeta  = CATEGORIES.find(c => c.key === category);

  return (
    <div className="intel-drop" data-testid="intel-drop-page">
      <div className="intel-bg" aria-hidden="true" />
      <div className="intel-scanline" aria-hidden="true" />

      <div className="intel-shell">
        {/* Header */}
        <div className="intel-header">
          <Link to="/" className="intel-back" data-testid="intel-back-home">
            <ArrowLeft size={14} weight="bold" /> TACTICAL ALLY
          </Link>
          <span className="intel-header__stamp">// CLASSIFICATION · ALLIANCE INTEL ONLY</span>
        </div>

        {/* Welcome banner (Ellie's message) */}
        <div className="intel-welcome" data-testid="intel-welcome">
          <span className="intel-corner tl" /><span className="intel-corner tr" />
          <span className="intel-corner bl" /><span className="intel-corner br" />
          <div className="intel-welcome__eyebrow">
            <ShieldCheck size={14} weight="fill" />
            OFFICIAL BRIEFING · [OTS] &amp; ALLIES
          </div>
          <h1 className="intel-welcome__title">
            Welcome, OTS &amp; Allies
          </h1>
          <p className="intel-welcome__body">
            <strong>EllieMoonRider</strong> here — thank you for helping build <strong>CypherAI</strong> into a
            Strategic Planning Guru. Every scrap of verified intel you drop here makes Cypher sharper,
            faster, and more accurate for every player who follows.
          </p>
          <p className="intel-welcome__body">
            This is where your knowledge becomes <strong>doctrine</strong>. Filed intel gets attributed
            to you (if you want), and rolls straight into Cypher&apos;s live playbook once verified.
            No account needed — just drop the intel and go.
          </p>
          <p className="intel-welcome__signoff">~ EllieMoonRider, R5 of OTS ◇ Creator of Tactical Ally ~</p>
        </div>

        {done ? (
          /* === Success state === */
          <div className="intel-success" data-testid="intel-success">
            <span className="intel-corner tl" /><span className="intel-corner tr" />
            <span className="intel-corner bl" /><span className="intel-corner br" />
            <CheckCircle size={56} weight="fill" className="intel-success__icon" />
            <h2 className="intel-success__title">INTEL RECEIVED</h2>
            <div className="intel-success__ref">
              Reference: <strong data-testid="intel-reference">{done.reference}</strong>
            </div>
            <p className="intel-success__msg">{done.message}</p>
            <p className="intel-success__msg intel-success__msg--muted">
              Screenshot this reference number if you want to follow up. We review the queue
              daily.
            </p>
            <div className="intel-success__actions">
              <button
                onClick={resetForm}
                className="intel-btn intel-btn--primary"
                data-testid="intel-submit-another"
              >
                DROP MORE INTEL <span>▸</span>
              </button>
              <Link to="/" className="intel-btn intel-btn--ghost" data-testid="intel-back-app">
                RETURN TO BASE
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* Tutorial — single condensed box, balanced text (no orphan lines) */}
            <div className="intel-tutorial" data-testid="intel-tutorial">
              <span className="intel-corner tl" /><span className="intel-corner tr" />
              <span className="intel-corner bl" /><span className="intel-corner br" />
              <div className="intel-tutorial__label">// HOW TO DROP INTEL</div>
              <ol className="intel-tutorial__list">
                <li>
                  <strong>Pick the theater</strong> — P&amp;C, P&amp;S, or P&amp;Chaos.
                </li>
                <li>
                  <strong>Drop your intel</strong> — type it out OR attach a screenshot.
                  Either works. Both is even better.
                </li>
                <li>
                  <strong>Add your name</strong> for credit (optional), then tap TRANSMIT.
                </li>
              </ol>
            </div>

            {/* The form */}
            <form onSubmit={submit} className="intel-form" data-testid="intel-form">
              {/* Game picker */}
              <div className="intel-field">
                <label className="intel-label">
                  <GameController size={14} weight="duotone" /> WHICH THEATER? <span className="intel-req">*</span>
                </label>
                <div className="intel-games">
                  {GAMES.map(g => (
                    <button
                      key={g.slug}
                      type="button"
                      onClick={() => setGame(g.slug)}
                      className={`intel-game ${game === g.slug ? "intel-game--active" : ""}`}
                      data-testid={`intel-game-${g.slug}`}
                    >
                      <span className="intel-game__tag">{g.tag}</span>
                      <span className="intel-game__name">{g.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Category */}
              <div className="intel-field">
                <label className="intel-label" htmlFor="intel-category">
                  <Info size={14} weight="duotone" /> INTEL TYPE <span className="intel-req">*</span>
                </label>
                <select
                  id="intel-category"
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="intel-select"
                  data-testid="intel-category"
                >
                  {CATEGORIES.map(c => (
                    <option key={c.key} value={c.key}>{c.label}</option>
                  ))}
                </select>
                {catMeta?.help && <div className="intel-hint">{catMeta.help}</div>}
              </div>

              {/* Intel text — OPTIONAL if a screenshot is attached */}
              <div className="intel-field">
                <label className="intel-label" htmlFor="intel-text">
                  <Sparkle size={14} weight="duotone" /> THE INTEL <span className="intel-optional">— optional if screenshot attached</span>
                </label>
                <textarea
                  id="intel-text"
                  value={text}
                  onChange={e => setText(e.target.value)}
                  placeholder={`Type your intel for ${gameMeta?.name} — or leave this blank and just attach a screenshot below. Mechanics, hero names, event schedules, exploits, source quotes — all welcome.`}
                  className="intel-textarea"
                  rows={12}
                  minLength={0}
                  maxLength={20000}
                  data-testid="intel-text"
                />
                <div className="intel-count">
                  <span>
                    {text.length} / 20,000 chars
                  </span>
                </div>
              </div>

              {/* Source URL */}
              <div className="intel-field">
                <label className="intel-label" htmlFor="intel-source">
                  <Envelope size={14} weight="duotone" /> SOURCE URL (optional)
                </label>
                <input
                  id="intel-source"
                  type="url"
                  value={sourceUrl}
                  onChange={e => setSourceUrl(e.target.value)}
                  placeholder="YouTube link, Twitch VOD, Reddit post, Discord message, dev blog…"
                  className="intel-input"
                  data-testid="intel-source"
                />
                <div className="intel-hint">Helps us verify your intel faster.</div>
              </div>

              {/* Screenshots — using <label> wrapper (bulletproof cross-browser file-input pattern).
                  Clicking the label triggers the input natively, no JS refs required. */}
              <div className="intel-field">
                <label className="intel-label">
                  <ImageIcon size={14} weight="duotone" /> SCREENSHOTS (optional · up to {MAX_IMAGES})
                </label>
                <label
                  className={`intel-upload-btn ${images.length >= MAX_IMAGES ? "intel-upload-btn--disabled" : ""}`}
                  data-testid="intel-upload-btn"
                >
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={e => { addFiles(e.target.files); e.target.value = ""; }}
                    className="intel-file-hidden"
                    disabled={images.length >= MAX_IMAGES}
                    data-testid="intel-file-input"
                  />
                  <UploadSimple size={18} weight="bold" />
                  {images.length >= MAX_IMAGES ? "MAX REACHED" : "TAP TO ATTACH SCREENSHOTS"}
                </label>
                {images.length > 0 && (
                  <>
                    <div className="intel-attached-header" data-testid="intel-attached-count">
                      ✓ {images.length} SCREENSHOT{images.length > 1 ? "S" : ""} ATTACHED
                    </div>
                    <div className="intel-previews">
                      {images.map((im, i) => (
                        <div key={i} className="intel-preview">
                          <img src={im.preview} alt="" />
                          <button
                            type="button"
                            onClick={() => removeImage(i)}
                            className="intel-preview__remove"
                            aria-label="Remove"
                            data-testid={`intel-preview-remove-${i}`}
                          >
                            <X size={12} weight="bold" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </>
                )}
                <div className="intel-hint">PNG · JPEG · WebP · GIF · max 5MB each</div>
              </div>

              {/* Contributor credit */}
              <div className="intel-credit">
                <div className="intel-credit__label">// CREDIT (optional but appreciated)</div>
                <div className="intel-credit__grid">
                  <div>
                    <label className="intel-label--sm" htmlFor="intel-name">YOUR NAME / HANDLE</label>
                    <input
                      id="intel-name"
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      placeholder="e.g., EllieMoonRider"
                      className="intel-input"
                      maxLength={80}
                      data-testid="intel-name"
                    />
                  </div>
                  <div>
                    <label className="intel-label--sm" htmlFor="intel-handle">DISCORD / GAMER TAG</label>
                    <input
                      id="intel-handle"
                      type="text"
                      value={handle}
                      onChange={e => setHandle(e.target.value)}
                      placeholder="e.g., ellie#1234"
                      className="intel-input"
                      maxLength={80}
                      data-testid="intel-handle"
                    />
                  </div>
                </div>
                <div className="intel-hint">
                  Leave blank to stay anonymous. Otherwise, we&apos;ll credit you in the dossier when filed.
                </div>
              </div>

              {/* Submit — always visually enabled, requirements validated on click for
                  clear feedback instead of a dead-looking disabled button */}
              <div className="intel-submit-row">
                {/* Readiness indicator — clear visual confirmation that content is queued */}
                <div
                  className={`intel-readiness ${(text.trim().length >= 1 || images.length > 0) ? "intel-readiness--ready" : "intel-readiness--empty"}`}
                  data-testid="intel-readiness"
                >
                  {(text.trim().length >= 1 || images.length > 0) ? (
                    <>
                      ✓ READY TO TRANSMIT ·{" "}
                      {text.trim().length >= 1 && <span>{text.length} chars</span>}
                      {text.trim().length >= 1 && images.length > 0 && " · "}
                      {images.length > 0 && <span>{images.length} screenshot{images.length > 1 ? "s" : ""}</span>}
                    </>
                  ) : (
                    <>◇ Type intel or attach a screenshot to enable transmission ◇</>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={busy}
                  className="intel-btn intel-btn--primary intel-btn--big"
                  data-testid="intel-submit-btn"
                >
                  {busy ? "TRANSMITTING…" : <>TRANSMIT INTEL <span>▸</span></>}
                </button>
                <p className="intel-tos">
                  By submitting, you confirm this intel is your own or from a public source, and does
                  not violate 37Games&apos; Terms of Service.
                </p>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
