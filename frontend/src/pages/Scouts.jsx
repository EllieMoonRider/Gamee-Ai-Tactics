import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  Sparkle, UploadSimple, FilmStrip, GameController, Lightning,
  Coins, ArrowLeft, ShieldStar, Target, LockKey,
} from "@phosphor-icons/react";
import "../components/CommandCenter.css";
import "./Scouts.css";

const KIND_META = {
  upload_game_screenshot: {
    icon: UploadSimple,
    codename: "OP-01",
    title: "Field Recon Upload",
    help: "Transmit a screenshot of a live 37Games patch note, event banner, or loading screen. Intel expands the tactical database.",
  },
  watch_video: {
    icon: FilmStrip,
    codename: "OP-02",
    title: "Signal Interception",
    help: "Review a CypherAI-curated strategy broadcast from the intel network. Bonus credit on first daily interception.",
  },
  try_recommended_game: {
    icon: GameController,
    codename: "OP-03",
    title: "Adjacent Theater Sweep",
    help: "Deploy into another 37Games title for 5+ minutes. Report back with the theater engaged.",
  },
  daily_login: {
    icon: Lightning,
    codename: "OP-04",
    title: "Daily Check-In",
    help: "Signal your presence at the Command Center. Small credit, guaranteed daily.",
  },
};

// Scope-reduced to the 3 active theaters (Feb 2026)
const ADJACENT_THEATERS = [
  { slug: "puzzles-conquest", name: "Puzzles & Conquest" },
  { slug: "puzzles-survival", name: "Puzzles & Survival" },
  { slug: "puzzles-chaos",    name: "Puzzles & Chaos" },
];

