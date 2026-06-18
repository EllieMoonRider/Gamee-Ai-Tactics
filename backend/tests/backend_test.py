"""Backend API tests for 37Games AI Strategy Assistant."""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://gamer-ai-tactics.preview.emergentagent.com"
API = f"{BASE_URL}/api"

TEST_EMAIL = "test@tactician.gg"
TEST_PASSWORD = "strongpw1"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=15)
    if r.status_code != 200:
        # Try register
        rr = requests.post(f"{API}/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "username": "CommanderOne"}, timeout=15)
        if rr.status_code == 200:
            return rr.json()["token"]
        pytest.skip(f"Cannot auth: login={r.status_code} register={rr.status_code}")
    return r.json()["token"]


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# --- Health ---
def test_root():
    r = requests.get(f"{API}/", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# --- Games ---
def test_list_games():
    r = requests.get(f"{API}/games", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 10
    slugs = [g["slug"] for g in data]
    assert "puzzles-conquest" in slugs


def test_get_game_by_slug():
    r = requests.get(f"{API}/games/puzzles-conquest", timeout=10)
    assert r.status_code == 200
    assert r.json()["slug"] == "puzzles-conquest"


def test_get_game_404():
    r = requests.get(f"{API}/games/does-not-exist", timeout=10)
    assert r.status_code == 404


# --- Auth ---
def test_register_new_user():
    email = f"TEST_{uuid.uuid4().hex[:8]}@tactician.gg"
    r = requests.post(f"{API}/auth/register", json={"email": email, "password": "abc12345", "username": "TestUser"}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "token" in body and isinstance(body["token"], str) and len(body["token"]) > 10
    assert body["user"]["email"] == email.lower()
    assert body["user"]["username"] == "TestUser"
    assert "id" in body["user"]


def test_login_wrong_password():
    r = requests.post(f"{API}/auth/login", json={"email": TEST_EMAIL, "password": "wrongpass!!"}, timeout=10)
    assert r.status_code == 401


def test_login_success_and_me(token):
    r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    assert r.status_code == 200
    assert r.json()["email"] == TEST_EMAIL


def test_me_without_token():
    r = requests.get(f"{API}/auth/me", timeout=10)
    assert r.status_code in (401, 403)


# --- Chat sessions ---
def test_chat_session_crud(auth_headers):
    # No auth
    no_auth = requests.get(f"{API}/chat/sessions", timeout=10)
    assert no_auth.status_code in (401, 403)

    # Create
    r = requests.post(f"{API}/chat/sessions", headers=auth_headers, json={"game_slug": "puzzles-conquest", "title": "TEST_session"}, timeout=10)
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    assert r.json()["game_slug"] == "puzzles-conquest"

    # List
    r2 = requests.get(f"{API}/chat/sessions", headers=auth_headers, timeout=10)
    assert r2.status_code == 200
    assert any(s["id"] == sid for s in r2.json())

    # Delete
    r3 = requests.delete(f"{API}/chat/sessions/{sid}", headers=auth_headers, timeout=10)
    assert r3.status_code == 200


def test_chat_session_invalid_slug(auth_headers):
    r = requests.post(f"{API}/chat/sessions", headers=auth_headers, json={"game_slug": "invalid-game"}, timeout=10)
    assert r.status_code == 400


# --- Streaming chat ---
def test_chat_streaming_and_persistence(auth_headers):
    # create
    r = requests.post(f"{API}/chat/sessions", headers=auth_headers, json={"game_slug": "puzzles-conquest"}, timeout=10)
    sid = r.json()["id"]
    try:
        with requests.post(f"{API}/chat/sessions/{sid}/messages", headers=auth_headers,
                           json={"content": "Give me 3 quick tips for new players."},
                           stream=True, timeout=60) as resp:
            assert resp.status_code == 200
            ct = resp.headers.get("content-type", "")
            assert "text/event-stream" in ct
            chunks = []
            saw_done = False
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload == "[DONE]":
                        saw_done = True
                        break
                    chunks.append(payload)
            assert saw_done, "Stream did not end with [DONE]"
            assert len(chunks) > 0, "No content chunks received"

        # verify persistence
        msgs = requests.get(f"{API}/chat/sessions/{sid}/messages", headers=auth_headers, timeout=10).json()
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "assistant" in roles
    finally:
        requests.delete(f"{API}/chat/sessions/{sid}", headers=auth_headers, timeout=10)


# --- Optimizer ---
def test_optimizer(auth_headers):
    r = requests.post(f"{API}/optimizer", headers=auth_headers,
                      json={"game_slug": "puzzles-conquest", "objective": "Beat KvK as F2P"},
                      timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "result" in body
    assert isinstance(body["result"], str) and len(body["result"]) > 20


# --- Builds ---
def test_builds_crud(auth_headers):
    r = requests.post(f"{API}/builds", headers=auth_headers,
                      json={"game_slug": "puzzles-conquest", "title": "TEST_build", "team": ["Athena", "Merlin"], "notes": "x"},
                      timeout=10)
    assert r.status_code == 200, r.text
    bid = r.json()["id"]
    lst = requests.get(f"{API}/builds", headers=auth_headers, timeout=10).json()
    assert any(b["id"] == bid for b in lst)
    d = requests.delete(f"{API}/builds/{bid}", headers=auth_headers, timeout=10)
    assert d.status_code == 200


# --- Guides ---
def test_guides_filter():
    r = requests.get(f"{API}/guides?game_slug=puzzles-conquest", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 3
    assert all(g["game_slug"] == "puzzles-conquest" for g in data)


def test_guides_all():
    r = requests.get(f"{API}/guides", timeout=10)
    assert r.status_code == 200
    assert len(r.json()) >= 13


# --- Tasks ---
def test_tasks_crud(auth_headers):
    c = requests.post(f"{API}/tasks", headers=auth_headers,
                     json={"game_slug": "puzzles-conquest", "title": "TEST_task", "priority": "high"},
                     timeout=10)
    assert c.status_code == 200, c.text
    tid = c.json()["id"]
    assert c.json()["completed"] is False

    lst = requests.get(f"{API}/tasks", headers=auth_headers, timeout=10).json()
    assert any(t["id"] == tid for t in lst)

    p = requests.patch(f"{API}/tasks/{tid}", headers=auth_headers, json={"completed": True}, timeout=10)
    assert p.status_code == 200
    assert p.json()["completed"] is True

    d = requests.delete(f"{API}/tasks/{tid}", headers=auth_headers, timeout=10)
    assert d.status_code == 200
