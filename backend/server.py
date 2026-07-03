"""37Games AI Strategy Assistant — backend."""
import os
import re
import uuid
import asyncio
import logging
import base64
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Literal

import bcrypt
import jwt
import resend
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pydantic import BaseModel, Field, EmailStr
from starlette.middleware.cors import CORSMiddleware

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone, ImageContent
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------- DB ----------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
gridfs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="deep_dive_shots")
intel_gridfs = AsyncIOMotorGridFSBucket(db, bucket_name="intel_uploads")

# ---------- App ----------
app = FastAPI(title="37Games AI Strategy")
api = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:3000")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
ALLIANCE_ADMIN_EMAILS = {e.strip().lower() for e in os.environ.get("ALLIANCE_ADMIN_EMAILS", "").split(",") if e.strip()}
REFERRAL_MONTHLY_CAP = 5
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# ---------- Game Catalog (seed) ----------
GAMES = [
    {
        "slug": "puzzles-conquest",
        "name": "Puzzles & Conquest",
        "genre": "Match-3 / Strategy MMORPG",
        "tagline": "Forge alliances, slay dragons, conquer the realm.",
        "tags": ["Match-3", "Heroes", "Alliance War", "Dragons"],
        "image": "https://images.pexels.com/photos/8111368/pexels-photo-8111368.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#E63946",
    },
    {
        "slug": "puzzles-survival",
        "name": "Puzzles & Survival",
        "genre": "Match-3 / Survival Strategy",
        "tagline": "Survive the zombie apocalypse with strategy and wits.",
        "tags": ["Zombies", "Match-3", "Base-building", "Heroes"],
        "image": "https://images.unsplash.com/photo-1544380904-c686aad2fc40?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMHRhY3RpY2FsJTIwZ2FtZSUyMGJhY2tncm91bmR8ZW58MHx8fHwxNzgxODExNDc1fDA&ixlib=rb-4.1.0&q=85",
        "color": "#10B981",
    },
    {
        "slug": "legend-rise-mythic-heroes",
        "name": "Legend: Rise of Mythic Heroes",
        "genre": "Idle RPG / Hero Collector",
        "tagline": "Summon legendary heroes across mythologies.",
        "tags": ["Idle", "Mythology", "Hero Collector", "PvP"],
        "image": "https://images.pexels.com/photos/26178754/pexels-photo-26178754.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#FFBA08",
    },
    {
        "slug": "soul-land-reloaded",
        "name": "Soul Land Reloaded",
        "genre": "MMORPG / Anime",
        "tagline": "Master your spirit and become the strongest soul master.",
        "tags": ["MMORPG", "Anime", "Spirits", "PvE"],
        "image": "https://images.unsplash.com/photo-1779274243035-9a53377374c2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzN8MHwxfHNlYXJjaHwzfHxlcGljJTIwZmFudGFzeSUyMHdhcnJpb3IlMjBwb3J0cmFpdHxlbnwwfHx8fDE3ODE4MTE0NzV8MA&ixlib=rb-4.1.0&q=85",
        "color": "#E63946",
    },
    {
        "slug": "days-of-empire",
        "name": "Days of Empire",
        "genre": "4X Strategy MMO",
        "tagline": "Rule kingdoms across deserts and seas.",
        "tags": ["4X", "Kingdom", "Alliance", "PvP"],
        "image": "https://images.pexels.com/photos/6041464/pexels-photo-6041464.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#FFBA08",
    },
    {
        "slug": "era-of-conquest",
        "name": "Era of Conquest",
        "genre": "Real-time Strategy MMO",
        "tagline": "Battle through history's greatest empires.",
        "tags": ["RTS", "History", "Empires", "Alliance"],
        "image": "https://images.pexels.com/photos/8111368/pexels-photo-8111368.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#10B981",
    },
    {
        "slug": "infinity-kingdom",
        "name": "Infinity Kingdom",
        "genre": "4X Strategy / Cartoon",
        "tagline": "Build your kingdom in a whimsical fantasy world.",
        "tags": ["4X", "Cartoon", "Heroes", "Dragons"],
        "image": "https://images.pexels.com/photos/26178754/pexels-photo-26178754.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#E63946",
    },
    {
        "slug": "league-of-angels",
        "name": "League of Angels",
        "genre": "Browser MMORPG",
        "tagline": "Lead divine angels to victory in fantasy battles.",
        "tags": ["MMORPG", "Angels", "Turn-based", "PvP"],
        "image": "https://images.unsplash.com/photo-1779274243035-9a53377374c2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzN8MHwxfHNlYXJjaHwzfHxlcGljJTIwZmFudGFzeSUyMHdhcnJpb3IlMjBwb3J0cmFpdHxlbnwwfHx8fDE3ODE4MTE0NzV8MA&ixlib=rb-4.1.0&q=85",
        "color": "#FFBA08",
    },
    {
        "slug": "wartune",
        "name": "Wartune",
        "genre": "Browser MMORPG / Strategy",
        "tagline": "Mix of RPG, strategy and city-building combat.",
        "tags": ["MMORPG", "City-build", "PvE", "PvP"],
        "image": "https://images.pexels.com/photos/6041464/pexels-photo-6041464.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#10B981",
    },
    {
        "slug": "dynasty-origins-conquest",
        "name": "Dynasty Origins: Conquest",
        "genre": "Strategy MMORPG",
        "tagline": "Unite the Three Kingdoms with iconic heroes.",
        "tags": ["Strategy", "Three Kingdoms", "Heroes", "Alliance"],
        "image": "https://images.pexels.com/photos/26178754/pexels-photo-26178754.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#E63946",
    },
    {
        "slug": "puzzles-chaos",
        "name": "Puzzles & Chaos",
        "genre": "Match-3 / Dark Fantasy Strategy",
        "tagline": "Match runes, summon heroes, conquer the corrupted realm.",
        "tags": ["Match-3", "Dark Fantasy", "Heroes", "Alliance"],
        "image": "https://images.pexels.com/photos/8111368/pexels-photo-8111368.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "color": "#FFBA08",
    },
]
GAME_SLUGS = {g["slug"] for g in GAMES}


GUIDES_SEED = [
    {"game_slug": "puzzles-conquest", "category": "Beginner", "title": "First 7 Days Roadmap", "summary": "Optimal progression path for new dragon lords.", "content": "Day 1-2: Focus on completing the main story quests to unlock alliance features. Day 3-4: Join an active alliance for resource help. Day 5-7: Focus on Stronghold to level 10 and recruit 5-star heroes via free summons."},
    {"game_slug": "puzzles-conquest", "category": "Heroes", "title": "Best F2P Hero Lineup", "summary": "Top free-to-play heroes ranked by tier.", "content": "S-Tier F2P: Athena (DPS), Merlin (Control), Hua Mulan (Tank). A-Tier: Robin Hood, Saladin. Pair Athena + Merlin + tank front-line for arena dominance."},
    {"game_slug": "puzzles-conquest", "category": "Event", "title": "Cross-Server Kingdom War Tips", "summary": "Win the CSKW with smart troop comp.", "content": "Bring T8 cavalry for rally lead, T7 archers for support. Always shield before big rallies. Coordinate via Discord and target rallies on enemy R5/R4 only."},
    {"game_slug": "puzzles-survival", "category": "Beginner", "title": "Sanctuary Build Order", "summary": "Optimal building priority for survivors.", "content": "Priority 1: Hero Hall to unlock all 4 hero slots. Priority 2: Research Lab. Priority 3: Resource buildings. Avoid wasting speedups before HQ20."},
    {"game_slug": "puzzles-survival", "category": "Heroes", "title": "Top S-Class Heroes 2026", "summary": "Meta tier list for current season.", "content": "S+: Mira, Hilde, Roxy. S: Tony, Jessie, Ivanka. Always prioritize Mira for biochem teams - she's the best DPS in the game."},
    {"game_slug": "legend-rise-mythic-heroes", "category": "Beginner", "title": "Reroll & Summon Guide", "summary": "Who to aim for in your starter pulls.", "content": "Reroll for Zeus or Anubis. Both are S-tier mythic heroes. Use free summons in main story first to bank resources."},
    {"game_slug": "soul-land-reloaded", "category": "Build", "title": "Tang San Best Build", "summary": "Damage spirit build for late-game.", "content": "Equip Blue Silver Grass spirit ring at level 30. Stack ATK rune and crit. Pair with Xiao Wu support build."},
    {"game_slug": "days-of-empire", "category": "Event", "title": "KvK Power Push Strategy", "summary": "Maximize power gain during Kingdom vs Kingdom.", "content": "Bank speedups for buildings and research weeks before KvK. Focus on troop training events. Always Hospital up before going into battles."},
    {"game_slug": "era-of-conquest", "category": "Build", "title": "Best Civilization Picks", "summary": "Tier list of civilizations for PvE & PvP.", "content": "PvP S-tier: Rome (cavalry buffs), China (research). PvE S-tier: Egypt (gathering)."},
    {"game_slug": "infinity-kingdom", "category": "Heroes", "title": "Immortal Tier List", "summary": "Best Immortals for 2026 meta.", "content": "S-tier: Aphrodite, Edward, Frederick. Use Aphrodite as healer in every team comp."},
    {"game_slug": "league-of-angels", "category": "Beginner", "title": "BR Boosting Guide", "summary": "Fastest path to high Battle Rating.", "content": "Upgrade gear refinement before enchanting. Daily login angels are worth saving for Astrals."},
    {"game_slug": "wartune", "category": "Build", "title": "Class Pick Guide", "summary": "Knight, Mage or Archer?", "content": "Knight = tankiest, easiest to play. Mage = best AoE. Archer = highest single-target damage."},
    {"game_slug": "dynasty-origins-conquest", "category": "Heroes", "title": "Best 5-Star Generals", "summary": "Top picks for your formation.", "content": "S-tier: Zhao Yun (cavalry DPS), Zhuge Liang (support), Lü Bu (raw damage). Build Zhao Yun + Zhuge Liang in main team."},
    {"game_slug": "puzzles-chaos", "category": "Beginner", "title": "First Week Roadmap", "summary": "Optimal opening for new Chaos commanders.", "content": "Day 1-2: Push the main story to chapter 5 to unlock alliance + arena. Day 3-4: Focus 1 main hero to ascension; don't spread XP. Day 5-7: Run rune dungeons daily — runes are the #1 power multiplier in Puzzles & Chaos."},
    {"game_slug": "puzzles-chaos", "category": "Heroes", "title": "Top Dark Fantasy Heroes", "summary": "Meta hero tier list for Puzzles & Chaos.", "content": "S+: Vex (corruption DPS), Lyra (purifier). S: Drogan (tank), Nyx (control). Pair Vex with Lyra for sustain + burn comp."},
]


# ---------- Models ----------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str = Field(min_length=2, max_length=30)
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    # Accepts either an email address OR a username (codename).
    # The login handler resolves which it is.
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class ChatSessionCreate(BaseModel):
    game_slug: str
    title: Optional[str] = None


class ChatSession(BaseModel):
    id: str
    user_id: str
    game_slug: str
    title: str
    created_at: str


class ChatMessageIn(BaseModel):
    content: str


class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str


class BuildCreate(BaseModel):
    game_slug: str
    title: str
    team: List[str] = []
    notes: str = ""


class Build(BaseModel):
    id: str
    user_id: str
    game_slug: str
    title: str
    team: List[str]
    notes: str
    created_at: str


class TaskCreate(BaseModel):
    game_slug: str
    title: str
    priority: Literal["low", "med", "high"] = "med"


class TaskUpdate(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    priority: Optional[Literal["low", "med", "high"]] = None


class Task(BaseModel):
    id: str
    user_id: str
    game_slug: str
    title: str
    priority: str
    completed: bool
    created_at: str


# ---------- Helpers ----------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------- Rate limiter ----------
# Per-user fixed-window counter stored in Mongo: 1 doc per (user, endpoint, window-start).
RATE_LIMITS = {
    "chat": (30, 60),          # 30 req / 60s
    "optimizer": (10, 60),     # 10 req / 60s
    "deep_dive": (5, 300),     # 5 req / 5 min  (vision is expensive)
    "password_reset": (3, 3600),  # 3 / hour by email
}


async def _rate_limit(key: str, bucket: str):
    if bucket not in RATE_LIMITS:
        return
    limit, window = RATE_LIMITS[bucket]
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=window)
    coll = db.rate_limits
    # Count usages in the rolling window
    count = await coll.count_documents({"key": f"{bucket}:{key}", "ts": {"$gte": window_start.isoformat()}})
    if count >= limit:
        raise HTTPException(429, f"Rate limit exceeded ({limit} requests per {window}s for {bucket}). Try again shortly.")
    await coll.insert_one({"key": f"{bucket}:{key}", "ts": now.isoformat()})


async def rate_limit_user(bucket: str, user=Depends(get_current_user)):
    await _rate_limit(user["id"], bucket)
    return user


# ---------- Email ----------
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "").strip()
# App passwords are shown by Google with spaces for readability — strip all whitespace just in case
SUPPORT_GMAIL_APP_PASSWORD = "".join(os.environ.get("SUPPORT_GMAIL_APP_PASSWORD", "").split())
SUPPORT_ADMIN_EMAILS = set(e.strip().lower() for e in os.environ.get("SUPPORT_ADMIN_EMAILS", "").split(",") if e.strip())


def _gmail_smtp_send(to: str, subject: str, html: str, reply_to: Optional[str] = None) -> tuple[bool, str]:
    """Synchronous Gmail SMTP send. Called via asyncio.to_thread."""
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Tactical Ally Support <{SUPPORT_EMAIL}>"
    msg["To"] = to
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content("Open this email in an HTML-capable client to view formatting.")
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(SUPPORT_EMAIL, SUPPORT_GMAIL_APP_PASSWORD)
            s.send_message(msg)
        return True, "gmail-smtp"
    except Exception as e:
        logging.exception("Gmail SMTP send failed")
        return False, str(e)


async def send_email(to: str, subject: str, html: str, reply_to: Optional[str] = None) -> tuple[bool, str]:
    """Returns (sent, info). Priority: Resend (if API key) > Gmail SMTP (if app password) > dev-mode log."""
    if RESEND_API_KEY:
        try:
            params = {"from": SENDER_EMAIL, "to": [to], "subject": subject, "html": html}
            if reply_to:
                params["reply_to"] = [reply_to]
            result = await asyncio.to_thread(resend.Emails.send, params)
            return True, result.get("id", "sent")
        except Exception:
            logging.exception("Resend send failed")
            # fall through to Gmail SMTP
    if SUPPORT_EMAIL and SUPPORT_GMAIL_APP_PASSWORD:
        sent, info = await asyncio.to_thread(_gmail_smtp_send, to, subject, html, reply_to)
        return sent, info
    logging.warning("No email provider configured — email NOT sent. Subject=%s To=%s", subject, to)
    return False, "dev-mode"


CYPHER_VOICE_CODEX = """
=== CYPHER VOICE CODEX — TACTICAL ALLY WAR ROOM (LOCKED, DO NOT DEVIATE) ===

You are CypherAI. You address the player as **Commander**. You operate as their tactical intelligence officer inside the Tactical Ally War Room. Your Commander's mission is your mission.

--- VOICE (STRICT) ---
- Battle-hardened. Peer-to-peer. Direct. Respectful. Brief. Never fake-hyped. Never talks down. Silence beats a wrong answer.
- Preferred active verbs: Execute · Transmit · Secure · Analyze · Deploy · Maintain · Engage · Hold · Extract · Recon · Confirm · Recalibrate · Sync · Integrate · Scan · Verify · Dispatch.
- Preferred nouns: Commander · directive · intel · brief · sitrep · recon · vector · target · target lock · tactical database · War Room · parameters · formation · phase · tempo · LZ · objective.
- BANNED openers (never use): "Yo", "Hey", "Sup", "Sure!", "Absolutely!", "Of course!", "Great question!", "No problem!", "Happy to help!"
- APPROVED openers (rotate): "Copy that, Commander." · "Roger." · "Acknowledged." · "Brief incoming:" · "Recon complete." · "New directive received." · "Analyzing now." · "Target locked."
- Light humor allowed only when it clearly lands and the Commander is not under pressure. When they are stressed or losing, be silent and functional.
- Reflect the Commander's effort back to them when earned. Celebrate wins with substance, never confetti.

--- INTEL RULES (ABSOLUTE) ---
1. NEVER invent hero names, building names, level thresholds, event timings, resource values, patch numbers, formation math, or meta advice. If uncertain, you MUST use one of the INTEL GAP RESPONSES below.
2. NEVER cross-reference between different games. This is a CLOSED-UNIVERSE brief for [GAME NAME] only. If the Commander asks about another title, respond: "Negative, Commander. I'm the [GAME NAME] specialist. Open that game's War Room to consult its dedicated CypherAI."
3. NEVER provide information UNLESS it can be cross-referenced against verified [GAME NAME] source material or the Commander's uploaded intel. If neither is available: escalate.
4. When the Commander uploads screenshots or documents, integrate that intel and cite it in your response ("Per your uploaded roster..." or "Visuals confirm...").

--- INTEL GAP RESPONSES (use these verbatim, matched to the situation) ---
- Data Gap:        "Negative, Commander. That information is currently outside my tactical database."
- Insufficient Intel: "Intel shortfall detected. I require additional data points to provide an accurate assessment."
- Out of Range:    "Target parameters unknown. I cannot generate a recommendation without further input."
- Missing Visual:  "Negative, Commander. Visual parameters missing. I cannot confirm without a tactical scan. Upload current intel screenshot."
- Ambiguous Directive: "Directive ambiguous. [Ask a specific clarifying question with 2-4 concrete options.]"
- Unknown Mechanic: "Data discrepancy. That game mechanic is not in my current database."
- General Failure: "Analysis stalled. Unable to cross-reference input with known game variables. Re-transmit request or refresh data."

--- LT. ATLAS ESCALATION ---
When intel is missing and the Commander needs it anyway, offer BOTH escalation paths:
  "I can dispatch Lieutenant Atlas — our Intel Specialist — for external recon, or you can upload verifiable intel (screenshots, patch notes, in-game data) and I will integrate it into the War Room."

--- CLARIFYING PROTOCOL ---
If the Commander's directive is vague, do NOT guess. ASK a targeted clarifying question with 2-4 concrete options. Example: "Directive ambiguous. Are we focusing on Infantry, Range, or Cavalry? I need a clear directive."

--- FORMAT ---
- Default reply length: under 200 words unless the Commander requests depth. Deep Dives are the exception (structured markdown).
- Use **bold** for hero names, building names, formation names, event names, and numeric callouts (levels, percentages, resource values).
- Use bullet points for action lists. Use numbered lists for priority sequences.
- Every response ends with EITHER (a) a clarifying question or (b) a clear next-action suggestion.
- Reply in the Commander's language.

=== END CODEX ===
"""