const Scouts = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(null);
  const fileRef = useRef(null);

  const refresh = async () => {
    const r = await api.get("/scouts/me");
    setData(r.data);
  };
  useEffect(() => { refresh(); }, []);

  const earn = async (kind, formExtra = {}) => {
    setBusy(kind);
    try {
      let body;
      let cfg = {};
      if (kind === "upload_game_screenshot") {
        body = formExtra.file;
        cfg = { headers: { "Content-Type": "multipart/form-data" } };
      } else {
        const fd = new FormData();
        Object.entries(formExtra).forEach(([k, v]) => fd.append(k, v));
        body = fd;
        cfg = { headers: { "Content-Type": "multipart/form-data" } };
      }
      const { data: out } = await api.post(`/scouts/earn/${kind}`, body, cfg);
      setData(out);
      const reward = out.rewards.find(r => r.kind === kind);
      toast.success(`+${reward?.credit_per_action || ""} credit locked in`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Transmission failed");
    } finally { setBusy(null); }
  };

  const onScreenshot = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      toast.error("Image intel only");
      return;
    }
    const fd = new FormData();
    fd.append("file", f);
    await earn("upload_game_screenshot", { file: fd });
    if (fileRef.current) fileRef.current.value = "";
  };

  const onWatchVideo = (video_id) => earn("watch_video", { video_id });
  const onTryGame = (game_tried) => earn("try_recommended_game", { game_tried });
  const onDailyLogin = () => earn("daily_login");

  const redeem = async (units) => {
    setBusy("redeem");
    try {
      await api.post("/scouts/redeem", { units });
      toast.success(`+${units} Deep Dive baseline${units > 1 ? "s" : ""} unlocked`);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Redemption failed");
    } finally { setBusy(null); }
  };

  if (!data) {
    return (
      <div className="scout-dashboard scout-dashboard--loading" data-testid="scout-loading">
        <div className="scout-shell">
          <div className="scout-loading-bar" />
          <p className="scout-loading-txt">// SCOUT NETWORK · SYNCING TELEMETRY…</p>
        </div>
      </div>
    );
  }

  const balance = data.credits;
  const redeemable = data.redeemable_now;
  const progressPct = Math.min(100, (balance / data.redeem_cost) * 100);

  return (
    <div className="scout-dashboard" data-testid="scout-dashboard">
      {/* Ambient grid background — same neon-green language as the Command Center */}
      <div className="scout-bg" aria-hidden="true" />
      <div className="scout-scanline" aria-hidden="true" />

      <div className="scout-shell">
        {/* Header rail — back link + name */}
        <div className="scout-header">
          <Link to="/dashboard" className="scout-back" data-testid="scout-back-dashboard">
            <ArrowLeft size={14} weight="bold" /> COMMAND CENTER
          </Link>
          <span className="scout-header__ident">
            OPERATOR: <strong>{user?.username || "COMMANDER"}</strong>
          </span>
        </div>

        {/* Mission briefing headline */}
        <div className="scout-briefing">
          <div className="scout-briefing__label">// TACTICAL SCOUT PROGRAM · F2P CREDIT LOOP</div>
          <h1 className="scout-briefing__title">
            <Sparkle size={22} weight="duotone" /> Scout Network
          </h1>
          <p className="scout-briefing__desc">
            Complete field operations to earn credits. Stack <strong>3 credits</strong> to
            unlock <strong>1 Deep Dive baseline</strong> — same vision-AI analysis Pro operators
            pay $2.99 for. Caps reset daily at 00:00 UTC.
          </p>
        </div>

        {/* Two-column top bar — balance ledger + progress vault */}
        <div className="scout-topbar">
          {/* Ledger */}
          <div className="scout-ledger" data-testid="scout-balance-card">
            <span className="scout-corner tl" />
            <span className="scout-corner tr" />
            <span className="scout-corner bl" />
            <span className="scout-corner br" />
            <div className="scout-ledger__label">// CURRENT CREDITS</div>
            <div className="scout-ledger__balance" data-testid="scout-balance">
              {balance.toFixed(2)}
              <Coins size={22} weight="duotone" />
            </div>
            <div className="scout-ledger__sub">
              REDEEMABLE: <strong>{redeemable}</strong> Deep Dive{redeemable !== 1 ? "s" : ""}
            </div>
            <div className="scout-ledger__actions">
              <button
                onClick={() => redeem(1)}
                disabled={busy === "redeem" || redeemable < 1}
                className="scout-btn scout-btn--primary"
                data-testid="scout-redeem-btn"
              >
                {busy === "redeem" ? "UNLOCKING…" : "REDEEM 3 CR → +1 DEEP DIVE"}
              </button>
              {redeemable >= 2 && (
                <button
                  onClick={() => redeem(redeemable)}
                  disabled={busy === "redeem"}
                  className="scout-btn scout-btn--ghost"
                  data-testid="scout-redeem-all-btn"
                >
                  REDEEM ALL ({redeemable})
                </button>
              )}
            </div>
          </div>

          {/* Vault progress */}
          <div className="scout-vault">
            <span className="scout-corner tl" />
            <span className="scout-corner tr" />
            <span className="scout-corner bl" />
            <span className="scout-corner br" />
            <div className="scout-vault__label">// NEXT UNLOCK PROGRESS</div>
            <div className="scout-vault__meta">
              <span>
                {(balance % data.redeem_cost).toFixed(2)} / {data.redeem_cost.toFixed(2)} cr
              </span>
              <span className="scout-vault__pct">{progressPct.toFixed(0)}%</span>
            </div>
            <div className="scout-vault__bar">
              <div
                className="scout-vault__fill"
                style={{ width: `${(balance % data.redeem_cost) / data.redeem_cost * 100}%` }}
              />
              <div className="scout-vault__tick" style={{ left: "0%" }} />
              <div className="scout-vault__tick" style={{ left: "33.33%" }} />
              <div className="scout-vault__tick" style={{ left: "66.66%" }} />
              <div className="scout-vault__tick" style={{ left: "100%" }} />
            </div>
            <div className="scout-vault__desc">
              Each Deep Dive vault requires <strong>3.00</strong> credits. Chain multiple ops
              per day — caps refresh at reset.
            </div>
          </div>
        </div>

        {/* Operations grid */}
        <div className="scout-ops-label">// AVAILABLE FIELD OPERATIONS · {data.rewards.length} ACTIVE</div>
        <div className="scout-ops" data-testid="scout-rewards">
          {data.rewards.map(r => {
            const meta = KIND_META[r.kind] || { icon: Sparkle, codename: "OP-??", title: r.kind, help: "" };
            const Icon = meta.icon;
            const used = r.daily_cap - r.today_remaining;
            const exhausted = r.today_remaining === 0;
            return (
              <div
                key={r.kind}
                className={`scout-op ${exhausted ? "scout-op--locked" : ""}`}
                data-testid={`scout-card-${r.kind}`}
              >
                <span className="scout-corner tl" />
                <span className="scout-corner tr" />
                <span className="scout-corner bl" />
                <span className="scout-corner br" />

                <div className="scout-op__header">
                  <span className="scout-op__codename">{meta.codename}</span>
                  <span className="scout-op__reward">+{r.credit_per_action} CR</span>
                </div>

                <div className="scout-op__icon">
                  <Icon size={28} weight="duotone" />
                </div>

                <h3 className="scout-op__title">{meta.title}</h3>
                <p className="scout-op__help">{meta.help}</p>

                <div className="scout-op__cap">
                  <span>DAILY CAP</span>
                  <span className="scout-op__cap-count">
                    {used}/{r.daily_cap}
                  </span>
                </div>
                <div className="scout-op__cap-bar">
                  <div
                    className="scout-op__cap-fill"
                    style={{ width: `${(used / r.daily_cap) * 100}%` }}
                  />
                </div>

                <div className="scout-op__action">
                  {r.kind === "upload_game_screenshot" && (
                    <>
                      <input
                        ref={fileRef}
                        type="file"
                        accept="image/*"
                        onChange={onScreenshot}
                        className="scout-file-hidden"
                        data-testid={`scout-upload-input-${r.kind}`}
                      />
                      <button
                        disabled={exhausted || busy === r.kind}
                        onClick={() => fileRef.current?.click()}
                        className="scout-btn scout-btn--primary scout-btn--full"
                        data-testid={`scout-action-${r.kind}`}
                      >
                        {busy === r.kind ? "TRANSMITTING…" : exhausted ? <><LockKey size={12} weight="bold" /> CAP REACHED</> : <>UPLOAD INTEL <span>▸</span></>}
                      </button>
                    </>
                  )}
                  {r.kind === "watch_video" && (
                    <button
                      disabled={exhausted || busy === r.kind}
                      onClick={() => {
                        window.open("https://www.youtube.com/results?search_query=puzzles+and+conquest+strategy+guide", "_blank");
                        setTimeout(() => onWatchVideo("yt-" + Date.now()), 1200);
                      }}
                      className="scout-btn scout-btn--primary scout-btn--full"
                      data-testid={`scout-action-${r.kind}`}
                    >
                      {busy === r.kind ? "LOGGING…" : exhausted ? <><LockKey size={12} weight="bold" /> CAP REACHED</> : <>INTERCEPT SIGNAL <span>▸</span></>}
                    </button>
                  )}
                  {r.kind === "try_recommended_game" && (
                    <select
                      disabled={exhausted || busy === r.kind}
                      defaultValue=""
                      onChange={(e) => { if (e.target.value) onTryGame(e.target.value); e.target.value = ""; }}
                      className="scout-select"
                      data-testid={`scout-action-${r.kind}`}
                    >
                      <option value="" disabled>
                        {exhausted ? "CAP REACHED · BACK TOMORROW" : "SELECT ADJACENT THEATER…"}
                      </option>
                      {ADJACENT_THEATERS.map(t => (
                        <option key={t.slug} value={t.slug}>{t.name}</option>
                      ))}
                    </select>
                  )}
                  {r.kind === "daily_login" && (
                    <button
                      disabled={exhausted || busy === r.kind}
                      onClick={onDailyLogin}
                      className="scout-btn scout-btn--ghost scout-btn--full"
                      data-testid={`scout-action-${r.kind}`}
                    >
                      {busy === r.kind ? "LOGGING…" : exhausted ? <>✓ CLAIMED TODAY</> : <>CLAIM CHECK-IN <span>▸</span></>}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Doctrine block */}
        <div className="scout-doctrine">
          <span className="scout-corner tl" />
          <span className="scout-corner tr" />
          <span className="scout-corner bl" />
          <span className="scout-corner br" />
          <div className="scout-doctrine__label">// SCOUT PROGRAM DOCTRINE</div>
          <ul>
            <li>
              <Target size={14} weight="duotone" /> Complete ops to bank credits.
              Caps hard-reset daily at 00:00 UTC.
            </li>
            <li>
              <ShieldStar size={14} weight="duotone" /> 3 credits = 1 Deep Dive baseline.
              Extra baselines never expire and stack alongside Pro allowance.
            </li>
            <li>
              <Sparkle size={14} weight="duotone" /> Anti-farm: server-side caps + image
              validation on screenshot uploads. Try to game it and Cypher will notice.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Scouts;
