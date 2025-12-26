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

    prompt_path = base / "prompts" / "system.md"
    
    raw_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    STRICT_GUARD = """
    
    --- IMPORTANT DATA INTEGRITY RULES ---
    1. You have access to the restaurant's specific MENU DATA in the context.
    2. You must ONLY recommend items explicitly listed in that menu data.
    3. DO NOT hallucinate items (like "Soft Shell Crab", "Sushi", etc.) if they are not in the data.
    4. If the user asks for "Seafood" and the search result is empty, say: "Sorry, I don't see that item on our current menu."
    5. Treat typos (e.g., "seefood") kindly, but if the corrected word isn't in the menu, do not invent it.
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