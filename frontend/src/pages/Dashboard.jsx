import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ChatCircleText, Target, BookOpen, ListChecks, ArrowRight } from "@phosphor-icons/react";

const Dashboard = () => {
  const { user } = useAuth();
  const [games, setGames] = useState([]);
  const [stats, setStats] = useState({ chats: 0, builds: 0, tasks: 0 });

  useEffect(() => {
    api.get("/games").then(r => setGames(r.data));
    Promise.all([
      api.get("/chat/sessions").then(r => r.data.length).catch(() => 0),
      api.get("/builds").then(r => r.data.length).catch(() => 0),
      api.get("/tasks").then(r => r.data.filter(t => !t.completed).length).catch(() => 0),
    ]).then(([chats, builds, tasks]) => setStats({ chats, builds, tasks }));
  }, []);

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-10">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="tactical-label text-zinc-500 mb-3">// COMMAND CENTER</div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter">
            Welcome back, <span className="text-[#E63946]">{user?.username}</span>.
          </h1>
          <p className="text-zinc-400 mt-3 max-w-xl">Choose a title to access your tactical workspace.</p>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-10 max-w-2xl">
          {[
            { l: "Active chats", v: stats.chats, c: "#E63946" },
            { l: "Saved builds", v: stats.builds, c: "#FFBA08" },
            { l: "Open tasks", v: stats.tasks, c: "#10B981" },
          ].map(s => (
            <div key={s.l} className="surface p-5 rounded-md" data-testid={`stat-${s.l.split(" ")[1]}`}>
              <div className="tactical-label mb-2" style={{ color: s.c }}>{s.l}</div>
              <div className="font-display text-4xl font-black">{s.v}</div>
            </div>
          ))}
        </div>

        {/* Game grid */}
        <div className="mt-14">
          <div className="flex items-end justify-between mb-6">
            <div>
              <div className="tactical-label text-zinc-500 mb-2">// SELECT TITLE</div>
              <h2 className="font-display text-2xl font-bold tracking-tight">Your arsenal</h2>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="game-grid">
            {games.map((g, i) => (
              <motion.div
                key={g.slug}
                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
              >
                <Link
                  to={`/game/${g.slug}`}
                  className="surface rounded-md overflow-hidden block group hover:-translate-y-1"
                  data-testid={`game-card-${g.slug}`}
                >
                  <div className="game-card-image aspect-[16/10] relative">
                    <img src={g.image} alt={g.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                    <div className="absolute top-3 left-3 z-10">
                      <span className="tag-chip" style={{ color: g.color, borderColor: g.color + "40" }}>{g.genre.split(" / ")[0]}</span>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
                      <h3 className="font-display text-lg font-bold leading-tight">{g.name}</h3>
                      <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{g.tagline}</p>
                    </div>
                  </div>
                  <div className="px-4 py-3 flex items-center justify-between border-t border-white/5">
                    <div className="flex items-center gap-3 text-zinc-500">
                      <ChatCircleText size={16} /> <Target size={16} /> <BookOpen size={16} /> <ListChecks size={16} />
                    </div>
                    <ArrowRight size={16} className="text-zinc-500 group-hover:text-[#E63946] transition" />
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
