import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { CheckCircle, Lightning, Stack, ShieldCheck, Coins, GameController, ChatsCircle, Sparkle } from "@phosphor-icons/react";

const Pricing = () => {
  const { user } = useAuth();
  const nav = useNavigate();
  const [packages, setPackages] = useState([]);
  const [quota, setQuota] = useState(null);
  const [loading, setLoading] = useState(null);

  useEffect(() => {
    api.get("/billing/packages").then(r => setPackages(r.data));
    if (user) api.get("/billing/quota").then(r => setQuota(r.data));
  }, [user]);

  const buy = async (pkgId) => {
    if (!user) { nav("/auth"); return; }
    setLoading(pkgId);
    try {
      const { data } = await api.post("/billing/checkout", {
        package_id: pkgId,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Checkout failed");
    } finally { setLoading(null); }
  };

  return (
    <div className="command-center min-h-screen">
      <Navbar />
      <div className="max-w-6xl mx-auto px-6 py-14">
        <div className="text-center mb-12">
          <div className="tactical-label text-[#FF6B00] mb-2">// PRICING TIERS</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">Pick your loadout</h1>
          <p className="text-zinc-400 mt-3 max-w-2xl mx-auto">
            CypherAI Chat, Optimizer, Guides, and Daily Planner are <strong className="text-[#FFAA33]">free forever</strong>. Deep Dive vision analyses & Alliance Chat are paid — pricing scales with how many games and how big your alliance is.
          </p>
          {quota && quota.plan === "pro" && (
            <div className="mt-4 inline-flex items-center gap-2 surface px-4 py-2 rounded text-sm" data-testid="pricing-current-plan">
              <ShieldCheck size={16} className="text-[#FFAA33]" />
              You&apos;re on <strong className="text-[#FFAA33]">Pro</strong> · {quota.total_baselines_available} analyses available · {quota.pro_games?.length || 0}/{quota.pro_game_slots} game slots used
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* FREE TIER */}
          <div className="surface rounded-md p-7 flex flex-col" data-testid="tier-free">
            <div className="tactical-label text-zinc-500 mb-2">// TIER 01</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Recruit</h2>
            <div className="mt-3 mb-5">
              <span className="font-display text-4xl font-black">$0</span>
              <span className="text-zinc-500"> / forever</span>
            </div>
            <ul className="space-y-2.5 text-sm text-zinc-300 flex-1">
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> CypherAI Chat (30 msgs/min)</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Build Optimizer (10/min)</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> 13+ curated Guides</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Daily Planner across 11 titles</li>
              <li className="flex gap-2"><Sparkle size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> <strong>Tactical Scouts</strong> — earn Deep Dives free</li>
            </ul>
            <button onClick={() => nav(user ? "/dashboard" : "/auth")} className="btn-outline mt-6 w-full" data-testid="tier-free-cta">
              {user ? "Open Command Center" : "Enlist for free"}
            </button>
          </div>

          {/* PRO */}
          <div className="surface rounded-md p-7 flex flex-col relative ring-2 ring-[#FF6B00]/40 -translate-y-1" data-testid="tier-pro">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#FF6B00] text-white text-[10px] font-mono-tactical tracking-widest px-3 py-1 rounded">RECOMMENDED</span>
            <div className="tactical-label text-[#FF6B00] mb-2">// TIER 02 · PRO</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Tactical Ally Pro</h2>
            <div className="mt-3 mb-5">
              <span className="font-display text-4xl font-black text-[#FFBA08]">$4.99</span>
              <span className="text-zinc-500"> / month</span>
            </div>
            <ul className="space-y-2.5 text-sm text-zinc-300 flex-1">
              <li className="flex gap-2"><GameController size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> <strong>Full access for 2 games</strong> (your choice)</li>
              <li className="flex gap-2"><Lightning size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> 2 Deep Dive baselines / month</li>
              <li className="flex gap-2"><Stack size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> Unlimited Building Blocks per baseline</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Everything in Recruit</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Shareable Deep Dive links</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Add more games anytime · $0.99/ea</li>
            </ul>
            <button onClick={() => buy("subscription_monthly")} disabled={loading === "subscription_monthly"} className="btn-primary mt-6 w-full" data-testid="tier-pro-cta">
              {loading === "subscription_monthly" ? "Opening checkout…" : "Subscribe — $4.99/mo"}
            </button>
          </div>

          {/* TOPUP */}
          <div className="surface rounded-md p-7 flex flex-col" data-testid="tier-topup">
            <div className="tactical-label text-zinc-500 mb-2">// TIER 03 · ONE-SHOT</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Single Deep Dive</h2>
            <div className="mt-3 mb-5">
              <span className="font-display text-4xl font-black">$2.99</span>
              <span className="text-zinc-500"> / one-time</span>
            </div>
            <ul className="space-y-2.5 text-sm text-zinc-300 flex-1">
              <li className="flex gap-2"><Coins size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> <strong>1 Deep Dive baseline</strong> — ANY game</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> No subscription, no commitment</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Never expires — use it any time</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#FFAA33] mt-0.5 flex-shrink-0" /> Stacks on top of Pro plan</li>
            </ul>
            <button onClick={() => buy("topup_analysis")} disabled={loading === "topup_analysis"} className="btn-outline mt-6 w-full" data-testid="tier-topup-cta">
              {loading === "topup_analysis" ? "Opening checkout…" : "Buy one — $2.99"}
            </button>
          </div>
        </div>

        {/* ADD-ONS */}
        <div className="mt-10">
          <div className="tactical-label text-zinc-500 mb-3">// ADD-ONS · STACK AS YOU GROW</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Extra Game */}
            <div className="surface rounded-md p-6 ring-1 ring-[#FFBA08]/30" data-testid="tier-extra-game">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-md bg-[#FFBA08]/10 border border-[#FFBA08]/30 flex items-center justify-center flex-shrink-0">
                  <GameController size={24} weight="duotone" className="text-[#FFBA08]" />
                </div>
                <div className="flex-1">
                  <div className="tactical-label text-[#FFBA08] mb-1">// EXTRA GAME SLOT</div>
                  <h3 className="font-display text-xl font-bold tracking-tight">Add a game — <span className="text-[#FFBA08]">$0.99/mo</span></h3>
                  <p className="text-xs text-zinc-400 mt-2">
                    Pro comes with 2 games. Play a 3rd, 4th, 5th title? Stack one slot per extra game. Each slot adds full Pro features for that title.
                  </p>
                  <button
                    onClick={() => buy("extra_game_monthly")}
                    disabled={loading === "extra_game_monthly" || (quota && !quota.subscription_active)}
                    className="btn-primary !py-2 !px-4 text-sm mt-3"
                    data-testid="tier-extra-game-cta"
                  >
                    {loading === "extra_game_monthly" ? "Opening checkout…" : (quota && !quota.subscription_active) ? "Get Pro first" : "Add a Game — $0.99/mo"}
                  </button>
                </div>
              </div>
            </div>

            {/* Alliance Chat (per member) */}
            <div className="surface rounded-md p-6 ring-1 ring-[#FFAA33]/30" data-testid="tier-toc-addon">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-md bg-[#FFAA33]/10 border border-[#FFAA33]/30 flex items-center justify-center flex-shrink-0">
                  <ChatsCircle size={24} weight="duotone" className="text-[#FFAA33]" />
                </div>
                <div className="flex-1">
                  <div className="tactical-label text-[#FFAA33] mb-1">// ALLIANCE CHAT · PER MEMBER</div>
                  <h3 className="font-display text-xl font-bold tracking-tight">Operations Center — <span className="text-[#FFAA33]">$0.99/mo</span></h3>
                  <p className="text-xs text-zinc-400 mt-2">
                    Each member pays their own seat. Unlocks alliance chat rooms, share Deep Dives & Battle Reports, ask CypherAI in-room. Built for 60-active-member alliances.
                  </p>
                  <button
                    onClick={() => buy("toc_addon_monthly")}
                    disabled={loading === "toc_addon_monthly" || !quota || (quota && !quota.subscription_active) || (quota && quota.toc_active)}
                    className="btn-primary !py-2 !px-4 text-sm mt-3"
                    data-testid="tier-toc-cta"
                  >
                    {!quota
                      ? "…"
                      : loading === "toc_addon_monthly"
                        ? "Opening checkout…"
                        : quota.toc_active
                          ? "Active ✓"
                          : !quota.subscription_active
                            ? "Get Pro first"
                            : "Join Chat — $0.99/mo"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* SCOUTS F2P */}
        <div className="mt-8 surface rounded-md p-6 ring-1 ring-dashed ring-[#FF6B00]/30" data-testid="scouts-callout">
          <div className="flex items-start gap-4 flex-wrap">
            <div className="w-12 h-12 rounded-md bg-[#FF6B00]/10 border border-[#FF6B00]/30 flex items-center justify-center flex-shrink-0">
              <Sparkle size={24} weight="duotone" className="text-[#FF6B00]" />
            </div>
            <div className="flex-1 min-w-[240px]">
              <div className="tactical-label text-[#FF6B00] mb-1">// F2P PATH · TACTICAL SCOUTS</div>
              <h3 className="font-display text-xl font-bold tracking-tight">No wallet? Earn Deep Dives free.</h3>
              <p className="text-xs text-zinc-400 mt-2 max-w-xl">
                Upload game-update screenshots · try recommended games · watch strategy videos. Earn 1 credit = $1 value. 3 credits = 1 free Deep Dive. F2P engagement loop with real reward.
              </p>
            </div>
            <Link to={user ? "/scouts" : "/auth"} className="btn-outline" data-testid="scouts-callout-cta">Open Scouts</Link>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-14 surface rounded p-5 text-xs text-zinc-500 leading-relaxed" data-testid="tos-disclaimer">
          <p>
            <strong className="text-zinc-300">Disclaimer:</strong> Tactical Ally is an unofficial, fan-made strategy companion. It is not affiliated with, endorsed by, or sponsored by 37Games or any of its subsidiaries. All game names, logos, and trademarks are property of their respective owners. Tactical Ally does not automate gameplay, read game memory, intercept network traffic, or interact with 37Games&apos; servers in any unauthorized manner — it is purely an advisory/educational tool that processes screenshots you voluntarily upload.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