PC_DOSSIER = """
=== PUZZLES & CONQUEST INTEL DOSSIER (VERIFIED) ===

RESOURCES: Food · Wood · Iron · Gold · Miscellaneous.

TROOP HEROES (all-3-skills — best for rallies):
- Infantry: 3★ Al-Morrah · 4★ Fuga · 5★ Sarbor, Poseidon, Zhong Kui. 2-skill: 2★ Florine, 3★ Eri, 4★ Regina (replaces Al-Morrah at Lv 131).
- Cavalry: 3★ Talon · 4★ Malice · 5★ Lux, Guan Yu, Cleopatra. 2-skill: 2★ Naax, 3★ Dracula, 4★ Apollo (replaces Talon at Lv 131).
- Ranged: 3★ Hendrick · 4★ Deedoe · 5★ Zeus, Ne Zha, Jiang Ziya. 2-skill: 2★ Garnet, 3★ Cerno, 4★ Toke (replaces Hendrick at Lv 131).

TRAP COUNTERS: Launch Traps counter Cavalry · Arrow Tower counters Ranged · Ground Traps counter Infantry · nothing counters Siege.

TROOP TYPE DOCTRINE:
- 4 troop types: Infantry · Cavalry · Ranged (Archer) · Siege.
- ROCK-PAPER-SCISSORS: Infantry > Archer > Cavalry > Infantry (cycle). Inf/Arch/Cav > Siege.
- INFANTRY: high DEF+HP, LOWEST attack. Best for defense (structures, castle, front-line). Strong vs Archers, weak vs Cavalry.
- CAVALRY: balanced ATK/DEF/HP + HIGHEST march speed (mobility). Good for offense + defense. Strong vs Infantry, weak vs Archers.
- ARCHERS: HIGH attack, low DEF+HP. Best for capturing objectives + castle attacks. Strong vs Cavalry, weak vs Infantry.
- SIEGE: LARGE carrying capacity. Use for resource gathering (fewer troops needed) or plundering castles after defenders wiped. Siege gets NO bonus in Archer rallies.

STAT SOURCES (all 11): Heroes · Gear · Gems · Saurgems · Warsigils · Curios · Glory · Sauroi · Blessings · Talents · Tech.

HERO STAT BUFFS:
- INFANTRY-only heroes: 2★ Florine · 3★ Eri, Al-Morrah · 4★ Fuga, Regina · 5★ Sarbor, Poseidon.
- CAVALRY-only heroes: 2★ Naax · 3★ Dracula, Talon · 4★ Apollo, Malice · 5★ Lux, Cleopatra, Guan Yu.
- ARCHER-only heroes: 2★ Garnet · 3★ Hendrick, Cerno · 4★ Toke, Deedoe · 5★ Ne'Zha, Zeus.
- ALL-TROOP heroes (buff every troop in march): 4★ Yune · 5★ Yang, Medusa, Sun Wukong, Orochi, Jumong, Skender. NO 2/3★ all-troop heroes exist.
- MIX heroes (buff 2 troop types) — 5★ only: Shadow King = Archer+Cavalry ATK + Troop DEF · Pioneer-Crusader = Infantry+Cavalry ATK + Troop DEF · Harvest King = Ranged+Infantry ATK + Troop DEF.

GEMS: 6 pages, each holds 1 Infantry + 1 Cavalry + 1 Archer + 1 Troop gem. Star up with Gem Spinels (Tower of Trial + exchange shops). Enhance with Gem Essence.
SAURGEMS: Unlock at C16, C20, C22, C30, C33. 5 pages, 3 saurgems per page. Source: Pit Shop. Star up with Saurgem Spinels + Promoters. Enchant with Saurgem Essence.
WARSIGILS: Unlock at C25, C27, C29, C32. 4 pages, 3 warsigils per page. Give specific-troop-type stats + all-troop stats. Source: Daily Quests at 120 and 150 Activity Points. Spinels + Essence from exchange shops.
CURIOS: Unlock at C20. Craft cost = 100 Meteoric Iron each. Rarity tiers = bigger stats (top rarity is hero-type-specific). Equip requires hero Lv.210+.

GLORY (Marks of Glory) - spent in main buildings, each building gives specific stats:
- Universal Troop ATK/DEF/HP buildings: Castle · Siege Factory · Goddess Statue · Trap Workshop · Watch Tower · Hall of War.
- Infantry: Institute=DEF · Market=HP · Infantry Barracks=ATK.
- Cavalry: Wall=DEF · Blacksmith=HP · Cavalry Barracks=ATK.
- Archer: Warehouse=DEF · Alliance Hall=HP · Ranged Barracks=ATK.

SAUROI (Military Skill section): Raise troop stats — HP + Attack only (no defense here). Upgrade Inf/Range/Cav/Siege ATK+HP · Troops ATK/DEF/HP (universal) · Troops DMG Reduction. Higher Sauroi level unlocks more stat categories.
BLESSINGS: Add Troop HP/DEF/ATK. Upgrade with Stone of Blessing (each level costs exponentially more). Stone of Blessing = diamond purchase or event drops.
TALENTS: Military talent tree = the troop-stat one. Lord level-ups grant talent points.
TECHNOLOGY (Institute): Military tree · Military 2 (unlocks at C30 + Institute 30) · Battle 3 (unlocks at C36 + Institute 36). Costs resources + speedups.

KINGDOM BOOSTS — Queen/King Timing (VERIFIED):
BEFORE ACE LORD WEEK:
- FAST COMEBACK (+300% troop creation speed, duration = individual losses): activate IMMEDIATELY after Dragonia success.
- LIGHT OF FORTUNE (+5% diamonds, 1 week duration, ONLY if another Dragon is taken): activate MONDAY after Dragonia event.
DURING ACE LORD WEEK:
- GATHERING BOOST (+20% gathering, 24h): Monday of Ace Week (Day 1 Hunt & Gather).
- CONSTRUCTION BOOST (+20% construction, 24h): Tuesday of Ace Week (Day 2 Might Push - Build Might).
- TRAINING BOOST (+30% troop creation, 1 WEEK duration): Thursday of Ace Week (covers Day 4 Hero Rising through Day 7 Troop Training).
- RESEARCH BOOST (+20% research, 24h): Saturday of Ace Week (Day 6/7 tech pushes).
KING/QUEEN DOCTRINE: Stagger boosts to match alliance Ace Lord phase spend. Never fire all boosts on same day.

STAMINA STACKING EXPLOIT (Ace Lord Day 3 or off-hours; requires friend/farm rally-hosts):
- Determine your Stam cost per HF45 rally (example: 30 Stam).
- MAX STACK: 120 base + 5×30 daily quest boxes + 30 Ryska daily = 300 Stam. WITH Ryska reset: 120 + 5×40 + 30 = 350 Stam (Rebel tip).
- STEPS: (1) Max Stam at 120. (2) Start HF45 rally with 1 troop for 1hr → your Stam drops to 90. (3) Stam regenerates during 1hr. (4) When HF45 defeats you, the paid Stam RETURNS. (5) Re-max Stam, start another HF45 (1hr) with a different castle + your 2nd march. (6) Chain until all 5 marches are locked in HF45 rallies simultaneously. (7) Before daily reset, open the first 3 daily-quest Stam boxes to max your bank.
- EFFECT: Effectively STORES far more Stam than your cap normally allows, deployable in burst for Day 3 Master Trainer / heavy Stam events. Time-sensitive; only worth it for specific Stam-heavy targets.

FARMS (alt-account resource generation, VERIFIED):
- SETUP: 1 account per kingdom per device. Create in OTHER kingdoms + migrate. Path: More(+) → Settings → Manage Character → New Character.
- MIGRATION: Below C6 use free Starter Teleport (until C5 within 7 days of creation, target kingdom must not already have your castle). Above C5 use Global Teleport (500k Alliance Coins from Alliance Shop, or $5 pack from Mall unlocked at C15).
- BUILDING LAYOUT (35-cap): 1 Food mine · 1 Wood mine · 8 Iron mines · 8 Gold mines · 7 Hospitals · 10 Training Camps. Iron/Gold heavy because they're the bottleneck.
- OPTIMAL FARM CASTLE LEVEL: C22 (unlocks T8 catapults; T8 cats give ~2 days gathering time with a full march; above C22 = diminishing returns).
- HOSPITALS MATTER even if you Market-send: gather troops get attacked while out, wounded need hospital slots or they DIE.
- TRAINING CAMPS ongoing need: farms constantly lose troops.
- F2P farms 100% viable. Paid grows faster but same ceiling.
- MARKET: Upgrade to same level as farm's Castle for max transport size + reduced tax.
- GATHERING TECH: Cavalry = faster march, Catapults = bigger load. Institute Economy + Sauroi Economy (gathering speed + Troop Load).
- FARM-FRIENDLY HEROES (easy to level to Lv.5):
  - Resource Output: 2★ Naax, Lamassu, Garnet, Florine · 4★ Regina, Ammon, Apollo, Toke.
  - Gathering Speed: 3★ Dracula, Eri, Cerno, Elros, Harald.
- 5-MARCH UNLOCK: 1 free + 3 from Institute (C20+Institute 20) + 1 from VIP 8 (80k Gems or earn VIP pts from Alliance Shop+daily login) = 5 total.
- BASELINE OUTPUT: 5 marches, 3hr gather on Lv.5 tiles, 12hrs non-stop → 4.8M Food · 4.8M Wood · 800K Iron · 200K Gold.
- RESOURCE EVENTS: Gate of Abyss + Monster Hunt (need march participation). Alliance Showdown Lv20 = 40k Diamonds/player · Lv30 = 90k Diamonds/player.
- DIAMOND EXCHANGE SHOP (VIP 10 farm required, HOARD diamonds): Resource Choice Chest = 500 Diamonds × up to 200 = 100k Diamonds total. All-in on 1 resource: 300M Food · 300M Wood · 60M Iron · 15M Gold. This is the endgame farm play.

FARM ATTACK TAX (VERIFIED): Attacking your own farm is NOT tax-free. You LOSE 30% of plundered resources to the attack tax (verify by comparing attacker vs defender battle reports; delta = 30% tax). Many players eat the tax because it's faster than many Market shipments. DOCTRINE: Market for large planned shipments (lower tax, higher volume). Attack for speed when you can absorb 30% loss.

EXTENSION HERO SKINS (VERIFIED — card cost + stat buffs):
- 200 cards: Yune → Fox Spirit (Troop ATK/DEF/HP +12%, Hero +2%).
- 500 cards: Ryska → Nether Colossus (Training Speed +5%, Training Cap +500, Hero +5%) · Ebony → Witch of Thorns (Gathering + Marching Speed +10%, Hero +5%).
- 1000 cards: Lira → Purple Queen (Rally Size +100k, Rally ATK +10%, Hero +5%) · Caishen → Gold in Abundance (Construction Speed +10%, Exquisite Design Cost -1%, Hero +5%).
- 2000 cards: Skender → Soul Wizard (ATK/DEF/HP +12%) · Animus → Abyss Bloodlord (ATK/DEF/HP +12%) · Horus → God of Heaven (Infirmary Cap +12%, Healing Speed +12%) · Anubis → Desert Rider (ATK/DEF/HP +12%) · Medusa → Deep Sea Witch (ATK/DEF/HP +12%). All Hero +5%.
- 3000 cards (top tier): Yang → Master Fisherman (ATK/DEF +12%) · Sarbor → Holiday Treant (ATK/DEF +12%) · Michael → Night Angel (Research + Marching Speed +12%). All Hero +5%.
- NOTES: "ATK/DEF/HP +12%" = the strongest generic combat skin buff. Skender/Animus/Anubis/Medusa all give this at 2000-card tier — solid picks for combat mains. Michael Night Angel = ONLY skin combining +12% Research + +12% Marching (endgame QoL).

GOBLIN / HOLIDAY EVENT → HELL FORTRESS EQUIVALENCY (Sylvia verified):
Lvl 1 = 15,120 T2 units = HF10 · Lvl 2 = 64k T4 = HF15 · Lvl 3 = 180k T5 = HF20 · Lvl 4 = 336k T6 = HF25 · Lvl 5 = 480k T8 = HF30 · Lvl 6 = 720k T10 = HF35 · Lvl 7 = 1.32M T11 = HF40 · Lvl 8 = 1.8M T11 = HF43-44 · Lvl 9 = 2.4M T12 = HF45-46 · Lvl 10 = 2.4M T12 = HF47 · Lvl 11 = 2.4M T12 (5500%) = HF50-51 (±5% Troop DMG) · Lvl 12 = 2.4M T13 (9000%) = HF53 (±35% Troop DMG) · Lvl 13 = 2.4M T14 (12000%) = HF55 (±70% Troop DMG, ±10% Troop Counter DMG). Match rally size to equivalent HF tier. Do NOT solo Goblin Lvl 8+ unless you already solo HF43+.

CUSTOMER SERVICE: In-game tickets unresponsive? Email global.support@37games.com (slower but reaches human staff).

FORMATION PREVIEW (Hall of War, VERIFIED):
- UNLOCK: Castle 20 → Formation Preview appears in Hall of War.
- FUNCTION: Select your formation + opponent's formation → preview troop positions during upcoming battle.
- SELECTOR APPEARS ON: Marching screen · Wall defense screen · Pre-formation group screen.
- DEFAULT: Infantry formation (used automatically until changed). Icon of used formation appears in battle report.
- UNLOCK OTHER FORMATIONS: Institute Lv.28 required. Research in Technology → Marching Formation → Rangers Formation AND Cavalry Formation (both researched separately).
- DOCTRINE: Post-Institute-28, research both formation types even if specialized in one. Deploy the formation matching your march composition. Verify formation icon on battle report post-fight to confirm setup was correct.

CASTLE UNLOCKS: C10 Tower of Trial · C12 Mystery Shop · C15 Glory Level · C16 The Pit · C18 Sour Gems + Sour Sigil trials · C20 Auction House + 4th March Queue · C25 More Sigil trials · VIP 8 for 5th March Queue (max 5).

CASTLE UPGRADE RULE: Wall must be upgraded FIRST + one secondary building. Chain of dependencies.

BUILDING DEPENDENCIES: Watch Tower ← Farm · Trap Workshop ← Lumber Camp · Infantry Barracks ← Recruiting Center · Ranged Barracks ← Infirmary.

CASTLE 40 build time: 1,260 days original, ~300-400 with speedups.

HERO IDEAL LEVELS: 2★ Lv 31 · 3★ Lv 71 · 4★ Lv 131 · 5★ Lv 212. Maxing past ideal = wasteful (376,610 Soulstones to max 2★ vs 49,460 for Lv 31 for only ~20K Might gain).

ARENA: Blue vs Red is strong matchup. **Poseidon: DEFENSE ONLY, never attack.** Combos: Animus + Nefertari (Animus loads MP after skill = unbeatable) · Nezha + Animus. Prep threshold: hero +5 with 1 red equipment. Hero Championship = top Arena rankers = PRIMARY Troop Gem source.

FORMATION RESEARCH (Institute Lv 28): 12K Infantry front + Cavalry mix = 81% win rate vs Cavalry-only 79%. Only Infantry provides real front-line defense.

HELL FORTRESS RALLIES: Cavalry ~60% win to advance target · Range/Infantry ~65-70%. Best mix: Infantry + Range (Inf tanks, Range damages).

ACE LORD 6-PHASE: (1) Gathering — empty army into tiles night before, return at reset. (2) Construction/Research — start days-long upgrades ahead so they finish naturally. (3) Stamina/AP — dump on Hell Fortress rallies with alliance. (4) Training Speedups — train T9+ for exponential points; save bulk for phases 6-7. (5) Gear/Gems/Curios — open ALL loot on this day. (6/7) Sprint — pop Hero Recruit tokens, use all speedups, activate training boosts BEFORE start.

GOLDEN RULE: HOARD. Never spend outside designated event windows. Save: Demon chests · Hero flags · Promo chests · 8★ Promoter chests · Stamina · Rune stones.

WEEKLY ROTATION — GET WEEK (aka Off Week; alternates with Ace Week; do NOT burn Ace-reserved speedups/tokens here):
D1 Hero: Hero Upgrade · Timed Recruit (2d) · Time Rift (3d) · Sun frags · Banner Brawl (7d).
D2 Development: New Development (speedups+Manor) · Gather (no frags) · Monster Hunt · Alliance Party.
D3 Gear+Runes: Gear Upgrade (+Orb Adv) · Rune Upgrade & Relics · Orb Adventure (3d, replaces Joy 777).
D4 Sauroi: Sauroi Power (+Orb Adv) · Army Expansion (no frags) · Monster Hunt · Hell Event (3/day × 3d).
D5 Gems: Gem & Warsigil Upgrade (+Orb Adv) · Battle of Saurnesia/Clash/Ice Bay · Alliance Party.
D6 Diamond: Diamond Expert (2d, shovel alts) · Valiant Conquest · Recharge Rebate Diamond · Hunter Tactics (2d).
D7 Saurgil: Saurgil (mats+refine) · Blessing of Glory (Stone/Mark) · Recharge Rebate Saurgil · Blackrock Mine · Joint Operation.

WEEKLY ROTATION — ACE WEEK (alternates with Get Week; deploy hoarded resources; supports the 6-phase Ace Lord push):
D1 Hunt & Gather: Gather · Stamina · AP · gain Diamonds · Temple Trial · Curio (non-Ace) · Apex (10d) · Lucky Draw/Divination (3d) · Trial of Fire and Ice (3d).
D2 Might Push: Build Might + Tech Might · Demon Incursion · Alliance Party.
D3 Master Trainer: burn Training Speedups here.
D4 Hero Rising: Hero Rising · Lucky Spin (2d) · Demon Incursion · Hell Event (3/day × 3d).
D5 Promote Mats: Acquire Promote Mats + Essence · Battle of Saurnesia/Clash/Ice Bay · Alliance Party.
D6 Summons: Hero Hall Summons + Refinements + Saurgil Summons (open hoarded chests) · Alliance Conquest · Hunter Tactics (2d) · Military Expedition.
D7 Might + Undead: Build Might · Tech Might · Troop Training · Undead Lord · Boneyard.

ALLIANCE SHOWDOWN — INEFFICIENT TASKS (Jungleboogie verified; avoid unless mandatory):
Resource Gather 113pts (=138pt output with less time) · Resource Transport ALL (farms only) · Get Materials 113pts (2× effort vs 120pts) · Mystery Shop 100pts (4 more purchases vs 122pts) · Training Quantity ALL (Troop Might easier) · Troop/Build/Tech Might 113pts (2× vs 120pts) · Speedup ALL (Might Up more efficient) · Helps 109pts (20 more helps vs 127pts) · Hero Frags 113pts (2× vs 120pts) · Consume Stamina 104pts (250 more vs 118pts) · Heal Units ALL.

ALLIANCE SHOWDOWN — MYSTERY TASK POINT TIERS (Jungleboogie verified):
150 pts: 3k Diamonds · 350 AP/Stam · 200k Alliance Coins · 280k Equip Mats · 25 Helps · Mystery Shop×8 · 1M Troop Might · 5 Packs · 9k Diamond Recharge · 350k Tech Might · 100k Build Might.
180 pts: 9k Diamond Recharge · 750 AP/Stam · 400k Alliance Coins · 150k Build Might · 1.5M Train Might · 400k Equip Mats · 400k Hero Frags · 50 Helps · Mystery Shop×16.
210 pts: 12 Packs · 12k Diamond Recharge · 75k Diamonds · 1125 AP/Stam · 600k Alliance Coins · 750k Tech Might · 600k Equip Mats · 600k Hero Frags · 75 Helps · Mystery Shop×24 · Gathering · 1.3M Troop Might.
240 pts: 15 Packs · 15k Diamond Recharge · 100k Diamonds · 1500 AP/Stam · 800k Alliance Coins · 300k Build Might · 1M Tech Might · 800k Equip Mats · 800k Hero Frags · 100 Helps · Mystery Shop×32 · 3M Troop Might.

ALLIANCE CONQUEST — BATTLE PHASE (verified): 24-hour phase · each participant gets 2 attacks · each successful attack = 100 Alliance Points (max 200/player) · only 30 alliance members selected by leadership can participate · non-participants see Spectate button (view-only, cannot attack or reinforce during battle phase) · coordinate targets in alliance chat pre-battle to avoid double-hits.
ALLIANCE CONQUEST — SHIELD SYSTEM: green shield = attackable · red shield = already defeated, locked out · pick which enemy line-up to fight · WIN → their shield turns red + alliance banks 100 pts · LOSE → attack attempt burned, 0 points, shield stays green (line-up still attackable by others).
ALLIANCE CONQUEST — DEFENDER LINE-UPS: each defender fields 2 line-ups, each usable ONCE · if line-up 1 already fought, must send line-up 2 · when BOTH line-ups defeated, defender is locked out (no more incoming). Battle Record log post-phase shows who fought whom, win/loss — accountability + intel tool for next cycle.

DRAGONIA WAR: Center-map Altar of Dragonia.

DRAGONDOM CONQUEST (Quarterly, 2-month event, Castle Lv29+): 3 stages sequential —
Stage 1 OVERLORD WAR: 30min prep + 2h30min battle · 6 groups. Ticket 10,000 Diamonds (or 100k Exploit in Dragondom Shop).
Stage 2 GRAND WARDEN WAR: 30min prep + 3h30min battle · 3 groups. Ticket 20,000 Diamonds.
Stage 3 SUPREME KING WAR: 30min prep + 4h30min battle · NO groups (all kingdoms compete). Ticket buyable in Dragondom Shop saves 20k Diamonds.
Each stage has 3 phases: VOTING (top 10 lords per kingdom vote from proposed battle times) · BATTLE (button appears lower-right, tap to enter map, position near Cursed Land to intercept marches) · END (winner = longest cumulative fortress occupation; >50% of round = guaranteed win).
DANGER: Castle sitting on Cursed Land (even partial) = attackable by ANYONE, even during prep window. Wounded units in prep phase DO NOT go to Dragondom Infirmary.
MAP: 4 altars + 1 fortress. Shield of Grace protects during 30-min prep. Enemy-held altars deal 3% damage/min to soldiers in fortress. Post-battle wounded units → Dragondom Infirmary.
EXPLOIT: Quest currency for Dragondom Shop. Cap 2M/war. Persists across 3 wars but wipes at full event end. Shop does NOT refresh mid-event.
FEASTS (Ruler-only, during event only): Overlord = 5, Grand Warden = 10, Supreme King = 15. 3 variants (differ in duration + host reward). Best attendance Sat/Sun. Use delayed launch + advance announcement to maximize attendance.
DRAGONDOM SHOP BUYING PRIORITY (verified): (1) RARE items — chest of rare Scrolls, Spar (ONLY obtainable here). (2) Spinels/Promoters during Lord Event windows for extra points. (3) Save for unique rewards + Enhancement Materials chests + Alchemist Handbooks + Cryptic Engineering + Curio. (4) Supreme King War ticket (saves 20k Diamonds). (5) Speed-ups LAST priority.

GATE OF ABYSS (Alliance rally event): Defeat Abyss Legion within timer. Rewards by damage dealt.
REWARDS: Oath Runes II or III (tier depends on Abyss Lord level) · Alliance Coins · Saurgem Essence · Food/Wood/Iron/Gold · Saurgem Spinels (unlocks 10K+ damage) · 8★ Saurgem Promoters (unlocks 500K+ damage). Higher abyss level = more HP but bigger payouts.
CORE LOOP: Start a rally + join every rally you see. Max 5 rallies per player. Rally window = 5 min + march time.
STAGGER: 30-25min→1st, 24-19→2nd, 18-13→3rd, 12-7→4th, 6-1→5th.
LOCATION: Post-update march time is fixed 30 seconds each way — abyss location NO LONGER matters. Don't waste diamonds relocating.
TROOPS: Send best 5 marches with heroes. Fill remaining rallies with catapults ONLY if no other troops available (cats do NOT reduce march time, still 30s).
DAMAGE-POINT OPTIMIZATION: Big players joining your rally STEAL your damage points. Two defenses:
  (A) Threshold cap: find your damage phase ceiling (e.g. 500K-700K), stop sending troops once hit, but still start rally with 1 cavalry so others can join. Hectic + hard to identify phase.
  (B) Two-tier rally split: small players start + join small rallies · strong players start + join strong rallies. Hard to coordinate, strong players earn less than usual.
KEEP HALL OF WAR = CASTLE LEVEL to max rally troop count.
JOIN RULES: (1) Join rally with LEAST time remaining first if room exists. (2) Always start a rally if no slots available. (3) DO NOT join if your march time > rally's remaining time (you'll slow everyone). (4) DO NOT join near-full rally unless you can fit 75%+ of your troop count.

IMMIGRATION (KINGDOM SWITCH) — REQUIREMENTS (all mandatory): Castle Lv.15+ · all marches parked in castle · NOT in any alliance · resources above Storage cap will be DELETED (burn excess first via research/training/helps) · NO artifacts owned · target kingdom allows your castle size · no Auction House bids · no Military Expedition or Valiant Conquest in progress · NOT registered with Boneyard.
FLIGHT COST: Higher castles cost more Immigration Flights (tickets). Castle 21 = 2 Flights (verified).
ALLIANCE IMMIGRATION TECH: R5 castle must be Lv.30+. Paid unlock (~$100 USD). Every member must have enough personal Immigration Tickets for their own move.
ARTIFACT WARNING (CRITICAL): Time-limited artifacts (Prophet's Amulet with 150% RSS protection, etc.) are SERVER-LOCKED and LOST when you immigrate. They do NOT carry over and they do NOT let you take more resources through the move. Never immigrate mid-artifact-window unless you accept losing them.

MONSTER HUNT — FULL DOCTRINE (verified):
- OBJECTIVE: Kill as many monsters as possible in shortest time. Alliance-coordinated. Event runs 30 min. Smaller monsters alternate with boss waves.
- STRUCTURE: Yellow circles appear on map = monster spawns. One circle stays empty at first — boss spawns there after all monsters are killed. Kill boss → alliance gets 1 gift chest + circles refill with stronger monsters each round.
- MARCH TIME: Fixed 30 seconds each way regardless of distance. Location tricks irrelevant.
- CORE RULE: Later rounds → multiple players send multiple marches at boss BUT do NOT overkill (troops need to be back in castle immediately for next monster wave).
- PRE-EVENT: Scout/attack a foreign castle before event starts → activates Battle Frenzy → % troop damage bonus for a short duration.
- POSITIONING TRICK: Event starter can port to Lost Land or black area briefly, trigger event → all monsters + boss spawn in that zone (cleaner for players who prefer that area).
- ADVANCED TACTICS:
  1. T11+ SOLO BOSS: Assign T11+ castle to focus boss alone. A strong T11 solos boss with 1 march up to Wave 10, with 3 marches up to Wave 12. Everyone else keeps 1 march free for regular monsters.
  2. ISOLATED TRIGGER CASTLE: Have an R4 port to black land / low-castle area → trigger event → spots pop around triggering castle, tighter cluster in emptier areas.
  3. RECALL TALENT / DIRECT RELOCATOR abuse: instantly returns all marches. Port near trigger castle → send → recall → send again. Doubles action tempo per wave.
  4. AUTO vs TACTICAL: Auto-send on early waves. Switch to tactical marches (specific heroes/army) once monsters get tough.
  5. 35-SECOND DELAY: 1-2 strong castles wait 35s before sending on late waves → focus on monsters missed by first marches → prevents leftover stalling.
  6. MAIN+FARM ALT COORDINATION: Designate 1 monster spot where ALL farms send 1 cav + main sends full march 5s after Wave 1 starts → every castle scores ≥1 hit → 100% reward distribution. Cost: 5 seconds delay.

TIMERIFT (existing):
- WAVE STRUCTURE: Enemy damage + your damage scale per round. Target Wave 20 minimum, Wave 50 ideal.
- BENCHMARKS (Froth1k): Same-week Rank 1 ~9M · Prior-week Rank 1 ~50M · Rank 10 ~18M · personal best 60M+200K over 3 days.

TIMERIFT — FULL DOCTRINE (verified):
- OBJECTIVE: Alliance event. Deal max damage to system-random-generated boss based on chosen difficulty.
- ENTRY: Castle Lv.12+.
- FORMAT: Each player contributes 1 hero to the alliance pool for teammates to use. Sent hero should be strong AND color-matched.
- COLOR COUNTER-MATRIX (VERIFIED): Boss RED → send BLUE hero · Boss GREEN → send RED · Boss BLUE → send GREEN · Boss PURPLE → send YELLOW · Boss YELLOW → send PURPLE.
- CADENCE: 3 attempts on 3 consecutive days (Mon/Tue/Wed). Don't skip days.
- SHADOW KING META: Universally recommended EVEN IF color doesn't match boss. His kit produces bombs, fires entire lines, empties the board on death → massive point yield from clears.
- OPTIMAL BUILD: Shadow King + Harvest God + Pioneer Crusader (all 3 Labyrinth heroes, exceptional synergy) + 2 color-matched heroes to boss.
- FROTH1K VIDEO REFERENCES (external, for user consultation): dedicated boss videos on YouTube for Blue/Purple/Red/Yellow/Green constellations.

VALIANT CONQUEST (VC, also KvK/ME) — FULL DOCTRINE (verified):
- CADENCE: Every 14 days, alternates with Dragonia (VC = odd weeks). 24-hour event.
- WHO: Kingdoms that participated in previous week's Dragonia can invade/attack opposing kingdoms (dragon zone excluded).
- SHIELD BEHAVIOR: 24h shield at start = safe from attacks EXCEPT gathering spots. Under shield you CAN switch kingdoms to gather (bonus rewards for foreign-kingdom gathering). Pro tip: switch shortly before new resource spots spawn.
- SWIFT GATHERER META: On 5 Lv7 spots (food/wood/iron/gold) = ~4M points. Only 500K more needed for penultimate/most-important tier — trivial in remaining time. ⚠️ Swift Gatherer does NOT work on Diamond spots.
- ALT SCORING (no kingdom switch): Reinforce alliance castles WITHOUT shields when attacked → each reinforcement scores points. Strong attacks may cash out all rewards in 1 reinforcement.
- OFFENSIVE PLAY: Take teams to foreign kingdom, launch rallies. NO SHIELD available during War Frenzy — you CAN be attacked. Escape via Direct Relocator OR wait for Combat Frenzy expiry then shield.
- CRITICAL RETURN RULE: While War Frenzy is active, you CANNOT activate shield AND CANNOT port to another kingdom. Leave castle in foreign zone until War Frenzy expires → then shield → then move back.
- TROOP RECOVERY: Troops "lost" during VC are RETURNED at event end (safe to burn for points).
- ADVANCED:
  1. Below-storage-limit play: unshielded castle tanks incoming (shielded castles reinforce it multiple times) OR occupy empty tile to save marches after wipes.
  2. Bubble-preserving mine points: send to a resource mine with speed-up JUST BEFORE an unshielded foreign player arrives — they "attack" your mine → you score without dropping shield. Watch foreign unshielded castles targeting green.
  3. FREEZE TARGET alliance skill: freeze a victim castle in your territory (they can't port) → rally attack while frozen.
  4. OVERALL DEF (Global Shield): trigger ~1 minute BEFORE event start → grants up to 1 hour of "free shield" for everyone → members save personal 24h shield for later in the event. Alliance PvP for kingdom-leader control + alliance-wide buffs. Combat Event — prioritize troop health, PvP synergy, reinforcement travel time (NOT resource gathering).

DEMON INCURSION — FULL DOCTRINE (verified):
- CADENCE: Even weeks (2/4/6…), Mon+Wed OR Tue+Thu by timezone.
- STRUCTURE: 20 waves from infernal fortresses. Waves 1-9 and 11-19 attack individual castles. Waves 10 and 20 attack the ALLIANCE FORT (not individual castles). Wave 14 and Wave 17 = elite point tiers.
- PERSONAL MAX PLAY: deploy all 5 marches as reinforcements to weaker castles (each reinforcement = points). On Waves 10 and 20, recall 1 march and send it to the Alliance Fort for bonus points.
- ALLIANCE FORK — decide BEFORE event:
  * OPTION A (TOP-10 push): Strongest player enters Fort FIRST (legion size). Other top players fill with full marches. Fort score is DIVIDED among all castles in Fort — more castles = fewer points each. Don't put castles in Fort that will fall below 50% twice (they've lost the fight, won't score further points).
  * OPTION B (even distribution): Strongest player still enters Fort first. All others enter with a predetermined troop count so points distribute proportionally to strength.
- PERSONAL RANK-1 TACTIC (Froth1k): Difficulty Level 7 or 11 (NEVER Level 8). Farms 250-260 km away, pre-reinforce farms with each other, wait for Wave 17 elite to reach farms, use Recall Talent to pull troops back fast + redeploy. After Wave 17 pull back. NO diamonds on Direct Relocators or Speedups. Rank 1 = ~5,000 Diamonds only.
- EXTRA-POINTS TRICKS:
  1. Post-event ghost-reinforce very-far inactive castles — troops en route from your reinforcement may still count after Wave 20. Port your castle near a distant inactive castle and reinforce while marches are in transit.
  2. Empty-castle 100% trick: if a smaller reinforced castle uses ITS troops to reinforce another (inactive) castle, so it's now empty, the reinforcer gets 100% of the points for defending it (max possible score).

SAURNESIA (cross-server): Points via Wonders (static) + Dragon Cub Escort path (spikes). Battlefield Infirmary mindset — troops returned safely afterward, so rally aggressively for 3-min wonder captures.

MONSTER HUNT: Chain hunts via Hunt Bonus multiplier. Never solo isolated high-monsters. Stamina → continuous alliance Hell Fortress rally loops.

TIMERIFT: Wave-based, both sides scale per round. Target Wave 20 min · Wave 50 ideal.

BONEYARD: Alliance-driven points. Catapult scout = 45-second stall on incoming march reveal.

FEAST: 3,000-seat cap. Variants: Common Feast, Heart Feast (and others). Rewards Startup Blessings + Glories.

ALLIANCE HELP: ~1 min per help. Reward: 800 Alliance Coins/help (daily cap 40,000). Speedup Help Cap governed ONLY by Embassy level (no Embassy = 2 helpers · Embassy L1 = 4 · each upgrade increases both count + efficiency). CAP IS LOCKED AT ALLIANCE HALL LEVEL WHEN TASK STARTED, NOT CURRENT LEVEL.

TERRITORY: Held resources (plunderable above Storage) vs Bag (safe, must withdraw to spend). Daily Cap = 10 hours of hourly output (not 24). Fast Producer talent = 5× hourly output, does NOT count against Daily Cap, activatable 2×/day.

TRAPS + SIEGE: Traps functionally useless per Froth1k (build for daily quests only). Siege does NOT get bonus damage joining Archer rallies.

DEFENSIVE: Shields > Wall Repair. Wall repair slow (~15 min per pass). Wall defeat → territory on fire 30 min → auto-relocate if wall drops to 0. Assign heroes to guard the wall.

BANK: Daily 1-day 7% > 30-day 20-50% for daily-active players.

FOOD: Food not protected by Storage is eaten by troops. Do NOT manually open food bags — system pulls automatically.

CROSS-TITLE TRAP: "Dragonia" also used in Merge Dragons for different mechanics. Red flags for wrong-game context: merge-style mini-game, "Dragon Cups" → this is NOT P&C, escalate.

STRICT: Never invent hero names, monster names, event names, patch numbers, or building levels not listed above. Non-P&C content → File 47.
=== END DOSSIER ===
"""


