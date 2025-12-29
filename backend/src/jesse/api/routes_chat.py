from __future__ import annotations

from typing import Union, Dict, Any, Tuple
from flask import Blueprint, current_app, jsonify, request, Response
from pydantic import ValidationError

from ..core.client_loader import load_client
from ..core.errors import JesseError
from ..core.security import require_api_key
from ..models.schemas import ChatRequest, ChatResponse, Message
from ..services.analytics_service import AnalyticsService
from ..services.hybrid_service import HybridService
from ..services.llm_service import LLMService
from ..services.response_service import get_greeting

bp = Blueprint("chat_api", __name__, url_prefix="/api")

def _client_id_from_request(data: Union[Dict[str, Any], None]) -> str:
    """Extract client_id from query params, headers, or JSON body."""
    cid = request.args.get("client_id") or request.headers.get("X-Client-Id")
    if cid:
        return str(cid)
    
    if data and isinstance(data, dict) and data.get("client_id"):
        return str(data["client_id"])
        
    raise JesseError("Missing client_id. Please provide it in Query Params, Headers, or Body.", 400)

def _first_text(messages: list[dict]) -> str:
    """Helper to extract the main text reply from a list of messages."""
    for m in messages:
        if m.get("type") == "text" and m.get("text"):
            return str(m["text"])
    return ""

@bp.get("/health")
def health() -> Response:
    """Simple health check endpoint."""
    return jsonify({"status": "ok", "service": "jesse-backend"})

# --- Greeting Detection Logic ---
import re
# Updated regex to handle "hey there", "hi!!", etc.
GREETING_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|yo|sup|greetings|howdy|what'?s\s*up)(\s+(there|all|buddy|mate))?[.!]*\s*$",
    re.IGNORECASE
)

def _is_greeting(text: str) -> bool:
    if not text:
        return False
    return bool(GREETING_PATTERN.match(text))
# --------------------------------

@bp.get("/greeting")
def greeting() -> Tuple[Response, int]:
    """Get the initial greeting for a specific client configuration."""
    try:
        settings = current_app.config["SETTINGS"]
        require_api_key(settings.global_api_key)

        client_id = _client_id_from_request(None)
        ctx = load_client(settings.clients_dir, client_id)

        messages, buttons = get_greeting(ctx)
        reply = _first_text(messages)

        response_data = {
            "reply": reply,
            "messages": messages,
            "buttons": buttons,
            "theme": ctx.theme or {},
            "plan_type": getattr(ctx, 'plan_type', 'basic'),
            "meta": {"client": ctx.name},
        }
        
        current_app.logger.info(f"Greeting served for client: {client_id}")
        return jsonify(response_data), 200

    except JesseError as e:
        current_app.logger.warning(f"JesseError in /greeting: {e}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in /greeting: {e}")
        return jsonify({"error": "Internal server error"}), 500

@bp.post("/chat")
def chat() -> Tuple[Response, int]:
    """Handle chat messages, including hybrid logic (RexEx -> Fuzzy -> LLM)."""
    try:
        settings = current_app.config["SETTINGS"]
        require_api_key(settings.global_api_key)

        data = request.get_json(silent=True) or {}

        try:
            client_id = _client_id_from_request(data)
            parsed = ChatRequest(
                client_id=client_id,
                message=data.get("message"),
                intent=data.get("intent"),
                user_id=data.get("user_id"),
            )
        except ValidationError as e:
            # Pydantic error formatting
            error_msg = e.errors()[0]["msg"]
            raise JesseError(f"Validation Error: {error_msg}", 400)

        # Validate logic
        if not parsed.message and not parsed.intent:
            raise JesseError("Either 'message' or 'intent' is required.", 400)

        # --- GREETING INTERCEPTION ---
        # If user types a greeting, use special LLM intent to skip search/static response
        if parsed.message and not parsed.intent:
            if _is_greeting(parsed.message):
                 parsed.intent = "llm_greeting"
        # -----------------------------

        # Load Context
        ctx = load_client(settings.clients_dir, parsed.client_id)

        # Rate Limiting
        limiter = current_app.config["RATE_LIMITER"]
        user_key = f"{request.remote_addr}:{ctx.id}"
        limiter.check(user_key)

        # Services Init
        llm = LLMService(settings)
        hybrid = HybridService(llm)
        analytics = AnalyticsService()

        # Execute Logic
        messages, buttons = hybrid.handle(ctx, parsed.message, parsed.intent)
        reply = _first_text(messages)

        # Analytics Tracking
        analytics_enabled = ctx.client_json.get("features", {}).get("analytics_enabled", True)
        if analytics_enabled:
            analytics.track(
                ctx,
                parsed.user_id or request.remote_addr,
                "chat",
                {"message": parsed.message, "intent": parsed.intent, "reply": reply},
            )

        # Validation of Output
        try:
            msg_models = [Message(**m) for m in messages]
        except Exception as e:
            current_app.logger.error(f"Message format error: {e}")
            # Fallback to prevent crash, but log it
            msg_models = []

        resp = ChatResponse(
            reply=reply,
            messages=msg_models,
            buttons=buttons,
            meta={"client": ctx.name},
        )
        
        current_app.logger.info(f"Chat handled for {client_id}. Reply len: {len(reply)}")
        return jsonify(resp.model_dump()), 200

    except JesseError as e:
        current_app.logger.warning(f"JesseError in /chat: {e}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in /chat: {e}")
        return jsonify({"error": "Internal server error"}), 500