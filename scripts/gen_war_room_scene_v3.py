"""Generate War Room Scene v3 — General Ellie's adjustments.
Changes from v1:
  - Dragon: SMALLER + moved DOWN (no longer dominates upper-left)
  - Tanks: REMOVED
  - Knights: behind castles, GHOSTLY translucent (ethereal sentinels)
  - Castles: faded, SLIGHTLY DARKER than the ghost knights (depth hierarchy)
  - Floor: holographic topographic GRID MAP (open battlefield projection)
  - Sword: KEEP (center crystal-sword landmark)
Run: python /app/scripts/gen_war_room_scene_v3.py
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

PROMPT = """Cinematic dark fantasy + sci-fi War Room concept art, vertical portrait composition optimized for a 9:16 mobile phone screen.

CENTERPIECE (upper-center of frame): a massive vibrant neon GREEN holographic radar/scanner — concentric glowing rings, crosshair lines, a rotating sweep beam, like a glowing dome of holographic light. Bright emerald green (#00FF80 / #39FF14) with cyan undertones. Scanlines and holographic flicker overlay it.

DRAGON: a sleek ethereal dragon, smaller in scale than typical hero composition, positioned in the MID-LEFT region of the frame (not the upper sky) — flying horizontally at roughly the midground height, wings outstretched, partly silhouetted against the radar's green glow, dark scales catching the green light. The dragon should feel like an observer, not a sky lord.

MIDGROUND — GHOST SENTINELS BEHIND THE WALLS: two armored medieval fantasy knights standing as SPECTRAL ghost guardians directly behind a row of castle ramparts. The knights are translucent, ethereal, ghostly — clearly visible silhouettes with armor and helms readable, glowing faintly with cool green spirit-light, like ancestral protectors watching over the war room. They are NOT in the foreground — they stand BEHIND the castle wall, peering forward.

MIDGROUND — FADED CASTLE WALL: a row of dark stone castle turrets and fortress ramparts stretching horizontally across the mid-lower portion of the frame, forming the wall the ghost knights stand behind. The castle wall is FADED and slightly darker than the ghost knights — like a memory rendered in shadow — so the hierarchy reads: ghost knights (lightest, glowing) → castle wall (faded, slightly darker) → deep background (darkest).

CENTER: a tall glowing crystal-sword landmark rising upward from the wall line, lit by green radar light, dramatic and iconic — the symbolic centerpiece of the war room.

FOREGROUND FLOOR — HOLOGRAPHIC TOPOGRAPHIC GRID MAP: the entire bottom 35-40% of the frame is a vast holographic topographic battlefield map projected on the floor — glowing neon green grid lines (perspective receding into the distance), contour lines showing terrain elevation (hills, valleys, ridges), faint terrain shading, a few scattered tactical markers. Think Pentagon situation room holographic war-table, but rendered as the floor of a sacred cinematic war room. The floor must be visually open, empty of figures, and inviting — leaving generous space for UI beacons to be layered on top later.

NO TANKS. NO foreground knights. NO foreground figures of any kind. The foreground floor stays clean and empty.

BACKGROUND: deep dark night atmosphere, volumetric green mist, faint stars, distant mountains barely visible. The deepest background is the DARKEST tonal value in the image.

Lighting: dominant neon GREEN ambient glow from the radar, deep blacks and charcoals everywhere else, dramatic rim lighting on the ghost knights and dragon, holographic shimmer, scanlines layered over everything. Depth hierarchy by tone: ghost knights brightest (translucent green spirit-light) → castle wall faded slightly darker → mountains/sky deepest dark.

Style: cinematic painterly digital art, dark fantasy meets sci-fi command bridge, layered front-to-back depth, very atmospheric. Painterly but with crisp detail on the radar, sword, dragon, and the topographic grid lines.

CRITICAL: NO text, NO UI panels, NO data readouts, NO labels, NO logos, NO HUD overlays — pure atmospheric backdrop art only. The foreground floor (topographic map) must be CLEAR and OPEN for UI to layer on top.

Mood: epic, immersive, dramatic, sacred, ready-for-war, with a ghostly ancestral reverence."""


async def generate(variant_idx: int) -> Path:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"war-room-scene-v3-{variant_idx}",
        system_message="You are an expert concept artist generating cinematic dark-fantasy + sci-fi backdrop art for a tactical strategy game.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[v3-variant {variant_idx}] text chars={len(text or '')}, images={len(images) if images else 0}")
    if not images:
        return None
    img = images[0]
    out = OUT_DIR / f"war-room-scene-v3-{variant_idx}.jpg"
    out.write_bytes(base64.b64decode(img["data"]))
    print(f"[v3-variant {variant_idx}] saved → {out} ({out.stat().st_size // 1024} KB)")
    return out


async def main():
    paths = await asyncio.gather(generate(1), generate(2))
    print("\nDone. Generated:", [str(p) for p in paths if p])


if __name__ == "__main__":
    asyncio.run(main())
