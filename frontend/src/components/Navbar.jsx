import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { CrosshairSimple, SignOut, UserCircle } from "@phosphor-icons/react";

const Navbar = () => {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const onAuthPage = loc.pathname === "/auth";

  return (
    <header className="glass-nav sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2.5" data-testid="navbar-logo">
          <CrosshairSimple size={22} weight="duotone" className="text-[#E63946]" />
          <span className="font-display text-lg font-bold tracking-tight">TACTICAL ALLY<span className="text-[#E63946]">.</span></span>
          <span className="tactical-label hidden sm:inline ml-2">// 37GAMES WAR ROOM</span>
        </Link>
        <nav className="flex items-center gap-3">
          {user ? (
            <>
              <Link to="/dashboard" className="text-sm text-zinc-300 hover:text-white transition px-3 py-1.5" data-testid="navbar-dashboard">Command Center</Link>
              <Link to="/war-room" className="text-sm text-zinc-300 hover:text-white transition px-3 py-1.5" data-testid="navbar-war-room">War Room</Link>
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 surface rounded">
                <UserCircle size={16} className="text-zinc-400" />
                <span className="text-sm">{user.username}</span>
              </div>
              <button onClick={() => { logout(); nav("/"); }} className="btn-outline !py-2 !px-3 flex items-center gap-1.5" data-testid="navbar-logout">
                <SignOut size={16} /> <span className="hidden sm:inline">Logout</span>
              </button>
            </>
          ) : !onAuthPage ? (
            <Link to="/auth" className="btn-primary" data-testid="navbar-signin">Sign in</Link>
          ) : null}
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
