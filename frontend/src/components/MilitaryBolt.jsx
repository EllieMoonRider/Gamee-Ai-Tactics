/**
 * MilitaryBolt — Pitch-black FLAT-faced hex bolt with raised OTS scoring.
 *
 * • Hex body: FLAT pitch black across the entire face (no radial gradient
 *   that makes the center look like an oval). Light gray highlights live
 *   ONLY on the hex perimeter / corners, suggesting a flat metal disc lit
 *   from above-left.
 * • Bolt sits in a LIGHT gray countersink ring (instead of dark) so the
 *   bolt clearly reads as raised from the gunmetal plate.
 * • Three raised OTS scoring ridges in burnt orange.
 * • Slightly wider footprint (default size bump from 36 → 42).
 */
const MilitaryBolt = ({ size = 42, className = "", testid = "ots-bolt" }) => {
  const cx = 32, cy = 32, hexR = 27;
  const hexPath = (() => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 180) * (60 * i - 90);
      pts.push([cx + hexR * Math.cos(a), cy + hexR * Math.sin(a)]);
    }
    return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(" ") + " Z";
  })();
  // Smaller path used for the bright top-edge highlights (upper-left + top edges)
  const hexInner = (() => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 180) * (60 * i - 90);
      pts.push([cx + (hexR - 1.6) * Math.cos(a), cy + (hexR - 1.6) * Math.sin(a)]);
    }
    return pts;
  })();
  // Top 3 vertices (upper-left, top, upper-right) — for the light-edge highlight
  const topEdges = `M ${hexInner[4][0].toFixed(2)} ${hexInner[4][1].toFixed(2)} L ${hexInner[5][0].toFixed(2)} ${hexInner[5][1].toFixed(2)} L ${hexInner[0][0].toFixed(2)} ${hexInner[0][1].toFixed(2)} L ${hexInner[1][0].toFixed(2)} ${hexInner[1][1].toFixed(2)}`;

  const BURNT_ORANGE = "#A0410B";
  const BURNT_HIGHLIGHT = "#C25415";

  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={className}
      data-testid={testid}
      style={{ display: "block", filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.7))" }}
    >
      {/* LIGHT GRAY countersink ring — defines where the bolt meets the plate */}
      <ellipse cx={cx} cy={cy + 0.5} rx={hexR + 2.5} ry={hexR + 2.5}
               fill="none" stroke="rgba(180,188,196,0.35)" strokeWidth="1" />
      <ellipse cx={cx} cy={cy + 0.5} rx={hexR + 1.5} ry={hexR + 1.5}
               fill="none" stroke="rgba(140,148,156,0.45)" strokeWidth="0.6" />

      {/* Cast shadow under the bolt (offset down) */}
      <path d={hexPath} fill="rgba(0,0,0,0.65)" transform="translate(0.6, 1.6)" />

      {/* FLAT pitch black hex face — no gradient that creates an oval center */}
      <path d={hexPath} fill="#000000" />

      {/* Hex edge — sharp dark outline */}
      <path d={hexPath} fill="none" stroke="#1a1d20" strokeWidth="0.8" />

      {/* Light-gray highlight on the upper edges of the hex (top + upper-left + upper-right)
          — simulates light from above-left without affecting the flat center */}
      <path d={topEdges}
            fill="none"
            stroke="rgba(160,170,180,0.45)"
            strokeWidth="0.9"
            strokeLinecap="round" />

      {/* Tiny lighter accent right at the top vertex of the hex */}
      <circle cx={hexInner[0][0]} cy={hexInner[0][1]} r="1" fill="rgba(200,210,220,0.45)" />

      {/* === Three RAISED scoring ridges (inverted-Y / Mercedes pattern) === */}
      {/* Shadow beneath each ridge */}
      <g stroke="rgba(0,0,0,0.95)" strokeWidth="3" strokeLinecap="round" transform="translate(0.7, 1.0)">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 14} />
        <line x1={cx} y1={cy} x2={cx - 12.5} y2={cy - 8} />
        <line x1={cx} y1={cy} x2={cx + 12.5} y2={cy - 8} />
      </g>
      {/* Body of the ridge — burnt orange */}
      <g stroke={BURNT_ORANGE} strokeWidth="2.4" strokeLinecap="round">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 14} />
        <line x1={cx} y1={cy} x2={cx - 12.5} y2={cy - 8} />
        <line x1={cx} y1={cy} x2={cx + 12.5} y2={cy - 8} />
      </g>
      {/* Bright crest on top of each ridge */}
      <g stroke={BURNT_HIGHLIGHT} strokeWidth="0.85" strokeLinecap="round" transform="translate(-0.5, -0.7)">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 13} />
        <line x1={cx} y1={cy} x2={cx - 11.5} y2={cy - 7.3} />
        <line x1={cx} y1={cy} x2={cx + 11.5} y2={cy - 7.3} />
      </g>

      {/* === O / T / S letters between the ridges === */}
      <text x={cx} y={cy - 7.6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8"
        fill={BURNT_ORANGE}
        style={{ filter: "drop-shadow(0 0 1.5px rgba(255,90,15,0.4))" }}
      >O</text>
      <text x={cx - 7.5} y={cy + 6.5}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8"
        fill={BURNT_ORANGE}
        style={{ filter: "drop-shadow(0 0 1.5px rgba(255,90,15,0.4))" }}
      >T</text>
      <text x={cx + 7.5} y={cy + 6.5}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8"
        fill={BURNT_ORANGE}
        style={{ filter: "drop-shadow(0 0 1.5px rgba(255,90,15,0.4))" }}
      >S</text>
    </svg>
  );
};

export default MilitaryBolt;
