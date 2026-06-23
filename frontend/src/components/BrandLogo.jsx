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
          <circle cx={VB / 2} cy={VB / 2} r={140} />
        </clipPath>
        {/* Top arc — text reads L→R curving across the top above the circle */}
        <path
          id="bl-top-arc"
          d={`M ${VB / 2 - 195} ${VB / 2} A 195 195 0 0 1 ${VB / 2 + 195} ${VB / 2}`}
          fill="none"
        />
        {/* Bottom arc — text reads L→R curving across the bottom below the circle */}
        <path
          id="bl-bottom-arc"
          d={`M ${VB / 2 - 195} ${VB / 2} A 195 195 0 0 0 ${VB / 2 + 195} ${VB / 2}`}
          fill="none"
        />
      </defs>

      {/* Dragon icon clipped into the circle */}
      <image href={iconImg} x={VB / 2 - 140} y={VB / 2 - 140} width={280} height={280} clipPath="url(#bl-icon-clip)" />

      {/* Inner glow ring */}
      <circle cx={VB / 2} cy={VB / 2} r={142} fill="none" stroke="#FF6B00" strokeWidth="1.5" opacity="0.75"
              style={{ filter: "drop-shadow(0 0 10px rgba(255,107,0,0.8))" }} />
      {/* Outer dashed ring */}
      <circle cx={VB / 2} cy={VB / 2} r={158} fill="none" stroke="#FF6B00" strokeWidth="0.6" opacity="0.4" strokeDasharray="4 6" />

      {showText && (
        <>
          {/* TOP — TACTICAL ALLY */}
          <text
            fontFamily="Orbitron, sans-serif"
            fontWeight="900"
            fontSize="30"
            fill="#FF6B00"
            letterSpacing="4"
            style={{ filter: "drop-shadow(0 0 6px rgba(255,107,0,0.9)) drop-shadow(0 0 18px rgba(255,107,0,0.4))" }}
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
