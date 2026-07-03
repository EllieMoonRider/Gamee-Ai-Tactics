"""
Ice Bay Reminder — One-shot scheduled email sender.
Fires at 20:45 UTC (4:45 PM EDT) — 15 min before R5 EllieMoonRider's Ice Bay event.
Uses the same Gmail SMTP setup as server.py.
"""
import os
import sys
import time
import smtplib
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [reminder] %(message)s")

# Load env from backend/.env
load_dotenv(Path(__file__).parent / ".env")

TO_EMAIL = "elliemoonrider14@gmail.com"
FROM_EMAIL = os.environ.get("SUPPORT_EMAIL", "").strip()
APP_PASSWORD = "".join(os.environ.get("SUPPORT_GMAIL_APP_PASSWORD", "").split())

# Target: 20:45 UTC = 4:45 PM EDT
TARGET_HOUR_UTC = 20
TARGET_MINUTE_UTC = 45

SUBJECT = "GO TIME — Ice Bay in P&C · 15 min warning"
HTML = """<!doctype html>
<html><body style="margin:0;padding:0;background:#050505;font-family:'Helvetica Neue',Arial,sans-serif;color:#cfffe1;">
  <div style="max-width:560px;margin:0 auto;padding:36px 28px;background:linear-gradient(180deg,#0a0a0a 0%,#050505 100%);border:1px solid #FF6B00;">
    <div style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:0.28em;color:#FFBA08;margin-bottom:24px;">
      // TACTICAL ALLY · WAR ROOM ALERT
    </div>
    <h1 style="font-family:'Orbitron','Bebas Neue',sans-serif;font-weight:900;font-size:28px;color:#ffb060;text-align:center;margin:0 0 20px;letter-spacing:0.03em;">
      GO TIME
    </h1>
    <div style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:0.22em;color:#00FF80;margin-bottom:24px;">
      ◇ ICE BAY ◇ PUZZLES &amp; CONQUEST ◇
    </div>
    <p style="font-size:16px;line-height:1.65;text-align:center;color:#e5faed;margin:0 0 18px;">
      <strong style="color:#FFBA08;">15 minutes</strong> until Ice Bay kicks off.
    </p>
    <p style="font-size:15px;line-height:1.65;text-align:center;color:#a8c8b8;margin:0 0 28px;">
      Prep your marches. Sync alliance chat. Set your battle formation.<br>
      Event start: <strong style="color:#00FF80;">5:00 PM Eastern</strong>
    </p>
    <div style="margin:26px 0;padding:20px;background:rgba(0,22,12,0.7);border:1px solid rgba(0,255,128,0.35);text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.22em;color:rgba(0,255,128,0.85);margin-bottom:10px;">
        // BATTLE OF SAURNESIA / CLASH / ICE BAY
      </div>
      <div style="font-size:13px;color:#cfffe1;line-height:1.55;">
        Verified doctrine from your dossier: Day 5 of Ace Week aligns with this event.<br>
        Coordinate with alliance leadership before entering.
      </div>
    </div>
    <p style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.22em;color:#FFBA08;margin:24px 0 6px;">
      ~ Sent by Lt. Atlas · R4 Code Specialist ~
    </p>
    <p style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:0.2em;color:rgba(0,255,128,0.55);margin:0;">
      Tactical Ally &middot; 37Games Unaffiliated
    </p>
  </div>
</body></html>
"""

def send():
    if not FROM_EMAIL or not APP_PASSWORD:
        logging.error("SMTP credentials missing — cannot send.")
        return False
    msg = EmailMessage()
    msg["Subject"] = SUBJECT
    msg["From"] = f"Tactical Ally War Room <{FROM_EMAIL}>"
    msg["To"] = TO_EMAIL
    msg.set_content("Open this email in an HTML-capable client to view formatting. Ice Bay event in 15 minutes.")
    msg.add_alternative(HTML, subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as s:
            s.login(FROM_EMAIL, APP_PASSWORD)
            s.send_message(msg)
        logging.info("Email sent successfully to %s", TO_EMAIL)
        return True
    except Exception:
        logging.exception("Send failed")
        return False


def main():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=TARGET_HOUR_UTC, minute=TARGET_MINUTE_UTC, second=0, microsecond=0)
    delay = (target - now).total_seconds()
    if delay <= 0:
        logging.error("Target time already passed (target=%s now=%s). Aborting.", target.isoformat(), now.isoformat())
        return 1
    logging.info("Sleeping %.1f minutes until %s UTC (4:45 PM EDT)", delay / 60, target.isoformat())
    time.sleep(delay)
    ok = send()
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
