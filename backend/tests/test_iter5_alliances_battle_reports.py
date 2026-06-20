"""Iteration 5 backend tests: Tactical Operations Center (alliances + chat)
and first-class Battle Reports. Uses direct Mongo grant for Pro+TOC entitlements
to avoid real Stripe charges and to keep CyphrAI/vision LLM cost low.
"""
import os
import io
import uuid
import time
import struct
import zlib
from datetime import datetime, timezone, timedelta

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://gamer-ai-tactics.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# ---------- Helpers ----------
def _tiny_png_bytes(w=64, h=64):
    """A valid 64x64 RGBA PNG (so it passes server MIME + size checks)."""
    def chunk(tag: bytes, data: bytes):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    raw = b""
    for _ in range(h):
        raw += b"\x00" + b"\x33\x66\x99\xff" * w  # filter byte + RGBA pixels
    idat = zlib.compress(raw, 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _register(prefix="A5"):
    email = f"TEST_{prefix}_{uuid.uuid4().hex[:8]}@tactician.gg"
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": "abc12345", "username": f"U{uuid.uuid4().hex[:6]}"},
                      timeout=20)
    assert r.status_code == 200, r.text
    return email, r.json()["token"], r.json()["user"]["id"], r.json()["user"]["username"]


def _grant_pro_toc(user_id: str, days: int = 30):
    """Grant Pro subscription + TOC add-on via direct Mongo upsert."""
    c = MongoClient(MONGO_URL)
    try:
        end = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        res = c[DB_NAME].users.update_one(
            {"id": user_id},
            {"$set": {
                "subscription_status": "active",
                "subscription_period_end": end,
                "analyses_used_this_period": 0,
                "toc_period_end": end,
            }},
        )
        assert res.matched_count == 1, f"User {user_id} not found in DB {DB_NAME}"
    finally:
        c.close()


def _grant_toc_only(user_id: str, days: int = 30):
    """Grant only TOC add-on (no active Pro). Should still fail require_toc_access."""
    c = MongoClient(MONGO_URL)
    try:
        end = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        c[DB_NAME].users.update_one(
            {"id": user_id},
            {"$set": {"toc_period_end": end}, "$unset": {"subscription_period_end": ""}},
        )
    finally:
        c.close()


def _cleanup_alliance(aid: str):
    c = MongoClient(MONGO_URL)
    try:
        c[DB_NAME].alliances.delete_one({"id": aid})
        c[DB_NAME].alliance_messages.delete_many({"alliance_id": aid})
    finally:
        c.close()


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Packages + quota fields ----------
def test_iter5_packages_includes_toc_addon():
    r = requests.get(f"{API}/billing/packages", timeout=10)
    assert r.status_code == 200
    pkgs = r.json()
    ids = {p["id"]: p for p in pkgs}
    assert "toc_addon_monthly" in ids, f"Missing toc_addon_monthly in {list(ids.keys())}"
    toc = ids["toc_addon_monthly"]
    assert toc["amount"] == 0.99
    assert toc["kind"] == "toc_addon"
    assert "name" in toc and "description" in toc


def test_iter5_quota_has_toc_fields():
    _, tok, _, _ = _register("QTOC")
    r = requests.get(f"{API}/billing/quota", headers=_h(tok), timeout=10)
    assert r.status_code == 200
    q = r.json()
    assert "toc_active" in q
    assert "toc_period_end" in q
    assert q["toc_active"] is False
    assert q["toc_period_end"] is None


# ---------- TOC gating (402) ----------
def test_iter5_create_alliance_402_without_pro_and_toc():
    _, tok, _, _ = _register("NOTOC")
    r = requests.post(f"{API}/alliances",
                      headers=_h(tok),
                      json={"name": "TEST_X", "game_slug": "puzzles-conquest", "description": ""},
                      timeout=15)
    assert r.status_code == 402, r.text
    detail = r.json().get("detail", "")
    assert "Pro" in detail or "Operations" in detail or "TOC" in detail


