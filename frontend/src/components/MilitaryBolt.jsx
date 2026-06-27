/**
 * MilitaryBolt — Pitch-black hex bolt with RAISED OTS scoring lines.
 *
 * • Hex body: dark gunmetal edges, PITCH BLACK center so the hex
 *   shape reads clearly (no more rounded chrome dome).
 * • Three RAISED scoring lines (inverted-Y / Mercedes pattern):
 *   down, upper-left, upper-right. Each line has a top highlight + bottom
 *   shadow to read as a physical ridge rising off the black surface.
 * • OTS letters in DARK BURNT ORANGE — deep, burnished, not neon.
 */
const MilitaryBolt = ({ size = 36, className = "", testid = "ots-bolt" }) => {
  // Hexagon vertices around center (32,32). Flat-top (point-up) hex.
  const cx = 32, cy = 32, hexR = 26;
  const hexPath = (() => {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 180) * (60 * i - 90);
      pts.push([cx + hexR * Math.cos(a), cy + hexR * Math.sin(a)]);
    }
    return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(" ") + " Z";
  })();

  const BURNT_ORANGE = "#A0410B"; // deep burnt-orange for the OTS letters
  const BURNT_HIGHLIGHT = "#C25415"; // lighter highlight for raised ridge tops

  return (
    <svg
      viewBox="0 0 64 64"
      width={size}
      height={size}
      className={className}
      data-testid={testid}
      style={{ display: "block", filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.75))" }}
    >
      <defs>
        {/* Hex edge bevel — slight gunmetal highlight only at the outer rim */}
        <radialGradient id="ots-hex-edge" cx="50%" cy="50%" r="50%">
          <stop offset="76%" stopColor="rgba(0,0,0,1)" />
          <stop offset="88%" stopColor="#2a2e32" />
          <stop offset="100%" stopColor="#080a0c" />
        </radialGradient>

        {/* Pitch black hex face — "darkest desert night, no moon, no stars" */}
        <radialGradient id="ots-hex-black" cx="50%" cy="50%" r="60%">
          <stop offset="0%"   stopColor="#000000" />
          <stop offset="55%"  stopColor="#000000" />
          <stop offset="85%"  stopColor="#040404" />
          <stop offset="100%" stopColor="#0a0a0c" />
        </radialGradient>

        {/* The tiniest hint of metallic sheen on the hex perimeter */}
        <linearGradient id="ots-hex-rim" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"  stopColor="rgba(180,185,192,0.18)" />
          <stop offset="50%" stopColor="rgba(0,0,0,0)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0.5)" />
        </linearGradient>
      </defs>

      {/* Hex body shadow underneath (sits in the corner recess) */}
      <path d={hexPath} fill="rgba(0,0,0,0.6)" transform="translate(0.8, 1.4)" />

      {/* Hex body fill — pitch black */}
      <path d={hexPath} fill="url(#ots-hex-black)" />
      {/* Hex edge bevel ring */}
      <path d={hexPath} fill="url(#ots-hex-edge)" />
      {/* Faint top-to-bottom sheen across the hex */}
      <path d={hexPath} fill="url(#ots-hex-rim)" />
      {/* Crisp hex outline so the hex shape is unmistakable */}
      <path d={hexPath} fill="none" stroke="#1a1d20" strokeWidth="0.7" />

      {/* === Three RAISED scoring lines (inverted-Y / Mercedes pattern) ===
          Each line is rendered as a thick ridge with a bright burnt-orange
          highlight on top and a dark shadow underneath, so it reads as
          physically raised off the black surface. */}
      {/* Shadow beneath each ridge (offset slightly down-right) */}
      <g stroke="rgba(0,0,0,0.9)" strokeWidth="2.6" strokeLinecap="round" transform="translate(0.6, 0.9)">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 13} />
        <line x1={cx} y1={cy} x2={cx - 11.5} y2={cy - 7.5} />
        <line x1={cx} y1={cy} x2={cx + 11.5} y2={cy - 7.5} />
      </g>
      {/* Mid body of the ridge — burnt orange */}
      <g stroke={BURNT_ORANGE} strokeWidth="2.2" strokeLinecap="round">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 13} />
        <line x1={cx} y1={cy} x2={cx - 11.5} y2={cy - 7.5} />
        <line x1={cx} y1={cy} x2={cx + 11.5} y2={cy - 7.5} />
      </g>
      {/* Bright crest on TOP of the ridge — slightly offset up-left to simulate light source */}
      <g stroke={BURNT_HIGHLIGHT} strokeWidth="0.8" strokeLinecap="round" transform="translate(-0.5, -0.6)">
        <line x1={cx} y1={cy} x2={cx} y2={cy + 12} />
        <line x1={cx} y1={cy} x2={cx - 10.5} y2={cy - 6.8} />
        <line x1={cx} y1={cy} x2={cx + 10.5} y2={cy - 6.8} />
      </g>

      {/* === O / T / S letters in dark burnt orange, between the ridges === */}
      {/* O — TOP CENTER */}
      <text x={cx} y={cy - 7.2}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="7.5"
        fill={BURNT_ORANGE}
        style={{ filter: "drop-shadow(0 0 1.5px rgba(255,90,15,0.45))" }}
      >O</text>
      {/* T — LEFT */}
      <text x={cx - 7} y={cy + 6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="7.5"
        fill={BURNT_ORANGE}
        style={{ filter: "drop-shadow(0 0 1.5px rgba(255,90,15,0.45))" }}
      >T</text>
      {/* S — RIGHT */}
      <text x={cx + 7} y={cy + 6}
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="7.5"
        fill={BURNT_ORANGE}
        style={{ filter: "drop-shadow(0 0 1.5px rgba(255,90,15,0.45))" }}
      >S</text>
    </svg>
  );
};

export default MilitaryBolt;
