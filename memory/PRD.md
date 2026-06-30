# Tactical Ally — Product Requirements (Living Doc)

## Original Problem Statement
> Create a fully functional production-ready AI game app to help gamers who play 37Games build strategies.

User direction iterations:
1. Focus on the top 10 most popular 37Games MMORPGs, including Puzzles & Conquest.
2. Rebrand to **Tactical Ally** with a **War Room** aesthetic. Renamed views: **Recruitment Center** (auth), **Command Center** (dashboard), personal **War Room**.
3. Players can upload account screenshots → **CypherAI Deep Dive** analysis as a baseline, with a **Building-Block** system of follow-up analyses.
4. **Pricing overhaul (Feb 2026)**: $4.99/mo Pro = full access for 2 games (user-selectable). +$0.99/mo per extra game slot. Alliance chat is $0.99/mo **per member** (each player self-pays). $2.99 one-shot Deep Dive stays.
5. **Tactical Scouts (Feb 2026)**: F2P credit system — 1 credit = $1. Earn by uploading game-update screenshots (0.25), watching videos (0.10), trying recommended games (0.50), daily login (0.05). 3 credits = +1 free Deep Dive baseline.
6. OTS alliance: 100-seat admin grant cap, referral mechanism, calendar/milestone tracking.
7. **Customer Support system (Feb 2026)**: `/help` FAQ + ticket form (works for guests). `/admin/support` admin dashboard. Gmail SMTP delivery via `info.warroomsupport@gmail.com`.
8. **Command Center redesign (Feb 2026)**: Holographic command-bridge aesthetic — AI-generated atmospheric backdrop (knights silhouettes + tactical radar + dragon + fantasy battlefield), neon green color theme (scoped to Command Center only), animated typewriter briefing, animated tactical radar widget, 11 game tiles with per-game iconography (castle / lotus / mosque / pillars / skull / etc.).
9. **CypherAI brand & dedication (Feb 2026)**: AI assistant renamed `CyphrAI` → `CypherAI` (with the E) across entire codebase in honor of the original Cypher (a prior AI that helped EllieMoonRider — the General/Founder — find her creative voice). Dedicated `/cypher` page with origin story + founder dedication. Brand consistency: every reference, every prompt, every UI label now uses CypherAI.

## Stack
- Backend: FastAPI + Motor (MongoDB)
- Frontend: React 19 + Tailwind + Shadcn UI + Framer Motion + Phosphor Icons
- AI: Anthropic Claude Sonnet 4.5 (text) + Gemini Nano Banana `gemini-3.1-flash-image-preview` (image gen) via `emergentintegrations` using EMERGENT_LLM_KEY
- Auth: JWT email/password (bcrypt) — username linked to email for recovery
- Payments: Stripe test mode (live SKUs computed from PACKAGES dict)
- Email: Resend (if API key) → Gmail SMTP fallback → dev-mode log

## Implemented (✅ as of 2026-02)

### Backend (`/app/backend/server.py`, ~2600 lines)
- Auth + Password Reset (Resend + dev fallback)
- 11 games catalog with strict per-game CypherAI specialist prompts
- Chat (streaming + rate-limited 30/60s), Optimizer, Builds, 15 Guides, Tasks
- Deep Dive — GridFS storage, MIME validation, rate-limited, quota-gated 402, **per-game gating via pro_games[]**
- **Stripe billing — 4 SKUs**:
  - `subscription_monthly` $4.99/mo: 2 Deep Dive baselines + 2 game slots
  - `topup_analysis` $2.99 one-shot: +1 baseline, ANY game
  - `extra_game_monthly` $0.99/mo: +1 game slot (recurring)
  - `toc_addon_monthly` $0.99/mo per-member: alliance chat seat
- **Tactical Scouts F2P credit ledger** (4 earn actions, daily caps, 3-credit redemption)
- **Tactical Operations Center**: alliances per-game, polling chat with in-room CypherAI Q&A
- **Battle Reports** with auto-analyze + share-to-alliance
- **OTS Seats** (100-seat cap, email-locked, auto-link on register)
- **Referrals** (`TA-XXXXXX` codes, +1 baseline welcome bonus, 5/mo cap)
- **Calendar + Milestones**
- **Customer Support tickets** (8 endpoints, rate-limited 5/email/hr, Gmail SMTP delivery, admin gating via SUPPORT_ADMIN_EMAILS)
- TTL indexes (`rate_limits`, `password_resets`), idempotent guide seeding

