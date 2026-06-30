import { useEffect } from "react";
import "./LandscapePrompt.css";

/* ============================================================================
   LandscapePrompt
   Mobile-portrait gate for the cinematic Command Center. Tells the user to
   rotate to landscape so they never think the app is glitching at startup.

   Visibility is 100% CSS-driven via media queries — no JS toggling needed.
     Show when: (orientation: portrait) AND (max-width: 900px)
     Hide when: rotated to landscape OR on tablet/desktop widths

   Place inside any page that needs landscape (currently: Dashboard).
   ============================================================================ */

export default function LandscapePrompt() {
  // Add a body class while mounted so we can lock scroll under the overlay
  // only when the overlay is actually visible (the class itself is gated by
  // the same media query in CSS).
  useEffect(() => {
    document.body.classList.add("landscape-locked");
    return () => document.body.classList.remove("landscape-locked");
  }, []);

  return (
    <div
      className="landscape-prompt"
      role="dialog"
      aria-label="Please rotate your device to landscape"
      data-testid="landscape-prompt"
    >
      <div className="landscape-prompt__card">
        <span className="landscape-prompt__corner tl" />
        <span className="landscape-prompt__corner tr" />
        <span className="landscape-prompt__corner bl" />
        <span className="landscape-prompt__corner br" />

        <div className="landscape-prompt__label">// COMMAND CENTER · LANDSCAPE MODE</div>

        <div className="landscape-prompt__phone" aria-hidden="true" />

        <svg
          className="landscape-prompt__arrow"
          viewBox="0 0 56 36"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M4 18 Q 14 4, 32 6 L 26 2 M 32 6 L 30 12"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
          <path
            d="M52 18 Q 42 32, 24 30 L 30 34 M 24 30 L 26 24"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>

        <h2 className="landscape-prompt__title">Rotate Your Device</h2>

        <p className="landscape-prompt__body">
          The War Room was painted for <strong>landscape</strong>.<br />
          Turn your phone sideways to see the full battlefield.
        </p>

        <div className="landscape-prompt__beacon">
          <span className="landscape-prompt__beacon-dot" />
          <span>Awaiting orientation · landscape</span>
        </div>
      </div>
    </div>
  );
}
