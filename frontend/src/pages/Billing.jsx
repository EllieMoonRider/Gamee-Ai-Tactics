import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { CheckCircle, XCircle, Spinner, ArrowRight } from "@phosphor-icons/react";

export const BillingSuccess = () => {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [status, setStatus] = useState("polling");
  const [info, setInfo] = useState(null);
  const tries = useRef(0);
  const max = 10;

  useEffect(() => {
    if (!sessionId) { setStatus("error"); return; }
    let cancel = false;
    const poll = async () => {
      if (cancel) return;
      tries.current += 1;
      try {
        const { data } = await api.get(`/billing/checkout/${sessionId}/status`);
        setInfo(data);
        if (data.payment_status === "paid") { setStatus("paid"); return; }
        if (data.status === "expired") { setStatus("expired"); return; }
        if (tries.current >= max) { setStatus("timeout"); return; }
        setTimeout(poll, 2000);
      } catch (e) {
        setStatus("error");
      }
    };
    poll();
    return () => { cancel = true; };
  }, [sessionId]);

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-md mx-auto px-6 pt-20 text-center">
        {status === "polling" && (
          <div data-testid="billing-polling">
            <Spinner size={42} className="text-[#FFBA08] mx-auto animate-spin" />
            <h1 className="font-display text-2xl font-bold mt-4">Confirming payment…</h1>
            <p className="text-sm text-zinc-400 mt-2">Hold tight — this usually takes a few seconds.</p>
          </div>
        )}
        {status === "paid" && (
          <div data-testid="billing-paid">
            <CheckCircle size={56} weight="duotone" className="text-[#10B981] mx-auto mb-3" />
            <div className="tactical-label text-[#10B981] mb-2">// PAYMENT CONFIRMED</div>
            <h1 className="font-display text-3xl font-black tracking-tighter">Welcome to Pro, commander.</h1>
            <p className="text-sm text-zinc-400 mt-3">Your CyphrAI Deep Dive analyses are unlocked.</p>
            <Link to="/dashboard" className="btn-primary inline-flex items-center gap-2 mt-8" data-testid="billing-paid-cta">
              Enter Command Center <ArrowRight size={16} weight="bold" />
            </Link>
          </div>
        )}
        {(status === "expired" || status === "timeout" || status === "error") && (
          <div data-testid="billing-failed">
            <XCircle size={56} weight="duotone" className="text-[#E63946] mx-auto mb-3" />
            <h1 className="font-display text-2xl font-bold">{status === "expired" ? "Session expired" : status === "timeout" ? "Still processing" : "Something went wrong"}</h1>
            <p className="text-sm text-zinc-400 mt-2">
              {status === "timeout"
                ? "Your payment is still being verified by Stripe. Check back in a minute or contact support."
                : "No charge has been made if you didn't complete checkout."}
            </p>
            <Link to="/pricing" className="btn-outline inline-block mt-6">Back to pricing</Link>
          </div>
        )}
      </div>
    </div>
  );
};

export const BillingCancel = () => (
  <div className="min-h-screen">
    <Navbar />
    <div className="max-w-md mx-auto px-6 pt-20 text-center" data-testid="billing-cancel">
      <XCircle size={56} weight="duotone" className="text-zinc-500 mx-auto mb-3" />
      <h1 className="font-display text-2xl font-bold">Checkout cancelled</h1>
      <p className="text-sm text-zinc-400 mt-2">No worries — no charge has been made.</p>
      <Link to="/pricing" className="btn-primary inline-block mt-6">Back to pricing</Link>
    </div>
  </div>
);
