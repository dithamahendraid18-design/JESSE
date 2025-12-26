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
# 1. HELPER BARU: FORMAT MENU STRING (Anti-Halusinasi)
# =========================
def _get_menu_context_string(ctx: ClientContext) -> str:
    """
    Mengambil data menu real-time untuk ditempel LANGSUNG ke pesan user.
    Ini memaksa AI membaca menu sebelum menjawab.
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
            # Format: - Tonkotsu Ramen (Ramen) : AUD 18.99
            lines.append(f"- {name} ({cat_lbl}) : {currency} {price}")
            
    return "\n".join(lines)

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
# QUICK INTENT ROUTING
# =========================
INTENT_PATTERNS: dict[str, list[str]] = {
    "order_food": [
        r"\b(i\s*(want|wanna|would\s*like)\s*to\s*(order|buy|eat|have))\b",
        r"\b(can\s*i\s*(order|get|have))\b",
        r"\b(place\s*an?\s*order|make\s*an?\s*order|start\s*ordering)\b",
        r"\b(delivery|deliver|take\s*away|takeaway|pick[\s-]?up|pickup|to\s*go)\b",
    ],
    "menu": [
        r"\b(show\s*(me)?\s*the\s*menu|see\s*the\s*menu)\b",
        r"\b(menu|menus|food\s*list|drink\s*list)\b",
        r"\b(price|prices|pricing|cost|how\s*much\s*is\s*it)\b",
        r"\b(recommend|recommendation|suggest|suggestion|best\s*seller)\b",
    ],
    "hours": [
        r"\b(opening\s*hours?|business\s*hours?)\b",
        r"\b(what\s*time\s*(do\s*you|does\s*it)\s*(open|close))\b",
        r"\b(are\s*you\s*open|is\s*it\s*open)\b",
    ],
    "location": [
        r"\b(where\s*(are\s*you|is\s*the\s*restaurant|is\s*it))\b",
        r"\b(address|location|directions?|google\s*map(s)?)\b",
    ],
    "contact": [
        r"\b(contact|phone|call|whatsapp|wa|email)\b",
        r"\b(reserve|reservation|book(ing)?|table|seat)\b",
    ],
    "about_us": [
        r"\b(about\s*us|tell\s*me\s*about\s*(you|this\s*place))\b",
        r"\b(wifi|internet|password)\b",
        r"\b(halal)\b",
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
            if intent == "contact":
                data = (ctx.channels or {})
                text = (f"Contact & Reservation 📞\nPhone: {data.get('phone','-')}\n"
                        f"WA: {data.get('whatsapp','#')}\nFor reservations, please WhatsApp us!")
                return [{"type": "text", "text": text}], _nav_buttons()
            
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

        # B) PRO Feature: Smart Search (Cari menu spesifik)
        if message and plan_type == "pro":
            search_result = smart_search_menu(ctx, message)
            if search_result: return search_result

        # C) LLM WITH CONTEXT INJECTION (THE FIX IS HERE) 🛡️
        if message and llm_enabled:
            # Cek User Plan
            if plan_type != "pro":
                return [{"type": "text", "text": "AI Chat is a Pro feature 🔒"}], _nav_buttons()

            # Cek Config LLM
            if hasattr(self.llm, "is_configured") and not self.llm.is_configured():
                return [{"type": "text", "text": "LLM not configured."}], _nav_buttons()

            # --- SUNTIK DATA MENU KE PESAN USER ---
            # Kita ambil menu text real-time
            menu_context = _get_menu_context_string(ctx)
            
            # Kita bungkus pertanyaan user dengan DATA FAKTA
            augmented_message = f"""
[IMPORTANT: ANSWER BASED ON THIS DATA ONLY]
--- START MENU DATA ---
{menu_context}
--- END MENU DATA ---

USER QUESTION: "{message}"

INSTRUCTIONS:
1. Check if the User Question relates to an item in the MENU DATA above.
2. If the item is NOT in the MENU DATA (like 'crab', 'salmon', 'sushi'), you MUST say: "Sorry, we don't have that on our menu."
3. Do NOT hallucinate. Do NOT assume.
"""
            # Kirim pesan yang sudah "dioplos" ini ke AI
            # Kita override system_prompt di sini agar fokus ke instruksi data
            text = self.llm.answer("You are a helpful restaurant assistant. Be strict with menu data.", augmented_message)
            
            return [{"type": "text", "text": text}], _nav_buttons()

        # Fallback terakhir
        return get_intent_response(ctx, "fallback")