"""
Centralised configuration — all settings come from environment variables
with safe development defaults. Import `cfg` anywhere in the app.
"""
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHATBOT_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("CHATBOT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR: str    = os.path.join(_BASE_DIR, "data")
    LEADS_CSV: str   = os.path.join(DATA_DIR, "classified_leads.csv")
    AUDIT_LOG: str   = os.path.join(DATA_DIR, "audit_log.jsonl")
    KB_DIR: str      = os.path.join(_CHATBOT_DIR, "knowledge_bases")

    # ── Agent settings ────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str    = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    KB_MIN_SCORE: float     = float(os.getenv("KB_MIN_SCORE", "0.25"))
    KB_TOP_K: int           = int(os.getenv("KB_TOP_K", "3"))

    # ── History settings ──────────────────────────────────────────────────────
    HISTORY_MAX_MESSAGES: int = int(os.getenv("HISTORY_MAX_MESSAGES", "50"))

    # ── Server ────────────────────────────────────────────────────────────────
    DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    PORT: int   = int(os.getenv("PORT", "5000"))


# Singleton instance — `from config import cfg`
cfg = Config()
