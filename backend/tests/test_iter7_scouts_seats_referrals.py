"""Iteration 7 backend tests: Tactical Scouts (F2P credits), Pro game slots,
extra_game_monthly Stripe SKU, 100-seat cap, referrals, calendar/milestones.

Run: pytest /app/backend/tests/test_iter7_scouts_seats_referrals.py -v --tb=short
"""
import base64
import io
import os
import re
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://gamer-ai-tactics.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

TEST_EMAIL = "test@tactician.gg"
TEST_PASSWORD = "strongpw1"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# Small valid PNG (50x50 solid color, ~137 bytes — over the 100-byte minimum)
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAIAAACRXR/mAAAAUElEQVR4nO3OoQHAIADAMEBOo/n/"
    "zD0wU8VEckHms8/4n3U78E2r0Cq0Cq1Cq9AqtAqtQqvQKrQKrUKr0Cq0Cq1Cq9AqtAqtQqvQKrQK"
    "reIFycoAoLHBMGQAAAAASUVORK5CYII="
)


# ---------- shared fixtures ----------

@pytest.fixture(scope="module")
def mongo():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    yield db
    client.close()


@pytest.fixture(scope="module")
def auth():
    r = requests.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return {"token": data["token"], "user_id": data["user"]["id"], "headers": {"Authorization": f"Bearer {data['token']}"}}


# ---------- 1. Auth ----------

def test_login_returns_token():
    r = requests.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "token" in body and len(body["token"]) > 10
    assert body["user"]["email"] == TEST_EMAIL


# ---------- 2. Billing quota ----------

def test_quota_has_new_fields(auth):
    r = requests.get(f"{API}/billing/quota", headers=auth["headers"], timeout=10)
    assert r.status_code == 200
    q = r.json()
    for k in ("pro_game_slots", "pro_games", "pro_games_remaining", "scout_credits"):
        assert k in q, f"missing field {k}"
    assert isinstance(q["pro_games"], list)
    assert isinstance(q["pro_game_slots"], int)
    assert isinstance(q["scout_credits"], (int, float))


# ---------- 3. Billing packages ----------

def test_billing_packages():
    r = requests.get(f"{API}/billing/packages", timeout=10)
    assert r.status_code == 200
    pkgs = r.json()
    by_id = {p["id"]: p for p in pkgs}
    for pid in ("subscription_monthly", "topup_analysis", "extra_game_monthly", "toc_addon_monthly"):
        assert pid in by_id, f"missing package {pid}"
    sm = by_id["subscription_monthly"]
    assert sm["amount"] == 4.99
    assert sm["kind"] == "subscription"
    assert sm.get("included_games") == 2
    tp = by_id["topup_analysis"]
    assert tp["amount"] == 2.99
    assert tp["kind"] == "one_time"
    eg = by_id["extra_game_monthly"]
    assert eg["amount"] == 0.99
    assert eg["kind"] == "extra_game"
    toc = by_id["toc_addon_monthly"]
    assert toc["amount"] == 0.99
    assert toc["kind"] == "toc_addon"


# ---------- 4. Pro-games slot endpoint ----------

def test_pro_games_set_valid(auth, mongo):
    # Ensure subscription is active for test user (iter6 set it up; sanity check)
    mongo.users.update_one(
        {"id": auth["user_id"]},
        {"$set": {"pro_game_slots": 2, "pro_games": []}},
    )
    r = requests.post(
        f"{API}/billing/pro-games",
        headers=auth["headers"],
        json={"games": ["puzzles-conquest", "puzzles-chaos"]},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body["pro_games"]) == {"puzzles-conquest", "puzzles-chaos"}
    assert body["pro_game_slots"] >= 2


def test_pro_games_exceed_slots(auth, mongo):
    mongo.users.update_one({"id": auth["user_id"]}, {"$set": {"pro_game_slots": 2}})
    r = requests.post(
        f"{API}/billing/pro-games",
        headers=auth["headers"],
        json={"games": ["puzzles-conquest", "puzzles-chaos", "wartune"]},
        timeout=10,
    )
    assert r.status_code == 400
    assert "slot" in r.text.lower()


