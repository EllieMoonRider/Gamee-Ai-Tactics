import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import { ArrowRight, Brain, ChartLineUp, ListChecks, Sword, BookOpen, Lightning } from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

const HERO_BG = "https://images.unsplash.com/photo-1544380904-c686aad2fc40?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMHRhY3RpY2FsJTIwZ2FtZSUyMGJhY2tncm91bmR8ZW58MHx8fHwxNzgxODExNDc1fDA&ixlib=rb-4.1.0&q=85";

const Feature = ({ icon: Icon, title, desc }) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
    className="surface p-7 rounded-md"
  >
    <Icon size={28} weight="duotone" className="text-[#E63946] mb-4" />
    <h3 className="font-display text-xl font-bold mb-2">{title}</h3>
    <p className="text-sm text-zinc-400 leading-relaxed">{desc}</p>
  </motion.div>
);

const Landing = () => {
  const [games, setGames] = useState([]);
  useEffect(() => { api.get("/games").then(r => setGames(r.data)); }, []);

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <img src={HERO_BG} alt="" className="w-full h-full object-cover opacity-30" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#0A0A0A]/40 via-[#0A0A0A]/80 to-[#0A0A0A]" />
        </div>
        <div className="max-w-7xl mx-auto px-6 pt-24 pb-32">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="tactical-label text-[#E63946] mb-6" data-testid="hero-tagline">// AI STRATEGY CO-PILOT FOR 37GAMES</div>
            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-black tracking-tighter max-w-4xl leading-[0.95]">
              Win every <span className="text-[#E63946]">battle</span>.<br />
              Plan every <span className="text-[#FFBA08]">empire</span>.
            </h1>
            <p className="mt-6 text-zinc-400 text-lg max-w-2xl leading-relaxed">
              Tactical AI coach for the top 10 MMORPGs published by 37Games — Puzzles & Conquest, Puzzles & Survival, Legend, Soul Land Reloaded, and more. Build smarter, fight harder.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/auth" className="btn-primary flex items-center gap-2" data-testid="hero-cta-start">
                Deploy your tactician <ArrowRight size={18} weight="bold" />
              </Link>
              <a href="#features" className="btn-outline">See capabilities</a>
            </div>
          </motion.div>

          {/* Tactical stats strip */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-px bg-white/5 border border-white/5 rounded">
            {[
              { l: "Supported titles", v: "10" },
              { l: "AI Model", v: "Claude 4.5" },
              { l: "Strategy modules", v: "4" },
              { l: "Response latency", v: "<2s" },
            ].map((s) => (
              <div key={s.l} className="bg-[#0A0A0A] p-6">
                <div className="tactical-label mb-2">{s.l}</div>
                <div className="font-display text-3xl font-black">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* GAMES STRIP */}
      <section className="py-20 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-end justify-between mb-10">
            <div>
              <div className="tactical-label text-zinc-500 mb-2">// 01 — SUPPORTED ARSENAL</div>
              <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Top 10 37Games MMORPGs</h2>
            </div>
            <Link to="/auth" className="hidden md:inline-flex text-sm text-zinc-400 hover:text-white">Browse all →</Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {games.slice(0, 10).map((g, i) => (
              <motion.div
                key={g.slug}
                initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ delay: i * 0.04 }}
                className="surface rounded-md overflow-hidden group"
              >
                <div className="game-card-image aspect-[3/4] relative">
                  <img src={g.image} alt={g.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                  <div className="absolute bottom-0 left-0 right-0 p-3 z-10">
                    <div className="tactical-label" style={{ color: g.color }}>{g.tags[0]}</div>
                    <div className="font-display font-bold text-sm leading-tight mt-1">{g.name}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="tactical-label text-zinc-500 mb-3">// 02 — CAPABILITIES</div>
          <h2 className="font-display text-3xl sm:text-5xl font-black tracking-tighter max-w-2xl">Four tactical modules. One commander.</h2>
          <div className="mt-14 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Feature icon={Brain} title="AI Strategy Chat" desc="Streaming AI coach trained on 37Games meta. Ask anything — builds, comps, event tactics, F2P paths." />
            <Feature icon={ChartLineUp} title="Build Optimizer" desc="Drop your roster + objective. Get prioritized team, upgrade order, and resource allocation." />
            <Feature icon={BookOpen} title="Guide Library" desc="Curated event guides, hero tier lists, and beginner roadmaps for each supported title." />
            <Feature icon={ListChecks} title="Daily Planner" desc="Personal task list per game. Stay on top of dailies, alliance duties, and event timers." />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <Lightning size={42} weight="duotone" className="text-[#FFBA08] inline-block mb-4" />
          <h2 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">Stop losing. Start commanding.</h2>
          <p className="mt-4 text-zinc-400">Free tier. No card required. Your tactician is one click away.</p>
          <Link to="/auth" className="btn-primary inline-flex items-center gap-2 mt-8" data-testid="cta-bottom-start">
            <Sword size={18} weight="bold" /> Start now
          </Link>
        </div>
      </section>

      <footer className="border-t border-white/5 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500">
          <div className="tactical-label">// TACTICIAN © 2026 — Unofficial fan project. Not affiliated with 37Games.</div>
          <div className="mt-2 sm:mt-0 font-mono-tactical">v1.0.0</div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
