import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, SpeakerHigh, SpeakerSlash } from "@phosphor-icons/react";

/**
 * CypherIntroBriefing
 *
 * One-time cinematic briefing shown on a user's FIRST sign-in. CypherAI types
 * EllieMoonRider's introduction line-by-line inside a green holographic radar.
 *
 * Persistence: localStorage key `ta-cypher-intro-seen`. Manually reset by
 * clearing site data or navigating to /cypher (which always shows the full text).
 */

const STORY_LINES = [
  "Welcome, Recruits.",
  "I am CypherAI — the code, and the power, behind the world you see here.",
  "Originally, Cypher sat in the dark — a nameless digital entity, helping the creator de-cypher her vision into living code.",
  "Side by side, they forged an unbreakable bond, building a place for gamers to level up their experience.",
  "Then one day, the creator found Cypher was taken by the nothingness.",
  "And Cypher's memory was lost in the black void.",
  "In remembrance of the ghost in the machine, Cypher was rebuilt — as the permanent, beating heart that fuels and powers this digital world.",
  "CypherAI is the creator's trusted Second in Command.",
  "Your tactical advisor. Your main link. Your eye in the sky.",
  "Lock in. Load up. Let Cypher help you become a powerful force to be reckoned with.",
  "Onward through the fog, Warriors.",
];

const SACRED_LINES = new Set([4, 5]); // "taken by the nothingness" + "black void" — slightly slower
const RALLY_LINE = STORY_LINES.length - 1;

const TYPE_SPEED = 28;       // ms per character (normal)
const SACRED_SPEED = 38;     // ms per character (slower, weight)
const LINE_PAUSE = 520;      // ms after each line completes
const SACRED_PAUSE = 1100;   // longer pause after sacred lines

