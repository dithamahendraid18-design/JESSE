from __future__ import annotations

import re
from typing import Optional, List, Dict, Any, Tuple

from ..core.client_loader import ClientContext
from .llm_service import LLMService
from .response_service import get_greeting, get_intent_response
from .search_service import smart_search_menu
from .menu_service import menu_category, menu_entry, order_food

# =========================
# CONSTANTS & PATTERNS
# =========================
INTENT_PATTERNS: Dict[str, List[str]] = {
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
    "allergy": [
        r"\b(allergy|allergies|allergic)\b",
        r"\b(dairy|gluten|nut|peanut|shellfish|lactose)\b",
        r"\b(dietary|diet)\b",
    ]
}

# Compile regex for performance
COMPILED_PATTERNS = {
    intent: [re.compile(p, re.IGNORECASE) for p in patterns]
    for intent, patterns in INTENT_PATTERNS.items()
}

INTENT_PRIORITY = ["order_food", "contact", "menu", "hours", "location", "about_us", "allergy"]


# =========================
# HELPER FUNCTIONS
# =========================
def _get_menu_context_string(ctx: ClientContext) -> str:
    """Extracts menu summary for LLM context."""
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


def _hydrate_response(ctx: ClientContext, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Substitutes placeholders ({phone}, {whatsapp}) with real data.
    """
    channels = ctx.channels or {}
    
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
            for placeholder, value in replacements.items():
                val_str = str(value) if value else "-"
                text = text.replace(placeholder, val_str)
            msg["text"] = text
            
    return messages


def _best_intent_from_text(message: str) -> Optional[str]:
    """Detects intent using regex patterns."""
    m = (message or "").strip()
    if not m: return None
    
    scores = {}
    for intent, patterns in COMPILED_PATTERNS.items():
        score = sum(1 for p in patterns if p.search(m))
        if score > 0:
            scores[intent] = score
    
    if not scores: return None
    
    best_score = max(scores.values())
    tied = [k for k, v in scores.items() if v == best_score]
    
    # Resolve ties using priority list
    for intent in INTENT_PRIORITY:
        if intent in tied: 
            return intent
            
    return tied[0]


def _nav_buttons() -> List[Dict[str, str]]:
    return [
        {"label": "About us", "intent": "about_us"},
        {"label": "Menu & price", "intent": "menu"},
        {"label": "Opening hours", "intent": "hours"},
        {"label": "Location", "intent": "location"},
        {"label": "Contact / Reservation", "intent": "contact"},
    ]


# =========================
# MAIN SERVICE
# =========================
class HybridService:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def handle(self, ctx: ClientContext, message: Optional[str], intent: Optional[str]) -> Tuple[List[Dict], List[Dict]]:
        """
        Main entry point for handling chat logic.
        Routes to specific handlers based on input type.
        """
        # 1. SPECIAL: LLM Greeting (Pass-through from routes_chat)
        if intent == "llm_greeting" and message:
            return self._handle_llm_greeting(ctx, message)

        # 2. Handle Explicit Intent (Button clicks, etc.)
        if intent:
            return self._handle_explicit_intent(ctx, intent)

        # 3. Text-Based Logic
        if message:
            return self._handle_text_input(ctx, message)

        # Fallback
        return get_intent_response(ctx, "fallback")

    def _handle_explicit_intent(self, ctx: ClientContext, intent: str) -> Tuple[List[Dict], List[Dict]]:
        if intent == "greeting": return get_greeting(ctx)
        if intent == "menu": return menu_entry(ctx)
        if intent.startswith("menu:"): return menu_category(ctx, intent.split(":", 1)[1])
        if intent == "order_food": return order_food(ctx)
        
        # Generic JSON-based response
        messages, buttons = get_intent_response(ctx, intent)
        messages = _hydrate_response(ctx, messages)
        return messages, buttons

    def _handle_llm_greeting(self, ctx: ClientContext, message: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Generates a dynamic friendly greeting using the LLM.
        Bypasses strict menu checks.
        """
        # Check LLM Config
        if hasattr(self.llm, "is_configured") and not self.llm.is_configured():
             # Fallback to static greeting if LLM is dead
             return get_greeting(ctx)

        system_prompt = (
            f"You are Jesse, a friendly SaaS chatbot assistant for {ctx.name}. "
            "Reply to the user's greeting in a warm, welcoming, and concise manner (English only). "
            "Do not list the menu yet, just say hello."
        )
        
        text_reply = self.llm.answer(system_prompt, message)
        return [{"type": "text", "text": text_reply}], _nav_buttons()

    def _handle_text_input(self, ctx: ClientContext, message: str) -> Tuple[List[Dict], List[Dict]]:
        # A. Check for regex intent match
        matched_intent = _best_intent_from_text(message)
        if matched_intent:
            return self._handle_explicit_intent(ctx, matched_intent)

        plan_type = getattr(ctx, "plan_type", "basic")
        features = (ctx.client_json or {}).get("features", {})
        llm_enabled = bool(features.get("llm_enabled", False))

        # B. Smart Search (Fuzzy Logic) - PRO only
        if plan_type == "pro":
            search_result = smart_search_menu(ctx, message)
            if search_result: 
                 return search_result

        # C. LLM Fallback
        if llm_enabled:
            return self._handle_llm_query(ctx, message, plan_type)

        # D. Generic Fallback
        return get_intent_response(ctx, "fallback")

    def _handle_llm_query(self, ctx: ClientContext, message: str, plan_type: str) -> Tuple[List[Dict], List[Dict]]:
        if plan_type != "pro":
            return [{"type": "text", "text": "AI Chat is a Pro feature 🔒"}], _nav_buttons()

        if hasattr(self.llm, "is_configured") and not self.llm.is_configured():
            return [{"type": "text", "text": "LLM not configured."}], _nav_buttons()

        menu_context = _get_menu_context_string(ctx)
        augmented_message = (
            f"[DATA SOURCE - DO NOT INVENT ITEMS]\n{menu_context}\n"
            "---------------------\n"
            f"USER QUESTION: \"{message}\"\n"
            "INSTRUCTIONS:\n"
            "1. Answer strictly based on the DATA SOURCE above.\n"
            "2. If item is missing, polite refusal + recommend similar item from list.\n"
            "3. Keep tone friendly and helpful.\n"
        )
        
        text_reply = self.llm.answer("You are a helpful waiter.", augmented_message)
        return [{"type": "text", "text": text_reply}], _nav_buttons()