# ---------- 5. Stripe checkout (extra_game + regression) ----------

def test_checkout_extra_game_monthly(auth):
    origin = BASE_URL
    r = requests.post(
        f"{API}/billing/checkout",
        headers=auth["headers"],
        json={"package_id": "extra_game_monthly", "origin_url": origin},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "url" in body and body["url"].startswith("http")
    assert "session_id" in body and body["session_id"]


def test_checkout_subscription_monthly_regression(auth):
    r = requests.post(
        f"{API}/billing/checkout",
        headers=auth["headers"],
        json={"package_id": "subscription_monthly", "origin_url": BASE_URL},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("url", "").startswith("http")


def test_checkout_toc_addon_regression(auth):
    r = requests.post(
        f"{API}/billing/checkout",
        headers=auth["headers"],
        json={"package_id": "toc_addon_monthly", "origin_url": BASE_URL},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("url", "").startswith("http")


# ---------- 6. Tactical Scouts ----------

@pytest.fixture
def scouts_reset(auth, mongo):
    """Reset scout state for test user: clear scout_events today + scout_credits."""
    mongo.scout_events.delete_many({"user_id": auth["user_id"]})
    mongo.users.update_one({"id": auth["user_id"]}, {"$set": {"scout_credits": 0.0}})
    yield


def test_scouts_me_initial(auth, scouts_reset):
    r = requests.get(f"{API}/scouts/me", headers=auth["headers"], timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["credits"] == 0
    assert d["redeem_cost"] == 3.0
    assert isinstance(d["rewards"], list)
    assert len(d["rewards"]) == 4
    by_kind = {x["kind"]: x for x in d["rewards"]}
    assert by_kind["upload_game_screenshot"]["credit_per_action"] == 0.25
    assert by_kind["upload_game_screenshot"]["daily_cap"] == 4
    assert by_kind["watch_video"]["credit_per_action"] == 0.10
    assert by_kind["watch_video"]["daily_cap"] == 5
    assert by_kind["try_recommended_game"]["credit_per_action"] == 0.50
    assert by_kind["try_recommended_game"]["daily_cap"] == 2
    assert by_kind["daily_login"]["credit_per_action"] == 0.05
    assert by_kind["daily_login"]["daily_cap"] == 1


def test_scouts_daily_login_then_cap(auth, scouts_reset):
    r = requests.post(f"{API}/scouts/earn/daily_login", headers=auth["headers"], timeout=10)
    assert r.status_code == 200, r.text
    assert round(r.json()["credits"], 2) == 0.05
    # 2nd time hits 429
    r2 = requests.post(f"{API}/scouts/earn/daily_login", headers=auth["headers"], timeout=10)
    assert r2.status_code == 429, r2.text


def test_scouts_watch_video(auth, scouts_reset):
    r = requests.post(
        f"{API}/scouts/earn/watch_video",
        headers=auth["headers"],
        data={"video_id": "test123"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert round(r.json()["credits"], 2) == 0.10


def test_scouts_try_recommended_game(auth, scouts_reset):
    r = requests.post(
        f"{API}/scouts/earn/try_recommended_game",
        headers=auth["headers"],
        data={"game_tried": "puzzles-conquest"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert round(r.json()["credits"], 2) == 0.50


def test_scouts_upload_screenshot_png(auth, scouts_reset):
    files = {"file": ("ts.png", io.BytesIO(PNG_BYTES), "image/png")}
    r = requests.post(
        f"{API}/scouts/earn/upload_game_screenshot",
        headers=auth["headers"],
        files=files,
        timeout=20,
    )
    assert r.status_code == 200, r.text
    assert round(r.json()["credits"], 2) == 0.25


def test_scouts_upload_screenshot_rejects_text(auth, scouts_reset):
    files = {"file": ("hack.txt", io.BytesIO(b"not an image"), "text/plain")}
    r = requests.post(
        f"{API}/scouts/earn/upload_game_screenshot",
        headers=auth["headers"],
        files=files,
        timeout=20,
    )
    assert r.status_code == 400, r.text


def test_scouts_unknown_kind(auth, scouts_reset):
    r = requests.post(f"{API}/scouts/earn/some_unknown_kind", headers=auth["headers"], timeout=10)
    assert r.status_code == 400


def test_scouts_redeem_insufficient(auth, scouts_reset):
    # balance is 0 after reset
    r = requests.post(f"{API}/scouts/redeem", headers=auth["headers"], json={"units": 1}, timeout=10)
    assert r.status_code == 400
    assert "credits" in r.text.lower() or "need" in r.text.lower()


def test_scouts_redeem_success(auth, mongo, scouts_reset):
    # Earn 0.50 + 0.50 + 0.10*5 + 0.05 + 0.25*4 = 0.5+0.5+0.5+0.05+1 = 2.55 — not enough.
    # Simpler: directly grant 3.0 via DB (matches "Manually grant 3+ credits" intent).
    mongo.users.update_one({"id": auth["user_id"]}, {"$set": {"scout_credits": 3.0}})
    # Snapshot extra_baselines
    before = mongo.users.find_one({"id": auth["user_id"]}, {"_id": 0, "extra_baselines": 1})
    before_eb = int((before or {}).get("extra_baselines", 0))
    r = requests.post(f"{API}/scouts/redeem", headers=auth["headers"], json={"units": 1}, timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["redeemed"] == 1
    assert round(body["credits"], 2) == 0.0
    assert int(body["extra_baselines"]) == before_eb + 1


# ---------- 7. Seats (100-cap + admin status) ----------

def test_seat_admin_status_default(auth):
    r = requests.get(f"{API}/seats/admin-status", headers=auth["headers"], timeout=10)
    assert r.status_code == 200
    assert "is_alliance_admin" in r.json()
    assert isinstance(r.json()["is_alliance_admin"], bool)


def test_create_seat_with_admin(auth, mongo):
    # Grant admin to test user
    mongo.users.update_one({"id": auth["user_id"]}, {"$set": {"is_alliance_admin": True}})
    target_email = f"test_seat_{uuid.uuid4().hex[:8]}@tactician.gg"
    body = {"email": target_email, "alliance_name": "TEST_ALLIANCE", "note": "iter7 test"}
    r = requests.post(f"{API}/seats", headers=auth["headers"], json=body, timeout=10)
    assert r.status_code == 200, r.text
    seat = r.json()
    assert seat["email"] == target_email
    assert seat["alliance_name"] == "TEST_ALLIANCE"
    assert seat["status"] in ("pending", "active")
    # Clean up
    mongo.seat_grants.delete_one({"id": seat["id"]})


def test_seat_cap_message_says_100():
    # Static source check: the cap error message must mention 100 (not the legacy 60)
    with open("/app/backend/server.py", "r") as f:
        src = f.read()
    assert "Seat cap reached (100" in src, "Cap error message must mention 100"
    assert "active_count >= 100" in src, "Cap check must compare against 100"


# ---------- 8. Referrals ----------

def test_referral_me(auth):
    r = requests.get(f"{API}/referral/me", headers=auth["headers"], timeout=10)
    assert r.status_code == 200
    d = r.json()
    assert d["code"].startswith("TA-")
    assert "/auth?ref=" in d["share_url"]
    assert isinstance(d["total_referred"], int)
    assert isinstance(d["paid_referred"], int)
    assert isinstance(d["rewards_this_period"], int)
    assert d["cap"] == 5


def test_register_with_referral_grants_bonus(auth, mongo):
    # Get test user's referral code
    r = requests.get(f"{API}/referral/me", headers=auth["headers"], timeout=10)
    code = r.json()["code"]
    new_email = f"TEST_ref_{uuid.uuid4().hex[:8]}@tactician.gg"
    rr = requests.post(
        f"{API}/auth/register",
        json={"email": new_email, "password": "abc12345", "username": "Refee", "referral_code": code},
        timeout=15,
    )
    assert rr.status_code == 200, rr.text
    new_uid = rr.json()["user"]["id"]
    udoc = mongo.users.find_one({"id": new_uid}, {"_id": 0})
    assert udoc is not None
    assert udoc.get("referred_by") == auth["user_id"]
    assert int(udoc.get("extra_baselines", 0)) >= 1, "welcome bonus +1 extra_baseline not applied"
    # cleanup
    mongo.users.delete_one({"id": new_uid})


# ---------- 9. Events + Milestones ----------

def test_events_crud_and_milestone(auth, mongo):
    # Create
    payload = {
        "game_slug": "puzzles-conquest",
        "title": "TEST_iter7 event",
        "description": "test event",
        "start_at": "2026-06-01T10:00:00+00:00",
        "category": "general",
    }
    rc = requests.post(f"{API}/events", headers=auth["headers"], json=payload, timeout=10)
    assert rc.status_code == 200, rc.text
    eid = rc.json()["id"]
    # List
    rl = requests.get(f"{API}/events", headers=auth["headers"], timeout=10)
    assert rl.status_code == 200
    ids = [e["id"] for e in rl.json()]
    assert eid in ids
    # Milestone emitted
    rm = requests.get(f"{API}/milestones?game_slug=puzzles-conquest", headers=auth["headers"], timeout=10)
    assert rm.status_code == 200
    kinds = [m["kind"] for m in rm.json()]
    assert "event_created" in kinds
    # Delete
    rd = requests.delete(f"{API}/events/{eid}", headers=auth["headers"], timeout=10)
    assert rd.status_code == 200


# ---------- 10. Deep Dive 402 with Extra Game slot hint ----------

def test_deep_dive_extra_game_slot_402(auth, mongo):
    """When pro_games slots are full (2 used) and user requests a third game,
    consume_baseline must raise 402 with 'Extra Game slot' hint."""
    # Ensure user is Pro and reset pro_games + period usage
    from datetime import datetime, timezone, timedelta
    future = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    mongo.users.update_one(
        {"id": auth["user_id"]},
        {"$set": {
            "subscription_period_end": future,
            "analyses_used_this_period": 0,
            "pro_game_slots": 2,
            "pro_games": ["whiteout-survival", "last-war"],
        }},
    )
    # third, unrelated slug
    files = {"files": ("a.png", io.BytesIO(PNG_BYTES), "image/png")}
    data = {"game_slug": "puzzles-conquest", "title": "TEST", "notes": ""}
    r = requests.post(f"{API}/deep-dive", headers=auth["headers"], files=files, data=data, timeout=30)
    assert r.status_code == 402, f"expected 402 got {r.status_code} {r.text}"
    assert "Extra Game slot" in r.text


# ---------- 11. Regression: games & guides ----------

def test_games_list_regression():
    r = requests.get(f"{API}/games", timeout=10)
    assert r.status_code == 200
    games = r.json()
    assert len(games) == 11


def test_guides_seeded_regression():
    r = requests.get(f"{API}/guides", timeout=10)
    assert r.status_code == 200
    assert len(r.json()) > 0


# ---------- 12. Cleanup ----------

def test_zzz_cleanup(auth, mongo):
    """Reset test user mutations done by this suite (cap test only modified pro_games/credits)."""
    mongo.scout_events.delete_many({"user_id": auth["user_id"]})
    # Leave is_alliance_admin set (other regressions may rely; harmless) but reset scout credits + pro_games
    mongo.users.update_one(
        {"id": auth["user_id"]},
        {"$set": {"scout_credits": 0.0, "pro_games": ["puzzles-conquest", "puzzles-chaos"]}},
    )
    # Remove any stray TEST_seat alliance docs
    mongo.seat_grants.delete_many({"alliance_name": "TEST_ALLIANCE"})
    mongo.events.delete_many({"user_id": auth["user_id"], "title": "TEST_iter7 event"})
    assert True
