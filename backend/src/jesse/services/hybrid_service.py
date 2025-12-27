from __future__ import annotations

import re
from typing import Optional, List, Dict, Any

from ..core.client_loader import ClientContext
from .llm_service import LLMService
from .response_service import get_greeting, get_intent_response
from .search_service import smart_search_menu
from .menu_service import menu_category, menu_entry, order_food

# =========================
# 1. HELPER: FORMAT MENU STRING
# =========================
def _get_menu_context_string(ctx: ClientContext) -> str:
    menu = getattr(ctx, "menu", {})
    if not menu or "categories" not in menu:
        return "No menu data available."
        
    lines = []
    promo = menu.get("promo", {})
    if promo.get("enabled"):
        lines.append(f"🔥 ACTIVE PROMO: {promo.get('title')} ({promo.get('code')})")

    currency = menu.get("currency", "AUD")
    for cat in menu.get("categories", []):
        cat_lbl = cat.get("label", "General")
        for item in cat.get("items", []):
            name = item.get("name", "Unknown")
            price = item.get("price", "-")
            lines.append(f"- {name} ({cat_lbl}) : {currency} {price}")
            
    return "\n".join(lines)

# =========================
# 2. HELPER: HYDRATOR (MESIN PENUKAR VARIABEL)
# =========================
def _hydrate_response(ctx: ClientContext, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fungsi ini otomatis menukar {phone}, {whatsapp}, {email}, dll
    dengan data asli dari channels.json.
    """
    channels = ctx.channels or {}
    
    # Siapkan data penukar (default "-" jika kosong)
    replacements = {
        "{phone}": channels.get("phone", "-"),
        "{whatsapp}": channels.get("whatsapp") or channels.get("wa", "-"),
        "{email}": channels.get("email", "-"),
        "{instagram}": channels.get("instagram", "-"),
        "{wifi}": channels.get("wifi", "-"),
        "{website}": channels.get("website") or channels.get("order_url", "-")
    }

    for msg in messages:
        if msg.get("type") == "text":
            text = msg["text"]
            # Lakukan penukaran
            for placeholder, value in replacements.items():
                if value:
                    text = text.replace(placeholder, str(value))
                else:
                    text = text.replace(placeholder, "-")
            msg["text"] = text
            
    return messages

# =========================
# QUICK INTENT ROUTING
# =========================
INTENT_PATTERNS: dict[str, list[str]] = {
    "order_food": [
        r"\b(how\s*to\s*order)\b",
        r"\b(start\s*ordering)\b",
        r"\b(place\s*an?\s*order)\b",
        r"\b(delivery|deliver|take\s*away|takeaway|pick[\s-]?up|pickup|to\s*go)\b",
        r"\b(checkout|bill|check\s*please)\b",
        r"\b(grabfood|gofood|shopeefood|uber\s*eats)\b",
    ],
    "menu": [
        r"\b(show\s*(me)?\s*the\s*menu|see\s*the\s*menu)\b",
        r"\b(food\s*list|drink\s*list|wine\s*list)\b",
        r"\b(full\s*menu|all\s*menu)\b",
    ],
    "hours": [
        r"\b(opening\s*hours?|business\s*hours?|operating\s*hours?)\b",
        r"\b(what\s*time\s*(do\s*you|does\s*it)\s*(open|close))\b",
        r"\b(when\s*(do\s*you|are\s*you)\s*(open|close))\b",
        r"\b(are\s*you\s*open|is\s*it\s*open)\b",
    ],
    "location": [
        r"\b(where\s*(are\s*you|is\s*the\s*restaurant|is\s*it))\b",
        r"\b(address|location|directions?|google\s*map(s)?)\b",
        r"\b(parking|car\s*park)\b", 
    ],
    "contact": [
        r"\b(contact|phone|call|whatsapp|wa|email)\b",
        r"\b(reserve|reservation|book(ing)?|table|seat)\b",
        r"\b(book\s*a\s*table|get\s*a\s*table)\b",
    ],
    "about_us": [
        r"\b(about\s*us|tell\s*me\s*about\s*(you|this\s*place))\b",
        r"\b(wifi|internet|password)\b",
        r"\b(halal|pork|lard)\b", 
    ],
}

INTENT_PRIORITY = ["order_food", "contact", "menu", "hours", "location", "about_us"]

def _best_intent_from_text(message: str) -> Optional[str]:
    m = (message or "").strip().lower()
    if not m: return None
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, m))
        if score > 0: scores[intent] = score
    
    if not scores: return None
    best_score = max(scores.values())
    tied = [k for k, v in scores.items() if v == best_score]
    for intent in INTENT_PRIORITY:
        if intent in tied: return intent
    return tied[0]

def _nav_buttons() -> List[Dict[str, str]]:
    return [
        {"label": "About us", "intent": "about_us"},
        {"label": "Menu & price", "intent": "menu"},
        {"label": "Opening hours", "intent": "hours"},
        {"label": "Location", "intent": "location"},
        {"label": "Contact / Reservation", "intent": "contact"},
    ]

def _get_plan_type(ctx: ClientContext) -> str:
    client_json = (ctx.client_json or {})
    return str(client_json.get("plan_type", "basic")).lower().strip()

def _get_features(ctx: ClientContext) -> dict:
    return (ctx.client_json or {}).get("features", {})


# =========================
# SERVICE CLASS
# =========================
class HybridService:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def handle(self, ctx: ClientContext, message: Optional[str], intent: Optional[str]):
        # 1) INTENT-BASED
        if intent:
            # Fitur Fungsional
            if intent == "greeting": return get_greeting(ctx)
            if intent == "menu": return menu_entry(ctx)
            if intent.startswith("menu:"): return menu_category(ctx, intent.split(":", 1)[1])
            if intent == "order_food": return order_food(ctx)
            
            # ✅ AMBIL TEKS DARI JSON
            messages, buttons = get_intent_response(ctx, intent)
            
            # ✅ JALANKAN MESIN PENUKAR (HYDRATOR)
            # Ini akan mengubah "{phone}" menjadi "+62..." secara otomatis
            messages = _hydrate_response(ctx, messages)
            
            return messages, buttons

        # 2) TEXT-BASED LOGIC
        plan_type = _get_plan_type(ctx)
        features = _get_features(ctx)
        llm_enabled = bool(features.get("llm_enabled", False))

        if message:
            matched = _best_intent_from_text(message)
            if matched: return self.handle(ctx, None, matched)

        if message and plan_type == "pro":
            search_result = smart_search_menu(ctx, message)
            if search_result: return search_result

        if message and llm_enabled:
            if plan_type != "pro":
                return [{"type": "text", "text": "AI Chat is a Pro feature 🔒"}], _nav_buttons()

            if hasattr(self.llm, "is_configured") and not self.llm.is_configured():
                return [{"type": "text", "text": "LLM not configured."}], _nav_buttons()

            menu_context = _get_menu_context_string(ctx)
            
            augmented_message = f"""
[DATA SOURCE - DO NOT INVENT ITEMS]
{menu_context}
---------------------
USER QUESTION: "{message}"
INSTRUCTIONS:
1. Answer strictly based on the DATA SOURCE above.
2. If the user asks for an item NOT in the data (e.g. "Sashimi", "Crab"):
   - First, politely say we don't have it.
   - THEN, recommend 1 or 2 similar or popular items that ARE in the DATA SOURCE.
   - Example: "We don't have Sashimi, but our Gyoza and Tonkotsu Ramen are customer favorites!"
3. Keep the tone friendly, helpful, and inviting.
"""
            text = self.llm.answer("You are a helpful waiter.", augmented_message)
            return [{"type": "text", "text": text}], _nav_buttons()

        return get_intent_response(ctx, "fallback")