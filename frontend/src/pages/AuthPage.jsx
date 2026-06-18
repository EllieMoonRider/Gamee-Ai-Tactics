import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../lib/auth";
import Navbar from "../components/Navbar";
import { CrosshairSimple } from "@phosphor-icons/react";

const AuthPage = () => {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, username);
      toast.success(mode === "login" ? "Welcome back, commander." : "Tactician deployed.");
      nav("/dashboard");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-md mx-auto px-6 pt-16">
        <div className="text-center mb-10">
          <CrosshairSimple size={42} weight="duotone" className="text-[#E63946] inline-block mb-3" />
          <div className="tactical-label text-zinc-500 mb-2">// ACCESS POINT</div>
          <h1 className="font-display text-3xl font-black tracking-tighter">
            {mode === "login" ? "Resume command" : "Deploy your tactician"}
          </h1>
          <p className="text-sm text-zinc-400 mt-2">
            {mode === "login" ? "Sign in to access your dashboards" : "Create an account in seconds. No card required."}
          </p>
        </div>

        <form onSubmit={submit} className="surface p-7 rounded-md space-y-4" data-testid="auth-form">
          {mode === "register" && (
            <div>
              <label className="tactical-label block mb-2">Codename</label>
              <input
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                value={username} onChange={e => setUsername(e.target.value)}
                required minLength={2} data-testid="auth-input-username"
              />
            </div>
          )}
          <div>
            <label className="tactical-label block mb-2">Email</label>
            <input
              type="email" required
              className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
              value={email} onChange={e => setEmail(e.target.value)}
              data-testid="auth-input-email"
            />
          </div>
          <div>
            <label className="tactical-label block mb-2">Password</label>
            <input
              type="password" required minLength={6}
              className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
              value={password} onChange={e => setPassword(e.target.value)}
              data-testid="auth-input-password"
            />
          </div>
          <button
            type="submit" disabled={loading}
            className="btn-primary w-full mt-2" data-testid="auth-submit-btn"
          >
            {loading ? "Processing…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
          <button
            type="button"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            className="w-full text-sm text-zinc-400 hover:text-white mt-1"
            data-testid="auth-toggle-mode"
          >
            {mode === "login" ? "Need an account? Register →" : "Already have one? Sign in →"}
          </button>
        </form>

        <p className="text-center mt-6 text-xs text-zinc-500">
          By continuing you agree this is an unofficial strategy companion.
          <Link to="/" className="block text-zinc-400 hover:text-white mt-2">← Back to home</Link>
        </p>
      </div>
    </div>
  );
};

export default AuthPage;