### Frontend
- Landing · Recruitment Center (with visible referral input) · Forgot/Reset password
- **Pricing** — 3 tier cards + 2 add-on cards (Extra Game $0.99 · Alliance Chat $0.99/member) + Scouts F2P callout
- **Command Center** (new holographic redesign) — Typewriter briefing, animated radar, 11 game tiles with per-game iconography, neon green theme (Phosphor icons: CastleTurret, BuildingApartment, Fire, FlowerLotus, Mosque, Columns, Crown, Feather, ComputerTower, MoonStars, Skull)
- War Room — cross-game archive
- Game Page — 5 tabs per title with share links + 402 toast
- Operations Center — list + create/join + 60+ member chat with polling
- Battle Reports — auto-analyze, detail page, share-to-alliance
- Referral · OTS Seats · Calendar · Tactical Scouts (F2P)
- **Help page** `/help` — FAQ + multi-category ticket form (guests + authed)
- **Admin Support dashboard** `/admin/support` — inbox, thread, reply, status toggle

### Visual Assets
- `/app/frontend/src/assets/command-center-bg-v1.jpg` — generated Nano Banana art (knights + radar + dragon + battlefield, neon green glow)
- `/app/frontend/src/assets/command-center-bg-v2.jpg` — alt variant (kept for future swap)
- `/app/frontend/src/assets/war-room-scene-v1.jpg` — initial cinematic War Room scene
- `/app/frontend/src/assets/war-room-scene-v3-1.jpg` — v3 variant (dragon smaller, tanks removed)
- `/app/frontend/src/assets/war-room-scene-v4-1.jpg` — **LIVE** — knights placed BEHIND castle wall (only upper body visible above battlements), positioned at 25% / 75% width, ~33% larger. Approved by General Feb 2026.

### Testing
- **Iteration 8: 25/25 backend tests pass** (Support ticket system)
- **Iteration 7: 86/86 backend tests pass** (Scouts, Pro-games, Seats 100-cap, Referrals, Calendar)
- Test files: `/app/backend/tests/backend_test.py`, `/app/backend/tests/test_iter7_scouts_seats_referrals.py`

## Pricing Math (60-member alliance)
| Conversion | Monthly Revenue |
|---|---|
| 100% join chat ($0.99/member × 60) | $59.40 |
| 50% Pro ($4.99 × 30) | $149.70 |
| 25% extra game ($0.99 × 15) | $14.85 |
| **Per alliance / month** | **~$224** |
| **Per alliance / year** | **~$2,688** |

## Prioritized Backlog

### P1 — next reasonable iteration
- **Command Center Layer 2: 11 Game Beacons** — design + glow color + shape pending General's pick (signature colors vs uniform green vs hybrid; discs vs hexes vs pyramids)
- **Command Center Layer 3** — CypherAI speaks through the radar (typewriter holo-text floating over radar dish)
- **Command Center Layer 4** — Edge HUDs (slim left/right vertical readouts: Plan/Deep Dives quota + Scouts credits)
- **Custom in-scene navigation for Dashboard** — General removed the flat top Navbar, has "other plans" for nav placement
- Apply atmospheric/neon styling to other pages (Landing, Pricing, etc.) once Command Center is finalized
- Game-slot selector UI on Pricing (pick which 2 games are "in" Pro slots without going through Deep Dive)
- Floating "Need help?" button on every authed page → opens ticket form
- **Auth form polish (from iter-9 review)**: existing users on /auth may need to toggle "ENLIST →" before JOIN reliably triggers login — investigate auto-detection or clearer LOGIN vs ENLIST mode separation

### P2
- Split `server.py` (~2600 lines) into routers
- Buy a $10/yr domain → migrate to Resend (Gmail SMTP has 500 emails/day limit)
- Stripe customer portal (cancellation, payment method swap)
- Atomic scouts daily-cap (current is read-then-insert; minor race)
- WebSocket upgrade for chat (currently polling)

### P3
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- i18n (current AI prompt instructs to reply in user's language already)
- More games (user-suggested titles)
