"""Generate War Room Scene v4 — General Ellie's knight-placement fix.
CRITICAL CHANGES from v3:
  - Knights now placed BEHIND the castle wall (only torso + head visible above
    the battlements/ramparts — the wall OCCLUDES their lower body)
  - Knights ~33% larger than v3
  - Left knight horizontally centered at 25% of frame width
  - Right knight horizontally centered at 75% of frame width
  - Wall reads as a clear horizontal barrier in front of them
Everything else identical to v3-1 (the approved scene).
Run: python /app/scripts/gen_war_room_scene_v4.py
"""
import asyncio
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")

OUT_DIR = Path("/app/frontend/src/assets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = """Cinematic dark fantasy + sci-fi War Room concept art, horizontal landscape composition optimized for a wide screen, suitable for both desktop and 9:16 mobile crop.

=== SCENE LAYERS (front to back) ===

LAYER 1 — UPPER FRAME: a massive vibrant neon GREEN holographic radar/scanner dome dominating the upper-center of the frame. Concentric glowing rings, crosshair lines, rotating sweep beam, bright emerald green (#00FF80 / #39FF14) with cyan undertones. Scanlines and holographic flicker overlay it.

LAYER 2 — MID-LEFT FRAME: a sleek ethereal dragon mid-flight at roughly the midground horizon line, smaller scale (not dominating). Wings outstretched, dark scales silhouetted against the radar's green glow.

LAYER 3 — CENTER VERTICAL FOCAL POINT: a tall glowing crystal-sword landmark rising upward, lit by green radar light, centered horizontally in the frame.

LAYER 4 — FOREGROUND CASTLE WALL: a row of dark stone castle battlements / ramparts / crenellated wall stretching horizontally across the lower-mid portion of the frame. The wall has clear visible crenellations (the classic squared-off battlement teeth). The wall is a SOLID OPAQUE STONE BARRIER — it is in the FOREGROUND, in front of the knights. The wall must visually OCCLUDE the lower body of the knights standing behind it.

LAYER 5 — KNIGHTS BEHIND THE WALL (CRITICAL PLACEMENT): TWO large armored medieval knights standing BEHIND the castle wall, peering forward. ONLY THE UPPER BODY of each knight is visible — head, helm, shoulders, chest, and arms above the wall line. The lower half of each knight (waist, legs) is COMPLETELY HIDDEN BEHIND THE STONE WALL — occluded by the battlements. The wall cuts horizontally across them at roughly chest height. Think of soldiers in a trench peering over the parapet, or guards manning castle walls — that exact composition.

KNIGHT SIZE: Each knight is large and imposing — they occupy roughly 40-50% of the frame's vertical height (head + visible upper body). About 1.3x larger than typical background figures.

KNIGHT POSITIONS (horizontal):
- LEFT knight: horizontally centered at approximately 25% of frame width (i.e., halfway between the left edge and the central sword). Facing slightly toward the center.
- RIGHT knight: horizontally centered at approximately 75% of frame width (i.e., halfway between the central sword and the right edge). Facing slightly toward the center.
- The sword is dead center between them.

KNIGHT APPEARANCE: emerald-armored sentinels — solid plate armor catching green radar light, glowing with a cool spirit-green wash on metal surfaces, faintly translucent at the edges suggesting an ethereal/ancestral quality. Helms visored, posture commanding, like immortal guardians manning the wall.

LAYER 6 — HOLOGRAPHIC FLOOR (foreground bottom): leave the bottom 30-35% of the frame as a dark misty floor surface in front of the wall. This area is intentionally CLEAN and EMPTY — no figures, no obstacles — because a holographic grid will be projected onto it as a separate UI layer later.

LAYER 7 — DEEP BACKGROUND: deep dark night atmosphere behind everything, volumetric green mist, faint stars, distant mountains barely visible. Darkest tonal value in the image.

=== ABSOLUTE COMPOSITION RULES ===

- DO NOT place the knights in front of the wall.
- DO NOT show the knights' full body or legs.
- DO show the wall CUTTING horizontally across the knights at chest height.
- DO show only their upper bodies (head + chest + arms) visible above the battlements.
- The wall is OPAQUE STONE in the FOREGROUND. The knights are BEHIND it.

NO TANKS. NO foreground figures on the floor. NO text, NO UI panels, NO data readouts, NO labels, NO logos, NO HUD overlays.

Lighting: dominant neon GREEN ambient glow from the radar, deep blacks and charcoals everywhere else, dramatic rim lighting on the knights and dragon, holographic shimmer, scanlines layered over everything.

Style: cinematic painterly digital art, dark fantasy meets sci-fi command bridge, layered front-to-back depth, very atmospheric. Crisp painterly detail on the radar, sword, dragon, knight armor, and castle stonework.

Mood: epic, immersive, dramatic, sacred, ready-for-war."""


async def generate(variant_idx: int) -> Path:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"war-room-scene-v4-{variant_idx}",
        system_message="You are an expert concept artist generating cinematic dark-fantasy + sci-fi backdrop art for a tactical strategy game. You follow placement instructions exactly, especially front-to-back occlusion (a foreground wall MUST visually cover the lower half of figures standing behind it).",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[v4-variant {variant_idx}] text chars={len(text or '')}, images={len(images) if images else 0}")
    if not images:
        return None
    img = images[0]
    out = OUT_DIR / f"war-room-scene-v4-{variant_idx}.jpg"
    out.write_bytes(base64.b64decode(img["data"]))
    print(f"[v4-variant {variant_idx}] saved → {out} ({out.stat().st_size // 1024} KB)")
    return out


async def main():
    paths = await asyncio.gather(generate(1), generate(2), generate(3))
    print("\nDone. Generated:", [str(p) for p in paths if p])


if __name__ == "__main__":
    asyncio.run(main())
