from __future__ import annotations

import re
import difflib
from typing import Optional, List, Dict, Any

from ..core.client_loader import ClientContext
from .llm_service import LLMService
from .response_service import get_greeting, get_intent_response
from .search_service import smart_search_menu
from .menu_service import menu_category, menu_entry, order_food

SYNONYMS = {
    "shrimp": "prawn",
    "prawn": "shrimp",
    "coke": "cola",
    "soda": "soft drink",
    "veggie": "vegetarian",
}

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


def _get_menu(ctx: ClientContext) -> dict:
    return getattr(ctx, "menu", None) or {}


# =========================
# QUICK INTENT ROUTING (Re-Optimized)
# =========================
INTENT_PATTERNS: dict[str, list[str]] = {
    # 1) ORDER FOOD (High Priority: Niat ingin membeli/transaksi)
    "order_food": [
        r"\b(i\s*(want|wanna|would\s*like)\s*to\s*(order|buy|eat|have))\b",
        r"\b(can\s*i\s*(order|get|have))\b",
        r"\b(place\s*an?\s*order|make\s*an?\s*order|start\s*ordering)\b",
        r"\b(delivery|deliver|take\s*away|takeaway|pick[\s-]?up|pickup|to\s*go)\b",
        r"\b(grabfood|uber\s*eats|ubereats|doordash|go\s*food|gofood)\b",
        r"\b(checkout|bill|check\s*please)\b",
    ],

    # 2) MENU & PRICES (Niat ingin melihat daftar)
    "menu": [
        r"\b(show\s*(me)?\s*the\s*menu|see\s*the\s*menu)\b",
        r"\b(menu|menus|food\s*list|drink\s*list)\b",
        r"\b(price|prices|pricing|cost|how\s*much\s*is\s*it)\b",
        r"\b(recommend|recommendation|suggest|suggestion|best\s*seller|chef\s*choice)\b",
        r"\b(signature\s*dish|favorites|popular)\b",
        # Hapus "what do you have" generik agar tidak bentrok dengan pencarian menu spesifik
    ],

    # 3) OPENING HOURS
    "hours": [
        r"\b(opening\s*hours?|business\s*hours?|operating\s*hours?)\b",
        r"\b(what\s*time\s*(do\s*you|does\s*it)\s*(open|close))\b",
        r"\b(when\s*(do\s*you|are\s*you)\s*(open|close))\b",
        r"\b(are\s*you\s*open|is\s*it\s*open)\b",
        r"\b(closing\s*time|last\s*order)\b",
    ],

    # 4) LOCATION
    "location": [
        r"\b(where\s*(are\s*you|is\s*the\s*restaurant|is\s*it))\b",
        r"\b(address|location|directions?|google\s*map(s)?)\b",
        r"\b(how\s*to\s*get\s*there|how\s*do\s*i\s*get\s*there)\b",
        r"\b(near\s*me|closest|nearest)\b",
        r"\b(parking|park\s*car)\b",
    ],

    # 5) CONTACT / RESERVATION
    "contact": [
        r"\b(contact|phone|call|whatsapp|wa|email)\b",
        r"\b(reserve|reservation|book(ing)?|table|seat)\b",
        r"\b(can\s*i\s*book|i\s*want\s*to\s*book|book\s*a\s*table)\b",
        r"\b(for\s*\d+\s*(pax|people|person))\b", # misal: "for 2 pax"
    ],

    # 6) ABOUT US
    "about_us": [
        r"\b(about\s*us|tell\s*me\s*about\s*(you|this\s*place))\b",
        r"\b(who\s*are\s*you|what\s*is\s*jesse)\b", # Identitas bot
        r"\b(wifi|internet|password)\b", # Sering ditanya di "about"
        r"\b(halal\s*cert|is\s*it\s*halal)\b", # Pertanyaan sertifikasi umum
    ],

    # 7) ALLERGY / SAFETY (CRITICAL FIX)
    # HAPUS semua nama makanan (crab, shrimp, etc) dari sini!
    # Hanya trigger jika user MENYEBUTKAN masalah kesehatan.
    "allergy": [
        r"\b(allergy|allergic|allergen|allergens|anaphylaxis)\b",
        r"\b(safe\s*to\s*eat|can\s*i\s*eat\s*this)\b",
        r"\b(contains?\s*(nuts|peanuts|shellfish|gluten|dairy|pork|lard))\b", # "Contains X?" = Safety Check
        r"\b(dietary|requirement|intolerant|intolerance)\b",
        r"\b(gluten[\s-]*free|dairy[\s-]*free|celiac)\b",
        r"\b(poison|die|death|hospital|sick)\b",
    ],
}

