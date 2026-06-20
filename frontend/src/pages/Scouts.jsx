import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Sparkle, UploadSimple, FilmStrip, GameController, Lightning, Coins, Trophy, ArrowsClockwise } from "@phosphor-icons/react";

const KIND_META = {
  upload_game_screenshot: { icon: UploadSimple, color: "#FFBA08", title: "Upload game update screenshot", help: "Snap your latest 37Games loading screen / patch notes / event banner. Helps the community track new content." },
  watch_video: { icon: FilmStrip, color: "#10B981", title: "Watch a recommended video", help: "Open a CyphrAI-curated strategy video. Bonus credit on first daily click." },
  try_recommended_game: { icon: GameController, color: "#E63946", title: "Try a recommended game", help: "Open another 37Games title from the catalog and play 5+ min. Self-report; we trust commanders." },
  daily_login: { icon: Lightning, color: "#A1A1AA", title: "Daily login bonus", help: "Just for showing up." },
};

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
        body = formExtra.file;  // FormData
        cfg = { headers: { "Content-Type": "multipart/form-data" } };
      } else {
        const fd = new FormData();
        Object.entries(formExtra).forEach(([k, v]) => fd.append(k, v));
        body = fd;
        cfg = { headers: { "Content-Type": "multipart/form-data" } };
      }
      const { data: out } = await api.post(`/scouts/earn/${kind}`, body, cfg);
      setData(out);
      toast.success(`+${out.rewards.find(r => r.kind === kind)?.credit_per_action || ""} credit`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not record action");
    } finally { setBusy(null); }
  };

  const onScreenshot = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      toast.error("Image files only");
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
      toast.error(err?.response?.data?.detail || "Could not redeem");
    } finally { setBusy(null); }
  };

  if (!data) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <div className="max-w-5xl mx-auto px-6 py-10"><div className="h-16 shimmer rounded" /></div>
      </div>
    );
  }

  const balance = data.credits;
  const redeemable = data.redeemable_now;

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="tactical-label text-[#E63946] mb-2">// F2P PATH</div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tighter flex items-center gap-3">
              <Sparkle size={32} weight="duotone" className="text-[#E63946]" /> Tactical Scouts
            </h1>
            <p className="text-sm text-zinc-400 mt-2 max-w-xl">
              Earn credits by helping the community. <strong className="text-white">1 credit = $1</strong>. Stack <strong className="text-[#FFBA08]">3 credits</strong> to unlock 1 free Deep Dive (worth $2.99).
            </p>
          </div>
          {/* Balance card */}
          <div className="surface rounded-md p-5 min-w-[240px]" data-testid="scout-balance-card">
            <div className="tactical-label text-[#FFBA08] mb-1">// CURRENT CREDITS</div>
            <div className="flex items-baseline gap-2">
              <div className="font-display text-5xl font-black text-[#FFBA08]" data-testid="scout-balance">{balance.toFixed(2)}</div>
              <Coins size={20} weight="duotone" className="text-[#FFBA08]" />
            </div>
            <div className="mt-3 text-xs text-zinc-400">
              Redeemable now: <strong className="text-[#10B981]">{redeemable} Deep Dive{redeemable !== 1 ? "s" : ""}</strong>
            </div>
            <button
              onClick={() => redeem(1)}
              disabled={busy === "redeem" || redeemable < 1}
              className="btn-primary w-full mt-3 !py-2 text-sm"
              data-testid="scout-redeem-btn"
            >
              {busy === "redeem" ? "Unlocking…" : `Redeem 3 credits → +1 Deep Dive`}
            </button>
            {redeemable >= 2 && (
              <button
                onClick={() => redeem(redeemable)}
                disabled={busy === "redeem"}
                className="btn-outline w-full mt-2 !py-1.5 text-xs"
                data-testid="scout-redeem-all-btn"
              >
                Redeem all {redeemable} → +{redeemable} Deep Dives
              </button>
            )}
          </div>
        </div>

        {/* Rewards grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="scout-rewards">
          {data.rewards.map(r => {
            const meta = KIND_META[r.kind] || { icon: Sparkle, color: "#A1A1AA", title: r.kind, help: "" };
            const Icon = meta.icon;
            const used = r.daily_cap - r.today_remaining;
            const exhausted = r.today_remaining === 0;
            return (
              <div key={r.kind} className="surface rounded-md p-5" data-testid={`scout-card-${r.kind}`}>
                <div className="flex items-start gap-3">
                  <div className="w-11 h-11 rounded-md border flex items-center justify-center flex-shrink-0"
                       style={{ background: `${meta.color}15`, borderColor: `${meta.color}50` }}>
                    <Icon size={22} weight="duotone" style={{ color: meta.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <h3 className="font-display font-bold text-base">{meta.title}</h3>
                      <span className="tactical-label" style={{ color: meta.color }}>+{r.credit_per_action} cr</span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-1">{meta.help}</p>
                    <div className="mt-2 flex items-center justify-between text-[11px] font-mono-tactical text-zinc-500">
                      <span>TODAY: {used}/{r.daily_cap}</span>
                      <span>{r.today_remaining} REMAINING</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  {r.kind === "upload_game_screenshot" && (
                    <>
                      <input
                        ref={fileRef}
                        type="file"
                        accept="image/*"
                        onChange={onScreenshot}
                        className="hidden"
                        data-testid={`scout-upload-input-${r.kind}`}
                      />
                      <button
                        disabled={exhausted || busy === r.kind}
                        onClick={() => fileRef.current?.click()}
                        className="btn-primary w-full !py-2 text-sm"
                        data-testid={`scout-action-${r.kind}`}
                      >
                        {busy === r.kind ? "Uploading…" : exhausted ? "Cap reached · back tomorrow" : "Upload screenshot"}
                      </button>
                    </>
                  )}
                  {r.kind === "watch_video" && (
                    <button
                      disabled={exhausted || busy === r.kind}
                      onClick={() => { window.open("https://www.youtube.com/results?search_query=puzzles+and+conquest+strategy+guide", "_blank"); setTimeout(() => onWatchVideo("yt-" + Date.now()), 1200); }}
                      className="btn-primary w-full !py-2 text-sm"
                      data-testid={`scout-action-${r.kind}`}
                    >
                      {busy === r.kind ? "Recording…" : exhausted ? "Cap reached · back tomorrow" : "Watch a strategy video"}
                    </button>
                  )}
                  {r.kind === "try_recommended_game" && (
                    <select
                      disabled={exhausted || busy === r.kind}
                      defaultValue=""
                      onChange={(e) => { if (e.target.value) onTryGame(e.target.value); e.target.value = ""; }}
                      className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2 text-sm"
                      data-testid={`scout-action-${r.kind}`}
                    >
                      <option value="" disabled>{exhausted ? "Cap reached · back tomorrow" : "Pick a 37Games title you tried…"}</option>
                      <option value="puzzles-conquest">Puzzles & Conquest</option>
                      <option value="puzzles-survival">Puzzles & Survival</option>
                      <option value="puzzles-chaos">Puzzles & Chaos</option>
                      <option value="days-of-empire">Days of Empire</option>
                      <option value="infinity-kingdom">Infinity Kingdom</option>
                      <option value="legend-rise-mythic-heroes">Legend: Rise of Mythic Heroes</option>
                      <option value="soul-land-reloaded">Soul Land Reloaded</option>
                    </select>
                  )}
                  {r.kind === "daily_login" && (
                    <button
                      disabled={exhausted || busy === r.kind}
                      onClick={onDailyLogin}
                      className="btn-outline w-full !py-2 text-sm"
                      data-testid={`scout-action-${r.kind}`}
                    >
                      {busy === r.kind ? "Recording…" : exhausted ? "Claimed today ✓" : "Claim daily bonus"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* How it works */}
        <div className="surface rounded-md p-5 text-sm text-zinc-300">
          <div className="tactical-label text-[#FFBA08] mb-2">// HOW IT WORKS</div>
          <ul className="space-y-1.5 text-xs text-zinc-400">
            <li>· Earn credits by completing scout actions (caps reset daily UTC).</li>
            <li>· 3 credits = 1 Deep Dive baseline (worth $2.99 — same vision-AI quality).</li>
            <li>· Extra baselines never expire and stack with Pro.</li>
            <li>· Anti-farm: caps + image validation on screenshot uploads.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Scouts;
