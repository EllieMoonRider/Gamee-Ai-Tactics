import "./HolographicGridFloor.css";

/* ============================================================================
   HolographicGridFloor (Layer 1.5)
   Live animated topographic + perspective grid projected on the war-room
   floor. Layered between the scene art and the future Layer 2 beacons.
   Pointer-events: none — never blocks UI above it.
   ============================================================================ */

const TICK_POSITIONS = [
  { left: "18%", top: "62%" },
  { left: "82%", top: "58%" },
  { left: "32%", top: "78%" },
  { left: "68%", top: "82%" },
  { left: "50%", top: "44%" },
];

export default function HolographicGridFloor() {
  return (
    <div className="holo-floor" data-testid="holographic-grid-floor" aria-hidden="true">
      {/* Base perspective grid (fine 60px lattice) */}
      <div className="holo-floor__grid" />

      {/* Brighter accent grid (every ~5th line) */}
      <div className="holo-floor__grid--accent" />

      {/* Topographic contour rings — SVG for organic curves */}
      <svg
        className="holo-floor__contours"
        viewBox="0 0 1000 600"
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="contour-fade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00FF80" stopOpacity="0" />
            <stop offset="30%" stopColor="#00FF80" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#00FF80" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <g
          fill="none"
          stroke="url(#contour-fade)"
          strokeWidth="1.6"
          strokeLinecap="round"
        >
          {/* Concentric organic ridges (left hill) */}
          <path d="M 80 480 Q 200 420, 320 470 T 520 460" />
          <path d="M 60 440 Q 200 380, 340 430 T 540 420" />
          <path d="M 50 400 Q 200 340, 360 390 T 560 380" />
          {/* Right ridge */}
          <path d="M 500 470 Q 660 410, 820 460 T 980 480" />
          <path d="M 510 430 Q 670 370, 830 420 T 990 440" />
          <path d="M 520 390 Q 680 330, 840 380 T 1000 400" />
          {/* Far valley line */}
          <path d="M 0 540 Q 250 510, 500 530 T 1000 540" strokeOpacity="0.5" />
          <path d="M 0 580 Q 250 555, 500 575 T 1000 580" strokeOpacity="0.4" />
        </g>
      </svg>

      {/* Slow vertical scanning sweep */}
      <div className="holo-floor__sweep" />

      {/* Floating tactical coordinate ticks */}
      {TICK_POSITIONS.map((p, i) => (
        <span
          key={i}
          className="holo-floor__tick"
          style={{ left: p.left, top: p.top, animationDelay: `${i * 0.45}s` }}
        />
      ))}

      {/* Edge vignette to anchor the grid into the scene */}
      <div className="holo-floor__vignette" />
    </div>
  );
}
