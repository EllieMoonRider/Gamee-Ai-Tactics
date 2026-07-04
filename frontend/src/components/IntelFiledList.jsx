import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL;

const GAME_TAG = {
  "puzzles-conquest": "P&C",
  "puzzles-survival": "P&S",
  "puzzles-chaos":    "P&Chaos",
};

/**
 * IntelFiledList
 * Simple alphabetical flat list of intel already filed to CypherAI.
 * Used both inline (as a collapsible widget on /intel-drop) and as the main
 * body of the /intel-log page. Kept intentionally minimal — one line per entry
 * so contributors can quickly scan for duplicates.
 */
export default function IntelFiledList({ testidPrefix = "filed" }) {
  const [entries, setEntries] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/intel/log`)
      .then(r => setEntries(r.data.entries || []))
      .catch(() => setEntries([]));
  }, []);

  const sorted = useMemo(() => {
    if (!entries) return null;
    return [...entries].sort((a, b) => {
      const at = (a.title || "").toLowerCase();
      const bt = (b.title || "").toLowerCase();
      return at.localeCompare(bt);
    });
  }, [entries]);

  if (sorted === null) {
    return <p className="intel-filed__loading">SYNCING LOG…</p>;
  }
  if (sorted.length === 0) {
    return <p className="intel-filed__empty">Nothing filed yet. Be the first!</p>;
  }

  return (
    <ul className="intel-filed__list" data-testid={`${testidPrefix}-list`}>
      {sorted.map((e) => (
        <li key={e.reference} className="intel-filed__item" data-testid={`${testidPrefix}-item-${e.reference}`}>
          <span className="intel-filed__game">{GAME_TAG[e.game_slug] || "?"}</span>
          <span className="intel-filed__title">{e.title || "(no title)"}</span>
          {e.contributor_name && (
            <span className="intel-filed__author">· {e.contributor_name}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
