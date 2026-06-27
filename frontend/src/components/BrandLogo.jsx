/**
 * BrandLogo — The official Tactical Ally brand mark.
 * Dragon-in-radar circle with TACTICAL ALLY arched across the top and
 * CYPHERAI STRATEGIES arched across the bottom.
 *
 * Use this anywhere you'd otherwise repeat the splash emblem (auth page,
 * about page, share cards, footer, etc.). Sizing follows the `size` prop.
 */
import iconImg from "../assets/tactical-ally-icon.png";

const BrandLogo = ({ size = 220, showText = true, className = "", testid = "brand-logo" }) => {
  const VB = 460; // viewBox edge — square
  return (
    <svg
      viewBox={`0 0 ${VB} ${VB}`}
      preserveAspectRatio="xMidYMid meet"
      width={size}
      height={size}
      className={className}
      data-testid={testid}
      style={{ display: "block" }}
    >
      <defs>
        <clipPath id="bl-icon-clip">
          <circle cx={VB / 2} cy={VB / 2} r={110} />
        </clipPath>
        {/* Top arc — brought close to the smaller circle's outer edge */}
        <path
          id="bl-top-arc"
          d={`M ${VB / 2 - 132} ${VB / 2} A 132 132 0 0 1 ${VB / 2 + 132} ${VB / 2}`}
          fill="none"
        />
        {/* Bottom arc — same close spacing on the underside */}
        <path
          id="bl-bottom-arc"
          d={`M ${VB / 2 - 132} ${VB / 2} A 132 132 0 0 0 ${VB / 2 + 132} ${VB / 2}`}
          fill="none"
        />
      </defs>

      {/* Dragon icon clipped into the (smaller) circle */}
      <image href={iconImg} x={VB / 2 - 110} y={VB / 2 - 110} width={220} height={220} clipPath="url(#bl-icon-clip)" />

      {/* Inner glow ring */}
      <circle cx={VB / 2} cy={VB / 2} r={112} fill="none" stroke="#FF6B00" strokeWidth="1.5" opacity="0.75"
              style={{ filter: "drop-shadow(0 0 10px rgba(255,107,0,0.8))" }} />
      {/* Outer dashed ring */}
      <circle cx={VB / 2} cy={VB / 2} r={124} fill="none" stroke="#FF6B00" strokeWidth="0.6" opacity="0.4" strokeDasharray="4 6" />

      {showText && (
        <>
          {/* TOP — TACTICAL ALLY — same font size as bottom for visual symmetry */}
          <text
            fontFamily="Orbitron, sans-serif"
            fontWeight="900"
            fontSize="20"
            fill="#FF6B00"
            letterSpacing="3"
            style={{ filter: "drop-shadow(0 0 4px rgba(255,107,0,0.85)) drop-shadow(0 0 14px rgba(255,107,0,0.35))" }}
          >
            <textPath href="#bl-top-arc" startOffset="50%" textAnchor="middle">
              TACTICAL ALLY
            </textPath>
          </text>

          {/* BOTTOM — CYPHERAI STRATEGIES */}
          <text
            fontFamily="Orbitron, sans-serif"
            fontWeight="700"
            fontSize="20"
            fill="#FF6B00"
            letterSpacing="3"
            style={{ filter: "drop-shadow(0 0 4px rgba(255,107,0,0.7))" }}
          >
            <textPath href="#bl-bottom-arc" startOffset="50%" textAnchor="middle">
              CYPHERAI STRATEGIES
            </textPath>
          </text>
        </>
      )}
    </svg>
  );
};

export default BrandLogo;
