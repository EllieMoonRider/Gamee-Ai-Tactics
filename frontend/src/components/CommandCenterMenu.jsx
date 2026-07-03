import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";

/**
 * CommandCenterMenu
 * Top-right hamburger menu on the Command Center.
 * Items:
 *   • Who is Cypher   → /cypher
 *   • Q&A             → /help
 *   • Support         → /help#support
 *   • Logout          → clears session + redirects to /auth
 */
export default function CommandCenterMenu() {
  const [open, setOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const menuRef = useRef(null);
  const auth = useAuth();
  const nav = useNavigate();

  // Check admin status once user is loaded (drives visibility of Intel Review link)
  useEffect(() => {
    if (!auth?.user) return;
    api.get("/support/admin/check")
      .then(r => setIsAdmin(!!r.data?.is_admin))
      .catch(() => setIsAdmin(false));
  }, [auth?.user]);

  // Close on outside click / ESC
  useEffect(() => {
    if (!open) return;
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const handleLogout = (e) => {
    e.preventDefault();
    setOpen(false);
    auth?.logout?.();
    nav("/auth");
  };

  return (
    <div ref={menuRef} className="cc-menu-wrap">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-label="Open menu"
        aria-expanded={open}
        className="cc-menu-btn"
        data-testid="cc-menu-btn"
      >
        <span className="cc-menu-bar" />
        <span className="cc-menu-bar" />
        <span className="cc-menu-bar" />
      </button>

      {open && (
        <div className="cc-menu-panel" role="menu" data-testid="cc-menu-panel">
          <Link
            to="/cypher"
            className="cc-menu-item"
            role="menuitem"
            data-testid="cc-menu-cypher"
            onClick={() => setOpen(false)}
          >
            Who is Cypher
          </Link>
          <Link
            to="/help"
            className="cc-menu-item"
            role="menuitem"
            data-testid="cc-menu-qa"
            onClick={() => setOpen(false)}
          >
            Q&amp;A
          </Link>
          <Link
            to="/help#support"
            className="cc-menu-item"
            role="menuitem"
            data-testid="cc-menu-support"
            onClick={() => setOpen(false)}
          >
            Support
          </Link>
          <Link
            to="/intel-drop"
            className="cc-menu-item"
            role="menuitem"
            data-testid="cc-menu-intel-drop"
            onClick={() => setOpen(false)}
          >
            Drop Intel
          </Link>
          {isAdmin && (
            <Link
              to="/admin/intel"
              className="cc-menu-item cc-menu-item--admin"
              role="menuitem"
              data-testid="cc-menu-intel-review"
              onClick={() => setOpen(false)}
            >
              Intel Review Queue
            </Link>
          )}
          <button
            type="button"
            className="cc-menu-item cc-menu-item--danger"
            role="menuitem"
            data-testid="cc-menu-logout"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}
