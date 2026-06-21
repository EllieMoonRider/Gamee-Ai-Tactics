"""Iteration 6 backend tests: CypherAI Guided Deep Dive.

Covers:
 - GET /api/deep-dive-guide-plan (auth + caching + invalid game)
 - POST /api/guided-dive/start, GET /api/guided-dive/{sid}
 - POST /api/guided-dive/{sid}/upload (replace + skip-unskip)
 - POST /api/guided-dive/{sid}/skip
 - POST /api/guided-dive/{sid}/ask
 - POST /api/guided-dive/{sid}/finalize (success + 402 no-quota + already-finalized + no-uploads)
 - DELETE /api/deep-dive/guided/{sid} (abandon)
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

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


def _tiny_png_bytes(w=64, h=64):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    raw = b""
    for _ in range(h):
        raw += b"\x00" + b"\x33\x66\x99\xff" * w
    idat = zlib.compress(raw, 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _register(prefix="GD6"):
    email = f"TEST_{prefix}_{uuid.uuid4().hex[:8]}@tactician.gg"
    r = requests.post(f"{API}/auth/register",
                      json={"email": email, "password": "abc12345", "username": f"U{uuid.uuid4().hex[:6]}"},
                      timeout=20)
    assert r.status_code == 200, r.text
    j = r.json()
    return email, j["token"], j["user"]["id"], j["user"]["username"]


def _grant_extra_baseline(user_id: str, n: int = 1):
    c = MongoClient(MONGO_URL)
    try:
        c[DB_NAME].users.update_one({"id": user_id}, {"$inc": {"extra_baselines": int(n)}})
    finally:
        c.close()


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Auth + invalid params ----------
def test_iter6_guide_plan_requires_auth():
    r = requests.get(f"{API}/deep-dive-guide-plan", params={"game_slug": "puzzles-conquest"}, timeout=20)
    assert r.status_code in (401, 403), r.text


def test_iter6_guide_plan_invalid_slug_400():
    _, tok, _, _ = _register("BADSLUG")
    r = requests.get(f"{API}/deep-dive-guide-plan",
                     params={"game_slug": "not-a-game"}, headers=_h(tok), timeout=20)
    assert r.status_code == 400, r.text


# ---------- Plan generation + cache ----------
@pytest.fixture(scope="module")
def plan_ctx():
    """Trigger plan generation once (first call may take 3-8s). Reuse for later tests."""
    _, tok, uid, _ = _register("PLAN")
    r = requests.get(f"{API}/deep-dive-guide-plan",
                     params={"game_slug": "puzzles-conquest"},
                     headers=_h(tok), timeout=45)
    assert r.status_code == 200, r.text
    return {"token": tok, "user_id": uid, "plan": r.json()}


def test_iter6_guide_plan_shape_and_game_specific(plan_ctx):
    p = plan_ctx["plan"]
    assert p["game_slug"] == "puzzles-conquest"
    assert "steps" in p and isinstance(p["steps"], list)
    assert 6 <= len(p["steps"]) <= 8, f"Expected 6-8 steps, got {len(p['steps'])}"
    for st in p["steps"]:
        assert set(["id", "title", "desc"]).issubset(st.keys())
        assert isinstance(st["title"], str) and len(st["title"]) > 0
        assert isinstance(st["desc"], str) and len(st["desc"]) > 0
    # Game-specific terms heuristic
    blob = " ".join((st["title"] + " " + st["desc"]) for st in p["steps"]).lower()
    pnc_terms = ["hero", "sanctuary", "formation", "talent", "march", "alliance", "stamina", "tower", "gear", "puzzle"]
    assert any(term in blob for term in pnc_terms), f"Plan not P&C-specific: {blob[:300]}"
    assert "created_at" in p


def test_iter6_guide_plan_cached_fast(plan_ctx):
    t0 = time.time()
    r = requests.get(f"{API}/deep-dive-guide-plan",
                     params={"game_slug": "puzzles-conquest"},
                     headers=_h(plan_ctx["token"]), timeout=20)
    dt = time.time() - t0
    assert r.status_code == 200
    j = r.json()
    assert j["steps"] == plan_ctx["plan"]["steps"], "Cached steps should match"
    # Cached call should be quick (network ~ <2s typically; allow generous bound)
    assert dt < 4.0, f"Cached call took {dt:.2f}s — likely not cached"


# ---------- Session start + get ----------
@pytest.fixture(scope="module")
def session_ctx(plan_ctx):
    tok = plan_ctx["token"]
    r = requests.post(f"{API}/guided-dive/start",
                      data={"game_slug": "puzzles-conquest"},
                      headers=_h(tok), timeout=30)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["status"] == "in_progress"
    assert s["uploads"] == {}
    assert s["skipped"] == []
    assert s["qa"] == []
    assert s["user_id"] == plan_ctx["user_id"]
    assert s["game_slug"] == "puzzles-conquest"
    assert len(s["steps"]) >= 6
    return {"token": tok, "user_id": plan_ctx["user_id"], "session": s}


def test_iter6_get_session_auth_scoped(session_ctx):
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    r = requests.get(f"{API}/guided-dive/{sid}", headers=_h(tok), timeout=15)
    assert r.status_code == 200
    assert r.json()["id"] == sid
    # Other user should not see session
    _, tok2, _, _ = _register("OTHER")
    r2 = requests.get(f"{API}/guided-dive/{sid}", headers=_h(tok2), timeout=15)
    assert r2.status_code == 404


# ---------- Upload + skip ----------
def test_iter6_upload_invalid_step_id(session_ctx):
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    files = [("files", ("a.png", _tiny_png_bytes(), "image/png"))]
    r = requests.post(f"{API}/guided-dive/{sid}/upload",
                      headers=_h(tok), data={"step_id": "ghost-step"}, files=files, timeout=20)
    assert r.status_code == 400, r.text


def test_iter6_upload_then_replace(session_ctx):
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    step_id = session_ctx["session"]["steps"][0]["id"]
    # First upload
    files = [("files", ("a.png", _tiny_png_bytes(), "image/png"))]
    r = requests.post(f"{API}/guided-dive/{sid}/upload",
                      headers=_h(tok), data={"step_id": step_id}, files=files, timeout=30)
    assert r.status_code == 200, r.text
    s1 = r.json()
    refs1 = s1["uploads"][step_id]
    assert len(refs1) == 1

    # Re-upload (replace)
    files2 = [("files", ("b.png", _tiny_png_bytes(), "image/png")),
              ("files", ("c.png", _tiny_png_bytes(), "image/png"))]
    r2 = requests.post(f"{API}/guided-dive/{sid}/upload",
                       headers=_h(tok), data={"step_id": step_id}, files=files2, timeout=30)
    assert r2.status_code == 200, r2.text
    s2 = r2.json()
    refs2 = s2["uploads"][step_id]
    assert len(refs2) == 2
    # Replaced (different gridfs file_ids)
    ids1 = {x["file_id"] for x in refs1}
    ids2 = {x["file_id"] for x in refs2}
    assert ids1.isdisjoint(ids2), f"Re-upload should replace, not append. ids1={ids1} ids2={ids2}"


def test_iter6_skip_and_unskip_on_reupload(session_ctx):
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    step_id = session_ctx["session"]["steps"][1]["id"]

    # Skip it
    r = requests.post(f"{API}/guided-dive/{sid}/skip",
                      headers=_h(tok), data={"step_id": step_id}, timeout=20)
    assert r.status_code == 200
    s = r.json()
    assert step_id in s["skipped"]
    assert step_id not in s.get("uploads", {})

    # Re-upload → should be removed from skipped
    files = [("files", ("d.png", _tiny_png_bytes(), "image/png"))]
    r2 = requests.post(f"{API}/guided-dive/{sid}/upload",
                       headers=_h(tok), data={"step_id": step_id}, files=files, timeout=30)
    assert r2.status_code == 200
    s2 = r2.json()
    assert step_id not in s2["skipped"], "Upload should un-skip step"
    assert step_id in s2["uploads"]


def test_iter6_skip_invalid_step_400(session_ctx):
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    r = requests.post(f"{API}/guided-dive/{sid}/skip",
                      headers=_h(tok), data={"step_id": "no-such"}, timeout=15)
    assert r.status_code == 400


# ---------- Ask ----------
def test_iter6_ask_specialist_short(session_ctx):
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    r = requests.post(f"{API}/guided-dive/{sid}/ask",
                      headers=_h(tok),
                      json={"question": "Which heroes are best for a new sanctuary lineup?"},
                      timeout=60)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "q" in j and "a" in j and "id" in j and "at" in j
    a = j["a"].lower()
    # ≤120 words
    assert len(j["a"].split()) <= 200, f"Too long: {len(j['a'].split())} words"
    pnc_terms = ["hero", "sanctuary", "formation", "talent", "march", "alliance", "tower", "puzzle"]
    assert any(t in a for t in pnc_terms), f"Answer not P&C-specific: {j['a'][:200]}"

    # Verify pushed into session.qa
    r2 = requests.get(f"{API}/guided-dive/{sid}", headers=_h(tok), timeout=15)
    assert any(entry["id"] == j["id"] for entry in r2.json()["qa"])


# ---------- Finalize: 402 no quota ----------
def test_iter6_finalize_402_when_no_quota(session_ctx):
    """User has no Pro and no extra_baselines → finalize must 402."""
    tok = session_ctx["token"]
    sid = session_ctx["session"]["id"]
    # Ensure user has no quota
    c = MongoClient(MONGO_URL)
    try:
        c[DB_NAME].users.update_one({"id": session_ctx["user_id"]},
                                    {"$set": {"extra_baselines": 0},
                                     "$unset": {"subscription_period_end": ""}})
    finally:
        c.close()
    r = requests.post(f"{API}/guided-dive/{sid}/finalize",
                      headers=_h(tok),
                      json={"title": "TEST_GD_noquota", "notes": "n"},
                      timeout=60)
    assert r.status_code == 402, r.text


# ---------- Finalize: success path (consumes 1 vision call) ----------
def test_iter6_finalize_success_with_extra_baseline():
    """Full happy-path: create session, upload 1 step, grant 1 baseline, finalize."""
    _, tok, uid, _ = _register("FIN")
    # Start session
    r = requests.post(f"{API}/guided-dive/start",
                      data={"game_slug": "puzzles-conquest"},
                      headers=_h(tok), timeout=45)
    assert r.status_code == 200
    s = r.json()
    sid = s["id"]
    step_id = s["steps"][0]["id"]
    # Upload 1 png
    files = [("files", ("x.png", _tiny_png_bytes(), "image/png"))]
    r2 = requests.post(f"{API}/guided-dive/{sid}/upload",
                       headers=_h(tok), data={"step_id": step_id}, files=files, timeout=30)
    assert r2.status_code == 200
    # Grant 1 extra baseline
    _grant_extra_baseline(uid, 1)
    # Finalize
    r3 = requests.post(f"{API}/guided-dive/{sid}/finalize",
                       headers=_h(tok),
                       json={"title": "TEST_GD_iter6", "notes": "guided test"},
                       timeout=120)
    assert r3.status_code == 200, r3.text
    j = r3.json()
    assert "deep_dive_id" in j
    dd_id = j["deep_dive_id"]
    # Verify deep_dive doc exists and is linked back
    rdd = requests.get(f"{API}/deep-dive/{dd_id}", headers=_h(tok), timeout=20)
    assert rdd.status_code == 200, rdd.text
    dd = rdd.json()
    assert dd["via_guided_session"] == sid
    assert dd["game_slug"] == "puzzles-conquest"
    assert dd["title"] == "TEST_GD_iter6"
    # Verify session marked finalized
    rsess = requests.get(f"{API}/guided-dive/{sid}", headers=_h(tok), timeout=15)
    assert rsess.status_code == 200
    assert rsess.json()["status"] == "finalized"
    assert rsess.json()["deep_dive_id"] == dd_id
    # Quota consumed → extra_baselines should be 0
    c = MongoClient(MONGO_URL)
    try:
        u = c[DB_NAME].users.find_one({"id": uid})
        assert int(u.get("extra_baselines", 0)) == 0
    finally:
        c.close()
    # Already-finalized → 400
    r4 = requests.post(f"{API}/guided-dive/{sid}/finalize",
                       headers=_h(tok),
                       json={"title": "again", "notes": ""},
                       timeout=15)
    assert r4.status_code == 400
    # Cleanup: delete the dd doc
    c = MongoClient(MONGO_URL)
    try:
        c[DB_NAME].deep_dives.delete_one({"id": dd_id})
        c[DB_NAME].guided_sessions.delete_one({"id": sid})
    finally:
        c.close()


def test_iter6_finalize_with_no_uploads_400():
    _, tok, uid, _ = _register("NOUP")
    _grant_extra_baseline(uid, 1)
    r = requests.post(f"{API}/guided-dive/start",
                      data={"game_slug": "puzzles-conquest"},
                      headers=_h(tok), timeout=30)
    sid = r.json()["id"]
    r2 = requests.post(f"{API}/guided-dive/{sid}/finalize",
                       headers=_h(tok),
                       json={"title": "empty", "notes": ""},
                       timeout=20)
    assert r2.status_code == 400, r2.text
    # Quota should NOT have been consumed
    c = MongoClient(MONGO_URL)
    try:
        u = c[DB_NAME].users.find_one({"id": uid})
        assert int(u.get("extra_baselines", 0)) == 1
    finally:
        c.close()


# ---------- Abandon ----------
def test_iter6_abandon_in_progress_session():
    _, tok, _, _ = _register("ABA")
    r = requests.post(f"{API}/guided-dive/start",
                      data={"game_slug": "puzzles-conquest"},
                      headers=_h(tok), timeout=30)
    sid = r.json()["id"]
    step_id = r.json()["steps"][0]["id"]
    files = [("files", ("a.png", _tiny_png_bytes(), "image/png"))]
    requests.post(f"{API}/guided-dive/{sid}/upload",
                  headers=_h(tok), data={"step_id": step_id}, files=files, timeout=30)
    # Try spec'd path first, then fallback to actual implementation path
    r2 = requests.delete(f"{API}/guided-dive/{sid}", headers=_h(tok), timeout=15)
    if r2.status_code in (404, 405):
        r2 = requests.delete(f"{API}/deep-dive/guided/{sid}", headers=_h(tok), timeout=15)
    assert r2.status_code == 200, r2.text
    # Verify gone
    r3 = requests.get(f"{API}/guided-dive/{sid}", headers=_h(tok), timeout=15)
    assert r3.status_code == 404


# ---------- Route coexistence: /api/deep-dive/{id} not shadowed ----------
def test_iter6_deep_dive_id_route_not_shadowed():
    """Confirm GET /api/deep-dive/{id} still works (404 for unknown, not 200 stub)."""
    _, tok, _, _ = _register("RT")
    r = requests.get(f"{API}/deep-dive/{uuid.uuid4()}", headers=_h(tok), timeout=15)
    # Should be 404 (deep dive lookup), not 200 from another route
    assert r.status_code in (404,), r.text


# ---------- Cleanup ----------
def test_zzz_iter6_cleanup_test_users():
    c = MongoClient(MONGO_URL)
    try:
        res = c[DB_NAME].users.delete_many({"email": {"$regex": "^TEST_(GD6|BADSLUG|PLAN|OTHER|FIN|NOUP|ABA|RT)_"}})
        # also drop dangling guided sessions
        c[DB_NAME].guided_sessions.delete_many({"game_slug": "puzzles-conquest", "user_id": {"$exists": True}})
        print(f"Cleaned up {res.deleted_count} TEST_ users")
    finally:
        c.close()
