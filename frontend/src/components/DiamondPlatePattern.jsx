/**
 * DiamondPlatePattern — Gunmetal gray industrial diamond plate.
 * Matches the reference image: elongated horizontal "I-bar" / stretched-diamond
 * shapes raised from a matte gunmetal-gray surface, arranged in offset rows.
 * Cool gray palette (no warm tints), matte finish (no specular gleam).
 */
const DiamondPlatePattern = ({ className = "" }) => (
  <svg
    className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <defs>
      {/* Pattern tile — two diamonds per tile, offset rows for staggered look */}
      <pattern
        id="gunmetal-plate"
        x="0" y="0"
        width="80" height="42"
        patternUnits="userSpaceOnUse"
      >
        {/* Gunmetal base */}
        <rect width="80" height="42" fill="#3a4046" />
        {/* Subtle matte grain wash */}
        <rect width="80" height="42" fill="url(#gm-grain)" />

        {/* --- Diamond 1 (upper-left position) --- */}
        <g transform="translate(20 11)">
          {/* Soft cast shadow beneath the raised diamond */}
          <ellipse cx="0" cy="6.5" rx="20" ry="3.6" fill="rgba(0,0,0,0.42)" />
          {/* Diamond body — slightly elongated horizontal */}
          <path d="M -20 0 L 0 -7 L 20 0 L 0 7 Z" fill="#4b525a" />
          {/* Upper-half highlight (light from above) */}
          <path d="M -20 0 L 0 -7 L 20 0 Z" fill="#5d6571" />
          {/* Bright crest line along top edge */}
          <path d="M -18 -0.5 L 0 -6.5 L 18 -0.5" stroke="rgba(210,220,232,0.55)" strokeWidth="0.75" fill="none" strokeLinecap="round" />
          {/* Soft highlight gleam on upper-left face */}
          <path d="M -16 -1 L -4 -5.5 L -1 -3 L -10 0 Z" fill="rgba(195,208,222,0.30)" />
          {/* Bottom-half shadow */}
          <path d="M -20 0 L 0 7 L 20 0 Z" fill="#2e3338" />
          {/* Dark edge along bottom */}
          <path d="M -18 0.5 L 0 6.5 L 18 0.5" stroke="rgba(8,12,16,0.6)" strokeWidth="0.7" fill="none" strokeLinecap="round" />
        </g>

        {/* --- Diamond 2 (lower-right position, offset for staggered rows) --- */}
        <g transform="translate(60 32)">
          <ellipse cx="0" cy="6.5" rx="20" ry="3.6" fill="rgba(0,0,0,0.42)" />
          <path d="M -20 0 L 0 -7 L 20 0 L 0 7 Z" fill="#4b525a" />
          <path d="M -20 0 L 0 -7 L 20 0 Z" fill="#5d6571" />
          <path d="M -18 -0.5 L 0 -6.5 L 18 -0.5" stroke="rgba(210,220,232,0.55)" strokeWidth="0.75" fill="none" strokeLinecap="round" />
          <path d="M -16 -1 L -4 -5.5 L -1 -3 L -10 0 Z" fill="rgba(195,208,222,0.30)" />
          <path d="M -20 0 L 0 7 L 20 0 Z" fill="#2e3338" />
          <path d="M -18 0.5 L 0 6.5 L 18 0.5" stroke="rgba(8,12,16,0.6)" strokeWidth="0.7" fill="none" strokeLinecap="round" />
        </g>
      </pattern>

      {/* Matte brushed-metal grain — soft top-to-bottom vignette */}
      <linearGradient id="gm-grain" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor="rgba(255,255,255,0.03)" />
        <stop offset="50%" stopColor="rgba(0,0,0,0)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.18)" />
      </linearGradient>

      {/* Subtle overall darken at the edges so the plate has depth */}
      <radialGradient id="gm-vignette" cx="50%" cy="50%" r="75%">
        <stop offset="60%" stopColor="rgba(0,0,0,0)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.30)" />
      </radialGradient>
    </defs>

    <rect width="100%" height="100%" fill="url(#gunmetal-plate)" />
    <rect width="100%" height="100%" fill="url(#gm-vignette)" />
  </svg>
);

export default DiamondPlatePattern;