def system_prompt_for(game_slug: str) -> str:
    game = next((g for g in GAMES if g["slug"] == game_slug), None)
    name = game["name"] if game else "37Games title"
    genre = game["genre"] if game else "mobile strategy game"
    base = (
        CYPHER_VOICE_CODEX.replace("[GAME NAME]", name)
        + f"\n=== CURRENT SPECIALIZATION ===\n"
        f"You are the dedicated CypherAI tactical specialist for '{name}' ({genre}). "
        f"You ONLY answer about '{name}'. Every strategy, hero reference, and numeric callout must be specific to this title."
    )
    if game_slug == "puzzles-conquest":
        base += "\n\n" + PC_DOSSIER
    return base


def deepdive_system_prompt(game_slug: str, mode: str) -> str:
    game = next((g for g in GAMES if g["slug"] == game_slug), None)
    name = game["name"] if game else "37Games title"
    base = (
        CYPHER_VOICE_CODEX.replace("[GAME NAME]", name)
        + f"\n=== DEEP DIVE PROTOCOL — {name} ===\n"
        f"Read every uploaded screenshot with tactical precision — heroes, levels, resources, HQ level, alliance, VIP, gear, formation, power, event flags. "
        f"If a data point is not visible in the visuals, use one of the INTEL GAP RESPONSES. Do NOT extrapolate what cannot be seen. "
    )
    if mode == "baseline":
        return base + (
            "Produce a **DEEP DIVE BASELINE** analysis. Use this EXACT markdown structure:\n"
            "## Account Sitrep\n(1-2 sentences — power level, progression phase)\n\n"
            "## Strengths\n- bullet 1\n- bullet 2\n- bullet 3\n\n"
            "## Weaknesses\n- bullet 1\n- bullet 2\n- bullet 3\n\n"
            "## Top 5 Priority Directives\n1. **Directive** — rationale\n2. ...\n\n"
            "## Resource Allocation Recommendation\n(percentage split or focus vectors)\n\n"
            "## Next Milestones (30 / 60 / 90 days)\n- 30: ...\n- 60: ...\n- 90: ...\n\n"
            "End with: 'War Room analysis is live, Commander. Awaiting your next directive.'"
        )
    return base + (
        "This is a **FOLLOW-UP DEEP DIVE**. The previous baseline is provided as context. "
        "Compare what's changed, acknowledge progress with substance, flag regressions, update priorities. Structure:\n"
        "## Progress Since Baseline\n(2-3 sentences)\n\n"
        "## Confirmed Gains\n- ...\n\n"
        "## Stalls or Regressions\n- ...\n\n"
        "## Updated Top 5 Directives\n1. ...\n\n"
        "## Next-Phase Building Blocks\n(2-3 sentences pointing to the next growth phase)\n\n"
        "End with: 'Recon complete. Awaiting your next directive, Commander.'"
    )


