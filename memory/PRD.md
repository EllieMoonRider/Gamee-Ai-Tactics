# Tactical Ally — Product Requirements (Living Doc)

## Original Problem Statement
> Create a fully functional production-ready AI game app to help gamers who play 37Games build strategies.

User direction iterations:
1. Focus on the top 10 most popular 37Games MMORPGs, including Puzzles & Conquest.
2. Rebrand to **Tactical Ally** with a **War Room** aesthetic. Renamed views: **Recruitment Center** (auth), **Command Center** (dashboard), personal **War Room**. Welcome "Briefing" message uses username. Tutorial dropdown.
3. Players can upload account screenshots → **CyphrAI Deep Dive** analysis as a baseline, with a **Building-Block** system of follow-up analyses that track progress over time.

## Stack
- Backend: FastAPI + Motor (MongoDB)
- Frontend: React 19 + Tailwind + Shadcn UI + Framer Motion + Phosphor Icons
- AI: Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) via `emergentintegrations` using EMERGENT_LLM_KEY
- Auth: JWT email/password (bcrypt) — username linked to email for recovery

## User Personas
- **Free-to-play strategist** — wants meta tier lists, F2P paths, daily planning.
- **Alliance officer** — needs event prep guides + team optimizers.
- **Returning player** — uses CyphrAI Deep Dive to baseline their account and track resumption.

## Implemented (✅ as of 2026-02)
### Backend (`/app/backend/server.py`)
- Auth: register / login / me / forgot-password / reset-password (Resend + dev-mode fallback)
- 11 games catalog (Puzzles & Conquest, Puzzles & Chaos, Puzzles & Survival, Legend, Soul Land, Days of Empire, Era of Conquest, Infinity Kingdom, League of Angels, Wartune, Dynasty Origins)
- 15 seeded guides (idempotent per-guide upsert)
- Chat sessions + streaming (CyphrAI = STRICT per-game specialist, no cross-game refs)
- Optimizer · Builds · Tasks
- Deep Dive (CyphrAI vision) — GridFS storage, MIME validation, rate-limited (5/300s/user), quota-gated (402 when no plan/topup)
- **Stripe billing**: `/api/billing/packages|quota|checkout|checkout/{sid}/status` + `/api/webhook/stripe`. `subscription_monthly $4.99/mo = 2 baselines + unlimited follow-ups` and `topup_analysis $2.99 one-time = +1 baseline`. Idempotent entitlement application.
- **Share links**: `/api/deep-dive/{id}/share` & `/api/builds/{id}/share` → public `/api/share/d/{token}` and `/api/share/b/{token}` (no shots / no user_id leak)
- Per-user rate limiting (chat 30/60s, optimizer 10/60s, deep_dive 5/300s, password_reset 3/3600s)
- TTL indexes on `rate_limits` & `password_resets`

### Frontend
- Landing `/` (11 titles, footer disclaimer)
- Recruitment Center `/auth` · Forgot `/forgot-password` · Reset `/reset-password` · show/hide password everywhere
- **Pricing** `/pricing` — 3 tiers (Free / Pro $4.99 / Top-up $2.99) + 37Games disclaimer
- **Billing** `/billing/success` (status polling) + `/billing/cancel`
- Command Center `/dashboard` — updated Briefing + Quota Widget + Tutorial dropdown + Path Cards + 11-game grid
- War Room `/war-room` — cross-game archive
- Game Page `/game/:slug` — 5 tabs (Chat · Deep Dive · Optimizer · Guides · Planner) with share buttons + friendly 402 toast
- **Public share pages** `/share/d/:token` & `/share/b/:token` (no auth)

### Testing
- Iteration 4 (final): 42/42 backend pytest passing (4 skipped — pre-paywall lifecycle tests now blocked by 402, fully covered by new quota tests). Frontend 100% — landing, pricing, billing flows, dashboard quota, 11-game grid, deep dive 402 toast, share links public pages all verified.

## Prioritized Backlog
### P1 — next iteration
- **Tactical Scouts** (F2P credit-earning system): upload game-update screenshots → CyphrAI ingests new meta info → user earns credits redeemable for analyses; secondary tasks list (try recommended games, watch tutorial videos)
- **Tactical Operations Center**: alliance/clan rooms — create/join, chat, share Deep Dives/Builds within alliance, ask CyphrAI questions in shared context
- **CyphrAI Interactive Deep Dive guided upload**: AI walks user through what to screenshot, in what order, ability to Q&A mid-flow
- Atomic `_rate_limit` ($inc per-window doc)
- Dev-only `POST /api/billing/grant-baselines` (env-flag-guarded) so old lifecycle tests can be un-skipped
- Split `server.py` (~1300 lines) into routers

### P2
- Real Resend API key (user adds to `.env`)
- Customer portal for cancellation (Stripe portal)
- Email notifications on Deep Dive completion

### P2 (nice-to-haves)
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- Push reminders for daily tasks
- More games (allow user-suggested titles)

### P3
- i18n (current AI prompt instructs to reply in user's language already; UI strings to follow)
- Marketing pages: pricing/tier if monetized
