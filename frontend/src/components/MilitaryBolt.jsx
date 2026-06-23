/**
 * MilitaryBolt — a hex-head bolt rendered as if screwed into the corner of
 * the recruitment plate. The face shows three diagonal lines radiating from
 * the center to form a tri-sector head, with letters O / T / S placed in
 * each sector (OTS branding).
 *
 *      O   (top sector)
 *      |
 *  T--- ---S  (bottom-left and bottom-right sectors)
 */
const MilitaryBolt = ({ size = 36, className = "", testid = "ots-bolt" }) => (
  <svg
    viewBox="0 0 64 64"
    width={size}
    height={size}
    className={className}
    data-testid={testid}
    style={{ display: "block", filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.7))" }}
  >
    <defs>
      {/* Recessed countersink (the dark ring around the bolt) */}
      <radialGradient id="ots-countersink" cx="50%" cy="50%" r="50%">
        <stop offset="60%" stopColor="rgba(0,0,0,0.0)" />
        <stop offset="85%" stopColor="rgba(0,0,0,0.7)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.95)" />
      </radialGradient>
      {/* The bolt head itself — brushed gunmetal with a warm highlight */}
      <radialGradient id="ots-head" cx="35%" cy="32%" r="75%">
        <stop offset="0%"  stopColor="#9a8b7a" />
        <stop offset="30%" stopColor="#5a4c3f" />
        <stop offset="70%" stopColor="#2f261f" />
        <stop offset="100%" stopColor="#15110d" />
      </radialGradient>
      {/* Rim ring for the bolt edge */}
      <radialGradient id="ots-rim" cx="50%" cy="50%" r="50%">
        <stop offset="78%" stopColor="rgba(0,0,0,0)" />
        <stop offset="88%" stopColor="rgba(0,0,0,0.4)" />
        <stop offset="100%" stopColor="rgba(0,0,0,0.85)" />
      </radialGradient>
    </defs>

    {/* Outer recess shadow — the hole the bolt is screwed into */}
    <circle cx="32" cy="32" r="30" fill="url(#ots-countersink)" />
    {/* Bolt head shadow */}
    <circle cx="32" cy="32" r="25" fill="rgba(0,0,0,0.65)" />
    {/* Bolt head face */}
    <circle cx="32" cy="32" r="23" fill="url(#ots-head)" />
    {/* Bolt rim darkening */}
    <circle cx="32" cy="32" r="23" fill="url(#ots-rim)" />
    {/* Subtle top-left highlight to suggest light from upper-left */}
    <ellipse cx="25" cy="23" rx="7" ry="3" fill="rgba(255,210,170,0.18)" />

    {/* Three diagonal scoring lines radiating from center — pinwheel divider */}
    <g stroke="#080605" strokeWidth="2.2" strokeLinecap="round" opacity="0.9">
      <line x1="32" y1="32" x2="32" y2="11" />         {/* up */}
      <line x1="32" y1="32" x2="14.5" y2="42" />       {/* down-left */}
      <line x1="32" y1="32" x2="49.5" y2="42" />       {/* down-right */}
    </g>
    {/* Bright highlight on each scoring line so they read as recessed grooves */}
    <g stroke="rgba(255,180,120,0.25)" strokeWidth="0.7" strokeLinecap="round">
      <line x1="32" y1="32" x2="32" y2="13" />
      <line x1="32" y1="32" x2="16" y2="41" />
      <line x1="32" y1="32" x2="48" y2="41" />
    </g>

    {/* O T S letters in each tri-sector */}
    <text x="32" y="22"
      textAnchor="middle"
      fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8.5"
      fill="#FF6B00" style={{ filter: "drop-shadow(0 0 2px rgba(255,107,0,0.8))" }}
    >O</text>
    <text x="22" y="42"
      textAnchor="middle"
      fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8.5"
      fill="#FF6B00" style={{ filter: "drop-shadow(0 0 2px rgba(255,107,0,0.8))" }}
    >T</text>
    <text x="42" y="42"
      textAnchor="middle"
      fontFamily="Orbitron, sans-serif" fontWeight="900" fontSize="8.5"
      fill="#FF6B00" style={{ filter: "drop-shadow(0 0 2px rgba(255,107,0,0.8))" }}
    >S</text>
  </svg>
);

export default MilitaryBolt;
