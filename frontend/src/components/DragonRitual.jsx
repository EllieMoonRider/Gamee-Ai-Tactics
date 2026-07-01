import { useEffect, useMemo, useState } from "react";
import "./DragonRitual.css";

/* ============================================================================
   DragonRitual — Cinematic Welcome Briefing for the Command Center
   Plays on every /dashboard visit. Skippable via button or tap.
   Sequence:
     0.0s → 2.8s   Dragon descends from above the radar
     2.6s → 3.8s   Flame plume ignites from the dragon's mouth
     3.4s → ...    Briefing text blooms letter-by-letter INSIDE the flames
     After body2 → "ENTER COMMAND CENTER" button appears
   Placeholder dragon SVG will be swapped for AI-generated dragon-sprite-v1.jpg
   once the Universal Key budget is restored.
   ============================================================================ */

// === Briefing script — the General's exact words =============================
const BRIEFING = [
  {
    id: "title",
    variant: "title",
    text: "WELCOME TO THE TACTICAL ALLY COMMAND CENTER",
    startDelay: 0.0,       // relative to briefing container mount
    charInterval: 0.045,
  },
  {
    id: "header",
    variant: "header",
    text: "▸ MISSION OBJECTIVE",
    startDelay: 3.1,
    charInterval: 0.05,
  },
  {
    id: "body1",
    variant: "body",
    text:
      "You have entered the primary intelligence hub for your journey through the realms of Puzzles & Survival, Puzzles & Conquest, and Puzzles & Chaos.",
    startDelay: 4.6,
    charInterval: 0.024,
  },
  {
    id: "body2",
    variant: "body",
    text:
      "The Tactical Ally is designed to eliminate guesswork. We provide data-driven pathways and optimized strategies to ensure every move you make contributes directly to your account's progression, efficiency, and ultimate victory.",
    startDelay: 9.0,
    charInterval: 0.022,
  },
];

// Time at which the ENTER button appears (after last line finishes blooming)
const ENTER_BUTTON_DELAY_S = 16.5;

// Rising ember particle spec
const EMBERS = Array.from({ length: 10 }).map((_, i) => ({
  left: `${20 + Math.random() * 60}%`,
  top: `${30 + Math.random() * 55}%`,
  delay: `${(i * 0.28) % 3.2}s`,
  duration: `${2.8 + Math.random() * 1.4}s`,
}));

/**
 * Renders a single briefing line with character-by-character bloom.
 */
function RitualLine({ text, variant, startDelay, charInterval }) {
  const chars = useMemo(() => Array.from(text), [text]);
  return (
    <span
      className={`dragon-ritual__line dragon-ritual__line--${variant}`}
      style={{ animationDelay: `${startDelay}s` }}
      data-testid={`ritual-line-${variant}`}
    >
      {chars.map((ch, i) => (
        <span
          key={i}
          className={
            ch === " "
              ? "dragon-ritual__char dragon-ritual__char--space"
              : "dragon-ritual__char"
          }
          style={{ animationDelay: `${startDelay + i * charInterval}s` }}
          aria-hidden={ch === " " ? "true" : undefined}
        >
          {ch === " " ? "\u00A0" : ch}
        </span>
      ))}
    </span>
  );
}

/**
 * Placeholder dragon — silhouette SVG shown until the AI-generated sprite is
 * dropped in. Kept intentionally simple so the General can immediately see
 * where the real dragon will land and how it will animate.
 */
