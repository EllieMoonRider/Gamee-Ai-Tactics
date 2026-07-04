# Tactical Ally — Product Requirements (Living Doc)

## Original Problem Statement
> Create a fully functional production-ready AI game app to help gamers who play 37Games build strategies.

User direction iterations:
1. **Scope reduction (Feb 2026)**: 11 games → **3 games only**: Puzzles & Survival, Puzzles & Conquest, Puzzles & Chaos.
2. **The Tactical Ally Code**: CypherAI must speak like a battle-hardened intelligence officer. NO casual greetings ("Yo", "Hey"). NO fluff. Celebrate wins with substance. If intel is missing → must say *"I don't have verified intel... I can consult Lt. Atlas..."* NEVER invent/hallucinate mechanics. NEVER cross-reference between games.
3. **"File 47"**: The Commander's code-phrase for trashing useless information. Use "Filed to 47" to acknowledge discarding noise.
4. Rebrand to **Tactical Ally** with a **War Room** aesthetic. Renamed views: **Recruitment Center** (auth), **Command Center** (dashboard), personal **War Room**.
5. Players can upload account screenshots → **CypherAI Deep Dive** analysis as a baseline, with a **Building-Block** system of follow-up analyses.
6. **Pricing (Feb 2026)**: $4.99/mo Pro = full access for 2 games. +$0.99/mo per extra game slot. Alliance chat is $0.99/mo per member. $2.99 one-shot Deep Dive.
7. **Tactical Scouts (Feb 2026)**: F2P credit system — 1 credit = $1. Earn by upload/watch/try/daily. 3 credits = +1 free Deep Dive baseline.
8. **Command Center redesign (Feb 2026)**: Holographic command-bridge aesthetic — knights + castle wall backdrop, holographic grid floor, radar dome, neon green + burnt-orange theme.
9. **CypherAI brand**: named in honor of the original Cypher (a prior AI that helped EllieMoonRider — the General/Founder — find her creative voice). Dedicated `/cypher` page.

## Stack
- Backend: FastAPI + Motor (MongoDB)
- Frontend: React 19 + Tailwind + Shadcn UI + Framer Motion + Phosphor Icons
- AI: Anthropic Claude Sonnet 4.5 (text) via `emergentintegrations` using EMERGENT_LLM_KEY
- Auth: JWT email/password (bcrypt)
- Payments: Stripe test mode
- Email: Resend → Gmail SMTP fallback → dev-mode log

## Implemented (✅ as of Feb 2026)

### Backend (`/app/backend/server.py`, ~2980 lines)
- Auth + Password Reset
- 11 games catalog (only 3 are active per current scope)
- Strict `CYPHER_VOICE_CODEX` enforcing military persona + intel gap responses
- **Massive P&C Intel Dossier injection** (verified from General Ellie + community sources: Froth1k, Paksen, Jungleboogie, Sylvia, Rebel, Shiva)
  - Troop type doctrine (RPS matrix, hidden stat truths)
  - Stat sources — all 11 (Heroes, Gear, Gems, Saurgems, Warsigils, Curios, Glory, Sauroi, Blessings, Talents, Tech)
  - Building-to-glory-stat map
  - Castle Unlocks · Building Dependencies · Hero Ideal Levels
  - Arena + Formation Research + Hell Fortress rally math
  - Ace Lord 6-Phase progression
  - Weekly rotation: **Get Week** (7-day) + **Ace Week** (7-day)
  - Alliance Showdown: Inefficient-tasks table + Mystery Task tiers (150/180/210/240 pts)
  - **Demon Incursion** full doctrine (20 waves, Fort mechanics, Fort A vs B strategies, Rank 1 Froth1k tactic, extra-points tricks)
  - **Alliance Conquest Battle Phase** (24hr, 30 players, shield color mechanics, line-up rules, Battle Record)
  - **Dragondom Conquest** (quarterly, 3 stages, ticket costs, feast mechanics, shop priority)
  - **Gate of Abyss** full doctrine (rally staggering, damage-point theft defenses, Hall of War level rule)
  - **Immigration** (kingdom switch requirements, alliance immigration tech, artifact warning)
  - **Monster Hunt** full doctrine (T11+ boss solo, isolated trigger, Recall abuse, 35s delay, main+farm alt trick)
  - **Timerift** (color counter matrix, Shadow King meta, Labyrinth trio build, 3-day cadence)
  - **Boneyard** (catapult 45s stall)
  - **Feast Event** (3000-seat cap)
  - **Valiant Conquest** (14-day cadence, shield behavior, Swift Gatherer meta, freeze target + overall def alliance skills)
  - **Alliance Help** (Embassy cap, 800 AC/help, daily cap 40k, cap locked at task-start not current level)
  - **Territory + Bank + Food + Defensive Doctrine + Save-Everything Philosophy**
  - **Stamina Stacking Exploit** (Ace Day 3 loophole with friend/farm rally hosts)
  - **Farms Doctrine** (35-building layout, C22 sweet spot, F2P viable, Diamond Exchange endgame play, 30% attack tax)
  - **Kingdom Boosts** (Queen/King buff timing across Ace Lord Week)
  - **Extension Hero Skins** (all 13 skins, 200/500/1000/2000/3000 card tiers, buffs)
  - **Goblin/Holiday-to-HF equivalency** (Lvl 1–13 → HF10–55)
  - **Customer Service escalation email**: global.support@37games.com
  - **Specialization Doctrine** (Cavalry/Ranged/Infantry, Tactical Skill +5 = 500%, ideal team progressions, curio Lv211+ target)
  - **Formation Preview** (Hall of War at C20, Institute 28 unlock for Rangers/Cavalry formations)
