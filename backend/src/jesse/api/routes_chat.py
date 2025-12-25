from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
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

def _client_id_from_request(data: dict | None) -> str:
    cid = request.args.get("client_id") or request.headers.get("X-Client-Id")
    if cid:
        return cid
    if data and data.get("client_id"):
        return data["client_id"]
    raise JesseError("client_id is required", 400)

def _first_text(messages: list[dict]) -> str:
    for m in messages:
        if m.get("type") == "text" and m.get("text"):
            return str(m["text"])
    return ""

@bp.get("/health")
def health():
    return jsonify({"status": "ok"})

@bp.get("/greeting")
def greeting():
    try:
        settings = current_app.config["SETTINGS"]
        require_api_key(settings.global_api_key)

        client_id = _client_id_from_request(None)
        ctx = load_client(settings.clients_dir, client_id)

        messages, buttons = get_greeting(ctx)
        reply = _first_text(messages)

        response = {
            "reply": reply,            # kompatibilitas
            "messages": messages,      # format baru
            "buttons": buttons,
            "theme": ctx.theme or {},  # default empty dict jika None
            "plan_type": getattr(ctx, 'plan_type', 'basic'),  # default jika attribute error
            "meta": {"client": ctx.name},
        }
        current_app.logger.info(f"Greeting for client {client_id}: plan_type={response['plan_type']}")
        return jsonify(response)
    except JesseError as e:
        current_app.logger.error(f"JesseError in greeting: {e}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Unexpected error in greeting: {e}")
        return jsonify({"error": "Internal server error"}), 500

@bp.post("/chat")
def chat():
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
            raise JesseError(e.errors()[0]["msg"], 400)

        # wajib salah satu: message atau intent
        if not parsed.message and not parsed.intent:
            raise JesseError("message or intent is required", 400)

        ctx = load_client(settings.clients_dir, parsed.client_id)

        limiter = current_app.config["RATE_LIMITER"]
        limiter.check(f"{request.remote_addr}:{ctx.id}")

        llm = LLMService(settings)
        hybrid = HybridService(llm)
        analytics = AnalyticsService()

        messages, buttons = hybrid.handle(ctx, parsed.message, parsed.intent)
        reply = _first_text(messages)

        # analytics
        if ctx.client_json.get("features", {}).get("analytics_enabled", True):
            analytics.track(
                ctx,
                parsed.user_id or request.remote_addr,
                "chat",
                {"message": parsed.message, "intent": parsed.intent, "reply": reply},
            )

        # validate output via pydantic (biar format aman)
        try:
            msg_models = [Message(**m) for m in messages]
        except Exception as e:
            raise JesseError(f"Invalid message format: {e}", 500)

        resp = ChatResponse(
            reply=reply,
            messages=msg_models,
            buttons=buttons,
            meta={"client": ctx.name},
        )
        current_app.logger.info(f"Chat response for client {client_id}: {len(messages)} messages")
        return jsonify(resp.model_dump())
    except JesseError as e:
        current_app.logger.error(f"JesseError in chat: {e}")
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        current_app.logger.error(f"Unexpected error in chat: {e}")
        return jsonify({"error": "Internal server error"}), 500