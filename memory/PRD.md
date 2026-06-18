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
- Games catalog: 10 hardcoded 37Games MMORPG titles
- Chat sessions CRUD + SSE streaming with multi-turn context: `/api/chat/sessions[/messages]`
- AI optimizer: `/api/optimizer`
- Builds CRUD: `/api/builds`
- Guides: 13 seeded guides via `/api/guides`
- Tasks (daily planner) CRUD with priority + completed toggle: `/api/tasks`
- **Deep Dive (CyphrAI vision)**: `/api/deep-dive` (create baseline), `/api/deep-dive/{id}/followup` (building block), GET/DELETE — multipart screenshot upload (≤6 images, 6MB each) analyzed by Claude Sonnet 4.5 vision.

### Frontend
- Landing `/`: hero, supported arsenal, capabilities, CTA
- Recruitment Center `/auth`: login/register, username + recovery email
- Command Center `/dashboard`: Briefing, stats, Tutorial dropdown (6 walkthroughs), Path Cards, game grid
- War Room `/war-room`: cross-game archive of chats, builds, tasks
- Game Page `/game/:slug`: 5 tabs — AI Chat (streaming) · Deep Dive · Optimizer · Guides · Planner

### Testing
- Iteration 1: 16/16 backend pytest + frontend flow 100% (`/app/test_reports/iteration_1.json`)
- Iteration 2: 20/20 backend pytest including Deep Dive vision lifecycle + frontend rebrand & UI 100% (`/app/test_reports/iteration_2.json`)

## Prioritized Backlog
### P1 (next reasonable additions)
- Move Deep Dive screenshots from inline base64 to GridFS / S3 (avoid 16MB BSON limit at scale)
- Image MIME validation on Deep Dive upload
- Per-user rate limiting on AI endpoints (optimizer, deep-dive, chat) to protect EMERGENT_LLM_KEY budget
- Email recovery flow (password reset) leveraging the email/username link
- Sharing: public read-only links for Builds & Deep Dive baselines

### P2 (nice-to-haves)
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- Push reminders for daily tasks
- More games (allow user-suggested titles)

### P3
- i18n (current AI prompt instructs to reply in user's language already; UI strings to follow)
- Marketing pages: pricing/tier if monetized
