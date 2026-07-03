import { useNavigate } from "react-router-dom";
import { CastleTurret, BuildingApartment, Skull } from "@phosphor-icons/react";
import "./GameBeacons.css";

/* ============================================================================
   GameBeacons (Layer 2)
   Three cinematic tactical beacons placed on the holographic grid floor.
   Each represents one of the 3 active battle theaters (Feb 2026 scope).
   Click → routes to that game's War Room (/game/:slug).
   Positioned bottom-anchored so they sit inside the projected floor zone.
   ============================================================================ */

const BEACONS = [
  {
    slug: "puzzles-survival",
    name: "Puzzles & Survival",
    codename: "T-01",
    theater: "SURVIVAL THEATER",
    tagline: "Zombie ops · Sanctuary · Heroes",
    icon: BuildingApartment,
    intel: "PENDING",
    // Left-front position on the grid floor
    position: { left: "18%", bottom: "8%" },
    color: "#00FF80",
  },
  {
    slug: "puzzles-conquest",
    name: "Puzzles & Conquest",
    codename: "T-02",
    theater: "PRIMARY THEATER",
    tagline: "Kingdom war · Dragons · Alliance PvP",
    icon: CastleTurret,
    intel: "VERIFIED",
    // Center-front — hero position
    position: { left: "50%", bottom: "12%" },
    color: "#FF6B00",
    primary: true,
  },
  {
    slug: "puzzles-chaos",
    name: "Puzzles & Chaos",
    codename: "T-03",
    theater: "CHAOS THEATER",
    tagline: "Dark fantasy · Runes · Corrupted realm",
    icon: Skull,
    intel: "PENDING",
    // Right-front
    position: { left: "82%", bottom: "8%" },
    color: "#00FF80",
  },
];

export default function GameBeacons() {
  const nav = useNavigate();
  return (
    <div className="game-beacons" data-testid="game-beacons">
      {BEACONS.map((b, i) => {
        const Icon = b.icon;
        return (
          <button
            key={b.slug}
            onClick={() => nav(`/game/${b.slug}`)}
            className={`beacon ${b.primary ? "beacon--primary" : ""}`}
            style={{
              left: b.position.left,
              bottom: b.position.bottom,
              animationDelay: `${i * 0.18}s`,
              "--beacon-color": b.color,
            }}
            data-testid={`game-beacon-${b.slug}`}
            aria-label={`Enter ${b.name} war room`}
          >
            {/* Ground-anchor pulse ring — projected on the floor */}
            <span className="beacon__ring" aria-hidden="true" />
            <span className="beacon__ring beacon__ring--2" aria-hidden="true" />

            {/* Vertical light column */}
            <span className="beacon__column" aria-hidden="true" />

            {/* Tactical panel with icon + name */}
            <span className="beacon__panel">
              <span className="beacon__corner tl" />
              <span className="beacon__corner tr" />
              <span className="beacon__corner bl" />
              <span className="beacon__corner br" />

              <span className="beacon__header">
                <span className="beacon__codename">{b.codename}</span>
                <span className={`beacon__intel beacon__intel--${b.intel.toLowerCase()}`}>
                  {b.intel === "VERIFIED" ? "◆ INTEL VERIFIED" : "◇ INTEL PENDING"}
                </span>
              </span>

              <span className="beacon__icon-wrap">
                <Icon size={28} weight="duotone" />
              </span>

              <span className="beacon__theater">{b.theater}</span>
              <span className="beacon__name">{b.name}</span>
              <span className="beacon__tagline">{b.tagline}</span>

              <span className="beacon__cta">
                ENGAGE <span aria-hidden="true">▸</span>
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
