from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import JesseError

@dataclass(frozen=True)
class ClientContext:
    id: str
    name: str
    base_dir: Path
    client_json: dict
    theme: dict
    responses: dict
    channels: dict
    menu: dict
    system_prompt: str
    plan_type: str

def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _render_text(text: str, data: dict) -> str:
    return text.format_map(SafeDict(data))


def _render_messages(messages: list, data: dict) -> list:
    out = []
    for m in messages:
        if isinstance(m, dict) and m.get("type") == "text":
            out.append({**m, "text": _render_text(m.get("text", ""), data)})
        else:
            out.append(m)
    return out


def hydrate_responses(responses: dict, channels: dict) -> dict:
    if not isinstance(responses, dict):
        return responses

    hydrated = {}
    for key, block in responses.items():
        if isinstance(block, dict) and isinstance(block.get("messages"), list):
            hydrated[key] = {**block, "messages": _render_messages(block["messages"], channels)}
        else:
            hydrated[key] = block
    return hydrated


# --- UPDATE: FUNGSI FORMAT MENU KHUSUS STRUKTUR ANDA ---
def _format_menu_string(menu: dict) -> str:
    """Mengubah JSON Menu (Luna Ramen) menjadi Text agar bisa dibaca AI"""
    if not menu:
        return "No menu data available."

    lines = []
    
    # 1. Ambil Mata Uang
    currency = menu.get("currency", "AUD")

    # 2. Ambil Promo (Jika ada dan aktif)
    promo = menu.get("promo", {})
    if promo.get("enabled"):
        lines.append(f"🔥 ACTIVE PROMO: {promo.get('title')} - {promo.get('text')} (Code: {promo.get('code')})")
        lines.append("-" * 20)

    # 3. Loop Categories
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
    base = clients_dir / client_id
    if not base.exists():
        raise JesseError(f"Unknown client_id: {client_id}", 404)

    client_json = _read_json(base / "client.json")
    theme = _read_json(base / "theme" / "theme.json")
    responses = _read_json(base / "assets" / "responses.json")
    channels = _read_json(base / "integrations" / "channels.json")
    responses = hydrate_responses(responses, channels)
    menu = _read_json(base / "assets" / "menu.json")

    # 1. Siapkan Prompt Dasar
    prompt_path = base / "prompts" / "system.md"
    raw_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    # 2. Siapkan Data Menu dalam bentuk Teks (Pake fungsi baru di atas)
    menu_text = _format_menu_string(menu)

    # 3. Suntikkan Data Menu + Aturan Ketat
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
        menu=menu,
        id=client_id,
        name=name,
        base_dir=base,
        client_json=client_json,
        theme=theme,
        responses=responses,
        channels=channels,
        system_prompt=system_prompt,
        plan_type=plan_type,
    )