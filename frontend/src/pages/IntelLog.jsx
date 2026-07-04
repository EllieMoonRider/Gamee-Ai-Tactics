import { Link } from "react-router-dom";
import { ArrowLeft } from "@phosphor-icons/react";
import IntelFiledList from "../components/IntelFiledList";
import "../components/IntelFiledList.css";
import "./IntelDrop.css";
import "./IntelLog.css";

/**
 * IntelLog — public read-only page.
 * Simple alphabetical list of filed intel so contributors can check for duplicates
 * before submitting. Same list component as the collapsible widget on /intel-drop.
 */
export default function IntelLog() {
  return (
    <div className="intel-drop intel-log" data-testid="intel-log-page">
      <div className="intel-bg" aria-hidden="true" />
      <div className="intel-scanline" aria-hidden="true" />

      <div className="intel-shell">
        <div className="intel-header">
          <Link to="/intel-drop" className="intel-back" data-testid="log-back-drop">
            <ArrowLeft size={14} weight="bold" /> DROP MORE INTEL
          </Link>
          <span className="intel-header__stamp">// INTEL LOG · PUBLIC READ</span>
        </div>

        <h1 className="intel-log__title">Intel Log</h1>
        <p className="intel-log__desc">
          What&apos;s already filed. Check here before submitting to avoid duplicates.
          Sorted alphabetically by title.
        </p>

        <div className="intel-log__body" data-testid="intel-log-body">
          <IntelFiledList testidPrefix="log" />
        </div>

        <div className="intel-log__cta">
          Don&apos;t see your intel here?
          <Link to="/intel-drop">Drop it now →</Link>
        </div>
      </div>
    </div>
  );
}