INTENT_PRIORITY = [
    "order_food",
    "contact",
    "menu",
    "hours",
    "location",
    "about_us",
    "allergy",
]

def _best_intent_from_text(message: str) -> Optional[str]:
    m = (message or "").strip().lower()
    if not m:
        return None

    scores: dict[str, int] = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for p in patterns:
            if re.search(p, m):
                score += 1
        scores[intent] = score

    # pick best score
    best_score = max(scores.values()) if scores else 0
    if best_score == 0:
        return None

    # intents with the same max score
    tied = [k for k, v in scores.items() if v == best_score]

    # tie-break using priority list
    for intent in INTENT_PRIORITY:
        if intent in tied:
            return intent

    # fallback (should rarely happen)
    return tied[0]



# =========================
# ANTI-HALLUCINATION MENU GUARD
# =========================
STOPWORDS = {
    "do", "you", "have", "got", "is", "there", "any", "a", "an", "the", "to", 
    "please", "can", "could", "would", "menu", "price",
}

def _looks_like_availability_question(message: str) -> bool:
    m = (message or "").lower()
    return bool(re.search(r"\b(do you have|have you got|is there|do u have)\b", m))

def _extract_keywords(message: str) -> List[str]:
    m = (message or "").lower()
    tokens = re.findall(r"[a-z0-9']{3,}", m)
    
    out: List[str] = []
    seen = set()
    for k in tokens:
        if k not in STOPWORDS:
            # 1. Masukkan kata asli
            if k not in seen:
                seen.add(k)
                out.append(k)
            
            # 2. Masukkan sinonimnya juga (Optimasi)
            if k in SYNONYMS:
                syn = SYNONYMS[k]
                if syn not in seen:
                    seen.add(syn)
                    out.append(syn)
    return out

def _all_menu_items(ctx: ClientContext) -> List[Dict[str, Any]]:
    menu = _get_menu(ctx)
    cur = menu.get("currency") or "SGD"
    cats = menu.get("categories") or []

    out: List[Dict[str, Any]] = []
    for c in cats:
        cat_label = c.get("label") or "Menu"
        for it in (c.get("items") or []):
            name = (it.get("name") or "").strip()
            desc = (it.get("desc") or "").strip()
            price = it.get("price")
            image = it.get("image") or it.get("image_url") or ""
            if name:
                out.append({
                    "cat": cat_label,
                    "name": name,
                    "desc": desc,
                    "price": price,
                    "currency": cur,
                    "image": image,
                })
    return out