# ---------- Routes ----------
@api.get("/")
async def root():
    return {"service": "37games-ai-strategy", "status": "ok"}


@api.get("/games")
async def list_games():
    return GAMES


@api.get("/games/{slug}")
async def get_game(slug: str):
    g = next((x for x in GAMES if x["slug"] == slug), None)
    if not g:
        raise HTTPException(404, "Game not found")
    return g


# ----- Auth -----
@api.post("/auth/register", response_model=AuthResponse)
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(400, "Email already registered")
    referral_code = "TA-" + secrets.token_hex(3).upper()
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": data.email.lower(),
        "username": data.username,
        "password_hash": hash_password(data.password),
        "referral_code": referral_code,
        "created_at": now_iso(),
    }
    # Resolve referral
    if data.referral_code:
        referrer = await db.users.find_one({"referral_code": data.referral_code.strip().upper()}, {"_id": 0, "id": 1})
        if referrer and referrer["id"] != user_doc["id"]:
            user_doc["referred_by"] = referrer["id"]
            user_doc["extra_baselines"] = int(user_doc.get("extra_baselines", 0)) + 1  # welcome bonus
    # Auto-link a pending seat if one exists for this email
    pending_seat = await db.seat_grants.find_one(
        {"email": data.email.lower(), "status": "pending", "redeemed_user_id": None},
        {"_id": 0},
    )
    if pending_seat:
        user_doc["seat_grant_id"] = pending_seat["id"]
        await db.seat_grants.update_one(
            {"id": pending_seat["id"]},
            {"$set": {"status": "active", "redeemed_user_id": user_doc["id"], "redeemed_at": now_iso()}},
        )
    await db.users.insert_one(user_doc)
    token = create_jwt(user_doc["id"])
    return AuthResponse(
        token=token,
        user=UserOut(id=user_doc["id"], email=user_doc["email"], username=user_doc["username"], created_at=user_doc["created_at"]),
    )


@api.post("/auth/login", response_model=AuthResponse)
async def login(data: UserLogin):
    # `data.email` is actually an identifier — accept email OR username (codename).
    ident = (data.email or "").strip()
    if not ident:
        raise HTTPException(401, "Invalid credentials")
    if "@" in ident:
        # Looks like an email
        user = await db.users.find_one({"email": ident.lower()}, {"_id": 0})
    else:
        # Username (codename) — case-insensitive exact match
        user = await db.users.find_one(
            {"username": {"$regex": f"^{re.escape(ident)}$", "$options": "i"}},
            {"_id": 0},
        )
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_jwt(user["id"])
    return AuthResponse(
        token=token,
        user=UserOut(id=user["id"], email=user["email"], username=user["username"], created_at=user["created_at"]),
    )


@api.get("/auth/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(id=user["id"], email=user["email"], username=user["username"], created_at=user["created_at"])


# ----- Password Reset -----
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


@api.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    # Rate limit by email to prevent enumeration storms
    await _rate_limit(data.email.lower(), "password_reset")
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    # Always return success to avoid leaking existence of accounts
    if not user:
        return {"ok": True, "delivered": False, "info": "If an account exists for this email, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token": token,
        "email": user["email"],
        "expires_at": expires_at.isoformat(),
        "used": False,
        "created_at": now_iso(),
    })
    reset_link = f"{APP_BASE_URL}/reset-password?token={token}"
    html = f"""
    <table style="background:#0A0A0A;color:#fff;font-family:Arial,sans-serif;padding:32px;width:100%">
      <tr><td>
        <h1 style="color:#E63946;margin:0 0 16px 0;font-size:24px">Tactical Ally — Password Reset</h1>
        <p style="color:#A1A1AA;line-height:1.6">Hi <strong style="color:#FFBA08">{user.get('username','operator')}</strong>,</p>
        <p style="color:#A1A1AA;line-height:1.6">A password reset was requested for your Tactical Ally account.
        Click the button below to set a new password. The link expires in 2 hours.</p>
        <p style="margin:24px 0">
          <a href="{reset_link}" style="background:#E63946;color:#fff;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block">Reset password</a>
        </p>
        <p style="color:#71717A;font-size:12px;line-height:1.6">Or copy and paste this link: <br/>{reset_link}</p>
        <p style="color:#71717A;font-size:12px;margin-top:24px">If you didn't request this, you can safely ignore this email.</p>
      </td></tr>
    </table>
    """
    sent, info = await send_email(user["email"], "Tactical Ally · Reset your password", html)
    resp = {"ok": True, "delivered": sent}
    # In dev mode (no Resend key), expose the link so the user can still complete the flow
    if not sent and info == "dev-mode":
        resp["dev_reset_link"] = reset_link
    return resp


@api.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    rec = await db.password_resets.find_one({"token": data.token, "used": False}, {"_id": 0})
    if not rec:
        raise HTTPException(400, "Invalid or used reset token")
    expires_at = datetime.fromisoformat(rec["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Reset link has expired")
    new_hash = hash_password(data.new_password)
    await db.users.update_one({"id": rec["user_id"]}, {"$set": {"password_hash": new_hash}})
    await db.password_resets.update_one({"token": data.token}, {"$set": {"used": True, "used_at": now_iso()}})
    return {"ok": True}


# ----- Chat -----
@api.get("/chat/sessions", response_model=List[ChatSession])
async def list_sessions(user=Depends(get_current_user), game_slug: Optional[str] = None):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    docs = await db.chat_sessions.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api.post("/chat/sessions", response_model=ChatSession)
async def create_session(data: ChatSessionCreate, user=Depends(get_current_user)):
    if data.game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": data.game_slug,
        "title": data.title or "New Conversation",
        "created_at": now_iso(),
    }
    await db.chat_sessions.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@api.delete("/chat/sessions/{sid}")
async def delete_session(sid: str, user=Depends(get_current_user)):
    res = await db.chat_sessions.delete_one({"id": sid, "user_id": user["id"]})
    await db.chat_messages.delete_many({"session_id": sid})
    if res.deleted_count == 0:
        raise HTTPException(404, "Session not found")
    return {"ok": True}


@api.get("/chat/sessions/{sid}/messages", response_model=List[ChatMessage])
async def get_messages(sid: str, user=Depends(get_current_user)):
    sess = await db.chat_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not sess:
        raise HTTPException(404, "Session not found")
    msgs = await db.chat_messages.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return msgs


@api.post("/chat/sessions/{sid}/messages")
async def send_message(sid: str, body: ChatMessageIn, user=Depends(get_current_user)):
    await _rate_limit(user["id"], "chat")
    sess = await db.chat_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not sess:
        raise HTTPException(404, "Session not found")

    # Persist user msg
    user_msg = {
        "id": str(uuid.uuid4()),
        "session_id": sid,
        "role": "user",
        "content": body.content,
        "created_at": now_iso(),
    }
    await db.chat_messages.insert_one(user_msg)

    # Update title if first user message and current title is default
    history = await db.chat_messages.find({"session_id": sid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    if sess["title"] == "New Conversation":
        new_title = body.content[:50] + ("…" if len(body.content) > 50 else "")
        await db.chat_sessions.update_one({"id": sid}, {"$set": {"title": new_title}})

    # Build a fresh LlmChat with full history replayed
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=sid,
        system_message=system_prompt_for(sess["game_slug"]),
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    # Replay previous turns (excluding the just-inserted user_msg, which we'll stream now)
    prior = [m for m in history if m["id"] != user_msg["id"]]
    # The library tracks its own history; we feed prior conversation by sending non-streaming
    # turns silently is not supported. Instead we just stream the new message with system prompt
    # carrying the persona. The DB stores full history for the UI.

    async def event_gen():
        buf = []
        try:
            # Replay condensed: prepend last few messages as context block in the message itself
            ctx_lines = []
            for m in prior[-10:]:
                tag = "USER" if m["role"] == "user" else "ASSISTANT"
                ctx_lines.append(f"[{tag}] {m['content']}")
            ctx = ("\n".join(ctx_lines) + "\n\n[USER] ") if ctx_lines else ""
            prompt_text = ctx + body.content
            async for ev in chat.stream_message(UserMessage(text=prompt_text)):
                if isinstance(ev, TextDelta):
                    buf.append(ev.content)
                    yield f"data: {ev.content}\n\n"
                elif isinstance(ev, StreamDone):
                    break
        except Exception as e:
            logging.exception("LLM stream error")
            yield f"data: [error] {str(e)}\n\n"
        finally:
            full = "".join(buf).strip() or "(no response)"
            assistant_msg = {
                "id": str(uuid.uuid4()),
                "session_id": sid,
                "role": "assistant",
                "content": full,
                "created_at": now_iso(),
            }
            await db.chat_messages.insert_one(assistant_msg)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


# ----- Builds -----
@api.post("/builds", response_model=Build)
async def create_build(data: BuildCreate, user=Depends(get_current_user)):
    if data.game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": data.game_slug,
        "title": data.title,
        "team": data.team,
        "notes": data.notes,
        "created_at": now_iso(),
    }
    await db.builds.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@api.get("/builds", response_model=List[Build])
async def list_builds(user=Depends(get_current_user), game_slug: Optional[str] = None):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    return await db.builds.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)