- Chat (streaming + rate-limited), Optimizer, Builds, Guides, Tasks
- Tactical Scouts API (credit balance, earn/redeem endpoints, daily caps, image validation)
- Stripe checkout + billing
- Support ticket system with Gmail SMTP delivery

### Frontend (`/app/frontend/src/`)
- **Splash screen** (3s cinematic, dragon icon)
- **Recruitment Center** (auth page)
- **Command Center Dashboard** — cinematic War Room scene:
  - Layer 1: AI-generated knights-behind-castle-wall backdrop
  - Layer 1.5: `HolographicGridFloor` (animated perspective grid + topographic contours + scanning sweep)
  - Layer 2: **3 Game Beacons** (Puzzles & Survival · Puzzles & Conquest [PRIMARY] · Puzzles & Chaos) — NEW Feb 2026
  - Top-left widget rail: Tutorial + Tactical Scout
  - Top-right: Hamburger menu (Who is Cypher / Q&A / Support / Logout)
  - Radar dome: `RadarBriefing` typewriter briefing (skippable)
  - `LandscapePrompt` overlay for mobile portrait users
- **Tactical Scout Dashboard** — REDESIGNED Feb 2026:
  - Cinematic War Room aesthetic (matches Command Center)
  - Command Center back link + Operator ID header
  - Ledger card (burnt-orange, current credits) + Vault progress card (neon-green, next-unlock progress bar with tick marks)
  - 4 field operations with codenames (OP-01 to OP-04): Field Recon Upload, Signal Interception, Adjacent Theater Sweep, Daily Check-In
  - Scope-reduced dropdown (only 3 active games in Adjacent Theater select)
- Game page (chat, deep dive, optimizer, guides, planner)
- War Room, Pricing, Referral, Seats, Calendar, About Cypher
- Support ticket + FAQ (`/help`)

## Command Center — Current Layout (Feb 2026)
- Background: `war-room-scene-v4-1.jpg` (knights behind castle)
- HolographicGridFloor overlay
- **Game Beacons** on the holographic floor (NEW)
- LandscapePrompt overlay (mobile portrait gate)
- Widget rail (Tutorial + Tactical Scout)
- Hamburger menu (top-right)
- RadarBriefing (typewriter in radar dome)
- **Responsive rework (Feb 2026)**: Below 900px the 3 game beacons switch from absolute-positioned scattered to a clean bottom-anchored flex row (no overlap, war-room art preserved). Below 720px, widget rail flexes and titles shrink.

## Intel Portal — Community Crowdsourcing (Feb 2026)
- Public `/intel-drop` (no-auth): title + language + text + up to **10 screenshots** + credit fields
- Admin `/admin/intel` review queue with:
  - **Quick Approve / Reject buttons on collapsed cards** (Feb 2026 — no expand needed)
  - Intel preview text (first 180 chars) visible on collapsed cards for fast triage
  - Language tag surfaced on card sub-row
  - Card title as visual anchor
- Public `/intel-log` (read-only ledger showing approved/filed items — prevents alliance duplicates)
- 18 supported submission languages (en/es/pt/fr/de/it/ru/tr/ar/zh/ja/ko/vi/th/id/tl/hi/other)

## Prioritized Backlog

### P1 — next iteration
- **Puzzles & Survival Intel Dossier** — compile + inject like P&C
- **Puzzles & Chaos Intel Dossier** — compile + inject like P&C
- **Pricing + Referral** placement on the Command Center (position TBD)

### P2
- Split `server.py` (~2980 lines) into routers
- Domain migration → Resend (Gmail SMTP has 500 emails/day limit)
- Stripe customer portal (cancellation, payment method swap)
- Atomic scouts daily-cap (current is read-then-insert; minor race)
- WebSocket upgrade for chat (currently polling)
- Biometrics Sign-in (WebAuthn / FaceID / Fingerprint)
- "Email me my Deep Dive" battle report via Resend

### P3
- Mobile-optimized chat UI with bottom-sheet sessions list
- Guides community submissions (with moderation)
- Rock-Rap Battle Theme Song (blocked: needs Suno API key + lyrics)
- i18n