def test_iter5_create_alliance_402_with_toc_only_no_pro():
    """Edge: even with TOC entitlement, must have active Pro."""
    _, tok, uid, _ = _register("TOCONLY")
    _grant_toc_only(uid)
    r = requests.post(f"{API}/alliances",
                      headers=_h(tok),
                      json={"name": "TEST_Y", "game_slug": "puzzles-conquest"},
                      timeout=15)
    assert r.status_code == 402, r.text


def test_iter5_join_alliance_402_without_entitlements():
    _, tok, _, _ = _register("J402")
    r = requests.post(f"{API}/alliances/join", headers=_h(tok), json={"code": "ABCDEF"}, timeout=15)
    assert r.status_code == 402, r.text


# ---------- Happy path (Pro+TOC granted) ----------
@pytest.fixture(scope="module")
def alliance_ctx():
    """Create two Pro+TOC users + one alliance, return ctx. Tear down at module end."""
    _, tok_a, uid_a, uname_a = _register("OWNER")
    _grant_pro_toc(uid_a)
    _, tok_b, uid_b, uname_b = _register("MEMB")
    _grant_pro_toc(uid_b)

    r = requests.post(f"{API}/alliances",
                      headers=_h(tok_a),
                      json={"name": "TEST_ALLIANCE_5", "game_slug": "puzzles-conquest",
                            "description": "iter5 test alliance"},
                      timeout=20)
    assert r.status_code == 200, r.text
    a = r.json()
    yield {"tok_a": tok_a, "uid_a": uid_a, "uname_a": uname_a,
           "tok_b": tok_b, "uid_b": uid_b, "uname_b": uname_b,
           "alliance": a}
    _cleanup_alliance(a["id"])


def test_iter5_alliance_create_shape(alliance_ctx):
    a = alliance_ctx["alliance"]
    assert "id" in a and isinstance(a["id"], str)
    assert a["name"] == "TEST_ALLIANCE_5"
    assert a["game_slug"] == "puzzles-conquest"
    assert a["description"] == "iter5 test alliance"
    assert a["member_count"] == 1
    assert a["member_ids"] == [alliance_ctx["uid_a"]]
    assert isinstance(a["code"], str) and len(a["code"]) == 6
    # 6 hex chars
    int(a["code"], 16)


def test_iter5_alliances_mine(alliance_ctx):
    r = requests.get(f"{API}/alliances/mine", headers=_h(alliance_ctx["tok_a"]), timeout=10)
    assert r.status_code == 200
    items = r.json()
    assert any(x["id"] == alliance_ctx["alliance"]["id"] for x in items)


def test_iter5_join_alliance_second_user(alliance_ctx):
    code = alliance_ctx["alliance"]["code"]
    r = requests.post(f"{API}/alliances/join",
                      headers=_h(alliance_ctx["tok_b"]),
                      json={"code": code}, timeout=15)
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["member_count"] == 2
    assert alliance_ctx["uid_b"] in a["member_ids"]


def test_iter5_get_alliance_hydrates_members(alliance_ctx):
    aid = alliance_ctx["alliance"]["id"]
    r = requests.get(f"{API}/alliances/{aid}", headers=_h(alliance_ctx["tok_a"]), timeout=10)
    assert r.status_code == 200
    a = r.json()
    assert "members" in a and isinstance(a["members"], list)
    assert len(a["members"]) >= 2
    usernames = [m["username"] for m in a["members"]]
    assert alliance_ctx["uname_a"] in usernames
    assert alliance_ctx["uname_b"] in usernames