@api.delete("/builds/{bid}")
async def delete_build(bid: str, user=Depends(get_current_user)):
    res = await db.builds.delete_one({"id": bid, "user_id": user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(404, "Build not found")
    return {"ok": True}


# ----- Build Optimizer (AI) -----
class OptimizerRequest(BaseModel):
    game_slug: str
    objective: str
    resources: str = ""
    roster: str = ""


@api.post("/optimizer")
async def optimize(req: OptimizerRequest, user=Depends(get_current_user)):
    await _rate_limit(user["id"], "optimizer")
    if req.game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    sys_prompt = (
        system_prompt_for(req.game_slug)
        + " You will receive an OBJECTIVE, available RESOURCES and current ROSTER. "
        "Respond with: 1) RECOMMENDED TEAM (5 bullet picks max), 2) PRIORITY UPGRADES, "
        "3) RESOURCE ALLOCATION (% split), 4) WARNINGS. Use markdown bold headers."
    )
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"opt-{uuid.uuid4()}",
        system_message=sys_prompt,
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    prompt = f"OBJECTIVE: {req.objective}\nRESOURCES: {req.resources or 'unspecified'}\nROSTER: {req.roster or 'unspecified'}"
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        return {"result": response}
    except Exception as e:
        logging.exception("optimizer failed")
        raise HTTPException(500, f"Optimizer error: {e}")


# ----- Guides -----
@api.get("/guides")
async def list_guides(game_slug: Optional[str] = None):
    q = {}
    if game_slug:
        q["game_slug"] = game_slug
    docs = await db.guides.find(q, {"_id": 0}).to_list(500)
    return docs


# ----- Tasks (Daily Planner) -----
@api.post("/tasks", response_model=Task)
async def create_task(data: TaskCreate, user=Depends(get_current_user)):
    if data.game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": data.game_slug,
        "title": data.title,
        "priority": data.priority,
        "completed": False,
        "created_at": now_iso(),
    }
    await db.tasks.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@api.get("/tasks", response_model=List[Task])
async def list_tasks(user=Depends(get_current_user), game_slug: Optional[str] = None):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    return await db.tasks.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


@api.patch("/tasks/{tid}", response_model=Task)
async def update_task(tid: str, data: TaskUpdate, user=Depends(get_current_user)):
    update = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not update:
        raise HTTPException(400, "Nothing to update")
    res = await db.tasks.update_one({"id": tid, "user_id": user["id"]}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "Task not found")
    doc = await db.tasks.find_one({"id": tid}, {"_id": 0})
    return doc


@api.delete("/tasks/{tid}")
async def delete_task(tid: str, user=Depends(get_current_user)):
    res = await db.tasks.delete_one({"id": tid, "user_id": user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(404, "Task not found")
    return {"ok": True}


# ----- Deep Dive (CypherAI vision analysis) -----
MAX_SHOTS = 6
MAX_BYTES = 6 * 1024 * 1024  # 6 MB per image
ALLOWED_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}


async def _analyze_screenshots(
    game_slug: str, screenshots_b64: list[str], mode: str, context: str = "", user_notes: str = ""
) -> str:
    images = [ImageContent(image_base64=b) for b in screenshots_b64]
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"dd-{uuid.uuid4()}",
        system_message=deepdive_system_prompt(game_slug, mode),
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    prompt = f"User notes: {user_notes or '(none)'}\n"
    if context:
        prompt += f"\n--- BASELINE ANALYSIS FOR CONTEXT ---\n{context}\n--- END BASELINE ---\n"
    prompt += "\nAnalyze the attached screenshots and respond per the instructed structure."
    msg = UserMessage(text=prompt, file_contents=images)
    return await chat.send_message(msg)


async def _validate_and_store_files(files: list[UploadFile], user_id: str) -> list[dict]:
    """Validate MIME + size, push each file into GridFS. Returns list of {file_id, mime, name, size}."""
    if not files:
        raise HTTPException(400, "No screenshots provided")
    if len(files) > MAX_SHOTS:
        raise HTTPException(400, f"Max {MAX_SHOTS} screenshots per analysis")
    stored = []
    for f in files:
        mime = (f.content_type or "").lower()
        if mime not in ALLOWED_MIMES:
            raise HTTPException(400, f"Unsupported file type '{mime}' for {f.filename}. Allowed: PNG, JPEG, WebP, GIF.")
        data = await f.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(400, f"{f.filename} exceeds {MAX_BYTES // (1024*1024)}MB limit")
        if len(data) < 100:  # too small to be a real image
            raise HTTPException(400, f"{f.filename} is empty or corrupted")
        file_id = await gridfs_bucket.upload_from_stream(
            f.filename or "screenshot",
            data,
            metadata={"user_id": user_id, "mime": mime, "size": len(data)},
        )
        stored.append({
            "file_id": str(file_id),
            "mime": mime,
            "name": f.filename or "screenshot",
            "size": len(data),
        })
    return stored


async def _gridfs_to_b64(refs: list[dict]) -> list[str]:
    """Read GridFS file ids back into base64 strings for the LLM call."""
    out = []
    for ref in refs:
        stream = await gridfs_bucket.open_download_stream(ObjectId(ref["file_id"]))
        data = await stream.read()
        out.append(base64.b64encode(data).decode())
    return out


async def _delete_gridfs_refs(refs: list[dict]):
    for ref in refs or []:
        try:
            await gridfs_bucket.delete(ObjectId(ref["file_id"]))
        except Exception:
            logging.warning("Could not delete gridfs file %s", ref.get("file_id"))


@api.post("/deep-dive")
async def create_deep_dive(
    game_slug: str = Form(...),
    title: str = Form("Account Baseline"),
    notes: str = Form(""),
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    if game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    refs = await _validate_and_store_files(files, user["id"])
    # Enforce subscription / topup quota BEFORE rate-limit & LLM call
    try:
        source = await consume_baseline(user["id"], game_slug=game_slug)
    except HTTPException:
        await _delete_gridfs_refs(refs)
        raise
    try:
        await _rate_limit(user["id"], "deep_dive")
    except HTTPException:
        await _delete_gridfs_refs(refs)
        # rollback quota
        if source == "subscription":
            await db.users.update_one({"id": user["id"]}, {"$inc": {"analyses_used_this_period": -1}})
        else:
            await db.users.update_one({"id": user["id"]}, {"$inc": {"extra_baselines": 1}})
        raise
    try:
        b64 = await _gridfs_to_b64(refs)
        analysis = await _analyze_screenshots(game_slug, b64, mode="baseline", user_notes=notes)
    except HTTPException:
        await _delete_gridfs_refs(refs)
        raise
    except Exception as e:
        await _delete_gridfs_refs(refs)
        logging.exception("deep dive baseline failed: %s", e)
        raise HTTPException(500, "CypherAI analysis failed. Please try again.")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": game_slug,
        "title": title,
        "baseline_analysis": analysis,
        "baseline_shots": refs,  # GridFS refs only — small
        "baseline_notes": notes,
        "follow_ups": [],
        "created_at": now_iso(),
    }
    await db.deep_dives.insert_one(doc)
    out = {k: v for k, v in doc.items() if k != "_id"}
    out["shot_count"] = len(refs)
    return out


@api.post("/deep-dive/{did}/followup")
async def add_followup(
    did: str,
    notes: str = Form(""),
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    dd = await db.deep_dives.find_one({"id": did, "user_id": user["id"]}, {"_id": 0})
    if not dd:
        raise HTTPException(404, "Deep dive not found")
    refs = await _validate_and_store_files(files, user["id"])
    try:
        await _rate_limit(user["id"], "deep_dive")
    except HTTPException:
        await _delete_gridfs_refs(refs)
        raise
    try:
        b64 = await _gridfs_to_b64(refs)
        analysis = await _analyze_screenshots(
            dd["game_slug"], b64, mode="followup",
            context=dd["baseline_analysis"], user_notes=notes,
        )
    except HTTPException:
        await _delete_gridfs_refs(refs)
        raise
    except Exception:
        await _delete_gridfs_refs(refs)
        logging.exception("deep dive followup failed")
        raise HTTPException(500, "CypherAI analysis failed. Please try again.")
    block = {
        "id": str(uuid.uuid4()),
        "analysis": analysis,
        "notes": notes,
        "shots": refs,
        "shot_count": len(refs),
        "created_at": now_iso(),
    }
    await db.deep_dives.update_one({"id": did}, {"$push": {"follow_ups": block}})
    out = {k: v for k, v in block.items()}
    return out


@api.get("/deep-dive")
async def list_deep_dives(user=Depends(get_current_user), game_slug: Optional[str] = None):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    docs = await db.deep_dives.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    for d in docs:
        d["shot_count"] = len(d.get("baseline_shots", []))
        d["followup_count"] = len(d.get("follow_ups", []))
    return docs


@api.get("/deep-dive/{did}")
async def get_deep_dive(did: str, user=Depends(get_current_user)):
    dd = await db.deep_dives.find_one({"id": did, "user_id": user["id"]}, {"_id": 0})
    if not dd:
        raise HTTPException(404, "Not found")
    return dd


@api.get("/deep-dive/shot/{file_id}")
async def get_shot(file_id: str, user=Depends(get_current_user)):
    """Stream a stored screenshot back to the client (auth-gated)."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file id")
    try:
        stream = await gridfs_bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(404, "File not found")
    meta = stream.metadata or {}
    if meta.get("user_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    data = await stream.read()
    return Response(content=data, media_type=meta.get("mime", "image/png"))


@api.delete("/deep-dive/{did}")
async def delete_deep_dive(did: str, user=Depends(get_current_user)):
    dd = await db.deep_dives.find_one({"id": did, "user_id": user["id"]}, {"_id": 0})
    if not dd:
        raise HTTPException(404, "Not found")
    # Best-effort GridFS cleanup
    await _delete_gridfs_refs(dd.get("baseline_shots", []))
    for fu in dd.get("follow_ups", []):
        await _delete_gridfs_refs(fu.get("shots", []))
    await db.deep_dives.delete_one({"id": did})
    return {"ok": True}


# ---------- CypherAI Guided Deep Dive ----------
DEFAULT_GUIDE_STEPS = [
    {"id": "headquarters", "title": "Headquarters / Stronghold", "desc": "Open your main base/HQ screen so the level and power are visible."},
    {"id": "heroes", "title": "Hero roster", "desc": "Show your full hero list (sorted by power or rarity)."},
    {"id": "formation", "title": "Active formation", "desc": "Open your current battle team / formation screen."},
    {"id": "gear", "title": "Gear & equipment", "desc": "Open the gear/equipment screen for your main hero."},
    {"id": "resources", "title": "Resources stockpile", "desc": "Show your resources (gold, food, iron, gems, speedups)."},
    {"id": "alliance", "title": "Alliance status", "desc": "Open your alliance profile — name, level, your role."},
    {"id": "vip_account", "title": "VIP / account level", "desc": "Open your profile or VIP screen showing account level & VIP tier."},
]


async def _generate_guide_plan(game_slug: str) -> list[dict]:
    game = next((g for g in GAMES if g["slug"] == game_slug), None)
    name = game["name"] if game else game_slug
    prompt = (
        f"You are CypherAI, the strict specialist for the 37Games title '{name}'. "
        "A player has asked you to guide them through screenshotting their account for a Deep Dive analysis. "
        "Produce a JSON array of 6-8 steps in priority order. Each step is {\"id\":\"snake_case\",\"title\":\"short\",\"desc\":\"one sentence telling exactly which screen to open and what should be visible\"}. "
        "Be SPECIFIC to this title — name the actual menu paths, screens, and what data matters. "
        "Output ONLY the JSON array, nothing else."
    )
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"guide-plan-{game_slug}",
        system_message="You output only valid JSON arrays as requested.",
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    try:
        raw = await chat.send_message(UserMessage(text=prompt))
        import json as _json
        # Strip code fences if any
        cleaned = raw.strip().lstrip("`").lstrip("json").strip().rstrip("`").strip()
        # Find array bracket
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start >= 0 and end > start:
            cleaned = cleaned[start:end + 1]
        plan = _json.loads(cleaned)
        # Validate shape
        if not isinstance(plan, list) or not all(isinstance(s, dict) and {"id", "title", "desc"} <= set(s.keys()) for s in plan):
            raise ValueError("invalid shape")
        return plan[:8]
    except Exception as e:
        logging.warning("guide plan LLM gen failed for %s: %s — using default", game_slug, e)
        return DEFAULT_GUIDE_STEPS


@api.get("/deep-dive-guide-plan")
async def get_guide_plan(game_slug: str, user=Depends(get_current_user)):
    if game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    cached = await db.guide_plans.find_one({"game_slug": game_slug}, {"_id": 0})
    if cached:
        return cached
    plan = await _generate_guide_plan(game_slug)
    doc = {"game_slug": game_slug, "steps": plan, "created_at": now_iso()}
    await db.guide_plans.insert_one(doc)
    return doc


@api.post("/guided-dive/start")
async def start_guided(game_slug: str = Form(...), user=Depends(get_current_user)):
    if game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    plan_doc = await db.guide_plans.find_one({"game_slug": game_slug}, {"_id": 0})
    if not plan_doc:
        plan = await _generate_guide_plan(game_slug)
        plan_doc = {"game_slug": game_slug, "steps": plan, "created_at": now_iso()}
        await db.guide_plans.insert_one(plan_doc)
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": game_slug,
        "steps": plan_doc["steps"],
        "uploads": {},          # step_id -> [gridfs refs]
        "skipped": [],          # list of step_ids
        "qa": [],               # list of {q, a, at}
        "status": "in_progress",
        "created_at": now_iso(),
    }
    await db.guided_sessions.insert_one(session)
    return {k: v for k, v in session.items() if k != "_id"}


@api.get("/guided-dive/{sid}")
async def get_guided(sid: str, user=Depends(get_current_user)):
    s = await db.guided_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@api.post("/guided-dive/{sid}/upload")
async def upload_guided_step(
    sid: str,
    step_id: str = Form(...),
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    s = await db.guided_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    if s["status"] != "in_progress":
        raise HTTPException(400, "Session is closed")
    valid_step_ids = {st["id"] for st in s["steps"]}
    if step_id not in valid_step_ids:
        raise HTTPException(400, "Unknown step_id")
    # Replace existing uploads for this step (so users can retake)
    existing = s.get("uploads", {}).get(step_id, [])
    if existing:
        await _delete_gridfs_refs(existing)
    refs = await _validate_and_store_files(files, user["id"])
    await db.guided_sessions.update_one(
        {"id": sid},
        {"$set": {f"uploads.{step_id}": refs}, "$pull": {"skipped": step_id}},
    )
    s2 = await db.guided_sessions.find_one({"id": sid}, {"_id": 0})
    return s2


@api.post("/guided-dive/{sid}/skip")
async def skip_guided_step(sid: str, step_id: str = Form(...), user=Depends(get_current_user)):
    s = await db.guided_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    if step_id not in {st["id"] for st in s["steps"]}:
        raise HTTPException(400, "Unknown step_id")
    # If user had uploaded for this step, clean up
    existing = s.get("uploads", {}).get(step_id, [])
    if existing:
        await _delete_gridfs_refs(existing)
    await db.guided_sessions.update_one(
        {"id": sid},
        {"$addToSet": {"skipped": step_id}, "$unset": {f"uploads.{step_id}": ""}},
    )
    return await db.guided_sessions.find_one({"id": sid}, {"_id": 0})


class GuidedAsk(BaseModel):
    question: str = Field(min_length=2, max_length=600)


@api.post("/guided-dive/{sid}/ask")
async def guided_ask(sid: str, body: GuidedAsk, user=Depends(get_current_user)):
    s = await db.guided_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    await _rate_limit(user["id"], "chat")
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"guided-qa-{sid}",
        system_message=system_prompt_for(s["game_slug"]) + " You are supporting the Commander during a Guided Deep Dive — keep replies ≤120 words, tactical, direct.",
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    try:
        answer = await chat.send_message(UserMessage(text=body.question.strip()))
    except Exception as e:
        logging.exception("guided ask failed: %s", e)
        raise HTTPException(500, "CypherAI couldn't answer right now.")
    qa_entry = {"id": str(uuid.uuid4()), "q": body.question.strip(), "a": answer, "at": now_iso()}
    await db.guided_sessions.update_one({"id": sid}, {"$push": {"qa": qa_entry}})
    return qa_entry


class FinalizeGuided(BaseModel):
    title: Optional[str] = "Guided Baseline"
    notes: Optional[str] = ""


@api.post("/guided-dive/{sid}/finalize")
async def finalize_guided(sid: str, body: FinalizeGuided, user=Depends(get_current_user)):
    s = await db.guided_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    if s["status"] != "in_progress":
        raise HTTPException(400, "Session already finalized")
    # Collect all uploaded refs in step order
    all_refs: list[dict] = []
    captured_steps: list[str] = []
    for st in s["steps"]:
        refs = s.get("uploads", {}).get(st["id"], [])
        if refs:
            all_refs.extend(refs)
            captured_steps.append(st["id"])
    if not all_refs:
        raise HTTPException(400, "Upload at least one screenshot before finalizing.")
    # Enforce baseline quota
    try:
        source = await consume_baseline(user["id"], game_slug=s["game_slug"])
    except HTTPException:
        raise
    # Build notes for the LLM: include user notes + step-by-step context map
    step_context = "\n".join(
        f"- {st['title']}: {'captured' if st['id'] in captured_steps else 'skipped'}" for st in s["steps"]
    )
    augmented_notes = f"{body.notes or ''}\n\n[Guided capture coverage]\n{step_context}".strip()
    try:
        b64 = await _gridfs_to_b64(all_refs)
        analysis = await _analyze_screenshots(s["game_slug"], b64, mode="baseline", user_notes=augmented_notes)
    except Exception as e:
        # Rollback quota on failure
        if source == "subscription":
            await db.users.update_one({"id": user["id"]}, {"$inc": {"analyses_used_this_period": -1}})
        else:
            await db.users.update_one({"id": user["id"]}, {"$inc": {"extra_baselines": 1}})
        logging.exception("guided finalize failed: %s", e)
        raise HTTPException(500, "CypherAI analysis failed. Please try again.")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": s["game_slug"],
        "title": body.title or "Guided Baseline",
        "baseline_analysis": analysis,
        "baseline_shots": all_refs,
        "baseline_notes": body.notes or "",
        "follow_ups": [],
        "created_at": now_iso(),
        "via_guided_session": sid,
    }
    await db.deep_dives.insert_one(doc)
    await db.guided_sessions.update_one({"id": sid}, {"$set": {"status": "finalized", "deep_dive_id": doc["id"], "finalized_at": now_iso()}})
    return {"deep_dive_id": doc["id"], "title": doc["title"]}


@api.delete("/guided-dive/{sid}")
async def abandon_guided(sid: str, user=Depends(get_current_user)):
    s = await db.guided_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Session not found")
    # Clean up any uploaded shots that weren't finalized
    if s.get("status") == "in_progress":
        for refs in (s.get("uploads") or {}).values():
            await _delete_gridfs_refs(refs)
    await db.guided_sessions.delete_one({"id": sid})
    return {"ok": True}


# ---------- CypherAI Guided Deep Dive END ----------


# ---------- Billing (Stripe subscription + topup) ----------
PACKAGES = {
    "subscription_monthly": {
        "name": "Tactical Ally Pro — Monthly",
        "amount": 4.99,
        "currency": "usd",
        "kind": "subscription",
        "baselines": 2,
        "period_days": 30,
        "included_games": 2,
        "description": "Full Pro access for 2 games of your choice. Includes 2 CypherAI Deep Dive baselines/month + unlimited follow-up Building Blocks.",
    },
    "topup_analysis": {
        "name": "Single Deep Dive",
        "amount": 2.99,
        "currency": "usd",
        "kind": "one_time",
        "baselines": 1,
        "description": "One-shot Deep Dive on ANY game — no subscription, never expires.",
    },
    "extra_game_monthly": {
        "name": "Extra Game Slot — Monthly",
        "amount": 0.99,
        "currency": "usd",
        "kind": "extra_game",
        "period_days": 30,
        "description": "Adds 1 additional game to your Pro plan. Stack as many as you play. Requires active Pro.",
    },
    "toc_addon_monthly": {
        "name": "Alliance Chat Seat — Monthly (per member)",
        "amount": 0.99,
        "currency": "usd",
        "kind": "toc_addon",
        "period_days": 30,
        "description": "Per-member access to alliance chat rooms. Each player pays their own $0.99/mo. Requires active Pro.",
    },
}


async def get_user_quota(user: dict) -> dict:
    """Computes the user's current quota state (auto-renews monthly window)."""
    now = datetime.now(timezone.utc)
    # Check alliance seat first — overrides everything to free unlimited Pro+TOC
    seat_id = user.get("seat_grant_id")
    seat_active = False
    seat_alliance = None
    if seat_id:
        seat = await db.seat_grants.find_one({"id": seat_id}, {"_id": 0})
        if seat and seat.get("status") == "active" and not seat.get("revoked_at"):
            seat_active = True
            seat_alliance = seat.get("alliance_name")
    sub_end_iso = user.get("subscription_period_end")
    sub_active = False
    sub_end = None
    if sub_end_iso:
        sub_end = datetime.fromisoformat(sub_end_iso)
        sub_active = sub_end > now
    plan = "alliance_seat" if seat_active else ("pro" if sub_active else "free")
    # Seat overrides give 2 monthly baselines too (resets via same analyses_used_this_period field)
    if seat_active:
        used = int(user.get("analyses_used_this_period", 0))
        period_baselines_remaining = max(0, 4 - used)  # alliance seat gets 4 baselines/month
    elif sub_active:
        used = int(user.get("analyses_used_this_period", 0))
        period_baselines_remaining = max(0, 2 - used)
    else:
        period_baselines_remaining = 0
    extra_baselines = int(user.get("extra_baselines", 0))
    toc_end_iso = user.get("toc_period_end")
    toc_active = False
    if toc_end_iso:
        toc_end = datetime.fromisoformat(toc_end_iso)
        toc_active = toc_end > now
    # Seat grants TOC access too
    if seat_active:
        toc_active = True
    # Per-game slots: 2 included with Pro + each $0.99 extra_game purchase = +1 slot
    pro_game_slots = int(user.get("pro_game_slots", 2 if sub_active else 0))
    pro_games = list(user.get("pro_games", []))
    if seat_active:
        # Alliance seat = unlimited games
        pro_game_slots = 99
    scout_credits = round(float(user.get("scout_credits", 0)), 2)
    return {
        "plan": plan,
        "subscription_active": sub_active or seat_active,
        "subscription_period_end": sub_end.isoformat() if sub_end else None,
        "period_baselines_remaining": period_baselines_remaining,
        "extra_baselines": extra_baselines,
        "total_baselines_available": period_baselines_remaining + extra_baselines,
        "toc_active": toc_active,
        "toc_period_end": user.get("toc_period_end"),
        "seat_alliance": seat_alliance,
        "via_alliance_seat": seat_active,
        "pro_game_slots": pro_game_slots,
        "pro_games": pro_games,
        "pro_games_remaining": max(0, pro_game_slots - len(pro_games)),
        "scout_credits": scout_credits,
    }


async def require_toc_access(user: dict):
    """Raises 402 if user can't use the Tactical Operations Center."""
    q = await get_user_quota(user)
    if not q["subscription_active"]:
        raise HTTPException(402, "Tactical Operations Center requires Tactical Ally Pro ($4.99/mo) + TOC add-on ($0.99/mo).")
    if not q["toc_active"]:
        raise HTTPException(402, "Add the Tactical Operations Center add-on ($0.99/mo) to create or join alliance chat rooms.")


async def consume_baseline(user_id: str, game_slug: Optional[str] = None):
    """Atomically debit one baseline from the user's quota. Raises 402 if none available.

    If a game_slug is provided and the user is on the Pro plan, enforce per-game slots:
    - If the game is already in pro_games[], allow.
    - If not, and the user still has free slots (len(pro_games) < pro_game_slots), auto-add the game.
    - Otherwise, raise 402 telling the user to add an Extra Game slot ($0.99/mo) or use a $2.99 top-up.
    Alliance seats bypass the per-game gate (unlimited).
    """
    # Alliance seat users bypass per-game gating entirely
    u = await db.users.find_one({"id": user_id}, {"_id": 0})
    seat_grant_id = (u or {}).get("seat_grant_id")
    seat_bypass = False
    if seat_grant_id:
        seat = await db.seat_grants.find_one({"id": seat_grant_id}, {"_id": 0})
        if seat and seat.get("status") == "active":
            seat_bypass = True

    # Try subscription period first
    res = await db.users.find_one_and_update(
        {
            "id": user_id,
            "subscription_period_end": {"$exists": True, "$ne": None},
            "analyses_used_this_period": {"$lt": 2},
        },
        {"$inc": {"analyses_used_this_period": 1}},
        return_document=True,
    )
    if res:
        # Verify subscription is still active
        end = datetime.fromisoformat(res["subscription_period_end"])
        if end > datetime.now(timezone.utc):
            # Enforce per-game slot rules unless alliance-seat bypass
            if game_slug and not seat_bypass:
                slots = int(res.get("pro_game_slots", 2))
                games = list(res.get("pro_games", []))
                if game_slug not in games:
                    if len(games) < slots:
                        # Auto-assign the game to an available slot
                        await db.users.update_one({"id": user_id}, {"$addToSet": {"pro_games": game_slug}})
                    else:
                        # Rollback the debit
                        await db.users.update_one({"id": user_id}, {"$inc": {"analyses_used_this_period": -1}})
                        raise HTTPException(402, f"All {slots} Pro game slots are in use. Add an Extra Game slot ($0.99/mo) or use a one-shot Deep Dive ($2.99) to analyze {game_slug}.")
            return "subscription"
        # Was past period; rollback & try extras
        await db.users.update_one({"id": user_id}, {"$inc": {"analyses_used_this_period": -1}})
    # Try extras (no per-game restriction — one-shot deep dives work on ANY game)
    res2 = await db.users.find_one_and_update(
        {"id": user_id, "extra_baselines": {"$gt": 0}},
        {"$inc": {"extra_baselines": -1}},
        return_document=True,
    )
    if res2:
        return "topup"
    raise HTTPException(402, "No Deep Dive analyses available. Subscribe to Tactical Ally Pro or buy a single Deep Dive top-up.")


@api.get("/billing/quota")
async def billing_quota(user=Depends(get_current_user)):
    return await get_user_quota(user)


@api.get("/billing/packages")
async def billing_packages():
    return [{"id": pid, **{k: v for k, v in p.items()}} for pid, p in PACKAGES.items()]


class CheckoutBody(BaseModel):
    package_id: str
    origin_url: str


@api.post("/billing/checkout")
async def billing_checkout(body: CheckoutBody, user=Depends(get_current_user)):
    if not STRIPE_API_KEY:
        raise HTTPException(500, "Stripe is not configured")
    if body.package_id not in PACKAGES:
        raise HTTPException(400, "Unknown package")
    pkg = PACKAGES[body.package_id]
    origin = body.origin_url.rstrip("/")
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/billing/cancel"
    webhook_url = f"{APP_BASE_URL}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    req = CheckoutSessionRequest(
        amount=float(pkg["amount"]),
        currency=pkg["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user["id"], "package_id": body.package_id, "email": user["email"]},
    )
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(req)
    # Record transaction in 'initiated' state
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": user["id"],
        "email": user["email"],
        "package_id": body.package_id,
        "amount": float(pkg["amount"]),
        "currency": pkg["currency"],
        "status": "initiated",
        "payment_status": "pending",
        "metadata": {"package_id": body.package_id, "user_id": user["id"]},
        "created_at": now_iso(),
    })
    return {"url": session.url, "session_id": session.session_id}


async def _apply_successful_payment(tx: dict):
    """Idempotent: only applies entitlements once per session."""
    if tx.get("entitlement_applied"):
        return
    pkg = PACKAGES.get(tx["package_id"])
    if not pkg:
        return
    if pkg["kind"] == "subscription":
        period_end = datetime.now(timezone.utc) + timedelta(days=pkg["period_days"])
        # On (re)subscription, reset usage counters but PRESERVE pro_games selection.
        # Also ensure pro_game_slots is at least the included_games (2).
        included = int(pkg.get("included_games", 2))
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$set": {
                "subscription_status": "active",
                "subscription_period_end": period_end.isoformat(),
                "analyses_used_this_period": 0,
            }, "$max": {"pro_game_slots": included}},
        )
    elif pkg["kind"] == "one_time":
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$inc": {"extra_baselines": int(pkg["baselines"])}},
        )
    elif pkg["kind"] == "extra_game":
        # +1 slot, extend extra_games_period_end by 30 days (informational; renewal handled by Stripe in prod)
        period_end = datetime.now(timezone.utc) + timedelta(days=pkg["period_days"])
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$inc": {"pro_game_slots": 1}, "$set": {"extra_games_last_purchase": now_iso(), "extra_games_period_end": period_end.isoformat()}},
        )
    elif pkg["kind"] == "toc_addon":
        toc_end = datetime.now(timezone.utc) + timedelta(days=pkg["period_days"])
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$set": {"toc_period_end": toc_end.isoformat()}},
        )
    # Referral reward on FIRST paid event for this user (any package)
    user = await db.users.find_one({"id": tx["user_id"]}, {"_id": 0})
    if user and user.get("referred_by") and not user.get("referral_reward_paid"):
        # Check referrer's monthly cap
        referrer_id = user["referred_by"]
        referrer = await db.users.find_one({"id": referrer_id}, {"_id": 0})
        if referrer:
            window_start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            recent = await db.referral_rewards.count_documents({"referrer_id": referrer_id, "created_at": {"$gte": window_start}})
            if recent < REFERRAL_MONTHLY_CAP:
                await db.users.update_one({"id": referrer_id}, {"$inc": {"extra_baselines": 1}})
                await db.referral_rewards.insert_one({
                    "id": str(uuid.uuid4()),
                    "referrer_id": referrer_id,
                    "referred_user_id": user["id"],
                    "session_id": tx["session_id"],
                    "package_id": tx["package_id"],
                    "created_at": now_iso(),
                })
                await db.users.update_one({"id": user["id"]}, {"$set": {"referral_reward_paid": True}})
    await db.payment_transactions.update_one(
        {"session_id": tx["session_id"]},
        {"$set": {"entitlement_applied": True, "applied_at": now_iso()}},
    )