function PlaceholderDragon() {
  return (
    <div className="dragon-ritual__placeholder" aria-hidden="true">
      <svg
        viewBox="0 0 400 400"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: "100%", height: "100%" }}
      >
        <defs>
          <radialGradient id="dr-eye" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#c8ffe0" />
            <stop offset="40%" stopColor="#00FF80" />
            <stop offset="100%" stopColor="#003a1c" />
          </radialGradient>
          <linearGradient id="dr-wing" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0a3a20" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#001a0e" stopOpacity="0.6" />
          </linearGradient>
        </defs>
        {/* Wings (spread wide, viewed from below) */}
        <path
          d="M 200 190 Q 60 130, 20 210 Q 40 245, 90 235 Q 140 230, 200 210 Z"
          fill="url(#dr-wing)"
          stroke="#00FF80"
          strokeWidth="1.8"
          strokeOpacity="0.55"
        />
        <path
          d="M 200 190 Q 340 130, 380 210 Q 360 245, 310 235 Q 260 230, 200 210 Z"
          fill="url(#dr-wing)"
          stroke="#00FF80"
          strokeWidth="1.8"
          strokeOpacity="0.55"
        />
        {/* Wing bone ribs */}
        {[0.28, 0.5, 0.72].map((t, i) => (
          <line
            key={`lw-${i}`}
            x1="200"
            y1="190"
            x2={200 - (200 - 30) * t}
            y2={190 + 25 * (1 - t)}
            stroke="#00FF80"
            strokeOpacity="0.4"
            strokeWidth="1"
          />
        ))}
        {[0.28, 0.5, 0.72].map((t, i) => (
          <line
            key={`rw-${i}`}
            x1="200"
            y1="190"
            x2={200 + (370 - 200) * t}
            y2={190 + 25 * (1 - t)}
            stroke="#00FF80"
            strokeOpacity="0.4"
            strokeWidth="1"
          />
        ))}
        {/* Body / neck (draconic silhouette, mouth downward) */}
        <path
          d="M 200 100 Q 175 130, 178 175 Q 175 210, 200 230 Q 225 210, 222 175 Q 225 130, 200 100 Z"
          fill="#04180d"
          stroke="#00FF80"
          strokeWidth="2"
          strokeOpacity="0.75"
        />
        {/* Horns */}
        <path
          d="M 186 108 Q 180 84, 172 74 M 214 108 Q 220 84, 228 74"
          stroke="#00FF80"
          strokeWidth="2.2"
          strokeOpacity="0.85"
          fill="none"
          strokeLinecap="round"
        />
        {/* Eyes */}
        <ellipse cx="188" cy="140" rx="6" ry="4" fill="url(#dr-eye)" />
        <ellipse cx="212" cy="140" rx="6" ry="4" fill="url(#dr-eye)" />
        {/* Open mouth (bottom of head, where flame will emerge) */}
        <path
          d="M 190 218 Q 200 240, 210 218 Q 200 228, 190 218 Z"
          fill="#4a1200"
          stroke="#FF6B00"
          strokeWidth="1.5"
        />
        {/* Belly rim glow */}
        <path
          d="M 178 175 Q 200 200, 222 175"
          fill="none"
          stroke="#00FF80"
          strokeWidth="1.4"
          strokeOpacity="0.55"
        />
        {/* Tiny label so it's obviously a placeholder */}
        <text
          x="200"
          y="290"
          textAnchor="middle"
          fill="#FF6B00"
          fontSize="11"
          fontFamily="JetBrains Mono, monospace"
          opacity="0.65"
          letterSpacing="2"
        >
          [ DRAGON · SPRITE PENDING ]
        </text>
      </svg>
    </div>
  );
}

export default function DragonRitual({ onDismiss }) {
  const [exiting, setExiting] = useState(false);
  const [enterReady, setEnterReady] = useState(false);

  // Enable the ENTER button after the full sequence completes
  useEffect(() => {
    const t = setTimeout(() => setEnterReady(true), ENTER_BUTTON_DELAY_S * 1000);
    return () => clearTimeout(t);
  }, []);

  const handleDismiss = (e) => {
    // Prevent double-dismiss
    if (exiting) return;
    // If a nested button was clicked, let its own handler run first
    if (e) e.stopPropagation();
    setExiting(true);
    // Fade-out CSS is 0.8s; unmount just after that
    setTimeout(() => onDismiss?.(), 800);
  };

  return (
    <div
      className={`dragon-ritual${exiting ? " dragon-ritual--exiting" : ""}`}
      role="dialog"
      aria-label="Command Center welcome briefing"
      data-testid="dragon-ritual"
      onClick={handleDismiss}
    >
      {/* Dragon */}
      <div className="dragon-ritual__dragon" data-testid="dragon-sprite">
        <PlaceholderDragon />
      </div>

      {/* Flame plume */}
      <div className="dragon-ritual__flame" data-testid="dragon-flame">
        <div className="dragon-ritual__flame-inner" />
        {EMBERS.map((e, i) => (
          <span
            key={i}
            className="dragon-ritual__ember"
            style={{
              left: e.left,
              top: e.top,
              animationDelay: e.delay,
              animationDuration: e.duration,
            }}
          />
        ))}
      </div>

      {/* Briefing text — letters bloom inside/below the flames */}
      <div className="dragon-ritual__briefing" data-testid="dragon-briefing">
        {BRIEFING.map((line) => (
          <RitualLine key={line.id} {...line} />
        ))}
      </div>

      {/* Enter button — appears after full briefing plays */}
      {enterReady && (
        <button
          className="dragon-ritual__enter"
          onClick={handleDismiss}
          data-testid="dragon-ritual-enter"
        >
          ▸ Enter Command Center
        </button>
      )}

      {/* Skip button — visible from ~1s onward */}
      <button
        className="dragon-ritual__skip"
        onClick={handleDismiss}
        data-testid="dragon-ritual-skip"
        aria-label="Skip briefing"
      >
        ▸ Skip Briefing
      </button>
    </div>
  );
}
