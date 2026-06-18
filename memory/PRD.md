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
- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- **Password reset (Resend + dev fallback)**: `/api/auth/forgot-password`, `/api/auth/reset-password` — tokens single-use, 2h expiry, email rate-limited 3/hour, dev mode returns reset link inline when `RESEND_API_KEY` is empty
- Games catalog: 10 hardcoded 37Games MMORPG titles
- Chat sessions CRUD + SSE streaming (rate-limited 30/60s/user)
- AI optimizer (rate-limited 10/60s/user)
- Builds CRUD
- 13 seeded guides
- Tasks CRUD with priority + completed
- **Deep Dive (CyphrAI vision)** — `/api/deep-dive` (baseline + building-block follow-ups). **GridFS storage** for screenshots (≤6 images × 6MB), refs only in Mongo doc. **MIME validation** (PNG/JPEG/WebP/GIF). Auth-gated `/api/deep-dive/shot/{file_id}` streams the image. Rate-limited 5/300s/user. DELETE also cleans GridFS.
- TTL indexes on `rate_limits` and `password_resets` (auto-cleanup)

### Frontend
- Landing `/`, Recruitment Center `/auth`, Forgot Password `/forgot-password`, Reset Password `/reset-password`
- Command Center `/dashboard`: Briefing + Tutorial dropdown (6 walkthroughs) + Path Cards + game grid
- War Room `/war-room`: cross-game archive of chats, builds, tasks
- Game Page `/game/:slug`: 5 tabs — AI Chat (streaming) · Deep Dive · Optimizer · Guides · Planner
- Show/hide password toggle on Auth + Reset pages
- Forgot password link from auth page

### Testing
- Iteration 1: 16/16 backend pytest + frontend flow 100%
- Iteration 2: 20/20 backend pytest including Deep Dive vision lifecycle + frontend rebrand & UI 100%
- Iteration 3: 32/32 backend pytest (12 new: MIME validation, GridFS shot lifecycle, ownership 403, post-delete 404, rate-limit 429 on optimizer/chat/deep-dive, password reset happy path + single-use + bad-token + email rate-limit) + frontend show-hide + forgot/reset flow 100%

## Prioritized Backlog
### P1 (next reasonable additions)
- Atomic rate-limiter (find_one_and_update with $inc on per-window doc) — eliminates TOCTOU race on bursts
- Real email provider key (Resend) — user can add `RESEND_API_KEY` in `/app/backend/.env`
- Split `server.py` into routers (auth, chat, optimizer, deep_dive, guides, tasks)
- Per-user usage dashboard surfacing remaining rate-limit quota

### P2 (nice-to-haves)
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- Push reminders for daily tasks
- More games (allow user-suggested titles)

### P3
- i18n (current AI prompt instructs to reply in user's language already; UI strings to follow)
- Marketing pages: pricing/tier if monetized
