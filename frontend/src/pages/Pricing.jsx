import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { CheckCircle, Lightning, Stack, ShieldCheck, Coins } from "@phosphor-icons/react";

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

  const sub = packages.find(p => p.id === "subscription_monthly");
  const top = packages.find(p => p.id === "topup_analysis");

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-6xl mx-auto px-6 py-14">
        <div className="text-center mb-12">
          <div className="tactical-label text-[#E63946] mb-2">// PRICING TIERS</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">Pick your loadout</h1>
          <p className="text-zinc-400 mt-3 max-w-xl mx-auto">
            CyphrAI Chat, Optimizer, Guides, and Daily Planner are <strong className="text-[#10B981]">free forever</strong>. Deep Dive vision analyses require a Pro subscription or top-up.
          </p>
          {quota && quota.plan === "pro" && (
            <div className="mt-4 inline-flex items-center gap-2 surface px-4 py-2 rounded text-sm" data-testid="pricing-current-plan">
              <ShieldCheck size={16} className="text-[#10B981]" />
              You're on <strong className="text-[#10B981]">Pro</strong> · {quota.total_baselines_available} analyses available
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
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> CyphrAI Chat (30 msgs/min)</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Build Optimizer (10/min)</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> 13+ curated Guides</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Daily Planner across 11 titles</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Personal War Room archive</li>
            </ul>
            <button onClick={() => nav(user ? "/dashboard" : "/auth")} className="btn-outline mt-6 w-full" data-testid="tier-free-cta">
              {user ? "Open Command Center" : "Enlist for free"}
            </button>
          </div>

          {/* PRO */}
          <div className="surface rounded-md p-7 flex flex-col relative ring-2 ring-[#E63946]/40 -translate-y-1" data-testid="tier-pro">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#E63946] text-white text-[10px] font-mono-tactical tracking-widest px-3 py-1 rounded">RECOMMENDED</span>
            <div className="tactical-label text-[#E63946] mb-2">// TIER 02 · PRO</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Tactical Ally Pro</h2>
            <div className="mt-3 mb-5">
              <span className="font-display text-4xl font-black text-[#FFBA08]">$4.99</span>
              <span className="text-zinc-500"> / month</span>
            </div>
            <ul className="space-y-2.5 text-sm text-zinc-300 flex-1">
              <li className="flex gap-2"><Lightning size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> <strong>2 Deep Dive baselines</strong> / month</li>
              <li className="flex gap-2"><Stack size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> <strong>Unlimited Building Blocks</strong> on those baselines</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Everything in Recruit</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Shareable Deep Dive links</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Game-specialist CyphrAI per title</li>
            </ul>
            <button onClick={() => buy("subscription_monthly")} disabled={loading === "subscription_monthly"} className="btn-primary mt-6 w-full" data-testid="tier-pro-cta">
              {loading === "subscription_monthly" ? "Opening checkout…" : "Subscribe — $4.99/mo"}
            </button>
          </div>

          {/* TOPUP */}
          <div className="surface rounded-md p-7 flex flex-col" data-testid="tier-topup">
            <div className="tactical-label text-zinc-500 mb-2">// TIER 03 · TOP-UP</div>
            <h2 className="font-display text-2xl font-bold tracking-tight">Extra Analysis</h2>
            <div className="mt-3 mb-5">
              <span className="font-display text-4xl font-black">$2.99</span>
              <span className="text-zinc-500"> / one-time</span>
            </div>
            <ul className="space-y-2.5 text-sm text-zinc-300 flex-1">
              <li className="flex gap-2"><Coins size={16} weight="duotone" className="text-[#FFBA08] mt-0.5 flex-shrink-0" /> <strong>+1 Deep Dive baseline</strong></li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Never expires — use any time</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Stacks with Pro plan</li>
              <li className="flex gap-2"><CheckCircle size={16} weight="duotone" className="text-[#10B981] mt-0.5 flex-shrink-0" /> Same vision quality, same depth</li>
            </ul>
            <button onClick={() => buy("topup_analysis")} disabled={loading === "topup_analysis"} className="btn-outline mt-6 w-full" data-testid="tier-topup-cta">
              {loading === "topup_analysis" ? "Opening checkout…" : "Buy one — $2.99"}
            </button>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-14 surface rounded p-5 text-xs text-zinc-500 leading-relaxed" data-testid="tos-disclaimer">
          <p>
            <strong className="text-zinc-300">Disclaimer:</strong> Tactical Ally is an unofficial, fan-made strategy companion. It is not affiliated with, endorsed by, or sponsored by 37Games or any of its subsidiaries. All game names, logos, and trademarks are property of their respective owners. Tactical Ally does not automate gameplay, read game memory, intercept network traffic, or interact with 37Games' servers in any unauthorized manner — it is purely an advisory/educational tool that processes screenshots you voluntarily upload.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
