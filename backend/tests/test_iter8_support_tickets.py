"""Iteration 8 backend tests: Customer Support tickets + FAQ + Admin dashboard.

Covers:
- POST /api/support/tickets (guest + authed, validation, rate-limit)
- GET /api/support/admin/check (admin vs non-admin)
- GET /api/support/admin/tickets (+ status_filter)
- POST /api/support/admin/tickets/{id}/reply
- PATCH /api/support/admin/tickets/{id}/status
- GET /api/support/tickets/{id} (owner / admin / forbidden / 404)
- GET /api/support/my-tickets
- Regression: scouts/earn/daily_login, billing/quota, billing/packages, games

NOTE: Gmail SMTP currently fails auth (BadCredentials). create_support_ticket
uses asyncio.create_task() for emails — API must still 200.

Run: pytest /app/backend/tests/test_iter8_support_tickets.py -v --tb=short
"""
import os
import time
import uuid

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

TEST_EMAIL = "test@tactician.gg"
TEST_PASSWORD = "strongpw1"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# ---------- shared fixtures ----------

@pytest.fixture(scope="module")
def mongo():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    yield db
    client.close()


@pytest.fixture(scope="module")
def admin_auth():
    """test@tactician.gg is in SUPPORT_ADMIN_EMAILS env var."""
    r = requests.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    return {
        "token": data["token"],
        "user_id": data["user"]["id"],
        "email": data["user"]["email"],
        "headers": {"Authorization": f"Bearer {data['token']}"},
    }


@pytest.fixture(scope="module")
def non_admin_auth():
    """Register a fresh user that is NOT in SUPPORT_ADMIN_EMAILS."""
    email = f"TEST_nonadmin_{uuid.uuid4().hex[:8]}@tactician.gg"
    username = f"NonAdmin{uuid.uuid4().hex[:6]}"
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "password": "strongpw1", "username": username},
        timeout=15,
    )
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    data = r.json()
    return {
        "token": data["token"],
        "user_id": data["user"]["id"],
        "email": email,
        "headers": {"Authorization": f"Bearer {data['token']}"},
    }


@pytest.fixture
def cleanup_tickets(mongo):
    """Track ticket ids created during a test and clean them up afterwards."""
    created_ids = []
    yield created_ids
    if created_ids:
        mongo.support_tickets.delete_many({"id": {"$in": created_ids}})


# ---------- 1. Public ticket creation ----------

def _make_ticket_body(email_suffix=None, **overrides):
    email = overrides.pop("email", None) or f"TEST_guest_{email_suffix or uuid.uuid4().hex[:8]}@tactician.gg"
    body = {
        "name": "Test Guest",
        "email": email,
        "category": "technical",
        "subject": "Cannot login to dashboard",
        "message": "I keep getting an error when trying to access the dashboard after login.",
    }
    body.update(overrides)
    return body


def test_create_ticket_guest_returns_200(cleanup_tickets, mongo):
    body = _make_ticket_body()
    r = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text}"
    data = r.json()
    assert "id" in data and isinstance(data["id"], str) and len(data["id"]) > 0
    assert data["status"] == "open"
    cleanup_tickets.append(data["id"])

    # Verify persistence in DB
    row = mongo.support_tickets.find_one({"id": data["id"]})
    assert row is not None
    assert row["email"] == body["email"].lower()
    assert row["status"] == "open"
    assert row["user_id"] is None  # guest
    assert row["category"] == "technical"
    assert row["subject"] == body["subject"]
    assert row["message"] == body["message"]
    assert row["responses"] == []


def test_create_ticket_invalid_category_returns_400(cleanup_tickets):
    body = _make_ticket_body(category="invalid_value")
    r = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    assert r.status_code == 400, f"Expected 400 got {r.status_code}: {r.text}"


def test_create_ticket_short_message_returns_422(cleanup_tickets):
    body = _make_ticket_body(message="too shrt")  # < 10 chars
    r = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    assert r.status_code == 422, f"Expected 422 got {r.status_code}: {r.text}"


def test_create_ticket_authed_attaches_user_id(admin_auth, cleanup_tickets, mongo):
    body = _make_ticket_body(email=f"TEST_authed_{uuid.uuid4().hex[:8]}@tactician.gg")
    r = requests.post(f"{API}/support/tickets", json=body, headers=admin_auth["headers"], timeout=15)
    assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text}"
    tid = r.json()["id"]
    cleanup_tickets.append(tid)

    row = mongo.support_tickets.find_one({"id": tid})
    assert row is not None
    assert row["user_id"] == admin_auth["user_id"], f"Expected user_id={admin_auth['user_id']}, got {row.get('user_id')}"


