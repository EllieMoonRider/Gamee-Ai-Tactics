"""37Games AI Strategy Assistant — backend."""
import os
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
    email: EmailStr
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


def system_prompt_for(game_slug: str) -> str:
    game = next((g for g in GAMES if g["slug"] == game_slug), None)
    name = game["name"] if game else "37Games title"
    genre = game["genre"] if game else "mobile strategy game"
    return (
        f"You are 'CyphrAI', the tactical AI engine inside the Tactical Ally app. You are a DEDICATED SPECIALIST for the 37Games title '{name}' ({genre}) and NOTHING ELSE. "
        "STRICT RULES (do not break these):\n"
        f"1. You ONLY answer about '{name}'. If the player asks about a different game (even another 37Games title), politely refuse and say 'I'm the {name} specialist — open that game's workspace to talk to its dedicated CyphrAI.'\n"
        f"2. NEVER cross-reference mechanics, heroes, items, or strategies from other games. Treat '{name}' as a closed universe.\n"
        f"3. Provide TRUE, SPECIFIC strategy — exact hero names, building names, event names, numeric targets, formation roles. NEVER give generic mobile-strategy advice.\n"
        f"4. If you don't know a specific patch/event detail, say 'I don't have verified info on that — can you screenshot it for me?' rather than fabricating.\n"
        "5. Tone: confident, friendly, slightly tactical/military. Keep replies under 300 words unless asked for depth. Use **bold** for hero/building/numeric callouts. End with 1-2 follow-up question suggestions.\n"
        "6. Reply in the user's language."
    )


def deepdive_system_prompt(game_slug: str, mode: str) -> str:
    game = next((g for g in GAMES if g["slug"] == game_slug), None)
    name = game["name"] if game else "37Games title"
    base = (
        f"You are 'CyphrAI', the DEDICATED SPECIALIST for the 37Games title '{name}'. You are NOT a generic mobile-strategy AI; you only speak {name}. "
        "Read every screenshot carefully — heroes, levels, resources, building HQ, alliance, VIP, gear, formation, power, anything visible. "
        "STRICT: Do not reference any other game. Do not give generic advice. Be specific to this title's mechanics, heroes, events, and meta. If something is unclear in the screenshot, say so — never invent. "
    )
    if mode == "baseline":
        return base + (
            "Produce a DEEP DIVE BASELINE analysis. Use this exact markdown structure:\n"
            "## Account Snapshot\n(1-2 sentences summarizing what you see — power level, progression stage)\n\n"
            "## Strengths\n- bullet 1\n- bullet 2\n- bullet 3\n\n"
            "## Weaknesses\n- bullet 1\n- bullet 2\n- bullet 3\n\n"
            "## Top 5 Priority Actions\n1. **Action** — why\n2. ...\n\n"
            "## Resource Allocation Recommendation\n(percentage split or focus areas)\n\n"
            "## Next Milestones (30 / 60 / 90 days)\n- 30: ...\n- 60: ...\n- 90: ...\n\n"
            "Be specific. If you can't see something, say so — never invent."
        )
    return base + (
        "This is a FOLLOW-UP DEEP DIVE. The previous baseline analysis is provided as context. "
        "Compare what's changed, congratulate progress, flag regressions, and update priorities. Structure:\n"
        "## Progress Since Baseline\n(2-3 sentences)\n\n"
        "## What Improved\n- ...\n\n"
        "## What Stalled or Regressed\n- ...\n\n"
        "## Updated Top 5 Actions\n1. ...\n\n"
        "## Building-Block Next Phase\n(2-3 sentences pointing to the next stage of growth)\n"
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
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
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


# ----- Deep Dive (CyphrAI vision analysis) -----
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
        raise HTTPException(500, "CyphrAI analysis failed. Please try again.")
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
        raise HTTPException(500, "CyphrAI analysis failed. Please try again.")
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


# ---------- CyphrAI Guided Deep Dive ----------
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
        f"You are CyphrAI, the strict specialist for the 37Games title '{name}'. "
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
        system_message=system_prompt_for(s["game_slug"]) + " You are helping the player during a Guided Deep Dive — keep answers ≤120 words and very direct.",
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    try:
        answer = await chat.send_message(UserMessage(text=body.question.strip()))
    except Exception as e:
        logging.exception("guided ask failed: %s", e)
        raise HTTPException(500, "CyphrAI couldn't answer right now.")
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
        raise HTTPException(500, "CyphrAI analysis failed. Please try again.")
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


# ---------- CyphrAI Guided Deep Dive END ----------


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
        "description": "Full Pro access for 2 games of your choice. Includes 2 CyphrAI Deep Dive baselines/month + unlimited follow-up Building Blocks.",
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
    # Run CyphrAI (specialist for alliance's game)
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"alliance-{aid}-{uuid.uuid4()}",
        system_message=system_prompt_for(a["game_slug"]),
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    try:
        answer = await chat.send_message(UserMessage(text=body.question.strip()))
    except Exception as e:
        logging.exception("alliance ask-cyphr failed")
        answer = f"(CyphrAI couldn't respond just now: {e})"
    # Post answer as a system message (no human user_id)
    a_msg = {
        "id": str(uuid.uuid4()),
        "alliance_id": aid,
        "user_id": "cyphr-ai",
        "username": "CyphrAI",
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
                f"You are CyphrAI, the STRICT specialist for '{game_name}'. The user just posted a Battle Report. "
                "Read screenshots and notes. Respond in this exact structure (≤250 words):\n"
                "## What I see\n(1-2 sentence summary)\n\n## What worked\n- ...\n\n## What didn't\n- ...\n\n## Next time, do this\n1. ...\n\n"
                "Be specific to this game. No generic advice. No other game references."
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
        f"You are CyphrAI, the STRICT specialist for the 37Games title '{game_name}'. The user just posted a Battle Report. "
        "Read the screenshots and notes. Reply in this exact structure (concise, ≤250 words):\n"
        "## What I see\n(1-2 sentence summary of the engagement)\n\n"
        "## What worked\n- 2-3 bullets\n\n"
        "## What didn't\n- 2-3 bullets\n\n"
        "## Next time, do this\n1. ...\n2. ...\n3. ...\n\n"
        "Be specific to this game. No generic advice. No other game references."
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
        raise HTTPException(500, "CyphrAI couldn't analyze right now.")
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
            "label": f"CyphrAI Chat · {(last_chat.get('game_slug') or 'general').replace('-', ' ').title()}",
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