def test_iter5_post_and_fetch_messages(alliance_ctx):
    aid = alliance_ctx["alliance"]["id"]
    # Fetch baseline
    r0 = requests.get(f"{API}/alliances/{aid}/messages", headers=_h(alliance_ctx["tok_a"]), timeout=10)
    assert r0.status_code == 200
    baseline_count = len(r0.json())
    # post
    r = requests.post(f"{API}/alliances/{aid}/messages",
                      headers=_h(alliance_ctx["tok_a"]),
                      json={"content": "TEST_iter5_hello"}, timeout=15)
    assert r.status_code == 200, r.text
    m = r.json()
    assert m["type"] == "text"
    assert m["content"] == "TEST_iter5_hello"
    assert m["username"] == alliance_ctx["uname_a"]
    # incremental since
    since = m["created_at"]
    time.sleep(0.5)
    requests.post(f"{API}/alliances/{aid}/messages",
                  headers=_h(alliance_ctx["tok_b"]),
                  json={"content": "TEST_iter5_followup"}, timeout=15)
    r2 = requests.get(f"{API}/alliances/{aid}/messages",
                      headers=_h(alliance_ctx["tok_a"]),
                      params={"since": since}, timeout=10)
    assert r2.status_code == 200
    new_msgs = r2.json()
    assert all(x["created_at"] > since for x in new_msgs)
    assert any(x["content"] == "TEST_iter5_followup" for x in new_msgs)
    # full fetch grew by at least 2
    rf = requests.get(f"{API}/alliances/{aid}/messages", headers=_h(alliance_ctx["tok_a"]), timeout=10)
    assert len(rf.json()) >= baseline_count + 2


def test_iter5_ask_cyphr_specialist(alliance_ctx):
    aid = alliance_ctx["alliance"]["id"]
    r = requests.post(f"{API}/alliances/{aid}/ask-cyphr",
                      headers=_h(alliance_ctx["tok_a"]),
                      json={"question": "Which hero should I prioritize early for war and what building order helps power?"},
                      timeout=120)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "question" in body and "answer" in body
    q, a = body["question"], body["answer"]
    assert q["type"] == "cyphr_q"
    assert a["type"] == "cyphr_a"
    assert a["user_id"] == "cyphr-ai"
    assert a["username"] == "CyphrAI"
    assert isinstance(a["content"], str) and len(a["content"]) > 20
    # Specialist behavior: ensure no leakage to wrong-game refs
    lower = a["content"].lower()
    forbidden = ["lords mobile", "rise of kingdoms", "evony", "clash royale", "summoners war"]
    for token in forbidden:
        assert token not in lower, f"Cross-game ref leaked: {token}"


