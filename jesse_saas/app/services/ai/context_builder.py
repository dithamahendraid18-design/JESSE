import json
from datetime import datetime
import pytz
from app.services.ai.utils import safe_get, check_restaurant_status

def build_system_prompt(client_model, kb, menu_items):
    # --- Contextual Info ---
    rest_name = safe_get(client_model, 'restaurant_name', 'the restaurant')
    currency = safe_get(client_model, 'currency_symbol', '$')
    
    # Time & Status
    tz_name = safe_get(client_model, 'timezone', 'UTC')
    try: tz = pytz.timezone(tz_name)
    except: tz = pytz.utc
    now_in_tz = datetime.now(tz)
    status_str = "OPEN" if check_restaurant_status(client_model, now_in_tz) else "CLOSED"
    
    # Operating Hours Text
    operating_hours_text = "Open daily"
    try:
        op_hours = safe_get(client_model, 'operating_hours')
        hours_json = json.loads(op_hours or '{}')
        if isinstance(hours_json, dict) and len(hours_json) > 0:
            h_lines = []
            for day, data in hours_json.items():
                if data.get('is_closed'): h_lines.append(f"- {day.capitalize()}: CLOSED")
                else:
                    shifts = data.get('shifts', [])
                    s_txt = ", ".join([f"{s['start']}-{s['end']}".replace("00:00", "24:00") for s in shifts])
                    h_lines.append(f"- {day.capitalize()}: {s_txt}")
            operating_hours_text = "\n".join(h_lines)
    except: pass

    # Menu Formatting
    menu_lines = []
    if menu_items:
        for item in menu_items:
            price_str = f"{currency}{item.price}"
            if item.original_price and item.original_price > item.price:
                price_str += f" (Promo! Was {currency}{item.original_price})"
            
            meta = []
            if item.spiciness_level: meta.append(f"Spicines: {item.spiciness_level}/3")
            if item.prep_time: meta.append(f"Time: {item.prep_time}")
            meta_str = f" [{', '.join(meta)}]" if meta else ""
            
            menu_lines.append(f"- {item.name} ({price_str}): {item.labels or ''} {item.allergy_info or ''}.{meta_str}")
        menu_context = "\n".join(menu_lines)
    else:
        menu_context = "Menu items currently being updated."

    # Handoff Info
    mgr_contact = "Contact Management for support."
    handoff_reply = safe_get(kb, 'handoff_reply', 'Connecting you to staff.')
    try:
        h = json.loads(safe_get(kb, 'handoff_notifications') or '{}')
        if h: mgr_contact = f"Email: {h.get('email_address','-')} | WA: {h.get('wa_number','-')}"
    except: pass

    # Personality
    tone = safe_get(kb, 'personality_tone', 'friendly')
    
    return f"""
ROLE: JESSE, Concierge for {rest_name}. Status: {status_str}.
RULES: Fact-based only. COMPLAINTS -> {mgr_contact}.
Tone: {tone}
OPS: {operating_hours_text}
DATABASE:
{menu_context}
"""
