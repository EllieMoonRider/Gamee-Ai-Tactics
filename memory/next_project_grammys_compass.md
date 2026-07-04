# Grammy's Compass — Next-Project Brief

> **Logged**: Feb 2026, on behalf of R5 EllieMoonRider
> **Status**: On hold — starts the day Tactical Ally takes its first subscriber payment.
> **Author of the vision**: Ellie
> **Working name**: **Grammy's Compass** 🧭

---

## The Vision — in Ellie's Own Words

> *"I want to build an app that lets us go beyond the place we live."*
>
> *"The magic is they will have the memories of us being there after I've passed on and stories to tell their grandkids even if we weren't really there."*
>
> *"Real world places and how these places are. Except cleaned up. With some added treasures and kid activities."*

**This is not a travel app. It is a legacy app disguised as a travel app.**
Every VR-travel and imagination-adventure company builds the *destination*. Ellie's product is different — the destination is the wrapper, and **Grandma is the product**: her voice, her reactions, her presence, preserved forever so the grandkids' grandkids get to meet her too.

---

## Who It's For

**Primary user**: Grandmothers (and grandfathers) who want to give their grandchildren a shared adventure they can revisit forever — especially those who can't physically travel with them (distance, cost, health, time).

**Grandkids at the pilot family** (Ellie's own — her market fit is *her*):
- Granddaughter, 12
- Grandson, 6
- Granddaughter, soon-to-be 7
- Granddaughter, 5
- Grandson, arriving September 2026

**Two content tiers required from day one**:
- **Little Explorers** (ages 4–8): shorter scenes, simpler treasures, more Grandma voice
- **Adventurers** (ages 9–14): richer worldbuilding, harder treasure hunts, real cultural + historical layers

---

## The Product in One Sentence

**Google Street View, curated for kids, treasure-hunt-gamified, narrated by Grandma — and saved forever as a family memory book.**

---

## Core Mechanic

1. **Grandma picks a place** (real-world — Greece, Grand Canyon, Route 66, her hometown).
2. **The app renders it as a kid-safe scene** — real place, sanitized (no scary/dirty/dangerous, no ads, no strangers) and softened toward wonder.
3. **Treasures are sprinkled in** — collectibles, mini-activities, kid-scale challenges tied to that place (find the hidden macaron in Paris, feed the goats on Santorini, count the columns of the Parthenon).
4. **Grandma is co-present** — narrates, reacts, points things out. Either live (co-session) or via pre-recorded voice/video snippets she taped once, that the app plays contextually.
5. **The trip is saved** — a persistent memory book / passport / scrapbook that the grandchildren can revisit for the rest of their lives. Screenshots, treasures collected, Grandma's voice clips, dates, drawings.

---

## Why Nobody Else Has Built This

| Existing product | What it does | What it misses |
|---|---|---|
| StoryWorth | Grandma answers prompts, static book output | No adventure, no shared experience |
| Google Earth VR | Real places, immersive | No kid safety, no Grandma, no treasures, no legacy |
| Roblox / kid VR | Shared adventures | Fictional worlds, no real places, no family legacy |
| Family-tree / memoir apps | Preserve stories | No live shared experience, no grandkids-first UX |

**The unfilled category**: shared imaginary vacations with a real family elder, saved for generations. That's the whitespace.

---

## Launch Demo Destination

**Greece.** 🏛️🌊

Ellie's chosen first trip. The brief opens with the pilot family (5 grandkids) taking their first Adventures & Treasures trip to Greece with Grandma — Santorini cliffs, the Parthenon, an olive grove, a hidden treasure inside the Trojan Horse. This becomes the app's origin story and the seed marketing content.

---

## MVP — What We Actually Build

*(Rough scope, refined at kickoff time.)*

- **Map + destination picker** — real-world places, curated to kid-safe list, expandable
- **Scene renderer** — combines real map/photo data with AI-generated kid-safe overlays (softened lighting, added storybook elements, treasures placed)
- **Grandma layer** — voice recording + optional avatar. Either live during a session or async pre-recorded snippets triggered contextually.
- **Treasure & activity engine** — hidden objects, mini-quests, collectibles per destination
- **Memory book / passport** — persistent scrapbook per grandchild. Trips, treasures, Grandma's voice clips, dates. Exportable so the family owns the artifact forever (huge legacy angle).
- **Grandkid safety** — no external chat, no strangers, no ads. COPPA-compliant from day one.

## Tech We'd Reach For (Notes for Future Atlas)

- **Real-world imagery**: Google Maps Photorealistic 3D Tiles API, Mapbox, or curated stock photography per destination
- **Scene generation**: Gemini Nano Banana for kid-safe overlay art; possibly Sora 2 for short animated moments per destination
- **Grandma voice**: ElevenLabs voice cloning (one-time record → infinite Grandma narration), or simple recorded snippets
- **Persistence**: same Mongo stack, dedicated `families`, `trips`, `grandkids`, `memories` collections
- **PWA-first** — same posture as Tactical Ally so grandmas can install without an app store

## Business Model — Rough

- Freemium: first destination free (Greece pilot)
- Family Plan subscription (Grandma pays, all grandkids get access): ~$9.99/month
- Legacy Vault add-on: guaranteed persistence + physical printed memory book at year-end
- Optional one-time destination packs

---

## Why This Waits for Tactical Ally to Earn First

- **1 month of runway.** Can't build two apps from scratch on the same clock.
- Tactical Ally is 3–4 sessions from launch-ready. Adventures & Treasures is 6+ months minimum.
- **Ship-order rule**: Tactical Ally pays the rent so Adventures & Treasures gets to exist.
- The moment Tactical Ally hits its first paying subscribers, Adventures & Treasures kickoff begins.

## First Session Deliverables (When We Come Back)

1. Lock the final name (Adventures & Treasures or a replacement Ellie chooses)
2. Detailed grandkid safety spec (COPPA, no external contact, no PII exposure)
3. Greece launch demo prototype — one destination, one treasure, one Grandma voice clip
4. Family Plan Stripe pricing setup

---

*This brief is preserved in the repo. It cannot get lost. Ellie can point any future assistant at this file and pick up exactly where she left off — no context needs to be re-told.*