def _find_menu_matches_by_keywords(ctx: ClientContext, keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
    if not keywords:
        return []

    items = _all_menu_items(ctx)
    scored: List[tuple[int, Dict[str, Any]]] = []
    for it in items:
        hay = f"{it.get('name','')} {it.get('desc','')}".lower()
        score = sum(1 for k in keywords if k in hay)
        if score > 0:
            scored.append((score, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:limit]]

def _menu_not_found_response(ctx: ClientContext, keywords: List[str]):
    query = " ".join(keywords).strip() or "that item"
    names = [it["name"] for it in _all_menu_items(ctx)]
    suggestions = difflib.get_close_matches(query, names, n=3, cutoff=0.5) if names else []

    text = f"I don’t see '{query}' on our current menu 😅\n"
    if suggestions:
        text += "\nClosest matches you might like:\n" + "\n".join([f"• {s}" for s in suggestions])
    text += "\n\nTap 'Menu & price' to browse all categories 👇"

    return [{"type": "text", "text": text}], _nav_buttons()


# =========================
# SERVICE
# =========================
class HybridService:
    """
    Priority:
    1) intent -> deterministic
    2) text:
       - route to 5 intents directly (about_us/menu/hours/location/contact)
       - pro -> smart_search_menu
       - availability guard "do you have X" (no hallucination)
       - pro + llm_enabled + configured -> LLM
       - fallback
    """

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    def handle(self, ctx: ClientContext, message: Optional[str], intent: Optional[str]):
        # =========================
        # 1) INTENT-BASED
        # =========================
        if intent:
            if intent == "greeting":
                return get_greeting(ctx)

            if intent == "main_menu":
                return get_intent_response(ctx, "main_menu")

            if intent == "menu":
                return menu_entry(ctx)

            if intent.startswith("menu:"):
                category_id = intent.split(":", 1)[1]
                return menu_category(ctx, category_id)

            if intent == "order_food":
                return order_food(ctx)

            if intent == "contact":
                data = (ctx.channels or {})
                phone = data.get("phone", "-")
                wa_link = data.get("whatsapp", "#")
                email = data.get("email", "-")
                ig_link = data.get("instagram", "#")

                # Format pesan dengan f-string
                text = (
                    f"Contact & Reservation 📞 \n\n"
                    f"📞 Phone: {phone}\n"
                    f"💬 WhatsApp: {wa_link}\n"
                    f"📧 Email: {email}\n"
                    f"📸 Instagram: {ig_link}\n\n"
                    f"For reservations, simply message us on WhatsApp.\n"
                    f"Our team will confirm your table shortly! 🪑 ✨"
                )
                
                # Langsung kembalikan respons dinamis
                return [{"type": "text", "text": text}], _nav_buttons()
            # -----------------------------------------------

            messages, buttons = get_intent_response(ctx, intent)

            if intent == "open_maps":
                maps = (ctx.channels or {}).get("maps") or (ctx.client_json or {}).get("maps", "")
                if maps:
                    messages = [{"type": "text", "text": f"Open Maps: {maps}"}]

            return messages, buttons

        # =========================
        # 2) TEXT-BASED
        # =========================
        plan_type = _get_plan_type(ctx)
        features = _get_features(ctx)
        llm_enabled = bool(features.get("llm_enabled", False))
        menu_enabled = bool(features.get("menu_enabled", True))

        # ✅ (A) ROUTE 5 INTENTS DIRECTLY (seperti klik bubble)
        if message:
            matched = _best_intent_from_text(message)
            if matched == "menu":
                return menu_entry(ctx)
            if matched == "order_food":                
                return order_food(ctx)
            
            # Jika user mengetik "contact" atau "book table", kita arahkan ke logika intent di atas
            if matched == "contact":
                # Panggil diri sendiri (rekursif) dengan intent="contact"
                return self.handle(ctx, None, "contact")
                
            if matched in {"about_us", "hours", "location", "allergy"}:
                return get_intent_response(ctx, matched)

        # ✅ (B) PRO: smart search menu
        if message and plan_type == "pro":
            search_result = smart_search_menu(ctx, message)
            if search_result:
                return search_result

        # ✅ (C) Availability guard: "do you have X?"
        if message and menu_enabled and _looks_like_availability_question(message):
            keywords = _extract_keywords(message)
            if keywords:
                matches = _find_menu_matches_by_keywords(ctx, keywords, limit=5)
                if matches:
                    lines: List[str] = []
                    for it in matches:
                        name = it["name"]
                        cat = it["cat"]
                        price = it.get("price")
                        cur = it.get("currency") or "SGD"
                        if price is not None:
                            lines.append(f"• {name} — {cur} {price}  ({cat})")
                        else:
                            lines.append(f"• {name}  ({cat})")

                    msg = "Yes — here’s what I found on our menu ✅\n\n" + "\n".join(lines)
                    return [{"type": "text", "text": msg}], _nav_buttons()

                return _menu_not_found_response(ctx, keywords)

        # ✅ (D) LLM hanya PRO + llm_enabled
        if message and llm_enabled:
            if plan_type != "pro":
                messages = [{
                    "type": "text",
                    "text": "AI chat is available on the Pro plan only 😊\nPlease use the menu buttons below."
                }]
                return messages, _nav_buttons()

            if hasattr(self.llm, "is_configured") and callable(getattr(self.llm, "is_configured")):
                if not self.llm.is_configured():
                    messages = [{"type": "text", "text": "LLM is not configured on the server yet."}]
                    return messages, _nav_buttons()

            text = self.llm.answer(ctx.system_prompt, message)
            return [{"type": "text", "text": text}], _nav_buttons()

        # =========================
        # 3) FALLBACK
        # =========================
        return get_intent_response(ctx, "fallback")