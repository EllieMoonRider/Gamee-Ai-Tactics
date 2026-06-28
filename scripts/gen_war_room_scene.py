"""Generate the War Room Command Center backdrop matching Ellie's reference image.
GREEN holographic radar centerpiece + dragon + knights + castles + tanks.
Run: python /app/scripts/gen_war_room_scene.py
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

CENTERPIECE (upper half of frame): a massive vibrant neon GREEN holographic radar/scanner — concentric glowing rings, crosshair lines, a rotating sweep beam, sitting like a glowing dome of holographic light. Bright emerald green (#00FF80 / #39FF14) with cyan undertones. Scanlines and holographic flicker overlay it.

LEFT FOREGROUND: a powerful ethereal dragon mid-flight, wings outstretched, partly silhouetted against the radar's green glow, dark scales catching the green light.

CENTER-BOTTOM: two armored medieval fantasy knights standing as guards, facing the viewer, in full plate armor holding spears or polearms, lit from above by the radar's green light. Between them rises a tall glowing crystal-sword landmark.

BOTTOM SKYLINE: a row of dark stone castle turrets and fortress towers stretching across the bottom of the frame like a city skyline at night.

LOWER CORNERS: two military tanks / armored vehicles sitting in the corners (lower-left and lower-right), partially in shadow.

BACKGROUND: deep dark night atmosphere, volumetric green mist, faint stars, distant mountains barely visible.

Lighting: dominant neon GREEN ambient glow from the radar, deep blacks and charcoals everywhere else, dramatic rim lighting on the knights and dragon, holographic shimmer, scanlines layered over everything.

Style: cinematic painterly digital art, dark fantasy meets sci-fi command bridge, layered front-to-back depth (panels, mid-scene actors, background), very atmospheric. Painterly but with crisp detail on the radar and figures.

CRITICAL: NO text, NO UI panels, NO data readouts, NO labels, NO logos, NO HUD overlays — pure atmospheric backdrop art only. Leave breathing room for UI to layer on top later.

Mood: epic, immersive, dramatic, ready-for-war, sacred."""


async def generate(variant_idx: int) -> Path:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"war-room-scene-{variant_idx}",
        system_message="You are an expert concept artist generating cinematic dark-fantasy + sci-fi backdrop art for a tactical strategy game.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[variant {variant_idx}] text chars={len(text or '')}, images={len(images) if images else 0}")
    if not images:
        return None
    img = images[0]
    out = OUT_DIR / f"war-room-scene-v{variant_idx}.jpg"
    out.write_bytes(base64.b64decode(img["data"]))
    print(f"[variant {variant_idx}] saved → {out} ({out.stat().st_size // 1024} KB)")
    return out


async def main():
    paths = await asyncio.gather(generate(1), generate(2))
    print("\nDone. Generated:", [str(p) for p in paths if p])


if __name__ == "__main__":
    asyncio.run(main())