# ---------- Share Deep Dive via DB upsert (avoids vision call) ----------
def test_iter5_share_deepdive_in_alliance(alliance_ctx):
    aid = alliance_ctx["alliance"]["id"]
    uid = alliance_ctx["uid_a"]
    # Direct DB upsert of a deep dive (instead of paying for /api/deep-dive)
    dd_id = str(uuid.uuid4())
    c = MongoClient(MONGO_URL)
    try:
        c[DB_NAME].deep_dives.insert_one({
            "id": dd_id,
            "user_id": uid,
            "game_slug": "puzzles-conquest",
            "title": "TEST_DD_iter5",
            "follow_ups": [{"q": "x", "a": "y"}],
            "shots": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # Share to alliance
        r = requests.post(f"{API}/alliances/{aid}/share-deepdive",
                          headers=_h(alliance_ctx["tok_a"]),
                          json={"ref_id": dd_id}, timeout=20)
        assert r.status_code == 200, r.text
        msg = r.json()
        assert msg["type"] == "share_deepdive"
        refs = msg["refs"]
        assert refs["deep_dive_id"] == dd_id
        assert refs["title"] == "TEST_DD_iter5"
        assert "share_token" in refs and isinstance(refs["share_token"], str)
        assert refs["follow_ups"] == 1

        # Cross-game: insert DD for different game, share should 400
        dd2 = str(uuid.uuid4())
        c[DB_NAME].deep_dives.insert_one({
            "id": dd2,
            "user_id": uid,
            "game_slug": "puzzles-chaos",
            "title": "TEST_DD_iter5_wrong_game",
            "follow_ups": [],
            "shots": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        r2 = requests.post(f"{API}/alliances/{aid}/share-deepdive",
                           headers=_h(alliance_ctx["tok_a"]),
                           json={"ref_id": dd2}, timeout=15)
        assert r2.status_code == 400, r2.text
    finally:
        c[DB_NAME].deep_dives.delete_one({"id": dd_id})
        c[DB_NAME].deep_dives.delete_one({"id": dd2})
        c.close()


# ---------- Battle Reports (first-class) ----------
def test_iter5_battle_report_create_no_auto_then_analyze_then_cache():
    """Single test covers: create (no auto), GET list/detail, analyze (vision cost),
    analyze cache, then DELETE. Uses ONE vision call total (budget-conscious)."""
    _, tok, uid, _ = _register("BR1")
    _grant_pro_toc(uid)
    png = _tiny_png_bytes()
    # CREATE without auto_analyze
    files = [("files", ("br1.png", png, "image/png"))]
    data = {"game_slug": "puzzles-conquest", "title": "TEST_BR_iter5", "notes": "lost the fight", "auto_analyze": "false"}
    r = requests.post(f"{API}/battle-reports", headers=_h(tok), files=files, data=data, timeout=30)
    assert r.status_code == 200, r.text
    br = r.json()
    assert br["title"] == "TEST_BR_iter5"
    assert br["game_slug"] == "puzzles-conquest"
    assert br["cyphr_take"] in (None, "")
    assert isinstance(br["shots"], list) and len(br["shots"]) == 1
    rid = br["id"]

    # LIST
    rl = requests.get(f"{API}/battle-reports", headers=_h(tok), timeout=10)
    assert rl.status_code == 200
    assert any(x["id"] == rid for x in rl.json())

    # GET detail
    rg = requests.get(f"{API}/battle-reports/{rid}", headers=_h(tok), timeout=10)
    assert rg.status_code == 200
    assert rg.json()["id"] == rid

    # ANALYZE (vision call ~$0.05)
    ra = requests.post(f"{API}/battle-reports/{rid}/analyze", headers=_h(tok), timeout=180)
    assert ra.status_code == 200, ra.text
    aj = ra.json()
    assert "cyphr_take" in aj and isinstance(aj["cyphr_take"], str) and len(aj["cyphr_take"]) > 20
    assert aj.get("cached") is False

    # Calling analyze again → cached
    ra2 = requests.post(f"{API}/battle-reports/{rid}/analyze", headers=_h(tok), timeout=20)
    assert ra2.status_code == 200
    assert ra2.json().get("cached") is True

    # DELETE
    rd = requests.delete(f"{API}/battle-reports/{rid}", headers=_h(tok), timeout=15)
    assert rd.status_code == 200
    # Verify gone
    rg2 = requests.get(f"{API}/battle-reports/{rid}", headers=_h(tok), timeout=10)
    assert rg2.status_code == 404


def test_iter5_battle_report_auto_analyze_populates_cyphr_take():
    """auto_analyze=true returns doc with cyphr_take populated (one vision call)."""
    _, tok, uid, _ = _register("BR2")
    _grant_pro_toc(uid)
    files = [("files", ("auto.png", _tiny_png_bytes(), "image/png"))]
    data = {"game_slug": "puzzles-conquest", "title": "TEST_BR_AUTO", "notes": "test auto",
            "auto_analyze": "true"}
    r = requests.post(f"{API}/battle-reports", headers=_h(tok), files=files, data=data, timeout=180)
    assert r.status_code == 200, r.text
    br = r.json()
    take = br.get("cyphr_take")
    assert isinstance(take, str) and len(take) > 20, f"cyphr_take should be populated, got: {take!r}"
    # cleanup
    requests.delete(f"{API}/battle-reports/{br['id']}", headers=_h(tok), timeout=15)


def test_iter5_battle_report_share_to_alliance(alliance_ctx):
    """Share a BR to an alliance. Cross-game → 400."""
    aid = alliance_ctx["alliance"]["id"]
    tok = alliance_ctx["tok_a"]
    uid = alliance_ctx["uid_a"]
    # Create BR (no auto)
    files = [("files", ("br3.png", _tiny_png_bytes(), "image/png"))]
    data = {"game_slug": "puzzles-conquest", "title": "TEST_BR_SHARE", "notes": "share me",
            "auto_analyze": "false"}
    r = requests.post(f"{API}/battle-reports", headers=_h(tok), files=files, data=data, timeout=30)
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    try:
        # Share OK
        rs = requests.post(f"{API}/alliances/{aid}/share-battle-report",
                           headers=_h(tok), json={"ref_id": rid}, timeout=20)
        assert rs.status_code == 200, rs.text
        msg = rs.json()
        assert msg["type"] == "share_battle_report"
        assert msg["refs"]["battle_report_id"] == rid
        assert msg["refs"]["title"] == "TEST_BR_SHARE"
        assert "shot_count" in msg["refs"]
        # Cross-game BR for puzzles-chaos
        files2 = [("files", ("brx.png", _tiny_png_bytes(), "image/png"))]
        data2 = {"game_slug": "puzzles-chaos", "title": "TEST_BR_WG", "notes": "wrong game",
                 "auto_analyze": "false"}
        r2 = requests.post(f"{API}/battle-reports", headers=_h(tok), files=files2, data=data2, timeout=30)
        assert r2.status_code == 200, r2.text
        rid2 = r2.json()["id"]
        try:
            rx = requests.post(f"{API}/alliances/{aid}/share-battle-report",
                               headers=_h(tok), json={"ref_id": rid2}, timeout=15)
            assert rx.status_code == 400, rx.text
        finally:
            requests.delete(f"{API}/battle-reports/{rid2}", headers=_h(tok), timeout=15)
    finally:
        requests.delete(f"{API}/battle-reports/{rid}", headers=_h(tok), timeout=15)


# ---------- Leave alliance flows ----------
def test_iter5_leave_alliance_transfers_ownership_then_disbands():
    """Creator leaves with another member → ownership transfers.
    Then that sole member leaves → alliance disbanded."""
    _, tok_a, uid_a, _ = _register("OWN1")
    _grant_pro_toc(uid_a)
    _, tok_b, uid_b, _ = _register("MEM1")
    _grant_pro_toc(uid_b)
    # create
    r = requests.post(f"{API}/alliances", headers=_h(tok_a),
                      json={"name": "TEST_LEAVE", "game_slug": "puzzles-conquest"}, timeout=20)
    assert r.status_code == 200, r.text
    a = r.json()
    aid = a["id"]
    code = a["code"]
    try:
        # B joins
        r2 = requests.post(f"{API}/alliances/join", headers=_h(tok_b), json={"code": code}, timeout=15)
        assert r2.status_code == 200, r2.text
        # A (creator) leaves → ownership transfers to B
        rl = requests.post(f"{API}/alliances/{aid}/leave", headers=_h(tok_a), timeout=15)
        assert rl.status_code == 200, rl.text
        # Verify in DB
        c = MongoClient(MONGO_URL)
        try:
            doc = c[DB_NAME].alliances.find_one({"id": aid})
            assert doc is not None
            assert doc["creator_id"] == uid_b
            assert uid_a not in doc["member_ids"]
            assert uid_b in doc["member_ids"]
            assert len(doc["member_ids"]) == 1
        finally:
            c.close()
        # Now B (the new sole member) leaves → disbanded
        rl2 = requests.post(f"{API}/alliances/{aid}/leave", headers=_h(tok_b), timeout=15)
        assert rl2.status_code == 200
        assert rl2.json().get("disbanded") is True
        # alliance + messages purged
        c = MongoClient(MONGO_URL)
        try:
            assert c[DB_NAME].alliances.find_one({"id": aid}) is None
            assert c[DB_NAME].alliance_messages.count_documents({"alliance_id": aid}) == 0
        finally:
            c.close()
    finally:
        _cleanup_alliance(aid)


# ---------- Final cleanup of TEST_ users (best-effort) ----------
def test_zzz_iter5_cleanup_test_users():
    c = MongoClient(MONGO_URL)
    try:
        res = c[DB_NAME].users.delete_many({"email": {"$regex": "^TEST_(A5|OWNER|MEMB|NOTOC|TOCONLY|J402|QTOC|BR1|BR2|OWN1|MEM1)_"}})
        # Just informational; don't fail
        print(f"Cleaned {res.deleted_count} test users")
    finally:
        c.close()