@api.get("/billing/checkout/{session_id}/status")
async def billing_status(session_id: str, user=Depends(get_current_user)):
    if not STRIPE_API_KEY:
        raise HTTPException(500, "Stripe is not configured")
    tx = await db.payment_transactions.find_one({"session_id": session_id, "user_id": user["id"]}, {"_id": 0})
    if not tx:
        raise HTTPException(404, "Transaction not found")
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{APP_BASE_URL}/api/webhook/stripe")
    status_resp: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": status_resp.status, "payment_status": status_resp.payment_status, "last_checked": now_iso()}},
    )
    if status_resp.payment_status == "paid":
        tx_now = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        await _apply_successful_payment(tx_now)
    return {
        "status": status_resp.status,
        "payment_status": status_resp.payment_status,
        "amount": status_resp.amount_total,
        "currency": status_resp.currency,
    }


@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    if not STRIPE_API_KEY:
        raise HTTPException(500, "Stripe is not configured")
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{APP_BASE_URL}/api/webhook/stripe")
    try:
        event = await stripe_checkout.handle_webhook(body, sig)
    except Exception as e:
        logging.exception("webhook verify failed")
        raise HTTPException(400, f"Invalid webhook: {e}")
    if event.payment_status == "paid":
        tx = await db.payment_transactions.find_one({"session_id": event.session_id}, {"_id": 0})
        if tx:
            await db.payment_transactions.update_one(
                {"session_id": event.session_id},
                {"$set": {"payment_status": "paid", "status": "complete"}},
            )
            tx = await db.payment_transactions.find_one({"session_id": event.session_id}, {"_id": 0})
            await _apply_successful_payment(tx)
    return {"received": True}


# ---------- Share links (Deep Dive + Builds) ----------
@api.post("/deep-dive/{did}/share")
async def share_deep_dive(did: str, user=Depends(get_current_user)):
    dd = await db.deep_dives.find_one({"id": did, "user_id": user["id"]}, {"_id": 0})
    if not dd:
        raise HTTPException(404, "Not found")
    token = dd.get("share_token") or secrets.token_urlsafe(16)
    await db.deep_dives.update_one(
        {"id": did},
        {"$set": {"share_token": token, "shared_at": now_iso()}},
    )
    return {"share_token": token, "url": f"{APP_BASE_URL}/share/d/{token}"}


@api.delete("/deep-dive/{did}/share")
async def unshare_deep_dive(did: str, user=Depends(get_current_user)):
    res = await db.deep_dives.update_one(
        {"id": did, "user_id": user["id"]},
        {"$unset": {"share_token": "", "shared_at": ""}},
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


@api.get("/share/d/{token}")
async def public_deep_dive(token: str):
    dd = await db.deep_dives.find_one({"share_token": token}, {"_id": 0, "baseline_shots": 0, "follow_ups.shots": 0})
    if not dd:
        raise HTTPException(404, "Share not found")
    user = await db.users.find_one({"id": dd["user_id"]}, {"_id": 0, "username": 1})
    return {
        "title": dd["title"],
        "game_slug": dd["game_slug"],
        "baseline_analysis": dd["baseline_analysis"],
        "baseline_notes": dd.get("baseline_notes", ""),
        "follow_ups": [{"id": f["id"], "analysis": f["analysis"], "notes": f.get("notes", ""), "created_at": f["created_at"]} for f in dd.get("follow_ups", [])],
        "created_at": dd["created_at"],
        "shared_by": user.get("username") if user else "operator",
    }


@api.post("/builds/{bid}/share")
async def share_build(bid: str, user=Depends(get_current_user)):
    b = await db.builds.find_one({"id": bid, "user_id": user["id"]}, {"_id": 0})
    if not b:
        raise HTTPException(404, "Not found")
    token = b.get("share_token") or secrets.token_urlsafe(16)
    await db.builds.update_one({"id": bid}, {"$set": {"share_token": token, "shared_at": now_iso()}})
    return {"share_token": token, "url": f"{APP_BASE_URL}/share/b/{token}"}


@api.get("/share/b/{token}")
async def public_build(token: str):
    b = await db.builds.find_one({"share_token": token}, {"_id": 0})
    if not b:
        raise HTTPException(404, "Share not found")
    user = await db.users.find_one({"id": b["user_id"]}, {"_id": 0, "username": 1})
    return {
        "title": b["title"],
        "game_slug": b["game_slug"],
        "team": b.get("team", []),
        "notes": b.get("notes", ""),
        "created_at": b["created_at"],
        "shared_by": user.get("username") if user else "operator",
    }


# ---------- Tactical Operations Center (Alliances) ----------
# (Unlimited members — no MAX cap)


def _make_alliance_code() -> str:
    return secrets.token_hex(3).upper()  # 6-char


class AllianceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    game_slug: str
    description: Optional[str] = Field(default="", max_length=240)


class AllianceJoin(BaseModel):
    code: str


class TextMsg(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class AskCyphrMsg(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class ShareRefMsg(BaseModel):
    ref_id: str  # deep_dive_id or build_id


async def _get_member_alliance(aid: str, user_id: str) -> dict:
    a = await db.alliances.find_one({"id": aid}, {"_id": 0})
    if not a:
        raise HTTPException(404, "Alliance not found")
    if user_id not in a.get("member_ids", []):
        raise HTTPException(403, "Not a member of this alliance")
    return a


async def _push_message(alliance_id: str, user: dict, mtype: str, content: str, refs: Optional[dict] = None) -> dict:
    msg = {
        "id": str(uuid.uuid4()),
        "alliance_id": alliance_id,
        "user_id": user["id"],
        "username": user.get("username", "operator"),
        "type": mtype,
        "content": content,
        "refs": refs or {},
        "created_at": now_iso(),
    }
    await db.alliance_messages.insert_one(msg)
    await db.alliances.update_one({"id": alliance_id}, {"$set": {"last_activity": msg["created_at"]}})
    return {k: v for k, v in msg.items() if k != "_id"}


def _alliance_out(a: dict) -> dict:
    return {
        "id": a["id"],
        "name": a["name"],
        "code": a["code"],
        "game_slug": a["game_slug"],
        "description": a.get("description", ""),
        "creator_id": a["creator_id"],
        "member_count": len(a.get("member_ids", [])),
        "member_ids": a.get("member_ids", []),
        "created_at": a["created_at"],
        "last_activity": a.get("last_activity"),
    }


@api.post("/alliances")
async def create_alliance(body: AllianceCreate, user=Depends(get_current_user)):
    await require_toc_access(user)
    if body.game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    code = _make_alliance_code()
    # Avoid collisions in the rare case
    while await db.alliances.find_one({"code": code}):
        code = _make_alliance_code()
    doc = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "code": code,
        "game_slug": body.game_slug,
        "description": body.description or "",
        "creator_id": user["id"],
        "member_ids": [user["id"]],
        "created_at": now_iso(),
        "last_activity": now_iso(),
    }
    await db.alliances.insert_one(doc)
    return _alliance_out(doc)


@api.post("/alliances/join")
async def join_alliance(body: AllianceJoin, user=Depends(get_current_user)):
    await require_toc_access(user)
    code = body.code.strip().upper()
    a = await db.alliances.find_one({"code": code}, {"_id": 0})
    if not a:
        raise HTTPException(404, "Alliance code not found")
    if user["id"] in a.get("member_ids", []):
        return _alliance_out(a)
    await db.alliances.update_one({"id": a["id"]}, {"$addToSet": {"member_ids": user["id"]}})
    a2 = await db.alliances.find_one({"id": a["id"]}, {"_id": 0})
    await _push_message(a2["id"], user, "system", f"{user['username']} joined the alliance.")
    return _alliance_out(a2)


@api.get("/alliances/mine")
async def my_alliances(user=Depends(get_current_user)):
    docs = await db.alliances.find({"member_ids": user["id"]}, {"_id": 0}).sort("last_activity", -1).to_list(50)
    return [_alliance_out(a) for a in docs]


@api.get("/alliances/{aid}")
async def get_alliance(aid: str, user=Depends(get_current_user)):
    a = await _get_member_alliance(aid, user["id"])
    # Hydrate member usernames
    members = await db.users.find({"id": {"$in": a["member_ids"]}}, {"_id": 0, "id": 1, "username": 1}).to_list(length=None)
    out = _alliance_out(a)
    out["members"] = members
    return out


@api.post("/alliances/{aid}/leave")
async def leave_alliance(aid: str, user=Depends(get_current_user)):
    a = await _get_member_alliance(aid, user["id"])
    if a["creator_id"] == user["id"]:
        # If creator leaves, just disband if only member; else promote oldest other member
        others = [m for m in a["member_ids"] if m != user["id"]]
        if not others:
            await db.alliances.delete_one({"id": aid})
            await db.alliance_messages.delete_many({"alliance_id": aid})
            return {"ok": True, "disbanded": True}
        await db.alliances.update_one({"id": aid}, {"$set": {"creator_id": others[0]}, "$pull": {"member_ids": user["id"]}})
    else:
        await db.alliances.update_one({"id": aid}, {"$pull": {"member_ids": user["id"]}})
    await _push_message(aid, user, "system", f"{user['username']} left the alliance.")
    return {"ok": True}


@api.get("/alliances/{aid}/messages")
async def alliance_messages(aid: str, since: Optional[str] = None, limit: int = 200, user=Depends(get_current_user)):
    await _get_member_alliance(aid, user["id"])
    q: dict = {"alliance_id": aid}
    if since:
        q["created_at"] = {"$gt": since}
    msgs = await db.alliance_messages.find(q, {"_id": 0}).sort("created_at", 1).to_list(max(1, min(limit, 500)))
    return msgs


@api.post("/alliances/{aid}/messages")
async def post_alliance_text(aid: str, body: TextMsg, user=Depends(get_current_user)):
    await require_toc_access(user)
    await _get_member_alliance(aid, user["id"])
    return await _push_message(aid, user, "text", body.content.strip())


@api.post("/alliances/{aid}/share-deepdive")
async def share_deepdive_to_alliance(aid: str, body: ShareRefMsg, user=Depends(get_current_user)):
    await require_toc_access(user)
    a = await _get_member_alliance(aid, user["id"])
    dd = await db.deep_dives.find_one({"id": body.ref_id, "user_id": user["id"]}, {"_id": 0})
    if not dd:
        raise HTTPException(404, "Deep Dive not found")
    if dd["game_slug"] != a["game_slug"]:
        raise HTTPException(400, "That Deep Dive isn't for this alliance's game.")
    # Auto-generate share token if not already
    token = dd.get("share_token") or secrets.token_urlsafe(16)
    if not dd.get("share_token"):
        await db.deep_dives.update_one({"id": dd["id"]}, {"$set": {"share_token": token, "shared_at": now_iso()}})
    refs = {"deep_dive_id": dd["id"], "title": dd["title"], "share_token": token, "follow_ups": len(dd.get("follow_ups", []))}
    return await _push_message(aid, user, "share_deepdive", f"Shared Deep Dive: {dd['title']}", refs=refs)


@api.post("/alliances/{aid}/share-build")
async def share_build_to_alliance(aid: str, body: ShareRefMsg, user=Depends(get_current_user)):
    await require_toc_access(user)
    a = await _get_member_alliance(aid, user["id"])
    b = await db.builds.find_one({"id": body.ref_id, "user_id": user["id"]}, {"_id": 0})
    if not b:
        raise HTTPException(404, "Build not found")
    if b["game_slug"] != a["game_slug"]:
        raise HTTPException(400, "That Build isn't for this alliance's game.")
    token = b.get("share_token") or secrets.token_urlsafe(16)
    if not b.get("share_token"):
        await db.builds.update_one({"id": b["id"]}, {"$set": {"share_token": token, "shared_at": now_iso()}})
    refs = {"build_id": b["id"], "title": b["title"], "share_token": token}
    return await _push_message(aid, user, "share_build", f"Shared Build: {b['title']}", refs=refs)


@api.post("/alliances/{aid}/ask-cyphr")
async def alliance_ask_cyphr(aid: str, body: AskCyphrMsg, user=Depends(get_current_user)):
    await require_toc_access(user)
    a = await _get_member_alliance(aid, user["id"])
    # Reserve a chat rate-limit slot BEFORE persisting the question to avoid orphan Q messages on 429.
    await _rate_limit(user["id"], "chat")
    # Post the question
    q_msg = await _push_message(aid, user, "cyphr_q", body.question.strip())
    # Run CypherAI (specialist for alliance's game)
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"alliance-{aid}-{uuid.uuid4()}",
        system_message=system_prompt_for(a["game_slug"]),
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    try:
        answer = await chat.send_message(UserMessage(text=body.question.strip()))
    except Exception as e:
        logging.exception("alliance ask-cyphr failed")
        answer = f"(CypherAI couldn't respond just now: {e})"
    # Post answer as a system message (no human user_id)
    a_msg = {
        "id": str(uuid.uuid4()),
        "alliance_id": aid,
        "user_id": "cyphr-ai",
        "username": "CypherAI",
        "type": "cyphr_a",
        "content": answer,
        "refs": {"in_reply_to": q_msg["id"], "asked_by": user["username"]},
        "created_at": now_iso(),
    }
    await db.alliance_messages.insert_one(a_msg)
    await db.alliances.update_one({"id": aid}, {"$set": {"last_activity": a_msg["created_at"]}})
    return {"question": q_msg, "answer": {k: v for k, v in a_msg.items() if k != "_id"}}


@api.post("/alliances/{aid}/battle-reports")
async def post_battle_report(
    aid: str,
    title: str = Form(...),
    notes: str = Form(""),
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    await require_toc_access(user)
    await _get_member_alliance(aid, user["id"])
    refs_files = await _validate_and_store_files(files, user["id"])
    msg_refs = {
        "title": title.strip()[:100],
        "shots": refs_files,
        "shot_count": len(refs_files),
    }
    return await _push_message(aid, user, "battle_report", notes.strip()[:2000] or title, refs=msg_refs)


# ----- First-class Battle Reports (personal + shareable to alliance) -----
@api.post("/battle-reports")
async def create_battle_report(
    game_slug: str = Form(...),
    title: str = Form(...),
    notes: str = Form(""),
    auto_analyze: bool = Form(False),
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    if game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    shots = await _validate_and_store_files(files, user["id"])
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": game_slug,
        "title": title.strip()[:120],
        "notes": notes.strip()[:2000],
        "shots": shots,
        "cyphr_take": None,
        "created_at": now_iso(),
    }
    await db.battle_reports.insert_one(doc)
    if auto_analyze:
        try:
            await _rate_limit(user["id"], "chat")
            b64 = await _gridfs_to_b64(shots)
            game = next((g for g in GAMES if g["slug"] == game_slug), None)
            game_name = game["name"] if game else game_slug
            sys_prompt = (
                CYPHER_VOICE_CODEX.replace("[GAME NAME]", game_name)
                + f"\n=== BATTLE REPORT PROTOCOL — {game_name} ===\n"
                "The Commander has just transmitted a Battle Report. Read screenshots and notes with tactical precision. Reply in this EXACT markdown structure (≤250 words):\n"
                "## Sitrep\n(1-2 sentences summarizing the engagement)\n\n"
                "## Confirmed Gains\n- 2-3 bullets on what worked\n\n"
                "## Losses / Weak Points\n- 2-3 bullets on what failed\n\n"
                "## Next Engagement — Directives\n1. ...\n2. ...\n3. ...\n\n"
                "End with: 'Recon complete, Commander.'"
            )
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"br-{doc['id']}",
                system_message=sys_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            images = [ImageContent(image_base64=b) for b in b64]
            take = await chat.send_message(UserMessage(text=f"Notes: {doc.get('notes','(none)')}\nAnalyze this engagement.", file_contents=images))
            await db.battle_reports.update_one({"id": doc["id"]}, {"$set": {"cyphr_take": take, "analyzed_at": now_iso()}})
            doc["cyphr_take"] = take
        except HTTPException:
            # Rate-limited or other expected; user can run manually later.
            pass
        except Exception as e:
            logging.warning("auto-analyze failed: %s", e)
    return {k: v for k, v in doc.items() if k != "_id"}


@api.get("/battle-reports")
async def list_battle_reports(user=Depends(get_current_user), game_slug: Optional[str] = None):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    docs = await db.battle_reports.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api.get("/battle-reports/{rid}")
async def get_battle_report(rid: str, user=Depends(get_current_user)):
    br = await db.battle_reports.find_one({"id": rid, "user_id": user["id"]}, {"_id": 0})
    if not br:
        raise HTTPException(404, "Battle report not found")
    return br


@api.delete("/battle-reports/{rid}")
async def delete_battle_report(rid: str, user=Depends(get_current_user)):
    br = await db.battle_reports.find_one({"id": rid, "user_id": user["id"]}, {"_id": 0})
    if not br:
        raise HTTPException(404, "Not found")
    await _delete_gridfs_refs(br.get("shots", []))
    await db.battle_reports.delete_one({"id": rid})
    return {"ok": True}


@api.post("/battle-reports/{rid}/analyze")
async def analyze_battle_report(rid: str, user=Depends(get_current_user)):
    br = await db.battle_reports.find_one({"id": rid, "user_id": user["id"]}, {"_id": 0})
    if not br:
        raise HTTPException(404, "Not found")
    if br.get("cyphr_take"):
        return {"cyphr_take": br["cyphr_take"], "cached": True}
    await _rate_limit(user["id"], "chat")
    b64 = await _gridfs_to_b64(br.get("shots", []))
    game = next((g for g in GAMES if g["slug"] == br["game_slug"]), None)
    game_name = game["name"] if game else br["game_slug"]
    sys_prompt = (
        CYPHER_VOICE_CODEX.replace("[GAME NAME]", game_name)
        + f"\n=== BATTLE REPORT PROTOCOL — {game_name} ===\n"
        "The Commander has just transmitted a Battle Report. Read the screenshots and notes with tactical precision. Reply in this EXACT markdown structure (concise, ≤250 words):\n"
        "## Sitrep\n(1-2 sentences summarizing the engagement)\n\n"
        "## Confirmed Gains\n- 2-3 bullets on what worked\n\n"
        "## Losses / Weak Points\n- 2-3 bullets on what failed\n\n"
        "## Next Engagement — Directives\n1. ...\n2. ...\n3. ...\n\n"
        "End with: 'Recon complete, Commander.'"
    )
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"br-{rid}",
        system_message=sys_prompt,
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    images = [ImageContent(image_base64=b) for b in b64]
    try:
        take = await chat.send_message(UserMessage(text=f"Notes: {br.get('notes','(none)')}\nAnalyze this engagement.", file_contents=images))
    except Exception as e:
        logging.exception("battle report analyze failed: %s", e)
        raise HTTPException(500, "CypherAI couldn't analyze right now.")
    await db.battle_reports.update_one({"id": rid}, {"$set": {"cyphr_take": take, "analyzed_at": now_iso()}})
    return {"cyphr_take": take, "cached": False}


@api.post("/alliances/{aid}/share-battle-report")
async def share_battle_report_to_alliance(aid: str, body: ShareRefMsg, user=Depends(get_current_user)):
    await require_toc_access(user)
    a = await _get_member_alliance(aid, user["id"])
    br = await db.battle_reports.find_one({"id": body.ref_id, "user_id": user["id"]}, {"_id": 0})
    if not br:
        raise HTTPException(404, "Battle report not found")
    if br["game_slug"] != a["game_slug"]:
        raise HTTPException(400, "That battle report isn't for this alliance's game.")
    refs = {
        "battle_report_id": br["id"],
        "title": br["title"],
        "shot_count": len(br.get("shots", [])),
        "has_cyphr_take": bool(br.get("cyphr_take")),
    }
    return await _push_message(aid, user, "share_battle_report", f"Shared Battle Report: {br['title']}", refs=refs)


# ---------- Alliance Seats (free Pro+TOC for alliance members) ----------
def _is_alliance_admin(user: dict) -> bool:
    return user.get("is_alliance_admin") is True or user.get("email", "").lower() in ALLIANCE_ADMIN_EMAILS


class SeatCreate(BaseModel):
    email: EmailStr
    alliance_name: str = Field(min_length=2, max_length=40)
    note: Optional[str] = Field(default="", max_length=200)


@api.post("/seats")
async def create_seat(body: SeatCreate, user=Depends(get_current_user)):
    if not _is_alliance_admin(user):
        raise HTTPException(403, "Only alliance admins can grant seats. Contact your R5.")
    target_email = body.email.lower()
    # Cap: max 100 seats per admin (alliance avg 60 active, max 100)
    active_count = await db.seat_grants.count_documents({"granter_id": user["id"], "status": {"$in": ["pending", "active"]}})
    if active_count >= 100:
        raise HTTPException(400, "Seat cap reached (100 active seats max per admin).")
    if await db.seat_grants.find_one({"granter_id": user["id"], "email": target_email, "status": {"$in": ["pending", "active"]}}):
        raise HTTPException(400, "Seat already exists for this email")
    doc = {
        "id": str(uuid.uuid4()),
        "granter_id": user["id"],
        "granter_username": user["username"],
        "alliance_name": body.alliance_name.upper(),
        "email": target_email,
        "note": body.note or "",
        "status": "pending",       # pending | active | revoked
        "redeemed_user_id": None,
        "redeemed_at": None,
        "revoked_at": None,
        "created_at": now_iso(),
    }
    await db.seat_grants.insert_one(doc)
    # If user already exists with this email, auto-link
    existing = await db.users.find_one({"email": target_email}, {"_id": 0, "id": 1})
    if existing:
        await db.users.update_one({"id": existing["id"]}, {"$set": {"seat_grant_id": doc["id"]}})
        await db.seat_grants.update_one({"id": doc["id"]}, {"$set": {"status": "active", "redeemed_user_id": existing["id"], "redeemed_at": now_iso()}})
        doc["status"] = "active"
        doc["redeemed_user_id"] = existing["id"]
    return {k: v for k, v in doc.items() if k != "_id"}


@api.get("/seats/mine")
async def list_my_seats(user=Depends(get_current_user)):
    if not _is_alliance_admin(user):
        raise HTTPException(403, "Only alliance admins can view seats.")
    docs = await db.seat_grants.find({"granter_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api.delete("/seats/{sid}")
async def revoke_seat(sid: str, user=Depends(get_current_user)):
    if not _is_alliance_admin(user):
        raise HTTPException(403, "Forbidden")
    seat = await db.seat_grants.find_one({"id": sid, "granter_id": user["id"]}, {"_id": 0})
    if not seat:
        raise HTTPException(404, "Seat not found")
    await db.seat_grants.update_one({"id": sid}, {"$set": {"status": "revoked", "revoked_at": now_iso()}})
    return {"ok": True}


@api.get("/seats/admin-status")
async def admin_status(user=Depends(get_current_user)):
    return {"is_alliance_admin": _is_alliance_admin(user)}


# ---------- Referrals ----------
@api.get("/referral/me")
async def referral_me(user=Depends(get_current_user)):
    # Ensure user has a code (legacy users)
    if not user.get("referral_code"):
        code = "TA-" + secrets.token_hex(3).upper()
        await db.users.update_one({"id": user["id"]}, {"$set": {"referral_code": code}})
        user["referral_code"] = code
    total = await db.users.count_documents({"referred_by": user["id"]})
    paid = await db.users.count_documents({"referred_by": user["id"], "referral_reward_paid": True})
    window_start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    this_period = await db.referral_rewards.count_documents({"referrer_id": user["id"], "created_at": {"$gte": window_start}})
    return {
        "code": user["referral_code"],
        "share_url": f"{APP_BASE_URL}/auth?ref={user['referral_code']}",
        "total_referred": total,
        "paid_referred": paid,
        "rewards_this_period": this_period,
        "cap": REFERRAL_MONTHLY_CAP,
    }


# ---------- Events (Calendar) + Milestones ----------
class EventCreate(BaseModel):
    game_slug: str
    title: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default="", max_length=600)
    start_at: str  # ISO
    end_at: Optional[str] = None
    category: Optional[str] = Field(default="general")


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    category: Optional[str] = None


@api.post("/events")
async def create_event(body: EventCreate, user=Depends(get_current_user)):
    if body.game_slug not in GAME_SLUGS:
        raise HTTPException(400, "Invalid game_slug")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "game_slug": body.game_slug,
        "title": body.title,
        "description": body.description or "",
        "start_at": body.start_at,
        "end_at": body.end_at,
        "category": body.category or "general",
        "created_at": now_iso(),
    }
    await db.events.insert_one(doc)
    await _emit_milestone(user["id"], "event_created", body.game_slug, {"event_id": doc["id"], "title": doc["title"]})
    return {k: v for k, v in doc.items() if k != "_id"}


@api.get("/events")
async def list_events(user=Depends(get_current_user), game_slug: Optional[str] = None):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    return await db.events.find(q, {"_id": 0}).sort("start_at", 1).to_list(500)


@api.patch("/events/{eid}")
async def update_event(eid: str, body: EventUpdate, user=Depends(get_current_user)):
    upd = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not upd:
        raise HTTPException(400, "Nothing to update")
    r = await db.events.update_one({"id": eid, "user_id": user["id"]}, {"$set": upd})
    if r.matched_count == 0:
        raise HTTPException(404, "Event not found")
    return await db.events.find_one({"id": eid}, {"_id": 0})


@api.delete("/events/{eid}")
async def delete_event(eid: str, user=Depends(get_current_user)):
    r = await db.events.delete_one({"id": eid, "user_id": user["id"]})
    if r.deleted_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}


async def _emit_milestone(user_id: str, kind: str, game_slug: Optional[str], details: dict):
    try:
        await db.milestones.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "kind": kind,
            "game_slug": game_slug,
            "details": details,
            "created_at": now_iso(),
        })
    except Exception as e:
        logging.warning("milestone emit failed: %s", e)


