import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./lib/auth";
import Landing from "./pages/Landing";
import AuthPage from "./pages/AuthPage";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import GamePage from "./pages/GamePage";
import WarRoom from "./pages/WarRoom";
import Pricing from "./pages/Pricing";
import { BillingSuccess, BillingCancel } from "./pages/Billing";
import { PublicDeepDive, PublicBuild } from "./pages/Public";
import "./App.css";

const Protected = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-zinc-500 font-mono-tactical text-sm">LOADING…</div>;
  if (!user) return <Navigate to="/auth" replace />;
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster theme="dark" position="bottom-right" richColors />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/billing/success" element={<BillingSuccess />} />
          <Route path="/billing/cancel" element={<BillingCancel />} />
          <Route path="/share/d/:token" element={<PublicDeepDive />} />
          <Route path="/share/b/:token" element={<PublicBuild />} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/war-room" element={<Protected><WarRoom /></Protected>} />
          <Route path="/game/:slug" element={<Protected><GamePage /></Protected>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