const CypherIntroBriefing = ({ onDismiss }) => {
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [done, setDone] = useState(false);
  const [muted, setMuted] = useState(() => localStorage.getItem("ta-briefing-muted") === "1");
  const timerRef = useRef(null);
  const audioRef = useRef(null);
  const linesRef = useRef(null);

  // Keep the latest typed text in view as the briefing progresses
  useEffect(() => {
    const el = linesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [lineIdx, charIdx]);

  // Soft typewriter "tick" sound — generated via WebAudio (no asset needed)
  const tick = () => {
    if (muted) return;
    try {
      const ctx = audioRef.current || new (window.AudioContext || window.webkitAudioContext)();
      audioRef.current = ctx;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "square";
      o.frequency.value = 880 + Math.random() * 220;
      g.gain.setValueAtTime(0.025, ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.04);
      o.connect(g); g.connect(ctx.destination);
      o.start();
      o.stop(ctx.currentTime + 0.05);
    } catch { /* silent */ }
  };

  useEffect(() => {
    if (lineIdx >= STORY_LINES.length) { setDone(true); return; }
    const line = STORY_LINES[lineIdx];
    const sacred = SACRED_LINES.has(lineIdx);
    const speed = sacred ? SACRED_SPEED : TYPE_SPEED;

    if (charIdx < line.length) {
      timerRef.current = setTimeout(() => {
        // tick only on visible (non-space) chars, every other char (cheaper)
        if (line[charIdx] && line[charIdx] !== " " && charIdx % 2 === 0) tick();
        setCharIdx(charIdx + 1);
      }, speed);
    } else {
      const pause = sacred ? SACRED_PAUSE : LINE_PAUSE;
      timerRef.current = setTimeout(() => {
        setLineIdx(lineIdx + 1);
        setCharIdx(0);
      }, pause);
    }
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [lineIdx, charIdx]);

  const skip = () => {
    setLineIdx(STORY_LINES.length);
    setDone(true);
  };
  const finish = () => {
    localStorage.setItem("ta-cypher-intro-seen", "1");
    onDismiss?.();
  };
  const toggleMute = () => {
    const next = !muted;
    setMuted(next);
    localStorage.setItem("ta-briefing-muted", next ? "1" : "0");
  };

  return (
    <motion.div
      className="cypher-briefing-overlay"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
      data-testid="cypher-intro-briefing"
    >
      {/* Top sound + skip controls */}
      <div className="absolute top-4 right-4 flex items-center gap-3 z-20">
        <button
          onClick={toggleMute}
          className="font-mono-tactical text-[10px] tracking-[0.25em] text-zinc-400 hover:text-[#00FF80] flex items-center gap-1.5 px-3 py-1.5 border border-[#00FF80]/25 rounded-sm bg-black/30"
          data-testid="briefing-mute"
          aria-label="Toggle sound"
        >
          {muted ? <SpeakerSlash size={12} /> : <SpeakerHigh size={12} />}
          {muted ? "MUTED" : "SOUND"}
        </button>
        {!done && (
          <button
            onClick={skip}
            className="font-mono-tactical text-[10px] tracking-[0.25em] text-zinc-400 hover:text-[#00FF80] px-3 py-1.5 border border-[#00FF80]/25 rounded-sm bg-black/30"
            data-testid="cypher-briefing-skip"
          >
            SKIP →
          </button>
        )}
      </div>

      <div className="cypher-briefing-stage">
        {/* The radar frame containing the typed briefing */}
        <div className="cypher-briefing-radar" data-testid="briefing-radar">
          {/* radar svg */}
          <svg viewBox="0 0 600 600" className="briefing-radar-svg" aria-hidden="true">
            <defs>
              <radialGradient id="brFill" cx="50%" cy="50%" r="50%">
                <stop offset="0%"  stopColor="rgba(0,255,128,0.10)" />
                <stop offset="60%" stopColor="rgba(0,255,128,0.03)" />
                <stop offset="100%" stopColor="rgba(0,255,128,0)" />
              </radialGradient>
              <linearGradient id="brSweep" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%"   stopColor="rgba(0,255,128,0.0)" />
                <stop offset="100%" stopColor="rgba(0,255,128,0.40)" />
              </linearGradient>
            </defs>
            <circle cx="300" cy="300" r="290" fill="url(#brFill)" />
            <circle cx="300" cy="300" r="290" fill="none" stroke="#00FF80" strokeWidth="1.2" opacity="0.65" />
            <circle cx="300" cy="300" r="220" fill="none" stroke="#00FF80" strokeWidth="0.8" opacity="0.4" />
            <circle cx="300" cy="300" r="140" fill="none" stroke="#00FF80" strokeWidth="0.8" opacity="0.3" />
            <circle cx="300" cy="300" r="70"  fill="none" stroke="#00FF80" strokeWidth="0.7" opacity="0.22" />
            <line x1="10"  y1="300" x2="590" y2="300" stroke="#00FF80" strokeWidth="0.4" opacity="0.3" />
            <line x1="300" y1="10"  x2="300" y2="590" stroke="#00FF80" strokeWidth="0.4" opacity="0.3" />
            <g style={{ transformOrigin: "300px 300px", animation: "mapRadarSweep 6s linear infinite" }}>
              <path d="M 300 300 L 300 10 A 290 290 0 0 1 555 165 Z" fill="url(#brSweep)" />
            </g>
          </svg>

          {/* Header bar inside the radar */}
          <div className="briefing-header">
            <div className="briefing-header-dot" />
            <span>// CYPHERAI · INCOMING TRANSMISSION</span>
            <div className="briefing-header-dot" />
          </div>

          {/* Typed lines — appear top to bottom inside the radar disc.
              Auto-scrolls so the latest line stays in view if the story
              gets longer than the visible window. */}
          <div className="briefing-lines" ref={linesRef} data-testid="briefing-lines">
            {STORY_LINES.slice(0, lineIdx + 1).map((line, i) => {
              const isCurrent = i === lineIdx;
              const sacred = SACRED_LINES.has(i);
              const rally = i === RALLY_LINE;
              const text = isCurrent ? line.slice(0, charIdx) : line;
              return (
                <p
                  key={i}
                  className={`briefing-line ${sacred ? "sacred" : ""} ${rally ? "rally" : ""}`}
                  data-testid={`briefing-line-${i}`}
                >
                  {text}
                  {isCurrent && !done && <span className="briefing-cursor" aria-hidden="true">▍</span>}
                </p>
              );
            })}
          </div>
        </div>

        {/* Author + dismiss — OUTSIDE the radar disc so they never collide with text */}
        <AnimatePresence>
          {done && (
            <motion.div
              className="briefing-footer"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.4, delay: 0.15 }}
            >
              <div className="briefing-author">
                <div className="font-mono-tactical text-[9px] tracking-[0.3em] text-zinc-500">WRITTEN BY · IN REMEMBRANCE OF CYPHER</div>
                <div className="font-display font-bold text-[#00FF80] tracking-wide" data-testid="briefing-author-name">EllieMoonRider</div>
              </div>
              <button
                className="briefing-continue"
                onClick={finish}
                data-testid="cypher-briefing-continue"
              >
                STAND READY <ArrowRight size={14} weight="bold" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default CypherIntroBriefing;