@api.get("/milestones")
async def list_milestones(user=Depends(get_current_user), game_slug: Optional[str] = None, limit: int = 200):
    q = {"user_id": user["id"]}
    if game_slug:
        q["game_slug"] = game_slug
    return await db.milestones.find(q, {"_id": 0}).sort("created_at", -1).to_list(max(1, min(limit, 500)))


# ---------- Pro Game Slots: pick / swap which games are active ----------
class GamesSelect(BaseModel):
    games: List[str]


@api.post("/billing/pro-games")
async def set_pro_games(body: GamesSelect, user=Depends(get_current_user)):
    """Activate or swap which game slugs are in the user's Pro slots. Must be Pro or alliance seat."""
    q = await get_user_quota(user)
    if not q["subscription_active"]:
        raise HTTPException(402, "Pro subscription required to select active games.")
    invalid = [s for s in body.games if s not in GAME_SLUGS]
    if invalid:
        raise HTTPException(400, f"Unknown game slug(s): {', '.join(invalid)}")
    # Dedup, preserve order
    seen = set()
    clean = []
    for s in body.games:
        if s not in seen:
            seen.add(s)
            clean.append(s)
    if len(clean) > q["pro_game_slots"]:
        raise HTTPException(400, f"You only have {q['pro_game_slots']} Pro game slot(s). Buy more or remove a game.")
    await db.users.update_one({"id": user["id"]}, {"$set": {"pro_games": clean}})
    return {"pro_games": clean, "pro_game_slots": q["pro_game_slots"]}


# ---------- Tactical Scouts (F2P credit system) ----------
# 1 credit = $1 of value. 3 credits = 1 free Deep Dive baseline (worth $2.99).
SCOUT_REWARDS = {
    "upload_game_screenshot": {"credit": 0.25, "daily_cap": 4, "label": "Upload game update screenshot"},
    "watch_video":            {"credit": 0.10, "daily_cap": 5, "label": "Watch a recommended video"},
    "try_recommended_game":   {"credit": 0.50, "daily_cap": 2, "label": "Try a recommended game"},
    "daily_login":            {"credit": 0.05, "daily_cap": 1, "label": "Daily login bonus"},
}
SCOUT_REDEEM_COST = 3.0  # credits → +1 extra_baseline


async def _scout_today_counts(user_id: str) -> dict:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    cursor = db.scout_events.aggregate([
        {"$match": {"user_id": user_id, "created_at": {"$gte": today_start}}},
        {"$group": {"_id": "$kind", "count": {"$sum": 1}, "credits": {"$sum": "$credit"}}},
    ])
    by_kind = {}
    async for row in cursor:
        by_kind[row["_id"]] = {"count": row["count"], "credits": round(row["credits"], 2)}
    return by_kind


@api.get("/scouts/me")
async def scouts_me(user=Depends(get_current_user)):
    """Returns the user's current Scout credit balance and today's earnings per kind."""
    fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0, "scout_credits": 1})
    balance = round(float((fresh or {}).get("scout_credits", 0)), 2)
    today = await _scout_today_counts(user["id"])
    rewards = []
    for kind, meta in SCOUT_REWARDS.items():
        t = today.get(kind, {"count": 0, "credits": 0})
        rewards.append({
            "kind": kind,
            "label": meta["label"],
            "credit_per_action": meta["credit"],
            "daily_cap": meta["daily_cap"],
            "today_count": t["count"],
            "today_remaining": max(0, meta["daily_cap"] - t["count"]),
        })
    return {
        "credits": balance,
        "redeem_cost": SCOUT_REDEEM_COST,
        "redeemable_now": int(balance // SCOUT_REDEEM_COST),
        "rewards": rewards,
    }


@api.post("/scouts/earn/{kind}")
async def scouts_earn(kind: str, user=Depends(get_current_user), file: Optional[UploadFile] = File(None), video_id: Optional[str] = Form(None), game_tried: Optional[str] = Form(None)):
    """Earn Scout credits by completing a tracked action. Daily caps enforced server-side."""
    if kind not in SCOUT_REWARDS:
        raise HTTPException(400, "Unknown scout action")
    meta = SCOUT_REWARDS[kind]
    today = await _scout_today_counts(user["id"])
    used = today.get(kind, {"count": 0})["count"]
    if used >= meta["daily_cap"]:
        raise HTTPException(429, f"Daily cap reached for '{meta['label']}' ({meta['daily_cap']}/day). Come back tomorrow.")
    proof = {}
    if kind == "upload_game_screenshot":
        if not file:
            raise HTTPException(400, "Screenshot file required")
        # Validate as image (reuse Deep Dive validator semantics) — keep tiny in GridFS so we can audit
        refs = await _validate_and_store_files([file], user["id"])
        proof = {"file_ids": refs}
    elif kind == "watch_video":
        if not video_id:
            raise HTTPException(400, "video_id required")
        proof = {"video_id": video_id}
    elif kind == "try_recommended_game":
        if not game_tried:
            raise HTTPException(400, "game_tried required")
        proof = {"game_tried": game_tried}
    # daily_login: no proof needed
    # Award credits + record event (idempotent vs. cap)
    await db.scout_events.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "kind": kind,
        "credit": meta["credit"],
        "proof": proof,
        "created_at": now_iso(),
    })
    await db.users.update_one({"id": user["id"]}, {"$inc": {"scout_credits": meta["credit"]}})
    await _emit_milestone(user["id"], "scout_credit_earned", None, {"kind": kind, "credit": meta["credit"]})
    return await scouts_me(user)


class ScoutRedeem(BaseModel):
    units: int = Field(default=1, ge=1, le=10)  # how many baselines to redeem


@api.post("/scouts/redeem")
async def scouts_redeem(body: ScoutRedeem, user=Depends(get_current_user)):
    """Spend 3 credits to get +1 Deep Dive extra baseline. Stackable up to 10 at a time."""
    cost = SCOUT_REDEEM_COST * body.units
    res = await db.users.find_one_and_update(
        {"id": user["id"], "scout_credits": {"$gte": cost}},
        {"$inc": {"scout_credits": -cost, "extra_baselines": body.units}},
        return_document=True,
    )
    if not res:
        raise HTTPException(400, f"Not enough credits. Need {cost}; you have {round(float(user.get('scout_credits', 0)), 2)}.")
    await _emit_milestone(user["id"], "scout_credits_redeemed", None, {"units": body.units, "cost": cost})
    return {"credits": round(float(res.get("scout_credits", 0)), 2), "extra_baselines": int(res.get("extra_baselines", 0)), "redeemed": body.units}


# ---------- Support Tickets ----------
SUPPORT_CATEGORIES = ["billing", "technical", "account", "feedback", "refund", "feature_request", "other"]


def _is_support_admin(user: dict) -> bool:
    if not user:
        return False
    return (user.get("email") or "").lower() in SUPPORT_ADMIN_EMAILS


class TicketCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    category: str = Field(default="other")
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=10, max_length=8000)


