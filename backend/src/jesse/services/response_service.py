from __future__ import annotations

from typing import Any

from ..core.client_loader import ClientContext


def _normalize_messages(node: dict) -> list[dict[str, Any]]:
    """
    Support 2 format:
    Format lama:
      { "reply": "text", "buttons": [...] }

    Format baru:
      { "messages": [ {type:"text", text:"..."}, {type:"image", url:"..."} ], "buttons": [...] }
    """
    msgs = node.get("messages")
    if isinstance(msgs, list):
        return msgs

    reply = node.get("reply", "")
    if reply:
        return [{"type": "text", "text": reply}]
    return []


def get_greeting(ctx: ClientContext) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node = ctx.responses.get("greeting", {})
    messages = _normalize_messages(node)
    buttons = node.get("buttons", [])
    return messages, buttons


def get_intent_response(
    ctx: ClientContext, intent: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    intents = ctx.responses.get("intents", {})
    node = intents.get(intent)

    if not node:
        node = intents.get("fallback", {"reply": "Sorry, I didn't get that.", "buttons": []})

    messages = _normalize_messages(node)
    buttons = node.get("buttons", [])
    return messages, buttons