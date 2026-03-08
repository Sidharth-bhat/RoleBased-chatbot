"""
chatbot/api.py — kept for future use as a Flask Blueprint.

Currently all routes live in app.py for simplicity.  When the API grows,
move routes here and register with:

    from chatbot.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
"""
from flask import Blueprint

api_bp = Blueprint("api", __name__)

# Routes will be migrated here as the project scales.
