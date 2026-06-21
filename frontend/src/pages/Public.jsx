import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { API } from "../lib/api";
import { CrosshairSimple, MapTrifold, Brain, Target } from "@phosphor-icons/react";

const renderMd = (s) => (s || "")
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/^### (.+)$/gm, "<h3>$1</h3>")
  .replace(/^## (.+)$/gm, "<h2>$1</h2>")
  .replace(/^# (.+)$/gm, "<h1>$1</h1>")
  .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
  .replace(/^- (.+)$/gm, "<li>$1</li>")
  .replace(/(<li>.*?<\/li>(?:\n|$))+/gs, m => `<ul>${m}</ul>`)
  .replace(/\n/g, "<br />");

const PublicHeader = () => (
  <header className="glass-nav sticky top-0 z-50">
    <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2.5">
        <CrosshairSimple size={22} weight="duotone" className="text-[#E63946]" />
        <span className="font-display text-lg font-bold tracking-tight">TACTICAL ALLY<span className="text-[#E63946]">.</span></span>
      </Link>
      <Link to="/auth" className="btn-primary !py-2 !px-4 text-sm">Get your own analysis</Link>
    </div>
  </header>
);

export const PublicDeepDive = () => {
  const { token } = useParams();
  const [dd, setDd] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    fetch(`${API}/share/d/${token}`)
      .then(r => r.ok ? r.json() : Promise.reject("Share not found"))
      .then(setDd).catch(setErr);
  }, [token]);

  if (err) return (
    <div className="min-h-screen">
      <PublicHeader />
      <div className="max-w-md mx-auto px-6 py-24 text-center">
        <h1 className="font-display text-3xl font-bold">Share not found</h1>
        <p className="text-sm text-zinc-500 mt-2">This link may have expired or been revoked.</p>
        <Link to="/" className="btn-outline inline-block mt-6">Go home</Link>
      </div>
    </div>
  );

  if (!dd) return (
    <div className="min-h-screen">
      <PublicHeader />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="h-12 w-64 shimmer rounded mb-6" />
        <div className="h-48 shimmer rounded" />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen" data-testid="public-deepdive">
      <PublicHeader />
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="tactical-label text-[#E63946] mb-2">// SHARED DEEP DIVE</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tighter">{dd.title}</h1>
        <p className="text-sm text-zinc-400 mt-2">
          Shared by <strong className="text-[#FFBA08]">{dd.shared_by}</strong> · {new Date(dd.created_at).toLocaleDateString()} · {dd.game_slug}
        </p>

        <div className="surface rounded-md p-6 mt-8">
          <div className="tactical-label text-[#E63946] mb-3">// BASELINE</div>
          <div className="terminal-block markdown-output" dangerouslySetInnerHTML={{ __html: renderMd(dd.baseline_analysis) }} />
        </div>

        {dd.follow_ups?.length > 0 && (
          <div className="mt-6 space-y-3">
            <h2 className="font-display font-bold flex items-center gap-2"><Brain size={18} className="text-[#FFBA08]" /> {dd.follow_ups.length} Building Block{dd.follow_ups.length > 1 ? "s" : ""}</h2>
            {dd.follow_ups.map((fu, i) => (
              <div key={fu.id} className="surface-elev rounded-md p-5">
                <div className="tactical-label text-[#FFBA08] mb-2">// BLOCK {String(i + 1).padStart(2, "0")} · {new Date(fu.created_at).toLocaleDateString()}</div>
                <div className="terminal-block markdown-output" dangerouslySetInnerHTML={{ __html: renderMd(fu.analysis) }} />
              </div>
            ))}
          </div>
        )}

        <div className="mt-10 surface rounded p-6 text-center">
          <h3 className="font-display text-xl font-bold">Want one for your account?</h3>
          <p className="text-sm text-zinc-400 mt-1 mb-4">CypherAI specialist analysis across 11 titles. Free chat. Pro from $4.99/mo.</p>
          <Link to="/auth" className="btn-primary inline-block">Get my Deep Dive</Link>
        </div>
      </div>
    </div>
  );
};

export const PublicBuild = () => {
  const { token } = useParams();
  const [b, setB] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    fetch(`${API}/share/b/${token}`)
      .then(r => r.ok ? r.json() : Promise.reject("Not found"))
      .then(setB).catch(setErr);
  }, [token]);

  if (err) return (
    <div className="min-h-screen"><PublicHeader />
      <div className="max-w-md mx-auto px-6 py-24 text-center">
        <h1 className="font-display text-3xl font-bold">Build not found</h1>
        <Link to="/" className="btn-outline inline-block mt-6">Go home</Link>
      </div></div>
  );
  if (!b) return <div className="min-h-screen"><PublicHeader /><div className="max-w-3xl mx-auto px-6 py-10"><div className="h-12 w-64 shimmer rounded" /></div></div>;

  return (
    <div className="min-h-screen" data-testid="public-build">
      <PublicHeader />
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className="tactical-label text-[#FFBA08] mb-2">// SHARED BUILD</div>
        <h1 className="font-display text-3xl font-black tracking-tighter flex items-center gap-3"><Target size={28} className="text-[#FFBA08]" /> {b.title}</h1>
        <p className="text-sm text-zinc-400 mt-2">By <strong>{b.shared_by}</strong> · {b.game_slug}</p>
        {b.team?.length > 0 && (
          <div className="surface rounded-md p-5 mt-6">
            <div className="tactical-label mb-2">// TEAM</div>
            <div className="font-mono-tactical">{b.team.join(" · ")}</div>
          </div>
        )}
        {b.notes && (
          <div className="surface rounded-md p-5 mt-4">
            <div className="tactical-label mb-2">// NOTES</div>
            <p className="text-sm whitespace-pre-wrap">{b.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
};
