import { Link } from "react-router-dom";

/**
 * CommandCenterWidget
 * A compact, cinematic tap-target used on the Command Center for
 * top-level navigation (Tutorial, Tactical Scout, etc.). Neon-outlined
 * tactical pill with a mono-tactical label above a display headline.
 *
 * Props:
 *   to        — react-router path (or fragment link)
 *   label     — small monospace label above the title (e.g. "01 · TUTORIAL")
 *   title     — bold display headline (e.g. "How Tactical Ally Works")
 *   testid    — data-testid string for the anchor
 */
export default function CommandCenterWidget({ to, label, title, testid }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="cc-widget group"
    >
      <span className="cc-widget__label">{label}</span>
      <span className="cc-widget__title">{title}</span>
      <span className="cc-widget__arrow" aria-hidden="true">▸</span>
    </Link>
  );
}
