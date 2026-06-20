# Tactical Ally — Product Requirements (Living Doc)

## Original Problem Statement
> Create a fully functional production-ready AI game app to help gamers who play 37Games build strategies.

User direction iterations:
1. Focus on the top 10 most popular 37Games MMORPGs, including Puzzles & Conquest.
2. Rebrand to **Tactical Ally** with a **War Room** aesthetic. Renamed views: **Recruitment Center** (auth), **Command Center** (dashboard), personal **War Room**.
3. Players can upload account screenshots → **CyphrAI Deep Dive** analysis as a baseline, with a **Building-Block** system of follow-up analyses.
4. **Pricing overhaul (Feb 2026)**: $4.99/mo Pro = full access for 2 games (user-selectable). +$0.99/mo per extra game slot. Alliance chat is $0.99/mo **per member** (each player self-pays). $2.99 one-shot Deep Dive stays.
5. **Tactical Scouts (Feb 2026)**: F2P credit system — 1 credit = $1. Earn by uploading game-update screenshots (0.25), watching videos (0.10), trying recommended games (0.50), daily login (0.05). 3 credits = +1 free Deep Dive baseline.
6. OTS alliance: 100-seat admin grant cap, referral mechanism, calendar/milestone tracking.

## Stack
- Backend: FastAPI + Motor (MongoDB)
- Frontend: React 19 + Tailwind + Shadcn UI + Framer Motion + Phosphor Icons
- AI: Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) via `emergentintegrations` using EMERGENT_LLM_KEY
- Auth: JWT email/password (bcrypt) — username linked to email for recovery
- Payments: Stripe test mode (live SKUs computed from PACKAGES dict)

## Implemented (✅ as of 2026-02)

### Backend (`/app/backend/server.py`, 2384 lines)
- Auth + Password Reset (Resend + dev fallback)
- 11 games catalog with strict per-game CyphrAI specialist prompts
- Chat (streaming + rate-limited 30/60s), Optimizer, Builds, 15 Guides, Tasks
- Deep Dive — GridFS storage, MIME validation, rate-limited, quota-gated 402, **per-game gating via pro_games[]**
- **Stripe billing — 4 SKUs**:
  - `subscription_monthly` $4.99/mo: 2 Deep Dive baselines + 2 game slots
  - `topup_analysis` $2.99 one-shot: +1 baseline, ANY game
  - `extra_game_monthly` $0.99/mo: +1 game slot (recurring)
  - `toc_addon_monthly` $0.99/mo per-member: alliance chat seat
- **`/api/billing/pro-games`** — pick or swap which game slugs use Pro slots
- **Tactical Scouts F2P credit ledger**:
  - `/api/scouts/me` — balance + daily-earnings breakdown
  - `/api/scouts/earn/{kind}` — 4 actions with daily caps
  - `/api/scouts/redeem` — 3 credits → +1 extra_baseline
- **Tactical Operations Center**: alliances per-game, unlimited members, polling-friendly chat with in-room CyphrAI Q&A
- **Battle Reports** with auto-analyze + share-to-alliance + Stripe-style cleanup on delete
- **OTS Seats** (free Pro+TOC for alliance members) — 100-seat cap, email-locked, auto-link on register
- **Referrals** — `TA-XXXXXX` codes, +1 baseline welcome bonus, +1 baseline to referrer on referee's first paid event, 5/month cap
- **Calendar + Milestones** — user events with auto-emitted milestones (deep_dive_created, scout_credit_earned, event_created, etc.)
- TTL indexes (`rate_limits`, `password_resets`), idempotent guide seeding

### Frontend
- Landing · Recruitment Center (with visible referral input) · Forgot/Reset password
- **Pricing** — 3 tier cards (Free / Pro $4.99 / Single $2.99) + 2 add-on cards (Extra Game $0.99 · Alliance Chat $0.99/member) + Scouts F2P callout
- Command Center — Briefing + Quota Widget + 11-game grid
- War Room — cross-game archive
- Game Page — 5 tabs per title with share links + 402 toast
- **Operations Center** — list + create/join + 60+ member chat with polling
- **Battle Reports** — auto-analyze checkbox, detail page, share-to-alliance picker
- **Referral** (`/referral`) — code + share link + copy buttons + stats
- **OTS Seats** (`/seats`) — R5 admin grant/revoke flow, 100-seat dashboard
- **Calendar** (`/calendar`) — event scheduler + auto milestone feed
- **Tactical Scouts** (`/scouts`) — 4 earn cards (upload/video/try-game/daily-login), credit balance widget, redeem-N flow

### Testing
- **Iteration 7: 86/86 backend tests passing** (27 new + 59 regression).
  - New coverage: Scouts ledger (all 4 kinds + caps + redeem), pro_games slot enforcement, extra_game checkout, Seats 100-cap message, Referral linking + welcome bonus, Calendar/Milestone emission, Deep Dive 402 with Extra Game hint.
- Test files: `/app/backend/tests/backend_test.py`, `/app/backend/tests/test_iter7_scouts_seats_referrals.py`

## Pricing Math (60-member alliance, modeled by user)
| Conversion | Monthly Revenue |
|---|---|
| 100% join chat ($0.99/member × 60) | $59.40 |
| 50% Pro ($4.99 × 30) | $149.70 |
| 25% extra game ($0.99 × 15) | $14.85 |
| **Per alliance / month** | **~$224** |
| **Per alliance / year** | **~$2,688** |

## Prioritized Backlog

### P1 — next reasonable iteration
- **UI/Design changes** — user mentioned having ideas to share
- Game-slot selector UI on Pricing (so a Pro user can pick which 2 games are "in" their slots without going through Deep Dive)
- Scouts: link a "Try recommended game" action to a real catalog (currently self-report)
- Split `server.py` (2384 lines) into routers: `auth`, `billing`, `scouts`, `deep_dive`, `share`, `alliances`, `battle_reports`, `seats`, `referrals`, `calendar`

### P2
- Atomic scouts daily-cap (current is read-then-insert; minor race under burst load)
- `POST /api/billing/pro-games` → already returns 400 on unknown slug (fixed in iter7 post-test)
- Real `RESEND_API_KEY` (user-supplied) to ship Deep Dive / Battle Report emails
- Stripe customer portal (cancellation)
- WebSocket upgrade for chat (currently polling)

### P3
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- i18n (current AI prompt instructs to reply in user's language already)
- More games (user-suggested titles)
