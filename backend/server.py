"""37Games AI Strategy Assistant — backend."""
import os
import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Literal

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from starlette.middleware.cors import CORSMiddleware

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------- DB ----------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# ---------- App ----------
app = FastAPI(title="37Games AI Strategy")
api = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]

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


def system_prompt_for(game_slug: str) -> str:
    game = next((g for g in GAMES if g["slug"] == game_slug), None)
    name = game["name"] if game else "37Games title"
    genre = game["genre"] if game else "mobile strategy game"
    return (
        f"You are 'Tactician', a veteran strategy coach for the 37Games title '{name}' ({genre}). "
        "You give concrete, prioritized, actionable advice for free-to-play and light-spender gamers. "
        "When giving advice: 1) list priorities, 2) cite specific heroes / buildings / events when relevant, "
        "3) keep responses concise (under 300 words by default) but rich in tactical detail, "
        "4) use bold for hero names and key numbers, 5) suggest follow-up questions at the end. "
        "Never fabricate update patches you don't know about — be honest if uncertain. "
        "Tone: confident, friendly, slightly tactical/military. Reply in the user's language."
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


# ---------- Init ----------
@app.on_event("startup")
async def seed_data():
    count = await db.guides.count_documents({})
    if count == 0:
        for g in GUIDES_SEED:
            doc = {**g, "id": str(uuid.uuid4()), "created_at": now_iso()}
            await db.guides.insert_one(doc)
        logging.info("seeded %d guides", len(GUIDES_SEED))


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
