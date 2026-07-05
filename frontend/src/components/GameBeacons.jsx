import { useNavigate } from "react-router-dom";
import { Skull, Shield, Lightning } from "@phosphor-icons/react";
import WarBanner from "./WarBanner";
import "./WarBanner.css";
import "./GameBeacons.css";

/* ============================================================================
   GameBeacons (Layer 2)
   Three heraldic war banners hanging in the Command Center war-room, each
   representing one of the 3 active battle theaters. Click routes to that
   game's War Room. Uses the WarBanner component styled in the P&C banner
   language (gold winged crown + colored cloth + jagged tattered bottom).
   Order: LEFT=Survival · MIDDLE=Conquest (primary) · RIGHT=Chaos
   ============================================================================ */

const BEACONS = [
  {
    slug: "puzzles-survival",
    name: "Puzzles & Survival",
    codename: "T-01",
    tagline: "Zombie Ops · Sanctuary · Heroes",
    icon: Skull,
    intel: "PENDING",
    variant: "survival",
  },
  {
    slug: "puzzles-conquest",
    name: "Puzzles & Conquest",
    codename: "T-02",
    tagline: "Kingdom War · Dragons · Alliance",
    icon: Shield,
    intel: "VERIFIED",
    variant: "conquest",
    primary: true,
  },
  {
    slug: "puzzles-chaos",
    name: "Puzzles & Chaos",
    codename: "T-03",
    tagline: "Dark Fantasy · Runes · Corruption",
    icon: Lightning,
    intel: "PENDING",
    variant: "chaos",
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
            className="game-beacons__slot"
            style={{ animationDelay: `${i * 0.18}s` }}
            data-testid={`game-beacon-${b.slug}`}
            aria-label={`Enter ${b.name} war room`}
          >
            <WarBanner
              variant={b.variant}
              codename={b.codename}
              name={b.name}
              tagline={b.tagline}
              intelState={b.intel}
              primary={b.primary}
              testid={`war-banner-${b.slug}`}
              emblem={<Icon weight="fill" />}
            />
          </button>
        );
      })}
    </div>
  );
}
