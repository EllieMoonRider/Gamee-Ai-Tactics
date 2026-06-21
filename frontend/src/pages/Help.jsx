import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Lifebuoy, EnvelopeSimple, ChatCircle, CheckCircle, Question, CreditCard, Bug, ShieldWarning, Lightbulb, UserCircle } from "@phosphor-icons/react";

const CATEGORY_OPTIONS = [
  { value: "billing", label: "Billing & Payments", icon: CreditCard, color: "#FFBA08" },
  { value: "technical", label: "Bug / Technical issue", icon: Bug, color: "#E63946" },
  { value: "account", label: "Account & Login", icon: UserCircle, color: "#10B981" },
  { value: "refund", label: "Refund request", icon: ShieldWarning, color: "#A1A1AA" },
  { value: "feature_request", label: "Feature request", icon: Lightbulb, color: "#A78BFA" },
  { value: "feedback", label: "Feedback", icon: ChatCircle, color: "#60A5FA" },
  { value: "other", label: "Something else", icon: Question, color: "#A1A1AA" },
];

const FAQS = [
  {
    q: "How do Deep Dive baselines work?",
    a: "A baseline is your initial CypherAI analysis of a game screenshot. Each Pro subscription gives 2 baselines per month. After the baseline, you can ask unlimited follow-up Building Block questions about that same Deep Dive — those don't count against your quota.",
  },
  {
    q: "Can I get a refund?",
    a: "Yes. Tactical Ally has a 7-day refund window for subscriptions, no questions asked. One-shot Deep Dives ($2.99) are refundable only if unused. Submit a refund request via the form below with your transaction email.",
  },
  {
    q: "Why is my screenshot rejected?",
    a: "We only accept images (PNG, JPG, WebP) under 10 MB. Files must be at least 100 bytes of valid image data — corrupted or empty files are blocked. Try re-taking the screenshot or saving in a different format.",
  },
  {
    q: "How does the per-member alliance chat fee work?",
    a: "Each member pays their own $0.99/mo. Pro is also required. We chose self-pay so alliance leaders don't get stuck paying for inactive members. R5s can grant free seats through the OTS Seats page for trusted officers.",
  },
  {
    q: "What are Tactical Scouts credits?",
    a: "F2P path: earn credits by uploading game-update screenshots, watching strategy videos, or trying recommended games. 1 credit = $1 of in-app value. 3 credits unlock 1 free Deep Dive baseline.",
  },
  {
    q: "Is Tactical Ally affiliated with 37Games?",
    a: "No. Tactical Ally is an unofficial fan-made companion. We do not automate gameplay, read memory, or interact with 37Games servers. All game names and trademarks belong to their owners.",
  },
];

