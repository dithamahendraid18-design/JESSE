from __future__ import annotations

try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None  # fallback jika thefuzz tidak ada

from ..core.client_loader import ClientContext

def smart_search_menu(ctx: ClientContext, user_input: str) -> tuple[list, list] | None:
    """
    Fuzzy search untuk menu items.
    Jika cocok (>80%), return menu category atau item.
    """
    if fuzz is None:
        return None  # skip jika thefuzz tidak terinstall

    menu = ctx.menu
    if not menu or not isinstance(menu, dict):
        return None

    user_input_lower = user_input.lower().strip()
    best_match = None
    best_score = 0
    matched_item = None

    # Cari di categories dan items
    for category in menu.get("categories", []):
        cat_name = category.get("name", "").lower()
        score = fuzz.ratio(user_input_lower, cat_name)
        if score > best_score:
            best_score = score
            best_match = "category"
            matched_item = category

        for item in category.get("items", []):
            item_name = item.get("name", "").lower()
            score = fuzz.ratio(user_input_lower, item_name)
            if score > best_score:
                best_score = score
                best_match = "item"
                matched_item = item

    if best_score >= 80:  # threshold
        if best_match == "category":
            # Return menu category seperti di menu_service
            try:
                from .menu_service import menu_category
                return menu_category(ctx, matched_item["id"])
            except ImportError:
                return None
        elif best_match == "item":
            # Return detail item
            messages = [{"type": "text", "text": f"Found: {matched_item['name']} - {matched_item.get('description', '')}"}]
            buttons = [{"label": "Back to Menu", "intent": "menu"}]
            return messages, buttons

    return None  # no match