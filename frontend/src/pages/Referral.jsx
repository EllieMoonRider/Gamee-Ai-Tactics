import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Share, Copy, Sparkle, Users, Trophy, Lightning } from "@phosphor-icons/react";

const Referral = () => {
  const { user } = useAuth();
  const [info, setInfo] = useState(null);
  useEffect(() => { api.get("/referral/me").then(r => setInfo(r.data)); }, []);

  const copy = (text, label = "Copied") => {
    navigator.clipboard?.writeText(text);
    toast.success(label);
  };

  if (!info) return <div className="min-h-screen"><Navbar /><div className="max-w-3xl mx-auto px-6 py-10"><div className="h-12 w-64 shimmer rounded" /></div></div>;

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        <div>
          <div className="tactical-label text-[#FFBA08] mb-2">// SHARE & EARN</div>
          <h1 className="font-display text-4xl font-black tracking-tighter flex items-center gap-3">
            <Share size={32} weight="duotone" className="text-[#FFBA08]" /> Refer friends, {user?.username}
          </h1>
          <p className="text-zinc-400 mt-3 max-w-xl">
            Share your code. When a friend signs up using it and pays their first month, you BOTH get a free Deep Dive analysis.
          </p>
        </div>

        {/* Code card */}
        <div className="surface rounded-md p-6">
          <div className="tactical-label text-zinc-500 mb-2">// YOUR REFERRAL CODE</div>
          <div className="flex items-center gap-3 flex-wrap">
            <div className="font-display text-3xl font-black font-mono-tactical tracking-widest" data-testid="referral-code">{info.code}</div>
            <button onClick={() => copy(info.code, "Code copied")} className="btn-outline !py-1.5 !px-3 text-xs flex items-center gap-1" data-testid="referral-copy-code">
              <Copy size={12} /> Copy code
            </button>
            <button onClick={() => copy(info.share_url, "Share link copied")} className="btn-primary !py-1.5 !px-3 text-xs flex items-center gap-1" data-testid="referral-copy-link">
              <Share size={12} /> Copy share link
            </button>
          </div>
          <p className="text-xs text-zinc-500 mt-3 font-mono-tactical break-all">{info.share_url}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="surface rounded p-4">
            <div className="tactical-label text-zinc-500 mb-1">// SIGNED UP</div>
            <div className="font-display text-3xl font-black flex items-center gap-1"><Users size={20} className="text-zinc-500" />{info.total_referred}</div>
          </div>
          <div className="surface rounded p-4">
            <div className="tactical-label text-[#10B981] mb-1">// PAID</div>
            <div className="font-display text-3xl font-black flex items-center gap-1"><Trophy size={20} className="text-[#10B981]" />{info.paid_referred}</div>
          </div>
          <div className="surface rounded p-4">
            <div className="tactical-label text-[#FFBA08] mb-1">// EARNED 30D</div>
            <div className="font-display text-3xl font-black flex items-center gap-1"><Lightning size={20} className="text-[#FFBA08]" />{info.rewards_this_period}<span className="text-zinc-500 text-sm">/{info.cap}</span></div>
          </div>
        </div>

        {/* Rules */}
        <div className="surface rounded-md p-5 text-sm text-zinc-300 space-y-2">
          <div className="tactical-label text-[#E63946] mb-1">// HOW IT WORKS</div>
          <p>1. Share your code with a friend.</p>
          <p>2. They register with the code → they get <strong className="text-[#10B981]">+1 free Deep Dive baseline</strong> as a welcome bonus.</p>
          <p>3. When they pay for their first subscription or top-up → <strong className="text-[#FFBA08]">you also get +1 Deep Dive baseline</strong>.</p>
          <p>4. Max <strong>{info.cap} rewards</strong> per rolling 30 days. No farming, no bots — just friends helping friends rise.</p>
        </div>
      </div>
    </div>
  );
};

export default Referral;
