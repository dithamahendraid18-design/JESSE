from __future__ import annotations

from typing import List, Dict, Tuple, Optional

try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None  # fallback if thefuzz is not installed

from ..core.client_loader import ClientContext

def smart_search_menu(ctx: ClientContext, user_input: str) -> Optional[Tuple[List[Dict], List[Dict]]]:
    """
    Fuzzy search for menu items.
    If match > 80%, return menu category or item details.
    Searches in: Category Name, Item Name, Item Description.
    """
    if fuzz is None:
        return None

    menu = ctx.menu
    if not menu or not isinstance(menu, dict):
        return None

    user_input_lower = user_input.lower().strip()
    best_match_type = None
    best_score = 0
    matched_data = None

    # Thresholds
    THRESHOLD = 80

    # 1. Search Categories
    for category in menu.get("categories", []):
        cat_Name = category.get("label", "") or category.get("name", "")
        score = fuzz.partial_ratio(user_input_lower, cat_Name.lower())
        
        if score > best_score:
            best_score = score
            best_match_type = "category"
            matched_data = category

        # 2. Search Items (Name & Description)
        for item in category.get("items", []):
            item_name = item.get("name", "").lower()
            item_desc = item.get("desc", "") or item.get("description", "")
            
            # Score name (higher weight)
            score_name = fuzz.partial_ratio(user_input_lower, item_name)
            
            # Score description (lower weight, optional)
            score_desc = fuzz.partial_ratio(user_input_lower, item_desc.lower()) if item_desc else 0
            
            # Take max relevance
            current_max = max(score_name, score_desc)
            
            if current_max > best_score:
                best_score = current_max
                best_match_type = "item"
                matched_data = item

    if best_score >= THRESHOLD:
        if best_match_type == "category":
            # Return menu category view
            try:
                from .menu_service import menu_category
                # Some categories might use 'id' or just rely on label as key
                cat_id = matched_data.get("id") or matched_data.get("label")
                return menu_category(ctx, cat_id)
            except ImportError:
                return None
        
        elif best_match_type == "item":
            # Return specific item detail
            name = matched_data.get("name", "Unknown")
            desc = matched_data.get("desc") or matched_data.get("description") or "No description available."
            price = matched_data.get("price", "-")
            
            text_response = f"**{name}**\n{desc}\nPrice: {price}"
            messages = [{"type": "text", "text": text_response}]
            
            # Check for image
            if matched_data.get("image"):
                messages.insert(0, {"type": "image", "url": matched_data["image"]})

            buttons = [{"label": "Back to Menu", "intent": "menu"}]
            return messages, buttons

    return None