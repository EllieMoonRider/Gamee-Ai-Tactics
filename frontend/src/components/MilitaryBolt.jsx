/**
 * MilitaryBolt — Chrome-dome hex bolt (matches user reference).
 *
 * The shape: a dark gunmetal hexagonal base with a RAISED, polished CHROME
 * DOME taking up most of the hex face. Bright specular highlight on upper-left
 * of the dome (light from above-left) and a soft shadow on lower-right.
 *
 * The OTS design is laid OVER the dome in the brand orange:
 *   • Three scoring lines in an inverted-Y / Mercedes pattern
 *     (down, upper-left, upper-right)
 *   • O at top center sector
 *   • T at left sector
 *   • S at right sector
 *
 * The "0.0" marking from the reference is intentionally excluded.
 */
const MilitaryBolt = ({ size = 36, className = "", testid = "ots-bolt" }) => {
  // Hexagon vertices around center (32,32). Flat-top hex (pointing up & down).
  const cx = 32, cy = 32, hexR = 26;
  const hexPath = (() => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 180) * (60 * i - 90); // start at top vertex
      pts.push([cx + hexR * Math.cos(a), cy + hexR * Math.sin(a)]);
    }
    return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(" ") + " Z";
  })();

  // Chrome dome radius — fills most of the hex face
  const domeR = 18;

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
        {/* Dark gunmetal hex body — flat with subtle gradient */}
        <linearGradient id="ots-hex-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"  stopColor="#4a5158" />
          <stop offset="55%" stopColor="#2a2f34" />
          <stop offset="100%" stopColor="#15181b" />
        </linearGradient>

        {/* Chrome dome — bright polished steel with light from upper-left */}
        <radialGradient id="ots-dome" cx="36%" cy="30%" r="78%">
          <stop offset="0%"   stopColor="#f5f8fb" />
          <stop offset="22%"  stopColor="#d8dde2" />
          <stop offset="55%"  stopColor="#a4abb2" />
          <stop offset="82%"  stopColor="#6a7077" />
          <stop offset="100%" stopColor="#3a3e42" />
        </radialGradient>

        {/* Dome rim shading — slightly darker around the circle edge */}
        <radialGradient id="ots-dome-rim" cx="50%" cy="50%" r="50%">
          <stop offset="82%" stopColor="rgba(0,0,0,0)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0.5)" />
        </radialGradient>

        {/* Tiny cast shadow under the dome (so it reads as raised) */}
        <radialGradient id="ots-dome-shadow" cx="50%" cy="55%" r="50%">
          <stop offset="80%" stopColor="rgba(0,0,0,0.6)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0)" />
        </radialGradient>
      </defs>

      {/* Hex body shadow underneath the bolt (sits in the corner recess) */}
      <path d={hexPath} fill="rgba(0,0,0,0.55)" transform="translate(0.8, 1.4)" />

      {/* Hex body */}
      <path d={hexPath} fill="url(#ots-hex-body)" />
      {/* Hex edge outline */}
      <path d={hexPath} fill="none" stroke="rgba(8,10,12,0.8)" strokeWidth="0.5" />

      {/* Soft cast shadow ring underneath the dome to suggest the dome is raised */}
      <ellipse cx={cx} cy={cy + 0.6} rx={domeR + 1.5} ry={domeR + 1.5}
               fill="url(#ots-dome-shadow)" />

      {/* The chrome dome itself */}
      <circle cx={cx} cy={cy} r={domeR} fill="url(#ots-dome)" />
      {/* Dome rim darkening */}
      <circle cx={cx} cy={cy} r={domeR} fill="url(#ots-dome-rim)" />
      {/* Thin bright highlight along the upper-left rim */}
      <path
        d={`M ${cx - domeR + 1} ${cy - 1} A ${domeR - 1} ${domeR - 1} 0 0 1 ${cx - 2} ${cy - domeR + 1}`}
        fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth="0.6"
      />
      {/* Bright specular gleam — small bright spot on upper-left of the dome */}
      <ellipse cx={cx - 5.5} cy={cy - 7.5} rx="5.5" ry="2.8" fill="rgba(255,255,255,0.65)" />
      <ellipse cx={cx - 5.5} cy={cy - 7.5} rx="2.4" ry="1.1" fill="rgba(255,255,255,0.9)" />

      {/* ====== OTS design overlay (set aside from previous bolt — unchanged) ======
          Inverted-Y / Mercedes pattern: down, upper-left, upper-right
          Letters: O top, T left, S right */}
      <g stroke="rgba(20,22,26,0.55)" strokeWidth="1.6" strokeLinecap="round">
        {/* down */}
        <line x1={cx} y1={cy} x2={cx} y2={cy + 13} />
        {/* upper-left */}
        <line x1={cx} y1={cy} x2={cx - 11.5} y2={cy - 7.5} />
        {/* upper-right */}
        <line x1={cx} y1={cy} x2={cx + 11.5} y2={cy - 7.5} />
      </g>

      {/* O — TOP CENTER (between the two UPPER diagonals) */}
      <text x={cx} y={cy - 7.2}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="7.5"
        fill="#FF6B00"
        style={{ filter: "drop-shadow(0 0 1.5px rgba(0,0,0,0.7))" }}
      >O</text>

      {/* T — LEFT (between the upper-left diagonal and the DOWN line) */}
      <text x={cx - 7} y={cy + 6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="7.5"
        fill="#FF6B00"
        style={{ filter: "drop-shadow(0 0 1.5px rgba(0,0,0,0.7))" }}
      >T</text>

      {/* S — RIGHT (between the upper-right diagonal and the DOWN line) */}
      <text x={cx + 7} y={cy + 6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="7.5"
        fill="#FF6B00"
        style={{ filter: "drop-shadow(0 0 1.5px rgba(0,0,0,0.7))" }}
      >S</text>
    </svg>
  );
};

export default MilitaryBolt;
