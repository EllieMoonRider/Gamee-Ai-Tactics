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

**A cross-America Harley Davidson ride — with the grandkids in a sidecar, Grammy at the handlebars.** 🏍️🌄

Ellie's chosen first trip. Not Greece. Not a place she dreamed of — the road she's *actually ridden*, on her 2003 Anniversary Edition Dyna Superglide FXD. This is the app's origin story and its greatest strategic asset:

- **Authentic beats aspirational.** Every stop can be narrated by Grammy from lived experience — real diners, real overlooks, real weather she rode through.
- **The Harley + sidecar is the mascot.** Grandkids literally ride with Grammy. The mascot bike appears in every scene, cruising into every destination.
- **Infinite content shelf life.** A cross-country trip is not one destination — it's a *chapter model*. Route 66 alone is 8+ stops. All 50 states become future chapters. Ellie can never run out of things to add.
- **Marketing gold.** *"Ride across America with your Grammy — even if she's a thousand miles away, even after she's gone."* Documentary-quality tagline out of the box.

### MVP Launch Chapter — Suggested First Ride

Start with a **single iconic segment** — small enough to ship, big enough to sell. Candidates:
- **Route 66 highlights**: Chicago → Amarillo → Santa Fe → Grand Canyon → Santa Monica Pier (Grammy's greatest hits)
- **Blue Ridge Parkway**: Great Smoky Mountains → Asheville → Shenandoah
- **Pacific Coast Highway**: San Diego → Big Sur → Golden Gate
- **Sturgis pilgrimage** (nod to the Harley community): Denver → Devils Tower → Mount Rushmore → Sturgis

Every chapter has a small set of curated stops. At each stop: real place + Grammy voice + treasure to find + kid activity + a memory saved to the family passport.

### Later Chapters (unlocked with subscription)

- The Deep South loop (bayous, blues, BBQ)
- The Great Lakes ride
- Every U.S. National Park
- International Chapters (once demand proves out): Greece, Italy, Japan, New Zealand, Australia — the world eventually opens up, but **America first, because America is Grammy's road.**

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
- Tactical Ally is 3–4 sessions from launch-ready. Grammy's Compass is 6+ months minimum.
- **Ship-order rule**: Tactical Ally pays the rent so Grammy's Compass gets to exist.
- The moment Tactical Ally hits its first paying subscribers, Grammy's Compass kickoff begins.

## First Session Deliverables (When We Come Back)

1. Lock the launch chapter (Route 66? Blue Ridge? Sturgis pilgrimage? Pacific Coast?)
2. Detailed grandkid safety spec (COPPA, no external contact, no PII exposure)
3. MVP prototype: **one chapter, one Harley + sidecar mascot, one Grammy voice clip, one treasure, one memory saved**
4. Family Plan Stripe pricing setup
5. Design the family "Passport" — the persistent scrapbook that outlives Grammy and gets passed down

---

*This brief is preserved in the repo. It cannot get lost. Ellie can point any future assistant at this file and pick up exactly where she left off — no context needs to be re-told.*
