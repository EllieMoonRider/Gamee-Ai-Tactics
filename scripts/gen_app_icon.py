"""Generate Tactical Ally PWA icon (transparent, dark, neon green crosshair logo) via Nano Banana."""
import asyncio, os, base64
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv("/app/backend/.env")

OUT_DIR = Path("/app/frontend/public")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = """Generate a square 1024x1024 app icon for "Tactical Ally" — an AI gaming strategy companion.

Composition:
- Centered crosshair / tactical scope reticle made of clean neon green lines, with a small dragon silhouette in the center of the crosshair
- Behind it, a faint stylized castle turret silhouette at the bottom
- Dark charcoal/near-black background (#0a0a0a)
- Strong neon green glow accents (#39FF14)
- Subtle holographic circular rings around the crosshair
- Rounded square format with safe padding from the edges (about 12% margin) so it works as an iOS/Android home-screen icon
- No text, no letters, no words anywhere
- Clean, modern, game-app style — readable at 64x64 thumbnail

Style: cinematic dark fantasy + tactical sci-fi, vector-like clean shapes, bold silhouettes."""


async def main():
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id="tactical-ally-icon",
        system_message="You are an expert icon designer producing clean modern app icons.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    if not images:
        print("FAIL: no images returned")
        return
    img = images[0]
    out = OUT_DIR / "icon-1024.jpg"
    out.write_bytes(base64.b64decode(img["data"]))
    print(f"Saved → {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    asyncio.run(main())
