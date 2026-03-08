"""
Flask application — API Gateway for the role-based chatbot system.

Endpoints:
  POST  /api/login    — authenticate with phone number → JWT
  GET   /api/verify   — validate a stored JWT
  POST  /api/chat     — send a message, get role-scoped response
  GET   /api/history  — fetch current user's conversation history
  GET   /api/audit    — last 50 audit entries (requires auth)
  GET   /api/status   — health check (public)
"""
import os
import sys
import datetime
import functools
import pandas as pd
import jwt as pyjwt

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS

# Make sure chatbot package is importable when run as `python chatbot/app.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config  import cfg
from agents  import BuyerAgent, PartnerAgent, VisitorAgent, FallbackAgent
from audit   import AuditLogger
from history import ConversationHistory


# ── App & extensions ───────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

audit_logger = AuditLogger(cfg.AUDIT_LOG)
conv_history = ConversationHistory(max_messages=cfg.HISTORY_MAX_MESSAGES)


# ── ChatbotRouter ──────────────────────────────────────────────────────────────

class ChatbotRouter:
    """JWT-based deterministic router — main orchestration layer."""

    def __init__(self):
        print("🔄 Initialising agents...")
        self.agents = {
            "BUYER":           BuyerAgent(),
            "CHANNEL_PARTNER": PartnerAgent(),
            "SITE_VISIT":      VisitorAgent(),
            "UNKNOWN":         FallbackAgent(),
        }
        print("✅ All agents ready.")

    # ── JWT helpers ────────────────────────────────────────────────────────────

    def generate_jwt(self, user_id: str, role: str) -> str:
        payload = {
            "user_id": user_id,
            "role":    role,
            "exp":     datetime.datetime.now(datetime.timezone.utc)
                       + datetime.timedelta(hours=cfg.JWT_EXPIRY_HOURS),
        }
        return pyjwt.encode(payload, cfg.SECRET_KEY, algorithm=cfg.JWT_ALGORITHM)

    def verify_jwt(self, token: str) -> dict:
        """Returns decoded payload or raises pyjwt.InvalidTokenError."""
        return pyjwt.decode(token, cfg.SECRET_KEY, algorithms=[cfg.JWT_ALGORITHM])

    # ── Core routing ───────────────────────────────────────────────────────────

    def route(self, payload: dict, query: str) -> dict:
        role    = payload.get("role",    "UNKNOWN")
        user_id = payload.get("user_id", "anonymous")

        agent    = self.agents.get(role, self.agents["UNKNOWN"])
        response = agent.respond(query)

        guardrail = (
            "cannot provide that information" in response.lower()
            or "i apologize, but i cannot"   in response.lower()
        )

        audit_logger.log(user_id, role, query, response, guardrail)
        conv_history.add(user_id, role, query, response)

        return {
            "response":           response,
            "role":               role,
            "guardrail_triggered": guardrail,
            "interaction_id":     audit_logger.total,
        }


# ── Singleton router (initialised once at startup) ─────────────────────────────

router = ChatbotRouter()


# ── User database ──────────────────────────────────────────────────────────────

def load_user_database() -> dict:
    try:
        df = pd.read_csv(cfg.LEADS_CSV)
        db = {
            str(row["Phone Number"]): {"name": row["Name"], "role": row["Role"]}
            for _, row in df.iterrows()
        }
        print(f"✅ User DB loaded: {len(db)} users.")
        return db
    except FileNotFoundError:
        print("⚠️  classified_leads.csv not found. Run classify_leads.py first.")
        return {}


users_db = load_user_database()


# ── Auth helper & decorator ────────────────────────────────────────────────────

def _extract_token() -> str:
    """Pull Bearer token from the Authorization header."""
    header = request.headers.get("Authorization", "")
    return header.removeprefix("Bearer ").strip()


def require_auth(f):
    """
    Decorator that validates the JWT and stores the decoded payload in `g.user`.
    Returns 401 JSON on missing / invalid / expired tokens.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authorization header missing or malformed"}), 401
        try:
            g.user = router.verify_jwt(token)
        except pyjwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except pyjwt.InvalidTokenError as exc:
            return jsonify({"error": f"Invalid token: {exc}"}), 401
        return f(*args, **kwargs)
    return wrapper


# ── Global error handlers ──────────────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "detail": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.route("/api/login", methods=["POST"])
def login():
    """
    Authenticate a user by phone number.
    Body: { "phone": "7564209312" }
    Returns: { "token": "...", "name": "...", "role": "..." }
    """
    data  = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()

    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    user = users_db.get(phone)
    if not user:
        return jsonify({"error": "User not found. Check your phone number and try again."}), 401

    token = router.generate_jwt(phone, user["role"])
    return jsonify({"token": token, "name": user["name"], "role": user["role"]})


@app.route("/api/verify", methods=["GET"])
@require_auth
def verify():
    """
    Verify that the current JWT is valid and return its claims.
    Used by the frontend on page load to decide whether to skip the login screen.
    """
    return jsonify({
        "valid":   True,
        "user_id": g.user.get("user_id"),
        "role":    g.user.get("role"),
    })


@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    """
    Send a query. The role is read from the verified JWT — no client-supplied role.
    Body: { "query": "What is the price?" }
    Returns: { "response": "...", "role": "...", "guardrail_triggered": bool, "interaction_id": int }
    """
    data  = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400
    if len(query) > 1000:
        return jsonify({"error": "Query too long (max 1000 characters)"}), 400

    result = router.route(g.user, query)
    return jsonify(result)


@app.route("/api/history", methods=["GET"])
@require_auth
def history():
    """
    Return the conversation history for the authenticated user.
    Returns: { "user_id": "...", "messages": [...], "count": int }
    """
    user_id  = g.user.get("user_id", "anonymous")
    messages = conv_history.get(user_id)
    return jsonify({"user_id": user_id, "messages": messages, "count": len(messages)})


@app.route("/api/history", methods=["DELETE"])
@require_auth
def clear_history():
    """Clear the conversation history for the authenticated user."""
    user_id = g.user.get("user_id", "anonymous")
    conv_history.clear(user_id)
    return jsonify({"message": "History cleared."})


@app.route("/api/audit", methods=["GET"])
@require_auth
def audit():
    """
    Return the last 50 audit log entries.
    Persisted to data/audit_log.jsonl — survives server restarts.
    """
    n = min(int(request.args.get("limit", 50)), 200)
    return jsonify({"total": audit_logger.total, "log": audit_logger.get_recent(n)})


@app.route("/api/status", methods=["GET"])
def status():
    """Public health check endpoint."""
    return jsonify({
        "status":          "online",
        "users_loaded":    len(users_db),
        "roles":           list(router.agents.keys()),
        "total_interactions": audit_logger.total,
        "active_sessions": conv_history.user_count(),
    })


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(cfg.DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)
    print(f"🚀 Starting Flask Server → http://localhost:{cfg.PORT}")
    app.run(debug=cfg.DEBUG, port=cfg.PORT)
