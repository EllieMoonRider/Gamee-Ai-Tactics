"""Generate assets for The Dragon's Ritual (Command Center welcome briefing).

  A) war-room-scene-v5-1.jpg — SAME as v4-1 but with the dragon REMOVED.
     Upper-center sky must be CLEAN so our animated dragon sprite can land
     there via CSS overlay.
  B) dragon-sprite-v1.jpg — a fierce dragon painted on SOLID BLACK
     background, viewed from below in a hovering/diving pose. We'll composite
     this with mix-blend-mode: screen so the black BG drops out cleanly.

Run: python /app/scripts/gen_dragon_ritual_assets.py
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


SCENE_PROMPT = """Cinematic dark fantasy + sci-fi War Room concept art, horizontal landscape composition.

CENTERPIECE: a massive vibrant neon GREEN holographic radar/scanner dome in the upper-center. Concentric glowing rings, crosshair lines, rotating sweep beam. Bright emerald green (#00FF80).

CENTER VERTICAL: a tall glowing crystal-sword landmark rising upward, lit by green radar light, centered horizontally.

FOREGROUND CASTLE WALL: dark stone castle battlements/ramparts stretching horizontally across the lower-mid frame. Clear crenellations. This wall is a SOLID OPAQUE STONE BARRIER that OCCLUDES the lower half of the knights.

KNIGHTS BEHIND THE WALL: TWO large emerald-armored knights standing behind the wall, only upper body visible (head, helm, chest, arms). Wall cuts them at chest height. LEFT knight centered at 25% width, RIGHT knight centered at 75% width. Facing slightly inward. Solid plate armor catching green radar light with ethereal green rim glow.

FOREGROUND FLOOR (bottom 30-35%): dark misty stone floor — INTENTIONALLY CLEAN AND EMPTY, no figures, no obstacles. A holographic grid will layer on top later.

DEEP BACKGROUND: deep dark night atmosphere, volumetric green mist, faint stars, distant mountains barely visible.

⚠️ CRITICAL EXCLUSION: THERE IS NO DRAGON IN THIS SCENE. The upper-center airspace above the radar (from about 5% down to 40% of frame height, centered horizontally) must remain COMPLETELY CLEAR of any dragon, creature, wings, or flying figure. This is intentional — an animated dragon sprite will occupy this space via CSS overlay.

NO tanks. NO foreground figures. NO text/UI/labels/HUD. NO dragon.

Lighting: dominant neon GREEN glow from the radar, deep blacks and charcoals everywhere else, dramatic rim lighting on the knights, holographic shimmer, scanlines.

Style: cinematic painterly digital art, dark fantasy + sci-fi command bridge, layered depth. Mood: epic, immersive, sacred, ready-for-war."""


DRAGON_PROMPT = """A single fierce dragon in a hovering / gently diving pose, viewed from a low front-angle so its outstretched wings frame the composition and its long serpentine neck extends slightly downward toward the viewer with its mouth OPEN in a roar. Dark scaled body — deep charcoal, iron, and forest-green scales with subtle emerald-green rim lighting glowing along the edges of the wings, spine, and jawline. Sharp horns, glowing green eyes, teeth visible in the open mouth. Slightly ethereal — hints of translucent green energy trailing off the wingtips and tail.

⚠️ CRITICAL BACKGROUND: The entire background must be PURE SOLID BLACK (#000000) with ZERO detail — no sky, no stars, no mist, no light, no gradient, no atmosphere. Just flat pitch black. This will be composited over another scene using additive blending, so the black must be true 0,0,0 with no noise.

The dragon fills roughly the center 70% of the frame with generous black padding all around. Wings extend outward. Head/mouth is centered horizontally in the lower-third of the frame so the mouth-region is positioned where flames will emerge in the overlay animation.

Style: dark fantasy concept art, cinematic painterly digital art. The dragon itself is fully detailed and painterly. NO text, NO labels, NO logos, NO borders, NO ground, NO other creatures.

Mood: majestic, ancient, powerful — the vessel of an AI oracle about to deliver a mission briefing."""


async def gen_scene():
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id="war-room-scene-v5",
        system_message="You are an expert concept artist. Follow spatial rules exactly. If told to exclude an element, exclude it completely.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=SCENE_PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[scene v5] images={len(images) if images else 0}")
    if images:
        out = OUT_DIR / "war-room-scene-v5-1.jpg"
        out.write_bytes(base64.b64decode(images[0]["data"]))
        print(f"[scene v5] saved → {out} ({out.stat().st_size // 1024} KB)")
        return out


async def gen_dragon(variant_idx: int):
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"dragon-sprite-{variant_idx}",
        system_message="You are an expert concept artist producing isolated character sprites on solid black backgrounds for compositing.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=DRAGON_PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"[dragon v{variant_idx}] images={len(images) if images else 0}")
    if images:
        out = OUT_DIR / f"dragon-sprite-v{variant_idx}.jpg"
        out.write_bytes(base64.b64decode(images[0]["data"]))
        print(f"[dragon v{variant_idx}] saved → {out} ({out.stat().st_size // 1024} KB)")
        return out


async def main():
    results = await asyncio.gather(gen_scene(), gen_dragon(1), gen_dragon(2))
    print("\nDone:", [str(r) for r in results if r])


if __name__ == "__main__":
    asyncio.run(main())
