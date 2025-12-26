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
    """
    Render semua text message di responses.json menggunakan data dari channels.json.
    Placeholder format: {phone}, {whatsapp}, dst.
    """
    if not isinstance(responses, dict):
        return responses

    hydrated = {}
    for key, block in responses.items():
        if isinstance(block, dict) and isinstance(block.get("messages"), list):
            hydrated[key] = {**block, "messages": _render_messages(block["messages"], channels)}
        else:
            hydrated[key] = block
    return hydrated


# --- TAMBAHKAN HELPER KECIL INI DI ATAS load_client ---
def _format_menu_string(menu: dict) -> str:
    """Mengubah JSON Menu menjadi Text agar bisa dibaca AI"""
    if not menu or "categories" not in menu:
        return "No menu items available."
    
    lines = []
    for cat in menu.get("categories", []):
        cat_label = cat.get("label", "General")
        for item in cat.get("items", []):
            name = item.get("name", "Unknown")
            price = item.get("price", "-")
            desc = item.get("desc", "")
            # Hasil: "- Ramen (Mains): 12.0. Kuah pedas..."
            lines.append(f"- {name} ({cat_label}) : {price}. {desc}")
            
    return "\n".join(lines)


def load_client(clients_dir: Path, client_id: str) -> ClientContext:
    """
    Load semua data per klien dari folder:
      clients/<client_id>/*
    """
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

    # 2. Siapkan Data Menu dalam bentuk Teks
    menu_text = _format_menu_string(menu)

    # 3. Suntikkan Data Menu + Aturan Ketat
    STRICT_GUARD = f"""
    
    --- 🟢 REAL-TIME MENU DATA 🟢 ---
    (You must ONLY recommend items listed below. Do not invent others.)
    
    {menu_text}
    
    ---------------------------------

    --- IMPORTANT RULES ---
    1. The list above is the ONLY food we serve.
    2. If user asks for "Salmon" and it's NOT in the list above, say: "Sorry, I don't see that on our menu."
    3. Treat typos kindly (e.g. "seefood"), but verify against the list above.
    """

    system_prompt = raw_prompt + STRICT_GUARD
    # -------------------------

    name = client_json.get("name", client_id)
    plan_type = client_json.get("plan_type", "basic")  # default to basic

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