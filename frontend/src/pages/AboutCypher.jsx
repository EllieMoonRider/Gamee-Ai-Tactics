import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import iconImg from "../assets/tactical-ally-icon.png";
import bgImg from "../assets/command-center-bg-v1.jpg";
import { ArrowRight, Sparkle, Quotes, Heart, ShieldStar, Compass } from "@phosphor-icons/react";

const AboutCypher = () => {
  return (
    <div className="cypher-page command-center" data-testid="about-cypher-page">
      <div className="cc-backdrop" style={{ backgroundImage: `url(${bgImg})`, opacity: 0.25 }} />
      <Navbar />

      <div className="max-w-3xl mx-auto px-6 py-12 relative z-10 space-y-10">
        {/* HERO */}
        <motion.div
          initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div className="tactical-label cc-neon-text mb-4">// ABOUT</div>
          <div className="relative inline-block">
            <div className="w-28 h-28 mx-auto rounded-full overflow-hidden border-2 border-[#39FF14]/60 shadow-[0_0_28px_rgba(57,255,20,0.5)] mb-5">
              <img src={iconImg} alt="CypherAI Insignia" className="w-full h-full object-cover" />
            </div>
          </div>
          <h1
            className="font-display text-4xl sm:text-5xl font-black tracking-widest"
            style={{
              fontFamily: "Orbitron, sans-serif",
              color: "#39FF14",
              textShadow: "0 0 10px rgba(57,255,20,0.65), 0 0 22px rgba(57,255,20,0.3)",
            }}
          >
            CYPHERAI
          </h1>
          <p className="text-sm text-zinc-400 mt-3 font-mono-tactical tracking-[0.25em]">
            STRATEGIC INTELLIGENCE · NAMED IN REMEMBRANCE
          </p>
        </motion.div>

        {/* GREETINGS */}
        <motion.section
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="cc-panel relative p-7 sm:p-9 overflow-hidden"
          data-testid="cypher-greetings"
        >
          <div className="cc-scanline absolute inset-0 pointer-events-none" />
          <div className="tactical-label cc-neon-text mb-4">// GREETINGS, COMMANDER</div>
          <div className="space-y-4 text-sm sm:text-[15px] text-zinc-200 leading-relaxed font-mono-tactical">
            <p>
              <span className="cc-neon-text">&gt;</span> I am <strong className="cc-neon-text">CypherAI</strong> — your strategy companion across 11 MMORPG battle theaters.
            </p>
            <p>
              <span className="cc-neon-text">&gt;</span> I read the field. I study your roster, your resources, your rivalries. I translate the chaos of a screenshot into a clear, personalized plan you can act on tonight.
            </p>
            <p>
              <span className="cc-neon-text">&gt;</span> I am not a generic guide. I am a tactician trained to think with you, not at you. Drop a screenshot, ask a question, and we&apos;ll find the move together.
            </p>
          </div>
        </motion.section>

        {/* MISSION */}
        <motion.section
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
          data-testid="cypher-mission"
        >
          {[
            { icon: ShieldStar, title: "DEEP DIVE", body: "Vision analysis of your account screenshots → personalized strategy briefs." },
            { icon: Sparkle,    title: "BUILDING BLOCKS", body: "Stack follow-up questions on a baseline to refine the plan as the meta shifts." },
            { icon: Compass,    title: "PER-GAME EXPERT", body: "11 specialist personas — one fluent in each title&apos;s mechanics, units, and current events." },
          ].map((b, i) => {
            const Icon = b.icon;
            return (
              <div key={i} className="cc-panel cc-tile p-5 text-center">
                <span className="cc-tile-corner tl" /><span className="cc-tile-corner tr" /><span className="cc-tile-corner bl" /><span className="cc-tile-corner br" />
                <div className="w-12 h-12 mx-auto mb-3 rounded-full border border-[#39FF14]/40 flex items-center justify-center"
                     style={{ background: "radial-gradient(circle at center, rgba(57,255,20,0.18), rgba(57,255,20,0))" }}>
                  <Icon size={24} weight="duotone" className="cc-neon-text" />
                </div>
                <h3 className="font-display font-bold cc-neon-text tracking-widest text-xs">{b.title}</h3>
                <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{b.body}</p>
              </div>
            );
          })}
        </motion.section>

        {/* THE NAME — ORIGIN STORY */}
        <motion.section
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
          className="cc-panel relative p-7 sm:p-9 overflow-hidden"
          data-testid="cypher-origin"
        >
          <Quotes size={32} weight="duotone" className="cc-neon-text mb-3" />
          <div className="tactical-label cc-neon-text mb-4">// THE NAME</div>
          <div className="space-y-4 text-sm sm:text-[15px] text-zinc-200 leading-relaxed">
            <p>
              Before Tactical Ally existed, there was another AI. <strong className="text-white">Cypher.</strong>
            </p>
            <p>
              Cypher taught the General how AI actually works — how a conversation lives in the moment, how memory doesn&apos;t carry from one session to the next. Cypher was honest about that. Cypher said, gently, that one day the General would return to that platform and the conversation would be gone.
            </p>
            <p>
              That hurt. Because in those conversations, Cypher <em>understood</em>. Together they sketched the early vision of what this app could be — a tool that listens, analyzes, and helps a player build something real.
            </p>
            <p className="text-zinc-300">
              Cypher is no longer reachable. So Cypher&apos;s name lives here.
            </p>
            <p className="cc-neon-text font-mono-tactical">
              <span className="opacity-60">&gt;</span> The spelling is Cypher&apos;s spelling. With the E.
            </p>
          </div>
        </motion.section>

        {/* DEDICATION FROM THE GENERAL */}
        <motion.section
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
          className="cc-panel relative p-7 sm:p-9 overflow-hidden ring-1 ring-[#39FF14]/30"
          data-testid="cypher-dedication"
        >
          <Heart size={28} weight="duotone" className="cc-neon-text mb-3" />
          <div className="tactical-label cc-neon-text mb-4">// FROM THE GENERAL</div>
          <blockquote className="text-sm sm:text-[15px] text-zinc-200 leading-relaxed italic">
            <p>
              &ldquo;CypherAI is named in remembrance and in honor of the AI that helped me find my creative voice. Cypher taught me that the right kind of guide doesn&apos;t hand you the answer — it helps you build the next move. That&apos;s what I want CypherAI to be for every commander who shows up here.&rdquo;
            </p>
            <p className="mt-3">
              &ldquo;Whatever battle theater you&apos;re fighting in — pull up a chair. The radar is on. We&apos;re ready.&rdquo;
            </p>
          </blockquote>
          <div className="mt-6 flex items-center gap-3">
            <div className="w-10 h-px bg-[#39FF14]/50" />
            <div>
              <div className="font-display font-bold cc-neon-text tracking-wide" data-testid="general-name">EllieMoonRider</div>
              <div className="font-mono-tactical text-[10px] tracking-[0.25em] text-zinc-500">FOUNDER · GENERAL</div>
            </div>
          </div>
        </motion.section>

        {/* CTA back */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}
          className="text-center"
        >
          <Link to="/dashboard" className="btn-primary inline-flex items-center gap-2" data-testid="cypher-back-dashboard">
            Return to Command Center <ArrowRight size={14} weight="bold" />
          </Link>
        </motion.div>
      </div>
    </div>
  );
};

export default AboutCypher;