def test_create_ticket_rate_limit_429(cleanup_tickets, mongo):
    """Submit 6 tickets with the same email; 6th must return 429.
    Pre-clean any prior tickets for this email to make test deterministic."""
    email = f"TEST_ratelimit_{uuid.uuid4().hex[:8]}@tactician.gg"
    # Defensive: ensure no leftovers from prior runs
    mongo.support_tickets.delete_many({"email": email.lower()})

    status_codes = []
    for i in range(6):
        body = _make_ticket_body(email=email, subject=f"Rate-limit test #{i}")
        r = requests.post(f"{API}/support/tickets", json=body, timeout=15)
        status_codes.append(r.status_code)
        if r.status_code == 200:
            cleanup_tickets.append(r.json()["id"])

    # First 5 should succeed (200), 6th should be rate-limited (429)
    assert status_codes[:5] == [200, 200, 200, 200, 200], f"First 5 unexpected: {status_codes}"
    assert status_codes[5] == 429, f"Expected 6th to be 429, got {status_codes[5]} (all: {status_codes})"


# ---------- 2. Admin check ----------

def test_admin_check_true_for_admin(admin_auth):
    r = requests.get(f"{API}/support/admin/check", headers=admin_auth["headers"], timeout=10)
    assert r.status_code == 200
    assert r.json() == {"is_admin": True}


def test_admin_check_false_for_non_admin(non_admin_auth):
    r = requests.get(f"{API}/support/admin/check", headers=non_admin_auth["headers"], timeout=10)
    assert r.status_code == 200
    assert r.json() == {"is_admin": False}


def test_admin_check_requires_auth():
    r = requests.get(f"{API}/support/admin/check", timeout=10)
    assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"


# ---------- 3. Admin list tickets ----------

def test_admin_list_tickets_returns_counts(admin_auth, cleanup_tickets):
    # Seed a ticket so list is non-empty
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    assert r0.status_code == 200
    cleanup_tickets.append(r0.json()["id"])

    r = requests.get(f"{API}/support/admin/tickets", headers=admin_auth["headers"], timeout=10)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    data = r.json()
    assert "tickets" in data and isinstance(data["tickets"], list)
    assert "counts" in data
    for k in ("open", "in_progress", "resolved"):
        assert k in data["counts"], f"counts missing {k}"
        assert isinstance(data["counts"][k], int)


