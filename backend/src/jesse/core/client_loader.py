from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import JesseError

@dataclass(frozen=True)
class ClientContext:
    """
    Immutable context object holding all configuration for a specific client.
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

def _read_json(path: Path) -> Dict[str, Any]:
    """Helper to safely read a JSON file."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

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
    Pre-process responses.json to inject channel data (phone, etc.) 
    into all text fields globally at load time.
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


# --- UPDATE: FUNGSI FORMAT MENU KHUSUS STRUKTUR ANDA ---
def _format_menu_string(menu: Dict[str, Any]) -> str:
    """
    Converts the Menu JSON into a human-readable text block for the LLM System Prompt.
    """
    if not menu:
        return "No menu data available."

    lines = []
    
    # 1. Currency
    currency = menu.get("currency", "AUD")

    # 2. Promos
    promo = menu.get("promo", {})
    if promo.get("enabled"):
        lines.append(f"🔥 ACTIVE PROMO: {promo.get('title')} - {promo.get('text')} (Code: {promo.get('code')})")
        lines.append("-" * 20)

    # 3. Categories
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
            
            # Format: - Tonkotsu Ramen (Ramen) : AUD 18.99. Rich pork broth...
            lines.append(f"- {name} ({cat_label}) : {currency} {price}. {desc}")
            
    return "\n".join(lines)
# -------------------------------------------------------


def load_client(clients_dir: Path, client_id: str) -> ClientContext:
    """
    Main factory function to load all client configuration files into a Context.
    """
    base = clients_dir / client_id
    if not base.exists():
        raise JesseError(f"Client ID not found: {client_id}", 404)

    client_json = _read_json(base / "client.json")
    theme = _read_json(base / "theme" / "theme.json")
    responses = _read_json(base / "assets" / "responses.json")
    channels = _read_json(base / "integrations" / "channels.json")
    
    # Pre-render responses with static channel info
    responses = hydrate_responses(responses, channels)
    
    menu = _read_json(base / "assets" / "menu.json")

    # 1. Load Base System Prompt
    prompt_path = base / "prompts" / "system.md"
    raw_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    # 2. Format Menu for LLM
    menu_text = _format_menu_string(menu)

    # 3. Inject Menu & Guardrails into Prompt
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
    # -------------------------

    name = client_json.get("name", client_id)
    plan_type = client_json.get("plan_type", "basic")

    return ClientContext(
        id=client_id,
        name=name,
        base_dir=base,
        client_json=client_json,
        theme=theme,
        responses=responses,
        channels=channels,
        menu=menu,
        system_prompt=system_prompt,
        plan_type=plan_type,
    )