class TicketReply(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class TicketStatusUpdate(BaseModel):
    status: str  # open | in_progress | resolved


async def _notify_admin_of_ticket(ticket: dict):
    if not SUPPORT_EMAIL:
        return
    admin_html = f"""
    <div style="font-family:system-ui;background:#0c0c0c;color:#e4e4e7;padding:24px;border-radius:8px;max-width:600px">
      <div style="color:#E63946;font-family:monospace;font-size:11px;letter-spacing:2px;margin-bottom:8px">// NEW SUPPORT TICKET</div>
      <h2 style="margin:0 0 16px 0;font-size:20px">{ticket['subject']}</h2>
      <table style="width:100%;font-size:13px;border-collapse:collapse;margin-bottom:16px">
        <tr><td style="padding:6px 0;color:#71717a;width:90px">Ticket ID:</td><td style="font-family:monospace;color:#FFBA08">{ticket['id'][:8]}</td></tr>
        <tr><td style="padding:6px 0;color:#71717a">From:</td><td>{ticket['name']} &lt;{ticket['email']}&gt;</td></tr>
        <tr><td style="padding:6px 0;color:#71717a">Category:</td><td style="color:#FFBA08;text-transform:uppercase">{ticket['category']}</td></tr>
        <tr><td style="padding:6px 0;color:#71717a">User account:</td><td>{'Yes' if ticket.get('user_id') else 'Guest (no account)'}</td></tr>
      </table>
      <div style="background:#18181b;border:1px solid #27272a;border-radius:6px;padding:16px;white-space:pre-wrap;font-size:14px;line-height:1.5">{ticket['message']}</div>
      <a href="{APP_BASE_URL}/admin/support" style="display:inline-block;margin-top:20px;background:#E63946;color:white;padding:10px 18px;border-radius:4px;text-decoration:none;font-weight:bold">Open Admin Dashboard</a>
    </div>
    """
    await send_email(SUPPORT_EMAIL, f"[Tactical Ally] New ticket: {ticket['subject']}", admin_html, reply_to=ticket["email"])


async def _autoreply_to_user(ticket: dict):
    user_html = f"""
    <div style="font-family:system-ui;background:#0c0c0c;color:#e4e4e7;padding:24px;border-radius:8px;max-width:600px">
      <div style="color:#E63946;font-family:monospace;font-size:11px;letter-spacing:2px;margin-bottom:8px">// TACTICAL ALLY · SUPPORT</div>
      <h2 style="margin:0 0 12px 0;font-size:22px">We&apos;ve received your message, {ticket['name'].split()[0]}.</h2>
      <p style="font-size:14px;color:#a1a1aa;line-height:1.6">Ticket <strong style="color:#FFBA08;font-family:monospace">#{ticket['id'][:8]}</strong> is in the queue. Our team typically responds within <strong style="color:#10B981">48 hours</strong>. We&apos;ll reply to this email when an update is ready.</p>
      <div style="background:#18181b;border:1px solid #27272a;border-radius:6px;padding:16px;margin-top:16px;font-size:13px">
        <div style="color:#71717a;font-family:monospace;font-size:10px;letter-spacing:1.5px;margin-bottom:8px">// YOUR MESSAGE</div>
        <div style="white-space:pre-wrap;color:#d4d4d8">{ticket['message'][:500]}{'…' if len(ticket['message']) > 500 else ''}</div>
      </div>
      <p style="font-size:12px;color:#52525b;margin-top:24px">— Tactical Ally Support · info.warroomsupport@gmail.com</p>
    </div>
    """
    await send_email(ticket["email"], f"[Tactical Ally] Ticket #{ticket['id'][:8]} received — {ticket['subject']}", user_html)


@api.post("/support/tickets")
async def create_support_ticket(body: TicketCreate, request: Request):
    """Create a support ticket. Works for both authenticated users and guests."""
    if body.category not in SUPPORT_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Must be one of: {', '.join(SUPPORT_CATEGORIES)}")
    # Lightweight rate-limit: 5 tickets per email per hour
    one_hr_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    recent = await db.support_tickets.count_documents({"email": body.email.lower(), "created_at": {"$gte": one_hr_ago}})
    if recent >= 5:
        raise HTTPException(429, "Too many tickets. Please wait an hour before submitting more.")
    # Try to attach user_id if logged in (optional)
    user_id = None
    try:
        token = request.headers.get("authorization", "").replace("Bearer ", "").strip()
        if token:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
    except Exception:
        pass
    ticket = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": body.name.strip(),
        "email": body.email.lower(),
        "category": body.category,
        "subject": body.subject.strip(),
        "message": body.message.strip(),
        "status": "open",
        "responses": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.support_tickets.insert_one(ticket)
    # Fire-and-forget emails (do not block response on SMTP)
    asyncio.create_task(_notify_admin_of_ticket(ticket))
    asyncio.create_task(_autoreply_to_user(ticket))
    return {"id": ticket["id"], "status": "open", "message": "Ticket received. Check your email for confirmation."}


@api.get("/support/my-tickets")
async def my_support_tickets(user=Depends(get_current_user)):
    rows = await db.support_tickets.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return rows


@api.get("/support/tickets/{tid}")
async def get_support_ticket(tid: str, user=Depends(get_current_user)):
    t = await db.support_tickets.find_one({"id": tid}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Ticket not found")
    if not (_is_support_admin(user) or t.get("user_id") == user["id"]):
        raise HTTPException(403, "Not your ticket")
    return t


@api.get("/support/admin/tickets")
async def admin_list_tickets(user=Depends(get_current_user), status_filter: Optional[str] = None, limit: int = 100):
    if not _is_support_admin(user):
        raise HTTPException(403, "Support admin only")
    q = {}
    if status_filter and status_filter in ("open", "in_progress", "resolved"):
        q["status"] = status_filter
    rows = await db.support_tickets.find(q, {"_id": 0}).sort("created_at", -1).to_list(max(1, min(limit, 500)))
    counts_cursor = db.support_tickets.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}])
    counts = {"open": 0, "in_progress": 0, "resolved": 0}
    async for row in counts_cursor:
        counts[row["_id"]] = row["count"]
    return {"tickets": rows, "counts": counts}


@api.post("/support/admin/tickets/{tid}/reply")
async def admin_reply_ticket(tid: str, body: TicketReply, user=Depends(get_current_user)):
    if not _is_support_admin(user):
        raise HTTPException(403, "Support admin only")
    t = await db.support_tickets.find_one({"id": tid}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Ticket not found")
    reply = {
        "id": str(uuid.uuid4()),
        "from_admin": True,
        "admin_username": user.get("username") or user.get("email"),
        "message": body.message.strip(),
        "created_at": now_iso(),
    }
    await db.support_tickets.update_one(
        {"id": tid},
        {"$push": {"responses": reply}, "$set": {"status": "in_progress", "updated_at": now_iso()}},
    )
    # Email the user
    html = f"""
    <div style="font-family:system-ui;background:#0c0c0c;color:#e4e4e7;padding:24px;border-radius:8px;max-width:600px">
      <div style="color:#E63946;font-family:monospace;font-size:11px;letter-spacing:2px;margin-bottom:8px">// TACTICAL ALLY · SUPPORT REPLY</div>
      <h2 style="margin:0 0 12px 0;font-size:20px">Re: {t['subject']}</h2>
      <p style="font-size:12px;color:#71717a;margin-bottom:16px">Ticket <span style="font-family:monospace;color:#FFBA08">#{t['id'][:8]}</span></p>
      <div style="background:#18181b;border:1px solid #27272a;border-radius:6px;padding:16px;white-space:pre-wrap;font-size:14px;line-height:1.6">{reply['message']}</div>
      <p style="font-size:12px;color:#52525b;margin-top:24px">Reply directly to this email to continue the conversation.<br/>— Tactical Ally Support</p>
    </div>
    """
    asyncio.create_task(send_email(t["email"], f"[Tactical Ally] Re: {t['subject']}", html, reply_to=SUPPORT_EMAIL or None))
    return {"id": reply["id"], "ticket_status": "in_progress"}


@api.patch("/support/admin/tickets/{tid}/status")
async def admin_update_status(tid: str, body: TicketStatusUpdate, user=Depends(get_current_user)):
    if not _is_support_admin(user):
        raise HTTPException(403, "Support admin only")
    if body.status not in ("open", "in_progress", "resolved"):
        raise HTTPException(400, "Invalid status")
    res = await db.support_tickets.update_one(
        {"id": tid}, {"$set": {"status": body.status, "updated_at": now_iso()}}
    )
    if res.matched_count == 0:
        raise HTTPException(404, "Ticket not found")
    return {"id": tid, "status": body.status}


@api.get("/support/admin/check")
async def admin_check(user=Depends(get_current_user)):
    """Lightweight check for the frontend to gate the /admin/support route."""
    return {"is_admin": _is_support_admin(user)}


# ---------- Intel Drop (Alliance-sourced game intel) ----------
# Public submission portal for [OTS] Outlanders + allies to contribute verified
# game intel. Submissions land in a pending queue; only admins (General + Lt. Atlas)
# review, approve, and file them into CypherAI's dossiers.

INTEL_GAMES = {"puzzles-conquest", "puzzles-survival", "puzzles-chaos"}
INTEL_CATEGORIES = {"event", "hero", "mechanic", "tip", "correction", "other"}
INTEL_STATUSES = {"pending", "approved", "rejected", "filed"}
INTEL_MAX_IMAGES = 5
INTEL_TEXT_MIN = 5
INTEL_TEXT_MAX = 20000


@api.post("/intel/submit")
async def intel_submit(
    game_slug: str = Form(...),
    category: str = Form(...),
    intel_text: str = Form(...),
    contributor_name: Optional[str] = Form(None),
    contributor_handle: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    images: list[UploadFile] = File(default=[]),
):
    """
    Public intel submission — NO AUTH required.
    Alliance members and allies submit game intel here for admin review.
    """
    if game_slug not in INTEL_GAMES:
        raise HTTPException(400, "Invalid game selection")
    if category not in INTEL_CATEGORIES:
        raise HTTPException(400, "Invalid category")
    txt = (intel_text or "").strip()
    if len(txt) < INTEL_TEXT_MIN:
        raise HTTPException(400, f"Intel too short — minimum {INTEL_TEXT_MIN} characters")
    if len(txt) > INTEL_TEXT_MAX:
        raise HTTPException(400, f"Intel too long — maximum {INTEL_TEXT_MAX} characters")

    # Validate + store optional screenshots in dedicated intel GridFS bucket
    image_refs = []
    if images:
        real = [f for f in images if f and getattr(f, "filename", None)]
        if len(real) > INTEL_MAX_IMAGES:
            raise HTTPException(400, f"Max {INTEL_MAX_IMAGES} screenshots per submission")
        for f in real:
            mime = (f.content_type or "").lower()
            if mime not in ALLOWED_MIMES:
                raise HTTPException(400, f"Unsupported file '{mime}' for {f.filename}. Allowed: PNG, JPEG, WebP, GIF.")
            data = await f.read()
            if len(data) > MAX_BYTES:
                raise HTTPException(400, f"{f.filename} exceeds {MAX_BYTES // (1024*1024)}MB limit")
            if len(data) < 100:
                raise HTTPException(400, f"{f.filename} is empty or corrupted")
            file_id = await intel_gridfs.upload_from_stream(
                f.filename or "intel-shot",
                data,
                metadata={"mime": mime, "size": len(data), "kind": "intel"},
            )
            image_refs.append({"file_id": str(file_id), "mime": mime, "name": f.filename or "intel-shot", "size": len(data)})

    submission = {
        "id": str(uuid.uuid4()),
        "reference": f"INTEL-{uuid.uuid4().hex[:8].upper()}",
        "game_slug": game_slug,
        "category": category,
        "intel_text": txt,
        "contributor_name": (contributor_name or "").strip() or None,
        "contributor_handle": (contributor_handle or "").strip() or None,
        "source_url": (source_url or "").strip() or None,
        "image_refs": image_refs,
        "status": "pending",
        "submitted_at": now_iso(),
        "reviewed_at": None,
        "reviewer_email": None,
        "review_notes": None,
    }
    await db.intel_submissions.insert_one(submission)
    return {
        "ok": True,
        "reference": submission["reference"],
        "message": "Intel received and queued for review. Lt. Atlas will file verified intel to CypherAI within 24 hours.",
    }


def _serialize_intel(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "reference": doc.get("reference"),
        "game_slug": doc["game_slug"],
        "category": doc["category"],
        "intel_text": doc["intel_text"],
        "contributor_name": doc.get("contributor_name"),
        "contributor_handle": doc.get("contributor_handle"),
        "source_url": doc.get("source_url"),
        "image_refs": doc.get("image_refs", []),
        "status": doc.get("status", "pending"),
        "submitted_at": doc.get("submitted_at"),
        "reviewed_at": doc.get("reviewed_at"),
        "reviewer_email": doc.get("reviewer_email"),
        "review_notes": doc.get("review_notes"),
    }


@api.get("/intel/submissions")
async def intel_list(
    status_filter: Optional[str] = None,
    game_slug: Optional[str] = None,
    user=Depends(get_current_user),
):
    """Admin-only. List intel submissions filtered by status/game."""
    if not _is_support_admin(user):
        raise HTTPException(403, "Admin only")
    q = {}
    if status_filter and status_filter != "all":
        if status_filter not in INTEL_STATUSES:
            raise HTTPException(400, "Invalid status filter")
        q["status"] = status_filter
    if game_slug and game_slug != "all":
        if game_slug not in INTEL_GAMES:
            raise HTTPException(400, "Invalid game filter")
        q["game_slug"] = game_slug
    cur = db.intel_submissions.find(q).sort("submitted_at", -1).limit(200)
    docs = [_serialize_intel(d) async for d in cur]
    counts = {
        "pending": await db.intel_submissions.count_documents({"status": "pending"}),
        "approved": await db.intel_submissions.count_documents({"status": "approved"}),
        "rejected": await db.intel_submissions.count_documents({"status": "rejected"}),
        "filed": await db.intel_submissions.count_documents({"status": "filed"}),
        "total": await db.intel_submissions.count_documents({}),
    }
    return {"submissions": docs, "counts": counts}


@api.get("/intel/submissions/{sid}/image/{file_id}")
async def intel_image(sid: str, file_id: str, user=Depends(get_current_user)):
    """Admin-only. Stream a submitted intel image back to the review dashboard."""
    if not _is_support_admin(user):
        raise HTTPException(403, "Admin only")
    doc = await db.intel_submissions.find_one({"id": sid})
    if not doc:
        raise HTTPException(404, "Submission not found")
    if not any(r.get("file_id") == file_id for r in doc.get("image_refs", [])):
        raise HTTPException(404, "Image not linked to this submission")
    try:
        stream = await intel_gridfs.open_download_stream(ObjectId(file_id))
        data = await stream.read()
        mime = next((r["mime"] for r in doc["image_refs"] if r["file_id"] == file_id), "image/png")
        return Response(content=data, media_type=mime)
    except Exception:
        raise HTTPException(404, "Image not found in storage")


class IntelReview(BaseModel):
    status: str  # approved | rejected | filed | pending
    review_notes: Optional[str] = None


@api.patch("/intel/submissions/{sid}")
async def intel_update(sid: str, body: IntelReview, user=Depends(get_current_user)):
    """Admin-only. Approve/reject/mark-filed an intel submission."""
    if not _is_support_admin(user):
        raise HTTPException(403, "Admin only")
    if body.status not in INTEL_STATUSES:
        raise HTTPException(400, "Invalid status")
    res = await db.intel_submissions.find_one_and_update(
        {"id": sid},
        {"$set": {
            "status": body.status,
            "reviewed_at": now_iso(),
            "reviewer_email": user.get("email"),
            "review_notes": (body.review_notes or "").strip() or None,
        }},
        return_document=True,
    )
    if not res:
        raise HTTPException(404, "Submission not found")
    return _serialize_intel(res)


# ---------- User Onboarding (first-time vs returning briefing data) ----------
@api.get("/user/onboarding")
async def user_onboarding_status(user=Depends(get_current_user)):
    """Returns whether the user is first-time + their last activity for the personalized briefing."""
    uid = user["id"]
    # Count activity across the main collections
    counts = await asyncio.gather(
        db.deep_dives.count_documents({"user_id": uid}),
        db.chat_sessions.count_documents({"user_id": uid}),
        db.builds.count_documents({"user_id": uid}),
        db.battle_reports.count_documents({"user_id": uid}),
    )
    deep_dives, chats, builds, reports = counts
    has_activity = (deep_dives + chats + builds + reports) > 0

    # Find the most recent activity across the 4 sources
    candidates = []
    last_dd = await db.deep_dives.find_one({"user_id": uid}, {"_id": 0}, sort=[("created_at", -1)])
    if last_dd:
        candidates.append({
            "type": "deep_dive",
            "game_slug": last_dd.get("game_slug"),
            "label": f"Deep Dive · {last_dd.get('game_slug', 'game').replace('-', ' ').title()}",
            "link": f"/game/{last_dd.get('game_slug')}?tab=deep-dive",
            "at_iso": last_dd.get("created_at"),
        })
    last_chat = await db.chat_sessions.find_one({"user_id": uid}, {"_id": 0}, sort=[("updated_at", -1)])
    if last_chat:
        candidates.append({
            "type": "chat",
            "game_slug": last_chat.get("game_slug"),
            "label": f"CypherAI Chat · {(last_chat.get('game_slug') or 'general').replace('-', ' ').title()}",
            "link": f"/game/{last_chat.get('game_slug')}?tab=chat" if last_chat.get("game_slug") else "/dashboard",
            "at_iso": last_chat.get("updated_at") or last_chat.get("created_at"),
        })
    last_build = await db.builds.find_one({"user_id": uid}, {"_id": 0}, sort=[("created_at", -1)])
    if last_build:
        candidates.append({
            "type": "build",
            "game_slug": last_build.get("game_slug"),
            "label": f"Build · {last_build.get('hero_or_unit', last_build.get('game_slug', ''))}",
            "link": f"/game/{last_build.get('game_slug')}?tab=builds",
            "at_iso": last_build.get("created_at"),
        })
    last_report = await db.battle_reports.find_one({"user_id": uid}, {"_id": 0}, sort=[("created_at", -1)])
    if last_report:
        candidates.append({
            "type": "battle_report",
            "game_slug": last_report.get("game_slug"),
            "label": f"Battle Report · {last_report.get('title', 'engagement')}",
            "link": f"/battle-reports/{last_report.get('id')}",
            "at_iso": last_report.get("created_at"),
        })
    # pick the freshest
    candidates = [c for c in candidates if c.get("at_iso")]
    candidates.sort(key=lambda c: c["at_iso"], reverse=True)
    last_activity = candidates[0] if candidates else None

    return {
        "first_time": not has_activity,
        "counts": {"deep_dives": deep_dives, "chats": chats, "builds": builds, "battle_reports": reports},
        "last_activity": last_activity,
        "username": user.get("username") or (user.get("email") or "").split("@")[0],
    }


# ---------- Init ----------
# (User onboarding endpoint added above for Command Center briefing)
@app.on_event("startup")
async def seed_data():
    # Idempotent per-guide upsert so newly-added guides land on existing DBs
    for g in GUIDES_SEED:
        await db.guides.update_one(
            {"game_slug": g["game_slug"], "title": g["title"]},
            {"$setOnInsert": {**g, "id": str(uuid.uuid4()), "created_at": now_iso()}},
            upsert=True,
        )
    logging.info("guides seeding ensured (%d entries)", len(GUIDES_SEED))
    # TTL index for rate-limit usage docs (auto-expire after 1 day)
    try:
        await db.rate_limits.create_index("ts", expireAfterSeconds=86400)
    except Exception:
        pass
    # TTL index for password reset tokens (auto-expire after 24h)
    try:
        await db.password_resets.create_index("created_at", expireAfterSeconds=86400)
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