const Help = () => {
  const { user } = useAuth();
  const [form, setForm] = useState({
    name: user?.username || "",
    email: user?.email || "",
    category: "technical",
    subject: "",
    message: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (form.message.trim().length < 10) {
      toast.error("Please provide a bit more detail (at least 10 characters).");
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await api.post("/support/tickets", form);
      setSubmittedId(data.id);
      toast.success("Ticket submitted! Check your email.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <div>
          <div className="tactical-label text-[#E63946] mb-2">// COMMAND CENTER · SUPPORT</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tighter flex items-center gap-3">
            <Lifebuoy size={32} weight="duotone" className="text-[#E63946]" /> Help & Support
          </h1>
          <p className="text-sm text-zinc-400 mt-2 max-w-xl">
            Got a question, bug, or refund request? We typically reply within <strong className="text-[#10B981]">48 hours</strong>. Browse the FAQ below first — many answers live there.
          </p>
        </div>

        {/* FAQ */}
        <div className="surface rounded-md p-6">
          <div className="tactical-label text-[#FFBA08] mb-4">// FREQUENTLY ASKED</div>
          <div className="space-y-3" data-testid="faq-list">
            {FAQS.map((f, i) => (
              <details key={i} className="group border border-white/5 rounded-md bg-[#0c0c0c] open:ring-1 open:ring-[#E63946]/30" data-testid={`faq-item-${i}`}>
                <summary className="cursor-pointer list-none p-4 flex items-center justify-between gap-3 select-none">
                  <span className="text-sm font-medium text-zinc-200">{f.q}</span>
                  <span className="text-[#FFBA08] text-xl leading-none group-open:rotate-45 transition-transform">+</span>
                </summary>
                <div className="px-4 pb-4 text-sm text-zinc-400 leading-relaxed border-t border-white/5 pt-3">{f.a}</div>
              </details>
            ))}
          </div>
        </div>

        {/* Contact form OR confirmation */}
        {submittedId ? (
          <div className="surface rounded-md p-8 text-center" data-testid="ticket-confirmation">
            <CheckCircle size={48} weight="duotone" className="text-[#10B981] mx-auto mb-3" />
            <h2 className="font-display text-2xl font-bold tracking-tight">Ticket received</h2>
            <p className="text-sm text-zinc-400 mt-2">
              Your ticket <strong className="text-[#FFBA08] font-mono-tactical">#{submittedId.slice(0, 8)}</strong> is in the queue. We&apos;ll respond to <strong className="text-white">{form.email}</strong> within 48 hours.
            </p>
            <div className="flex gap-3 justify-center mt-6 flex-wrap">
              <button onClick={() => { setSubmittedId(null); setForm({ ...form, subject: "", message: "" }); }} className="btn-outline" data-testid="ticket-submit-another">Submit another</button>
              {user && <Link to="/dashboard" className="btn-primary" data-testid="ticket-back-dashboard">Back to Command Center</Link>}
            </div>
          </div>
        ) : (
          <form onSubmit={submit} className="surface rounded-md p-6 space-y-5" data-testid="support-form">
            <div className="tactical-label text-[#10B981] mb-1">// SUBMIT A TICKET</div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="tactical-label mb-2 block">Your name</label>
                <input
                  value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                  required maxLength={80}
                  className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                  data-testid="support-input-name"
                />
              </div>
              <div>
                <label className="tactical-label mb-2 block">Email <span className="text-zinc-600">(for reply)</span></label>
                <input
                  type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                  required
                  className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                  data-testid="support-input-email"
                />
              </div>
            </div>

            <div>
              <label className="tactical-label mb-2 block">Category</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2" data-testid="support-categories">
                {CATEGORY_OPTIONS.map(opt => {
                  const Icon = opt.icon;
                  const active = form.category === opt.value;
                  return (
                    <button
                      key={opt.value} type="button"
                      onClick={() => setForm({ ...form, category: opt.value })}
                      className={`p-2.5 rounded-md border text-xs flex items-center gap-2 transition ${active ? "bg-white/5 ring-1" : "border-white/10 hover:border-white/30"}`}
                      style={active ? { borderColor: opt.color, color: opt.color, "--tw-ring-color": opt.color } : {}}
                      data-testid={`support-cat-${opt.value}`}
                    >
                      <Icon size={16} weight="duotone" style={{ color: opt.color }} />
                      <span className="truncate text-left">{opt.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="tactical-label mb-2 block">Subject</label>
              <input
                value={form.subject} onChange={e => setForm({ ...form, subject: e.target.value })}
                required minLength={1} maxLength={200}
                placeholder="e.g. Can't upload screenshot in Puzzles & Conquest"
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm"
                data-testid="support-input-subject"
              />
            </div>

            <div>
              <label className="tactical-label mb-2 block">Describe the issue <span className="text-zinc-600">(min 10 chars)</span></label>
              <textarea
                value={form.message} onChange={e => setForm({ ...form, message: e.target.value })}
                required minLength={10} maxLength={8000} rows={7}
                placeholder="Include steps to reproduce, what you expected, what actually happened, error messages, browser, device, etc."
                className="w-full bg-[#0c0c0c] border border-white/10 rounded px-3 py-2.5 text-sm font-sans leading-relaxed"
                data-testid="support-input-message"
              />
              <div className="text-[11px] text-zinc-500 mt-1 font-mono-tactical text-right">{form.message.length}/8000</div>
            </div>

            <button
              type="submit" disabled={submitting}
              className="btn-primary w-full" data-testid="support-submit-btn"
            >
              {submitting ? "Submitting…" : "Submit Ticket"}
            </button>

            <p className="text-[11px] text-zinc-500 text-center">
              Or email us directly: <a href="mailto:info.warroomsupport@gmail.com" className="text-[#FFBA08] hover:underline" data-testid="support-direct-email">info.warroomsupport@gmail.com</a>
            </p>
          </form>
        )}

        {user && (
          <Link to="/support/my-tickets" className="block surface rounded-md p-4 hover:ring-1 hover:ring-[#FFBA08]/40 transition" data-testid="view-my-tickets-link">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <EnvelopeSimple size={20} weight="duotone" className="text-[#FFBA08]" />
                <div>
                  <div className="font-display font-bold">View my tickets</div>
                  <div className="text-xs text-zinc-500">Check status & responses on previously submitted tickets</div>
                </div>
              </div>
              <span className="text-zinc-500">→</span>
            </div>
          </Link>
        )}
      </div>
    </div>
  );
};

export default Help;
