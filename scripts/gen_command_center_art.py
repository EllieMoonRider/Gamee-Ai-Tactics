"""One-shot script to generate Command Center backdrop art via Gemini Nano Banana.
Run: python /app/scripts/gen_command_center_art.py
"""
import asyncio
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")

OUT_DIR = Path("/app/frontend/public/assets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = """Wide cinematic 16:9 widescreen concept art for a video game command room interior.

Foreground: two armored medieval-fantasy knight silhouettes (only their backs visible, dark) standing slightly apart, looking forward and slightly down toward a massive glowing holographic tactical scanner.

Center: a large floating circular holographic radar/scanner with concentric rings and a sweeping line, projected in vibrant neon green light, hovering above an isometric battlefield map.

Map (below the radar): a deep dark fantasy battlefield with scattered glowing castle outposts, watch towers, fortresses, and tiny troops, all rendered as wireframe-style holographic projections in neon green light.

Background: a massive ethereal dragon flying through distant atmospheric mist and dark mountains, very faded into the deep background.

Lighting: heavy neon green ambient glow (hex #39FF14 / #00FF94), volumetric mist, deep blacks and charcoal grays, dramatic rim lighting on the knights, holographic shimmer.

Style: dark fantasy meets sci-fi command bridge, cinematic, photoreal but painterly, layered depth, very moody. No text, no UI labels, no data panels, no readouts, no HUD overlays, no logos. Pure atmospheric backdrop art that leaves the center-upper area calm for UI to sit on top.

Mood: epic, immersive, dramatic, ready-for-war.

Aspect ratio: 16:9 widescreen panorama."""


async def generate(variant_idx: int) -> Path:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"command-center-art-{variant_idx}",
        system_message="You are an expert concept artist generating cinematic dark-fantasy/sci-fi backdrop art for a strategy game UI.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[variant {variant_idx}] text response chars={len(text or '')}, images={len(images) if images else 0}")
    if not images:
        return None
    img = images[0]
    out = OUT_DIR / f"command-center-bg-v{variant_idx}.jpg"
    out.write_bytes(base64.b64decode(img["data"]))
    print(f"[variant {variant_idx}] saved → {out} ({out.stat().st_size // 1024} KB, mime={img.get('mime_type')})")
    return out


async def main():
    paths = await asyncio.gather(generate(1), generate(2))
    print("\nDone. Generated:", [str(p) for p in paths if p])


if __name__ == "__main__":
    asyncio.run(main())
