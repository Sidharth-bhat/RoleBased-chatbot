import json
import sys
import os
import pytest

# ── Ensure project root is in path so `from chatbot.xxx import ...` works ──────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
# Also add chatbot/ so bare imports inside app.py (from config, from agents…) work
sys.path.insert(0, os.path.join(PROJECT_ROOT, "chatbot"))
os.chdir(PROJECT_ROOT)  # ensure relative paths in config resolve

from chatbot.app import app, users_db, router, audit_logger


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def get_token(client, phone: str) -> str:
    """Helper: login and return JWT."""
    resp = client.post(
        "/api/login",
        json={"phone": phone},
        content_type="application/json",
    )
    assert resp.status_code == 200, f"Login failed for {phone}: {resp.get_data(as_text=True)}"
    return resp.get_json()["token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Login ──────────────────────────────────────────────────────────────────────

def test_login_valid_buyer(client):
    resp = client.post("/api/login", json={"phone": "7564209312"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data
    assert data["role"] == "BUYER"


def test_login_valid_partner(client):
    resp = client.post("/api/login", json={"phone": "9105578047"})
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "CHANNEL_PARTNER"


def test_login_valid_visitor(client):
    resp = client.post("/api/login", json={"phone": "6941460145"})
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "SITE_VISIT"


def test_login_unknown_user(client):
    resp = client.post("/api/login", json={"phone": "6682751893"})
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "UNKNOWN"


def test_login_missing_phone(client):
    resp = client.post("/api/login", json={})
    assert resp.status_code == 400


def test_login_invalid_phone(client):
    resp = client.post("/api/login", json={"phone": "0000000000"})
    assert resp.status_code == 401


# ── Token verification ─────────────────────────────────────────────────────────

def test_verify_valid_token(client):
    token = get_token(client, "7564209312")
    resp  = client.get("/api/verify", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["valid"] is True


def test_verify_invalid_token(client):
    resp = client.get("/api/verify", headers={"Authorization": "Bearer not.a.token"})
    assert resp.status_code == 401


def test_verify_missing_header(client):
    resp = client.get("/api/verify")
    assert resp.status_code == 401


# ── Buyer agent ────────────────────────────────────────────────────────────────

def test_buyer_allowed_price_query(client):
    token = get_token(client, "7564209312")
    resp  = client.post("/api/chat", json={"query": "What is the price?"}, headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["guardrail_triggered"] is False
    assert data["role"] == "BUYER"
    assert len(data["response"]) > 0


def test_buyer_blocked_commission(client):
    token = get_token(client, "7564209312")
    resp  = client.post("/api/chat", json={"query": "What is the commission rate?"}, headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["guardrail_triggered"] is True


def test_buyer_blocked_referral(client):
    token = get_token(client, "7564209312")
    resp  = client.post("/api/chat", json={"query": "Tell me about referral incentives"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["guardrail_triggered"] is True


# ── Partner agent ──────────────────────────────────────────────────────────────

def test_partner_allowed_commission(client):
    token = get_token(client, "9105578047")
    resp  = client.post("/api/chat", json={"query": "What is my commission structure?"}, headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["guardrail_triggered"] is False
    assert data["role"] == "CHANNEL_PARTNER"


def test_partner_blocked_pricing(client):
    token = get_token(client, "9105578047")
    resp  = client.post("/api/chat", json={"query": "What is the apartment price?"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["guardrail_triggered"] is True


def test_partner_blocked_emi(client):
    token = get_token(client, "9105578047")
    resp  = client.post("/api/chat", json={"query": "Tell me about EMI options"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["guardrail_triggered"] is True


# ── Visitor agent ──────────────────────────────────────────────────────────────

def test_visitor_allowed_location(client):
    token = get_token(client, "6941460145")
    resp  = client.post("/api/chat", json={"query": "Where is the project located?"}, headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["guardrail_triggered"] is False
    assert data["role"] == "SITE_VISIT"


def test_visitor_blocked_commission(client):
    token = get_token(client, "6941460145")
    resp  = client.post("/api/chat", json={"query": "What is the commission?"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["guardrail_triggered"] is True


# ── Fallback agent ─────────────────────────────────────────────────────────────

def test_unknown_fallback_response(client):
    token = get_token(client, "6682751893")
    resp  = client.post("/api/chat", json={"query": "I need help"}, headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "UNKNOWN"
    assert "BUY" in data["response"] or "CHANNEL PARTNER" in data["response"]


# ── Input validation ───────────────────────────────────────────────────────────

def test_chat_empty_query(client):
    token = get_token(client, "7564209312")
    resp  = client.post("/api/chat", json={"query": ""}, headers=auth_headers(token))
    assert resp.status_code == 400


def test_chat_no_auth(client):
    resp = client.post("/api/chat", json={"query": "What is the price?"})
    assert resp.status_code == 401


def test_chat_query_too_long(client):
    token = get_token(client, "7564209312")
    resp  = client.post("/api/chat", json={"query": "x" * 1001}, headers=auth_headers(token))
    assert resp.status_code == 400


# ── History ────────────────────────────────────────────────────────────────────

def test_history_grows_with_messages(client):
    token = get_token(client, "7564209312")
    client.post("/api/chat", json={"query": "What is the price?"}, headers=auth_headers(token))
    resp = client.get("/api/history", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] >= 2   # at least one user + one assistant turn


def test_history_clear(client):
    token = get_token(client, "7564209312")
    client.delete("/api/history", headers=auth_headers(token))
    resp  = client.get("/api/history", headers=auth_headers(token))
    assert resp.get_json()["count"] == 0


# ── Audit ──────────────────────────────────────────────────────────────────────

def test_audit_log_grows(client):
    token    = get_token(client, "7564209312")
    before   = audit_logger.total
    client.post("/api/chat", json={"query": "EMI options?"}, headers=auth_headers(token))
    assert audit_logger.total == before + 1


def test_audit_endpoint_requires_auth(client):
    resp = client.get("/api/audit")
    assert resp.status_code == 401


def test_audit_endpoint_returns_log(client):
    token = get_token(client, "7564209312")
    resp  = client.get("/api/audit", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total" in data and "log" in data


# ── Status (public) ────────────────────────────────────────────────────────────

def test_status_endpoint(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "online"
    assert data["users_loaded"] > 0


# ── Error handlers ─────────────────────────────────────────────────────────────

def test_404_returns_json(client):
    resp = client.get("/api/nonexistent")
    assert resp.status_code == 404
    assert resp.get_json().get("error") is not None


def test_405_returns_json(client):
    resp = client.get("/api/login")   # login only accepts POST
    assert resp.status_code == 405
    assert resp.get_json().get("error") is not None
