/**
 * DiamondPlatePattern — RAISED industrial aluminum tread plate (truck toolbox style).
 * Each diamond reads as a physically raised stud with a strong bright highlight on
 * the upper-left face and a deep shadow underneath, sitting on a brushed gunmetal
 * base. The plate has a warm orange-tinted brand sheen across the surface.
 */
const DiamondPlatePattern = ({ className = "" }) => (
  <svg
    className={`absolute inset-0 w-full h-full pointer-events-none ${className}`}
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <defs>
      <pattern
        id="diamond-plate-v2"
        x="0" y="0"
        width="46" height="24"
        patternUnits="userSpaceOnUse"
      >
        {/* Brushed metal base — gradient gives faint sheen */}
        <rect width="46" height="24" fill="#23201c" />
        <rect width="46" height="24" fill="url(#dp-brush)" />

        {/* === Diamond 1 (left of cell) === */}
        {/* Subtle drop-shadow on the surface beneath the raised diamond */}
        <ellipse cx="12" cy="14.5" rx="10" ry="3.5" fill="rgba(0,0,0,0.35)" />
        {/* Raised body — mid-tone diamond */}
        <path d="M 12 2 L 22 12 L 12 22 L 2 12 Z" fill="#3a342d" />
        {/* Strong top-left bevel highlight (light source upper-left) */}
        <path d="M 12 2 L 17 7 L 12 12 L 7 7 Z" fill="rgba(255,210,170,0.32)" />
        {/* Specular gleam — small bright spot on upper-left face */}
        <path d="M 9 5 L 12 8 L 9.5 9.5 L 7 7 Z" fill="rgba(255,235,200,0.5)" />
        {/* Mid-tone right face */}
        <path d="M 12 2 L 17 7 L 22 12 L 17 7 Z" fill="rgba(255,170,90,0.07)" />
        {/* Strong bottom-right shadow */}
        <path d="M 12 22 L 17 17 L 22 12 L 17 17 Z" fill="rgba(0,0,0,0.55)" />
        <path d="M 12 22 L 7 17 L 12 17 Z" fill="rgba(0,0,0,0.35)" />

        {/* === Diamond 2 (right of cell, offset half row) === */}
        <ellipse cx="35" cy="14.5" rx="10" ry="3.5" fill="rgba(0,0,0,0.35)" />
        <path d="M 35 2 L 45 12 L 35 22 L 25 12 Z" fill="#3a342d" />
        <path d="M 35 2 L 40 7 L 35 12 L 30 7 Z" fill="rgba(255,210,170,0.32)" />
        <path d="M 32 5 L 35 8 L 32.5 9.5 L 30 7 Z" fill="rgba(255,235,200,0.5)" />
        <path d="M 35 2 L 40 7 L 45 12 L 40 7 Z" fill="rgba(255,170,90,0.07)" />
        <path d="M 35 22 L 40 17 L 45 12 L 40 17 Z" fill="rgba(0,0,0,0.55)" />
        <path d="M 35 22 L 30 17 L 35 17 Z" fill="rgba(0,0,0,0.35)" />
      </pattern>

      {/* Brushed-metal grain for the base */}
      <linearGradient id="dp-brush" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor="rgba(255,255,255,0.04)" />
        <stop offset="50%" stopColor="rgba(0,0,0,0)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.20)" />
      </linearGradient>

      {/* Faint warming wash across the whole plate */}
      <linearGradient id="dp-warm-v2" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor="rgba(255,107,0,0.06)" />
        <stop offset="50%" stopColor="rgba(0,0,0,0)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.30)" />
      </linearGradient>
    </defs>

    <rect width="100%" height="100%" fill="url(#diamond-plate-v2)" />
    <rect width="100%" height="100%" fill="url(#dp-warm-v2)" />
  </svg>
);

export default DiamondPlatePattern;
