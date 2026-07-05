import { forwardRef } from "react";

/**
 * WarBanner — heraldic banner in the P&C style.
 *
 * Structure:
 *  ┌── SVG crown (winged gold ornament + center jewel)
 *  │      ▼
 *  ├── Cloth body (colored, with subtle fold gradient)
 *  │    ├── central emblem (game icon)
 *  │    ├── codename badge
 *  │    ├── game name
 *  │    └── tagline
 *  │      ▼
 *  └── Jagged/tattered bottom edge (clip-path)
 *
 * All colors are CSS variables — swap the variant class for a new palette.
 */
const WarBanner = forwardRef(function WarBanner(
  { variant = "conquest", emblem, codename, name, tagline, cta = "ENGAGE ▸", intelState, primary, testid, ...rest },
  ref
) {
  return (
    <div
      ref={ref}
      className={`war-banner war-banner--${variant} ${primary ? "war-banner--primary" : ""}`}
      data-testid={testid}
      {...rest}
    >
      {/* Gold crown ornament — SVG so it scales cleanly */}
      <svg
        className="war-banner__crown"
        viewBox="0 0 200 60"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id={`wb-gold-${variant}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--banner-gold-light)" />
            <stop offset="50%" stopColor="var(--banner-gold)" />
            <stop offset="100%" stopColor="var(--banner-gold-dark)" />
          </linearGradient>
          <linearGradient id={`wb-jewel-${variant}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--banner-jewel-light)" />
            <stop offset="100%" stopColor="var(--banner-jewel)" />
          </linearGradient>
        </defs>

        {/* Left wing */}
        <path
          d="M 12 40 L 30 22 L 55 34 L 78 28 L 100 40 L 100 52 L 12 52 Z"
          fill={`url(#wb-gold-${variant})`}
          stroke="var(--banner-gold-dark)"
          strokeWidth="0.8"
        />
        {/* Right wing (mirror) */}
        <path
          d="M 188 40 L 170 22 L 145 34 L 122 28 L 100 40 L 100 52 L 188 52 Z"
          fill={`url(#wb-gold-${variant})`}
          stroke="var(--banner-gold-dark)"
          strokeWidth="0.8"
        />
        {/* Center jewel diamond */}
        <path
          d="M 100 8 L 112 24 L 100 40 L 88 24 Z"
          fill={`url(#wb-jewel-${variant})`}
          stroke="var(--banner-gold-dark)"
          strokeWidth="0.8"
        />
        {/* Jewel highlight */}
        <path d="M 100 12 L 106 22 L 100 30 L 94 22 Z" fill="var(--banner-jewel-light)" opacity="0.6" />
        {/* Small side spikes */}
        <path
          d="M 55 20 L 60 32 L 50 32 Z"
          fill={`url(#wb-gold-${variant})`}
          stroke="var(--banner-gold-dark)"
          strokeWidth="0.5"
        />
        <path
          d="M 145 20 L 150 32 L 140 32 Z"
          fill={`url(#wb-gold-${variant})`}
          stroke="var(--banner-gold-dark)"
          strokeWidth="0.5"
        />
      </svg>

      {/* Cloth body — where the emblem + text lives */}
      <div className="war-banner__cloth">
        {/* Vertical fold highlights */}
        <span className="war-banner__fold war-banner__fold--l" aria-hidden="true" />
        <span className="war-banner__fold war-banner__fold--r" aria-hidden="true" />

        {/* Codename badge (top-left of cloth) */}
        {codename && (
          <span className="war-banner__codename">
            {codename}
            {intelState && (
              <span className={`war-banner__intel war-banner__intel--${intelState.toLowerCase()}`}>
                {intelState === "VERIFIED" ? "◆" : "◇"}
              </span>
            )}
          </span>
        )}

        {/* Central emblem */}
        <div className="war-banner__emblem">
          <span className="war-banner__emblem-glow" aria-hidden="true" />
          {emblem}
        </div>

        {/* Game name */}
        <div className="war-banner__name">{name}</div>

        {/* Optional tagline */}
        {tagline && <div className="war-banner__tagline">{tagline}</div>}

        {/* Engage CTA at the very bottom */}
        <div className="war-banner__cta">{cta}</div>
      </div>
    </div>
  );
});

export default WarBanner;
