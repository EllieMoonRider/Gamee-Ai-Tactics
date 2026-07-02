import { useEffect, useState } from "react";

/**
 * RadarBriefing
 * The Command Center welcome briefing, typed inside the giant green radar
 * dome (upper-center of the war-room scene). Uses Orbitron (font-display) to
 * match the CypherAI remembrance story on /cypher.
 *
 * Behavior (per General's spec):
 *   • Plays every /dashboard visit (no localStorage gate)
 *   • Skippable via SKIP button
 *   • After the briefing finishes typing, holds for AMPLE_READ_MS then
 *     auto-dismisses. onDismiss() unmounts the overlay.
 */
const BRIEFING = [
  { variant: "title",  text: "WELCOME TO THE TACTICAL ALLY COMMAND CENTER" },
  { variant: "header", text: "MISSION OBJECTIVE" },
  { variant: "body",   text: "You have entered the primary intelligence hub for your journey through the realms of Puzzles & Survival, Puzzles & Conquest, and Puzzles & Chaos." },
  { variant: "body",   text: "The Tactical Ally is designed to eliminate guesswork. We provide data-driven pathways and optimized strategies to ensure every move you make contributes directly to your account's progression, efficiency, and ultimate victory." },
];

const TYPE_SPEED_MS = 26;     // per-character typing speed
const LINE_PAUSE_MS = 320;    // pause between lines
const AMPLE_READ_MS = 5000;   // hold after last char before auto-dismiss

export default function RadarBriefing({ onDismiss }) {
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [done, setDone] = useState(false);

  // Type through the briefing
  useEffect(() => {
    if (lineIdx >= BRIEFING.length) { setDone(true); return; }
    const line = BRIEFING[lineIdx].text;
    if (charIdx < line.length) {
      const t = setTimeout(() => setCharIdx(charIdx + 1), TYPE_SPEED_MS);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      setLineIdx(lineIdx + 1);
      setCharIdx(0);
    }, LINE_PAUSE_MS);
    return () => clearTimeout(t);
  }, [lineIdx, charIdx]);

  // Auto-dismiss after the briefing finishes + ample reading time
  useEffect(() => {
    if (!done) return;
    const t = setTimeout(() => onDismiss?.(), AMPLE_READ_MS);
    return () => clearTimeout(t);
  }, [done, onDismiss]);

  const handleSkip = () => onDismiss?.();

  return (
    <div className="radar-briefing" data-testid="radar-briefing" role="dialog" aria-label="Command Center welcome briefing">
      <div className="radar-briefing__scroll">
        {BRIEFING.slice(0, lineIdx + 1).map((line, i) => {
          const isCurrent = i === lineIdx && !done;
          const text = isCurrent ? line.text.slice(0, charIdx) : line.text;
          const cls = `radar-briefing__line radar-briefing__line--${line.variant}`;
          return (
            <p key={i} className={cls}>
              {text}
              {isCurrent && <span className="radar-briefing__cursor" aria-hidden="true">▍</span>}
            </p>
          );
        })}
      </div>

      <button
        type="button"
        className="radar-briefing__skip"
        onClick={handleSkip}
        data-testid="radar-briefing-skip"
      >
        SKIP ▸
      </button>
    </div>
  );
}
