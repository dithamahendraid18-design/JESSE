from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .config import load_settings
from .core.errors import register_error_handlers
from .core.logging import setup_logging
from .core.security import SimpleRateLimiter
from .api.routes_chat import bp as chat_bp
from .api.routes_admin import bp as admin_bp
from flask import send_from_directory
from .core.errors import JesseError

def create_app() -> Flask:
    """
    App factory (standar internasional):
    - gampang dites (pytest)
    - gampang untuk multi environment
    """
    load_dotenv()
    setup_logging()

    app = Flask(__name__)
    CORS(app)  # biar frontend dev server bisa akses /api

    settings = load_settings()
    app.config["SETTINGS"] = settings
    app.config["RATE_LIMITER"] = SimpleRateLimiter(settings.rate_limit_per_minute)
    
    @app.get("/client-assets/<client_id>/<path:filename>")
    def client_assets(client_id: str, filename: str):
        settings = app.config["SETTINGS"]
        public_dir = settings.clients_dir / client_id / "assets" / "public"
        if not public_dir.exists():
            raise JesseError("Asset folder not found", 404)
        
        resp = send_from_directory(public_dir, filename)

        if app.debug:
            resp.headers["Cache-Control"] = "no-store"
        else:
            # PROD: cache kuat, aman karena kita pakai version query (?v=2, ?v=3, dst)
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        return resp
    
    # routes
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)

    # error handlers
    register_error_handlers(app)

    return app