def test_admin_list_tickets_status_filter_open(admin_auth, cleanup_tickets):
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    assert r0.status_code == 200
    cleanup_tickets.append(r0.json()["id"])

    r = requests.get(
        f"{API}/support/admin/tickets",
        headers=admin_auth["headers"],
        params={"status_filter": "open"},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    for t in data["tickets"]:
        assert t["status"] == "open", f"Expected only open tickets, got {t['status']}"


def test_admin_list_tickets_forbidden_for_non_admin(non_admin_auth):
    r = requests.get(f"{API}/support/admin/tickets", headers=non_admin_auth["headers"], timeout=10)
    assert r.status_code == 403, f"Expected 403 got {r.status_code}: {r.text}"


# ---------- 4. Admin reply ----------

def test_admin_reply_pushes_to_responses_and_sets_in_progress(admin_auth, cleanup_tickets, mongo):
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    reply_body = {"message": "Thanks, we are looking into this."}
    r = requests.post(
        f"{API}/support/admin/tickets/{tid}/reply",
        headers=admin_auth["headers"],
        json=reply_body,
        timeout=15,
    )
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    data = r.json()
    assert data["ticket_status"] == "in_progress"
    assert "id" in data

    # Verify persistence
    row = mongo.support_tickets.find_one({"id": tid})
    assert row["status"] == "in_progress"
    assert len(row["responses"]) == 1
    assert row["responses"][0]["from_admin"] is True
    assert row["responses"][0]["message"] == reply_body["message"]


def test_admin_reply_forbidden_for_non_admin(admin_auth, non_admin_auth, cleanup_tickets):
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    r = requests.post(
        f"{API}/support/admin/tickets/{tid}/reply",
        headers=non_admin_auth["headers"],
        json={"message": "should fail"},
        timeout=10,
    )
    assert r.status_code == 403


# ---------- 5. Admin status update ----------

def test_admin_status_update_resolved(admin_auth, cleanup_tickets, mongo):
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    r = requests.patch(
        f"{API}/support/admin/tickets/{tid}/status",
        headers=admin_auth["headers"],
        json={"status": "resolved"},
        timeout=10,
    )
    assert r.status_code == 200
    assert r.json() == {"id": tid, "status": "resolved"}

    row = mongo.support_tickets.find_one({"id": tid})
    assert row["status"] == "resolved"


def test_admin_status_update_invalid_returns_400(admin_auth, cleanup_tickets):
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    r = requests.patch(
        f"{API}/support/admin/tickets/{tid}/status",
        headers=admin_auth["headers"],
        json={"status": "garbage"},
        timeout=10,
    )
    assert r.status_code == 400


def test_admin_status_update_forbidden_for_non_admin(admin_auth, non_admin_auth, cleanup_tickets):
    body = _make_ticket_body()
    r0 = requests.post(f"{API}/support/tickets", json=body, timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    r = requests.patch(
        f"{API}/support/admin/tickets/{tid}/status",
        headers=non_admin_auth["headers"],
        json={"status": "resolved"},
        timeout=10,
    )
    assert r.status_code == 403


# ---------- 6. GET single ticket ----------

def test_get_ticket_owner_can_access(non_admin_auth, cleanup_tickets):
    # Create authed ticket as the non-admin user
    body = _make_ticket_body(email=non_admin_auth["email"])
    r0 = requests.post(f"{API}/support/tickets", json=body, headers=non_admin_auth["headers"], timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    r = requests.get(f"{API}/support/tickets/{tid}", headers=non_admin_auth["headers"], timeout=10)
    assert r.status_code == 200, f"Owner should access; got {r.status_code}: {r.text}"
    assert r.json()["id"] == tid


def test_get_ticket_admin_can_access(admin_auth, non_admin_auth, cleanup_tickets):
    # Ticket owned by non-admin
    body = _make_ticket_body(email=non_admin_auth["email"])
    r0 = requests.post(f"{API}/support/tickets", json=body, headers=non_admin_auth["headers"], timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    r = requests.get(f"{API}/support/tickets/{tid}", headers=admin_auth["headers"], timeout=10)
    assert r.status_code == 200


def test_get_ticket_forbidden_for_non_owner(admin_auth, non_admin_auth, cleanup_tickets):
    # Ticket owned by admin
    body = _make_ticket_body(email=admin_auth["email"])
    r0 = requests.post(f"{API}/support/tickets", json=body, headers=admin_auth["headers"], timeout=15)
    tid = r0.json()["id"]
    cleanup_tickets.append(tid)

    # Non-admin (not the owner) tries to access -> 403
    r = requests.get(f"{API}/support/tickets/{tid}", headers=non_admin_auth["headers"], timeout=10)
    assert r.status_code == 403, f"Expected 403 got {r.status_code}: {r.text}"


def test_get_ticket_404_for_unknown_id(admin_auth):
    fake_id = str(uuid.uuid4())
    r = requests.get(f"{API}/support/tickets/{fake_id}", headers=admin_auth["headers"], timeout=10)
    assert r.status_code == 404


# ---------- 7. My tickets ----------

def test_my_tickets_returns_only_owned(non_admin_auth, admin_auth, cleanup_tickets):
    # Create one ticket as non-admin
    body_mine = _make_ticket_body(email=non_admin_auth["email"], subject="mine subject")
    r1 = requests.post(f"{API}/support/tickets", json=body_mine, headers=non_admin_auth["headers"], timeout=15)
    tid_mine = r1.json()["id"]
    cleanup_tickets.append(tid_mine)

    # Create one ticket as admin (different user)
    body_admin = _make_ticket_body(email=admin_auth["email"], subject="admin subject")
    r2 = requests.post(f"{API}/support/tickets", json=body_admin, headers=admin_auth["headers"], timeout=15)
    tid_admin = r2.json()["id"]
    cleanup_tickets.append(tid_admin)

    r = requests.get(f"{API}/support/my-tickets", headers=non_admin_auth["headers"], timeout=10)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    ids = [t["id"] for t in rows]
    assert tid_mine in ids
    assert tid_admin not in ids
    for t in rows:
        assert t["user_id"] == non_admin_auth["user_id"]


# ---------- 8. Regression: iter7 endpoints still work ----------

def test_regression_billing_quota_has_pro_game_slots(admin_auth):
    r = requests.get(f"{API}/billing/quota", headers=admin_auth["headers"], timeout=10)
    assert r.status_code == 200
    q = r.json()
    assert "pro_game_slots" in q
    assert isinstance(q["pro_game_slots"], int)


def test_regression_billing_packages_has_4(admin_auth):
    r = requests.get(f"{API}/billing/packages", timeout=10)
    assert r.status_code == 200
    pkgs = r.json()
    # Endpoint may return list or {packages:[...]}
    if isinstance(pkgs, dict) and "packages" in pkgs:
        pkgs = pkgs["packages"]
    assert isinstance(pkgs, list)
    assert len(pkgs) == 4, f"Expected 4 packages got {len(pkgs)}"


def test_regression_games_count_11():
    r = requests.get(f"{API}/games", timeout=10)
    assert r.status_code == 200
    games = r.json()
    if isinstance(games, dict) and "games" in games:
        games = games["games"]
    assert isinstance(games, list)
    assert len(games) == 11, f"Expected 11 games got {len(games)}"


def test_regression_scouts_daily_login(admin_auth, mongo):
    """Reset daily_login cap then call once — should 200."""
    # Reset earnings for daily_login so test is repeatable
    mongo.scout_earnings.delete_many({"user_id": admin_auth["user_id"], "kind": "daily_login"})
    r = requests.post(f"{API}/scouts/earn/daily_login", headers=admin_auth["headers"], timeout=10)
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
