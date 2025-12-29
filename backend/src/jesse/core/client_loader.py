from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from flask import current_app

from .errors import JesseError
from ..orm import Client, Theme, Channel, Response, MenuCategory, MenuItem

@dataclass(frozen=True)
class ClientContext:
    """
    Immutable context object holding all configuration for a specific client.
    Now loaded from SQLite DB.
    """
    id: str
    name: str
    base_dir: Path
    client_json: Dict[str, Any]
    theme: Dict[str, Any]
    responses: Dict[str, Any]
    channels: Dict[str, Any]
    menu: Dict[str, Any]
    system_prompt: str
    plan_type: str

class SafeDict(dict):
    """
    Dictionary subclass that returns the key itself (wrapped in braces) 
    if the key is missing. Used for safe string interpolation.
    """
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render_text(text: str, data: Dict[str, Any]) -> str:
    """Substitute placeholders like {phone} with values from data."""
    return text.format_map(SafeDict(data))


def _render_messages(messages: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Recursively render placeholders in a list of message objects."""
    out = []
    for m in messages:
        if isinstance(m, dict) and m.get("type") == "text":
            # Only render text content
            rendered_text = _render_text(m.get("text", ""), data)
            out.append({**m, "text": rendered_text})
        else:
            out.append(m)
    return out


def hydrate_responses(responses: Dict[str, Any], channels: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pre-process responses to inject channel data.
    """
    if not isinstance(responses, dict):
        return {}

    hydrated = {}
    for key, block in responses.items():
        if isinstance(block, dict) and isinstance(block.get("messages"), list):
            hydrated[key] = {
                **block, 
                "messages": _render_messages(block["messages"], channels)
            }
        else:
            hydrated[key] = block
    return hydrated


def _format_menu_string(menu: Dict[str, Any]) -> str:
    """
    Converts the Menu JSON into a human-readable text block for the LLM System Prompt.
    """
    if not menu:
        return "No menu data available."

    lines = []
    
    currency = menu.get("currency", "AUD")
    promo = menu.get("promo", {})
    if promo.get("enabled"):
        lines.append(f"🔥 ACTIVE PROMO: {promo.get('title')} - {promo.get('text')} (Code: {promo.get('code')})")
        lines.append("-" * 20)

    categories = menu.get("categories", [])
    if not categories:
        return "No categories found in menu."

    for cat in categories:
        cat_label = cat.get("label", "General")
        items = cat.get("items", [])
        
        for item in items:
            name = item.get("name", "Unknown")
            price = item.get("price", "Ask")
            desc = item.get("desc", "")
            
            lines.append(f"- {name} ({cat_label}) : {currency} {price}. {desc}")
            
    return "\n".join(lines)


def load_client(clients_dir: Path, client_id: str) -> ClientContext:
    """
    Loads client configuration from the DATABASE.
    reconstructs the dictionary format expected by the rest of the application.
    """
    client = Client.query.get(client_id)
    if not client:
        raise JesseError(f"Client ID not found: {client_id}", 404)

    # 1. Reconstruct client_json
    client_json = {
        "id": client.id,
        "name": client.name,
        "bot_avatar_url": client.bot_avatar_url,
        "locale": client.locale,
        "timezone": client.timezone,
        "public": client.public,
        "plan_type": client.plan_type,
        "features": client.features
    }

    # 2. Reconstruct theme
    theme_obj = client.theme
    theme = {}
    if theme_obj:
        theme = {
            "brand_name": theme_obj.brand_name,
            "primary_color": theme_obj.primary_color,
            "bubble_color": theme_obj.bubble_color,
            "background": theme_obj.background,
            "text_color": theme_obj.text_color,
            "font_family": theme_obj.font_family,
            "bot_avatar_url": theme_obj.bot_avatar_url
        }

    # 3. Reconstruct channels
    channel_obj = client.channels
    channels = channel_obj.data if channel_obj else {}

    # 4. Reconstruct responses
    raw_responses = {}
    
    # Organize by intent
    # Note: DB stores flattened list of responses. 
    # Original JSON structure: 
    # { "greeting": {...}, "main_menu": {...}, "intents": { "about_us": ... } }
    # Our DB: Response(intent="greeting", content={...}), Response(intent="about_us", ...)
    
    # We need to map them back. But strictly speaking, the app mostly accesses responses[intent].
    # So a flat dict keyed by intent is actually cleaner and easier for usage!
    # However, existing `responses.json` had nested `intents` key.
    # Let's see how it's used. `response_service.py` -> `get_intent_response` likely does `ctx.responses.get(intent)`.
    # So a flat dict is preferred!
    
    for r in client.responses:
        raw_responses[r.intent] = r.content

    # Hydrate
    responses = hydrate_responses(raw_responses, channels)

    # 5. Reconstruct Menu
    menu = {
        "currency": client.currency,
        "promo": client.promo,
        "categories": []
    }
    
    for cat in client.menu_categories:
        cat_dict = {
            "id": cat.category_id,
            "label": cat.label,
            "items": []
        }
        for item in cat.items:
            cat_dict["items"].append({
                "name": item.name,
                "price": item.price,
                "desc": item.desc,
                "image": item.image,
                "allergens": item.allergens,
                "may_contain": item.may_contain
            })
        menu["categories"].append(cat_dict)

    # 6. System Prompt
    # Originally read from file. For now, we construct it dynamically or use a default.
    # Migration didn't move system strings to DB except implicitly via manual setup?
    # Wait, client_loader.py read `prompts/system.md`.
    # My migration script DID NOT migrate prompts!
    # I should read the file from disk as fallback for now.
    
    base_dir = clients_dir / client_id
    prompt_path = base_dir / "prompts" / "system.md"
    raw_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "You are a helpful assistant."

    menu_text = _format_menu_string(menu)
    
    STRICT_GUARD = f"""
    
    --- 🟢 REAL-TIME MENU DATA 🟢 ---
    (This is the ONLY valid menu. Use this to answer user questions.)
    
    {menu_text}
    
    ---------------------------------

    --- RULES ---
    1. You must ONLY recommend items listed above.
    2. If user asks for "Salmon" and it's NOT in the list, say: "Sorry, we don't have that."
    3. If asked about promos, refer to the "ACTIVE PROMO" section above.
    """
    
    system_prompt = raw_prompt + STRICT_GUARD

    return ClientContext(
        id=client.id,
        name=client.name,
        base_dir=base_dir, # Keep physical path for assets
        client_json=client_json,
        theme=theme,
        responses=responses,
        channels=channels,
        menu=menu,
        system_prompt=system_prompt,
        plan_type=client.plan_type
    )