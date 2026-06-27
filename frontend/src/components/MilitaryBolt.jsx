/**
 * MilitaryBolt — a HEX-HEAD military bolt rendered as if screwed into the corner
 * of the recruitment plate. The hex head shows three diagonal scoring lines in a
 * Mercedes / inverted-Y pattern (one line straight down, two going up-left and
 * up-right). Letters O / T / S are placed in each of the three sectors:
 *
 *        O   (top sector — between upper-left and upper-right scoring lines)
 *      /   \
 *    T  ·  S  (left and right sectors — between each upper line and the down line)
 *       |
 *       |
 *
 * Sizing follows the `size` prop. Default 36px works for corner placement.
 */
const MilitaryBolt = ({ size = 36, className = "", testid = "ots-bolt" }) => {
  // Hexagon vertices around center (32,32) with circumradius ~24.
  // Flat-top hex orientation: vertices at 30°, 90°, 150°, 210°, 270°, 330°.
  const cx = 32, cy = 32, r = 23.5;
  const hexPath = (() => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      // Start at top vertex (rotate -90° from default)
      const a = (Math.PI / 180) * (60 * i - 90);
      pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
    }
    return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(" ") + " Z";
  })();

  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={className}
      data-testid={testid}
      style={{ display: "block", filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.7))" }}
    >
      <defs>
        {/* Recessed countersink — dark ring around the bolt */}
        <radialGradient id="ots-countersink" cx="50%" cy="50%" r="50%">
          <stop offset="60%" stopColor="rgba(0,0,0,0.0)" />
          <stop offset="85%" stopColor="rgba(0,0,0,0.7)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0.95)" />
        </radialGradient>
        {/* Hex face — brushed gunmetal with warm highlight from upper-left */}
        <radialGradient id="ots-head" cx="32%" cy="30%" r="80%">
          <stop offset="0%"  stopColor="#aa9784" />
          <stop offset="35%" stopColor="#5a4c3f" />
          <stop offset="75%" stopColor="#2a221c" />
          <stop offset="100%" stopColor="#100c0a" />
        </radialGradient>
        {/* Beveled edge ring at the rim of the hex */}
        <radialGradient id="ots-rim" cx="50%" cy="50%" r="50%">
          <stop offset="78%" stopColor="rgba(0,0,0,0)" />
          <stop offset="90%" stopColor="rgba(0,0,0,0.5)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0.85)" />
        </radialGradient>
      </defs>

      {/* Outer recess shadow (the hole the bolt is set into) */}
      <circle cx={cx} cy={cy} r="30" fill="url(#ots-countersink)" />

      {/* Hex head shadow */}
      <path d={hexPath} fill="rgba(0,0,0,0.65)" transform="translate(0.8, 1.4)" />

      {/* Hex head face */}
      <path d={hexPath} fill="url(#ots-head)" />
      {/* Hex rim shading */}
      <path d={hexPath} fill="url(#ots-rim)" />

      {/* Subtle bright highlight near upper-left edge of the hex */}
      <ellipse cx={cx - 7} cy={cy - 9} rx="6" ry="2.6" fill="rgba(255,210,170,0.22)" />

      {/* === Three scoring lines — INVERTED Y / Mercedes pattern ===
          down (6 o'clock), upper-left (10 o'clock), upper-right (2 o'clock) */}
      <g stroke="#0a0807" strokeWidth="2.2" strokeLinecap="round" opacity="0.92">
        {/* down */}
        <line x1={cx} y1={cy} x2={cx} y2={cy + 17} />
        {/* upper-left */}
        <line x1={cx} y1={cy} x2={cx - 14.5} y2={cy - 10} />
        {/* upper-right */}
        <line x1={cx} y1={cy} x2={cx + 14.5} y2={cy - 10} />
      </g>
      {/* Bright highlight along each scoring groove (top edge of recess) */}
      <g stroke="rgba(255,180,120,0.28)" strokeWidth="0.7" strokeLinecap="round">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 15} />
        <line x1={cx} y1={cy} x2={cx - 13} y2={cy - 9} />
        <line x1={cx} y1={cy} x2={cx + 13} y2={cy - 9} />
      </g>

      {/* === O / T / S letters in each sector === */}
      {/* O — TOP CENTER (between the two UPPER diagonals) */}
      <text x={cx} y={cy - 10}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8.5"
        fill="#FF6B00"
        style={{ filter: "drop-shadow(0 0 2px rgba(255,107,0,0.85))" }}
      >O</text>

      {/* T — LEFT (between the upper-left diagonal and the DOWN line) */}
      <text x={cx - 9} y={cy + 6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8.5"
        fill="#FF6B00"
        style={{ filter: "drop-shadow(0 0 2px rgba(255,107,0,0.85))" }}
      >T</text>

      {/* S — RIGHT (between the upper-right diagonal and the DOWN line) */}
      <text x={cx + 9} y={cy + 6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8.5"
        fill="#FF6B00"
        style={{ filter: "drop-shadow(0 0 2px rgba(255,107,0,0.85))" }}
      >S</text>
    </svg>
  );
};

export default MilitaryBolt;
