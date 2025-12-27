from __future__ import annotations

import re
import difflib
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
    """
    Mengambil data menu real-time untuk ditempel LANGSUNG ke pesan user.
    """
    menu = getattr(ctx, "menu", {})
    if not menu or "categories" not in menu:
        return "No menu data available."
        
    lines = []
    
    # Ambil Promo
    promo = menu.get("promo", {})
    if promo.get("enabled"):
        lines.append(f"🔥 ACTIVE PROMO: {promo.get('title')} ({promo.get('code')})")

    # Ambil Menu & Harga
    currency = menu.get("currency", "AUD")
    for cat in menu.get("categories", []):
        cat_lbl = cat.get("label", "General")
        for item in cat.get("items", []):
            name = item.get("name", "Unknown")
            price = item.get("price", "-")
            lines.append(f"- {name} ({cat_lbl}) : {currency} {price}")
            
    return "\n".join(lines)

# =========================
# QUICK INTENT ROUTING
# =========================
INTENT_PATTERNS: dict[str, list[str]] = {
    # 1) ORDER FOOD 
    "order_food": [
        r"\b(how\s*to\s*order)\b",
        r"\b(start\s*ordering)\b",
        r"\b(place\s*an?\s*order)\b",
        r"\b(delivery|deliver|take\s*away|takeaway|pick[\s-]?up|pickup|to\s*go)\b",
        r"\b(checkout|bill|check\s*please)\b",
        r"\b(grabfood|gofood|shopeefood|uber\s*eats)\b",
    ],

    # 2) MENU & PRICES
    "menu": [
        r"\b(show\s*(me)?\s*the\s*menu|see\s*the\s*menu)\b",
        r"\b(food\s*list|drink\s*list|wine\s*list)\b",
        r"\b(full\s*menu|all\s*menu)\b",
    ],

    # 3) OPENING HOURS
    "hours": [
        r"\b(opening\s*hours?|business\s*hours?|operating\s*hours?)\b",
        r"\b(what\s*time\s*(do\s*you|does\s*it)\s*(open|close))\b",
        r"\b(when\s*(do\s*you|are\s*you)\s*(open|close))\b",
        r"\b(are\s*you\s*open|is\s*it\s*open)\b",
    ],

    # 4) LOCATION
    "location": [
        r"\b(where\s*(are\s*you|is\s*the\s*restaurant|is\s*it))\b",
        r"\b(address|location|directions?|google\s*map(s)?)\b",
        r"\b(parking|car\s*park)\b", 
    ],

    # 5) CONTACT / RESERVATION
    "contact": [
        r"\b(contact|phone|call|whatsapp|wa|email)\b",
        r"\b(reserve|reservation|book(ing)?|table|seat)\b",
        r"\b(book\s*a\s*table|get\s*a\s*table)\b",
    ],

    # 6) ABOUT US
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

# =========================
# UI / NAV HELPERS
# =========================
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
    plan = (client_json.get("plan_type") or getattr(ctx, "plan_type", "basic") or "basic")
    return str(plan).lower().strip()

def _get_features(ctx: ClientContext) -> dict:
    client_json = (ctx.client_json or {})
    return (client_json.get("features") or {})


# =========================
# SERVICE CLASS
# =========================
class HybridService:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def handle(self, ctx: ClientContext, message: Optional[str], intent: Optional[str]):
        # 1) INTENT-BASED
        if intent:
            if intent == "greeting": return get_greeting(ctx)
            if intent == "menu": return menu_entry(ctx)
            if intent.startswith("menu:"): return menu_category(ctx, intent.split(":", 1)[1])
            if intent == "order_food": return order_food(ctx)
            
            # ✅✅✅ LOGIKA BARU: JSON CLIENT DULUAN ✅✅✅
            # Cek apakah intent ini ada di responses.json?
            # Jika ada, GUNAKAN itu (jangan di-override hardcode).
            if ctx.responses and intent in ctx.responses:
                return get_intent_response(ctx, intent)
            
            # --- JIKA JSON KOSONG, BARU PAKAI BACKUP DINAMIS ---
            
            # 1. Dynamic Contact Backup
            if intent == "contact":
                data = (ctx.channels or {})
                text = (
                    f"Contact & Reservation 📞 \n\n"
                    f"📞 Phone: {data.get('phone','-')}\n"
                    f"💬 WhatsApp: {data.get('whatsapp','#')}\n"
                    f"📧 Email: {data.get('email','-')}\n"
                    f"📸 Instagram: {data.get('instagram','#')}\n\n"
                    f"For reservations, please message us on WhatsApp! 🪑"
                )
                return [{"type": "text", "text": text}], _nav_buttons()

            # 2. Dynamic About Us Backup
            if intent == "about_us":
                client_info = ctx.client_json or {}
                name = client_info.get("name", "Jesse Bot")
                desc = client_info.get("description", "We serve authentic flavors! 🍜")
                wifi = (ctx.channels or {}).get("wifi") or client_info.get("wifi")
                
                text = f"**{name}**\n\n{desc}"
                if wifi: text += f"\n\n📶 **WiFi:** {wifi}"
                text += "\n\nCome visit us! ✨"
                return [{"type": "text", "text": text}], _nav_buttons()

            # Fallback jika tidak ada di JSON dan tidak ada backup dinamis
            messages, buttons = get_intent_response(ctx, intent)
            return messages, buttons


        # 2) TEXT-BASED LOGIC
        plan_type = _get_plan_type(ctx)
        features = _get_features(ctx)
        llm_enabled = bool(features.get("llm_enabled", False))

        # A) Cek apakah cocok dengan Intent (Regex)
        if message:
            matched = _best_intent_from_text(message)
            if matched: return self.handle(ctx, None, matched)

        # B) PRO Feature: Smart Search
        if message and plan_type == "pro":
            search_result = smart_search_menu(ctx, message)
            if search_result: return search_result

        # C) LLM WITH CONTEXT INJECTION (SMART UPSELLING)
        if message and llm_enabled:
            if plan_type != "pro":
                return [{"type": "text", "text": "AI Chat is a Pro feature 🔒"}], _nav_buttons()

            if hasattr(self.llm, "is_configured") and not self.llm.is_configured():
                return [{"type": "text", "text": "LLM not configured."}], _nav_buttons()

            # --- SUNTIK DATA MENU ---
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
            text = self.llm.answer("You are a helpful waiter. Be honest but persuasive.", augmented_message)
            return [{"type": "text", "text": text}], _nav_buttons()

        # Fallback
        return get_intent_response(ctx, "fallback")