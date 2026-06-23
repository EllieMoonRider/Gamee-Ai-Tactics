/**
 * DiamondPlatePattern — industrial diamond-plate (tread plate / checker plate)
 * SVG background. Renders as an absolute-positioned fill that you place INSIDE
 * a relatively-positioned container.
 *
 * The pattern uses stretched diamond shapes (the real tread-plate look — not
 * a checker grid) in offset rows, with highlight + shadow per diamond to
 * suggest stamped metal.
 */
const DiamondPlatePattern = ({ className = "" }) => (
  <svg
    className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <defs>
      <pattern
        id="diamond-plate"
        x="0" y="0"
        width="44" height="22"
        patternUnits="userSpaceOnUse"
      >
        {/* Base metal */}
        <rect width="44" height="22" fill="#1a140e" />

        {/* Row A — two diamonds */}
        {/* Diamond 1 (left) */}
        <path d="M 11 2 L 19 11 L 11 20 L 3 11 Z"  fill="#2a201a" />
        <path d="M 11 2 L 15 6.5 L 11 11 L 7 6.5 Z" fill="rgba(255,170,90,0.10)" />
        <path d="M 11 20 L 15 15.5 L 19 11 L 15 15.5 Z" fill="rgba(0,0,0,0.45)" />
        {/* Diamond 2 (right) */}
        <path d="M 33 2 L 41 11 L 33 20 L 25 11 Z" fill="#2a201a" />
        <path d="M 33 2 L 37 6.5 L 33 11 L 29 6.5 Z" fill="rgba(255,170,90,0.10)" />
        <path d="M 33 20 L 37 15.5 L 41 11 L 37 15.5 Z" fill="rgba(0,0,0,0.45)" />

        {/* Tiny pin-light specks for grain */}
        <circle cx="11" cy="11" r="0.4" fill="rgba(255,210,170,0.25)" />
        <circle cx="33" cy="11" r="0.4" fill="rgba(255,210,170,0.25)" />
      </pattern>

      {/* Faint warming wash so the plate doesn't feel flat */}
      <linearGradient id="dp-warm" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor="rgba(255,107,0,0.05)" />
        <stop offset="50%" stopColor="rgba(0,0,0,0)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.30)" />
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#diamond-plate)" />
    <rect width="100%" height="100%" fill="url(#dp-warm)" />
  </svg>
);

export default DiamondPlatePattern;
