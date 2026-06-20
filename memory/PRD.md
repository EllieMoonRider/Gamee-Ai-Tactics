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
- Auth + Password Reset (Resend + dev fallback)
- 11 games catalog with strict per-game CyphrAI specialist prompts (no cross-game refs, no generic advice)
- Chat (streaming + rate-limited 30/60s), Optimizer, Builds, 15 Guides, Tasks
- Deep Dive — GridFS storage, MIME validation, rate-limited, quota-gated 402
- **Stripe billing — 3 packages**: `subscription_monthly $4.99` (2 baselines + unlimited follow-ups), `topup_analysis $2.99` (+1 baseline), `toc_addon_monthly $0.99` (Operations Center access — requires active Pro). Idempotent entitlement application. Webhook handler covers all 3 kinds.
- Share links (public read-only) — Deep Dives & Builds
- **Tactical Operations Center**: alliances per-game, **unlimited members**, POST/GET CRUD, join-by-code, leave (with ownership transfer or disband). Messages CRUD (polling-friendly `since` filter). In-room actions: `share-deepdive`, `share-build`, `share-battle-report`, `ask-cyphr` (CyphrAI specialist answers in-room, deduped Q+A messages). Pro+TOC gated.
- **First-class Battle Reports** (`/api/battle-reports`): create with multipart upload + `auto_analyze` form param; manual `/{id}/analyze` for on-demand CyphrAI take (cached); share-to-alliance endpoint; GridFS cleanup on delete.
- TTL indexes (`rate_limits`, `password_resets`), idempotent guide seeding

### Frontend
- Landing · Recruitment Center · Forgot/Reset password (with show/hide)
- **Pricing** — 3 cards + Operations Center add-on row showing the $5.99 bundle math; CTA reflects user's current entitlements (`Get Pro first` / `Add Operations` / `Active ✓`).
- Billing success/cancel
- Command Center — Briefing + Quota Widget + Tutorial dropdown + 4 Path Cards (Deep Dive · Operations · Battle Reports · War Room) + 11-game grid
- War Room — cross-game archive
- Game Page — 5 tabs per title (Chat · Deep Dive · Optimizer · Guides · Planner) with share links + 402 toast
- **Operations Center** — list (`/operations`), Create + Join with codes, member list, leave/disband flow
- **Operations Room** — alliance chat with polling (3.5s, deduped by `msg.id`), text + Ask-CyphrAI mode toggle, Share modal for Deep Dives & Builds, Battle Report modal, copy-code button, members panel
- **Battle Reports** (`/battle-reports`) — create with auto-analyze checkbox, detail page with screenshots grid + optional CyphrAI take + share-to-alliance picker

### Testing
- Iteration 5: **59/59 backend tests passing** (42 regression + 17 new alliance/battle-report tests). Frontend 100% (alliance create/post/chat round-trip, pricing CTA states, battle report auto-analyze checkbox, all data-testids verified). 4 legacy deep-dive lifecycle tests skipped — fully covered by new 402 + quota tests.

## Prioritized Backlog
### P1 — next reasonable iteration
- **Tactical Scouts** (F2P credit system): upload game-update screenshots → earn credits → spend on analyses; secondary tasks (try recommended games, watch videos)
- **CyphrAI guided Deep Dive**: interactive walkthrough that tells the player exactly which screen to capture next + answers questions mid-upload
- Atomic rate-limiter (`find_one_and_update` with `$inc` per-window doc)
- Split `server.py` (1697 lines) into routers (`auth`, `billing`, `deep_dive`, `share`, `alliances`, `battle_reports`)
- Refund chat rate-limit slot when Battle Report `analyze` call fails

### P2
- Real `RESEND_API_KEY` (user-supplied)
- Stripe customer portal (cancellation)
- WebSocket upgrade for chat (currently polling)
- Email notifications on Deep Dive / Battle Report completion

### P2 (nice-to-haves)
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- Push reminders for daily tasks
- More games (allow user-suggested titles)

### P3
- i18n (current AI prompt instructs to reply in user's language already; UI strings to follow)
- Marketing pages: pricing/tier if monetized
