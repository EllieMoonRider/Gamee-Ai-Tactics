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
      {/* Pattern tile — LARGER diamonds, same staggered offset. The diamonds
          themselves are more prominent so the print reads clearly while the
          extra negative space around each one keeps it from feeling cluttered. */}
      <pattern
        id="gunmetal-plate"
        x="0" y="0"
        width="120" height="64"
        patternUnits="userSpaceOnUse"
      >
        {/* Gunmetal base */}
        <rect width="120" height="64" fill="#3a4046" />
        {/* Subtle matte grain wash */}
        <rect width="120" height="64" fill="url(#gm-grain)" />

        {/* --- Diamond 1 (upper-left position) — bigger, bolder --- */}
        <g transform="translate(30 18)">
          {/* Soft cast shadow beneath the raised diamond */}
          <ellipse cx="0" cy="9" rx="28" ry="4.4" fill="rgba(0,0,0,0.5)" />
          {/* Diamond body — slightly elongated horizontal */}
          <path d="M -28 0 L 0 -10 L 28 0 L 0 10 Z" fill="#4b525a" />
          {/* Upper-half highlight (light from above) */}
          <path d="M -28 0 L 0 -10 L 28 0 Z" fill="#5e6671" />
          {/* Bright crest line along top edge */}
          <path d="M -25 -0.7 L 0 -9.3 L 25 -0.7" stroke="rgba(215,225,235,0.65)" strokeWidth="1" fill="none" strokeLinecap="round" />
          {/* Soft highlight gleam on upper-left face */}
          <path d="M -22 -1.5 L -6 -8 L -1.5 -4.5 L -14 0 Z" fill="rgba(200,212,225,0.32)" />
          {/* Bottom-half shadow */}
          <path d="M -28 0 L 0 10 L 28 0 Z" fill="#2d3237" />
          {/* Dark edge along bottom */}
          <path d="M -25 0.7 L 0 9.3 L 25 0.7" stroke="rgba(8,12,16,0.7)" strokeWidth="0.9" fill="none" strokeLinecap="round" />
        </g>

        {/* --- Diamond 2 (lower-right position, offset for staggered rows) --- */}
        <g transform="translate(90 50)">
          <ellipse cx="0" cy="9" rx="28" ry="4.4" fill="rgba(0,0,0,0.5)" />
          <path d="M -28 0 L 0 -10 L 28 0 L 0 10 Z" fill="#4b525a" />
          <path d="M -28 0 L 0 -10 L 28 0 Z" fill="#5e6671" />
          <path d="M -25 -0.7 L 0 -9.3 L 25 -0.7" stroke="rgba(215,225,235,0.65)" strokeWidth="1" fill="none" strokeLinecap="round" />
          <path d="M -22 -1.5 L -6 -8 L -1.5 -4.5 L -14 0 Z" fill="rgba(200,212,225,0.32)" />
          <path d="M -28 0 L 0 10 L 28 0 Z" fill="#2d3237" />
          <path d="M -25 0.7 L 0 9.3 L 25 0.7" stroke="rgba(8,12,16,0.7)" strokeWidth="0.9" fill="none" strokeLinecap="round" />
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
