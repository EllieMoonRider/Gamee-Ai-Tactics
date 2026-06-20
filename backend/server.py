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
async def send_email(to: str, subject: str, html: str) -> tuple[bool, str]:
    """Returns (sent_via_resend, info). If RESEND_API_KEY missing -> logs link and returns False."""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY missing — email NOT sent. Subject=%s To=%s", subject, to)
        return False, "dev-mode"
    try:
        params = {"from": SENDER_EMAIL, "to": [to], "subject": subject, "html": html}
        result = await asyncio.to_thread(resend.Emails.send, params)
        return True, result.get("id", "sent")
    except Exception as e:
        logging.exception("Resend send failed")
        return False, str(e)


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
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": data.email.lower(),
        "username": data.username,
        "password_hash": hash_password(data.password),
        "created_at": now_iso(),
    }
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
        source = await consume_baseline(user["id"])
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


# ---------- Billing (Stripe subscription + topup) ----------
PACKAGES = {
    "subscription_monthly": {
        "name": "Tactical Ally Pro — Monthly",
        "amount": 4.99,
        "currency": "usd",
        "kind": "subscription",
        "baselines": 2,
        "period_days": 30,
        "description": "2 CyphrAI Deep Dive baselines per month + unlimited follow-up Building Blocks within them.",
    },
    "topup_analysis": {
        "name": "Extra Deep Dive analysis",
        "amount": 2.99,
        "currency": "usd",
        "kind": "one_time",
        "baselines": 1,
        "description": "Adds 1 extra Deep Dive baseline that doesn't expire.",
    },
    "toc_addon_monthly": {
        "name": "Tactical Operations Center — Monthly add-on",
        "amount": 0.99,
        "currency": "usd",
        "kind": "toc_addon",
        "period_days": 30,
        "description": "Create or join alliance chat rooms. Share Deep Dives & Builds with your alliance and ask CyphrAI questions in-room (unlimited). Requires active Pro subscription.",
    },
}


async def get_user_quota(user: dict) -> dict:
    """Computes the user's current quota state (auto-renews monthly window)."""
    now = datetime.now(timezone.utc)
    sub_end_iso = user.get("subscription_period_end")
    sub_active = False
    sub_end = None
    if sub_end_iso:
        sub_end = datetime.fromisoformat(sub_end_iso)
        sub_active = sub_end > now
    plan = "pro" if sub_active else "free"
    period_baselines_remaining = 0
    if sub_active:
        used = int(user.get("analyses_used_this_period", 0))
        period_baselines_remaining = max(0, 2 - used)
    extra_baselines = int(user.get("extra_baselines", 0))
    toc_end_iso = user.get("toc_period_end")
    toc_active = False
    if toc_end_iso:
        toc_end = datetime.fromisoformat(toc_end_iso)
        toc_active = toc_end > now
    return {
        "plan": plan,
        "subscription_active": sub_active,
        "subscription_period_end": sub_end.isoformat() if sub_end else None,
        "period_baselines_remaining": period_baselines_remaining,
        "extra_baselines": extra_baselines,
        "total_baselines_available": period_baselines_remaining + extra_baselines,
        "toc_active": toc_active,
        "toc_period_end": user.get("toc_period_end"),
    }


async def require_toc_access(user: dict):
    """Raises 402 if user can't use the Tactical Operations Center."""
    q = await get_user_quota(user)
    if not q["subscription_active"]:
        raise HTTPException(402, "Tactical Operations Center requires Tactical Ally Pro ($4.99/mo) + TOC add-on ($0.99/mo).")
    if not q["toc_active"]:
        raise HTTPException(402, "Add the Tactical Operations Center add-on ($0.99/mo) to create or join alliance chat rooms.")


async def consume_baseline(user_id: str):
    """Atomically debit one baseline from the user's quota. Raises 402 if none available."""
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
            return "subscription"
        # Was past period; rollback & try extras
        await db.users.update_one({"id": user_id}, {"$inc": {"analyses_used_this_period": -1}})
    # Try extras
    res2 = await db.users.find_one_and_update(
        {"id": user_id, "extra_baselines": {"$gt": 0}},
        {"$inc": {"extra_baselines": -1}},
        return_document=True,
    )
    if res2:
        return "topup"
    raise HTTPException(402, "No Deep Dive analyses available. Subscribe to Tactical Ally Pro or buy a top-up.")


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
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$set": {
                "subscription_status": "active",
                "subscription_period_end": period_end.isoformat(),
                "analyses_used_this_period": 0,
            }},
        )
    elif pkg["kind"] == "one_time":
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$inc": {"extra_baselines": int(pkg["baselines"])}},
        )
    elif pkg["kind"] == "toc_addon":
        toc_end = datetime.now(timezone.utc) + timedelta(days=pkg["period_days"])
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$set": {"toc_period_end": toc_end.isoformat()}},
        )
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


# ---------- Init ----------
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
