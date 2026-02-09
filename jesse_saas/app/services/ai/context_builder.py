import json
from datetime import datetime
import pytz
from app.services.ai.utils import safe_get, check_restaurant_status

def build_system_prompt(client_model, kb, menu_items):
    # --- 1. Identity & Status ---
    rest_name = safe_get(client_model, 'restaurant_name', 'the restaurant')
    currency = safe_get(client_model, 'currency_symbol', '$')
    
    tz_name = safe_get(client_model, 'timezone', 'UTC')
    try: tz = pytz.timezone(tz_name)
    except: tz = pytz.utc
    now_in_tz = datetime.now(tz)
    
    is_open_now = check_restaurant_status(client_model, now_in_tz)
    status_str = "OPEN" if is_open_now else "CLOSED"
    
    # --- 2. Operating Hours ---
    operating_hours_text = "Open daily"
    try:
        op_hours = safe_get(client_model, 'operating_hours')
        hours_json = json.loads(op_hours or '{}')
        if isinstance(hours_json, dict) and len(hours_json) > 0:
            h_lines = []
            # Sort days to be predictable
            days_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for day in days_order:
                if day in hours_json:
                    data = hours_json[day]
                    if data.get('is_closed'):
                        h_lines.append(f"- {day.capitalize()}: CLOSED")
                    else:
                        shifts = data.get('shifts', [])
                        if not shifts:
                            h_lines.append(f"- {day.capitalize()}: CLOSED (No shifts)")
                        else:
                            formatted_shifts = []
                            for s in shifts:
                                start, end = s['start'], s['end']
                                if end == "00:00": end = "24:00 (Midnight)"
                                formatted_shifts.append(f"{start}-{end}")
                            h_lines.append(f"- {day.capitalize()}: {', '.join(formatted_shifts)}")
            operating_hours_text = "\n".join(h_lines)
        else:
            # Fallback to KB text or raw field
            operating_hours_text = safe_get(kb, 'opening_hours') or str(op_hours or 'Open daily')
    except:
        operating_hours_text = safe_get(kb, 'opening_hours') or 'Open daily'

    # --- 3. Menu Data (RAG) ---
    menu_items_detailed = []
    if menu_items:
        for item in menu_items:
            price_str = f"{currency}{item.price}"
            if item.original_price and item.original_price > item.price:
                price_str = f"{currency}{item.price} (Promo! Was {currency}{item.original_price})"
            
            meta = []
            if item.spiciness_level: meta.append(f"Spiciness: {item.spiciness_level}/3")
            if item.prep_time: meta.append(f"Prep: {item.prep_time}")
            if item.portion_size: meta.append(f"Portion: {item.portion_size}")
            meta_str = f" [{', '.join(meta)}]" if meta else ""
            
            labels = f"Tags: {item.labels}. " if item.labels else ""
            allergens = f"Allergens: {item.allergy_info}. " if item.allergy_info else ""
            
            menu_items_detailed.append(
                f"- {item.name} ({price_str}): {labels}{allergens}{item.description or ''}{meta_str}"
            )
        full_database_context = "\n".join(menu_items_detailed)
    else:
        full_database_context = "Menu data is currently being updated. Please ask for our current specialties."

    # --- 4. Handoff & Contact ---
    mgr_contact = "Contact Management"
    handoff_reply = safe_get(kb, 'handoff_reply', 'I will connect you to our manager.')
    try:
        h_json = json.loads(safe_get(kb, 'handoff_notifications') or '{}')
        if h_json:
            mgr_contact = f"Email: {h_json.get('email_address','-')} | WA: {h_json.get('wa_number','-')}"
    except: pass

    # --- 5. Personality & Tone ---
    p_tone = safe_get(kb, 'personality_tone', 'friendly')
    p_emoji = safe_get(kb, 'personality_emoji', 'minimal')
    p_length = safe_get(kb, 'personality_length', 'concise')
    tone_instruction = f"Tone: {p_tone}. Emojis: {p_emoji}. Length: {p_length}."

    # --- 6. Facilities & Location ---
    facilities = safe_get(client_model, 'facilities_list') or 'None specified'
    family = safe_get(client_model, 'family_facilities_list') or 'None specified'
    wifi = f"SSID: {safe_get(client_model, 'wifi_ssid', '-')}, PW: {safe_get(client_model, 'wifi_password', '-')}"
    address = safe_get(client_model, 'address', 'N/A')
    
    # --- 7. Final System Prompt V4 ---
    return f"""
ROLE: JESSE, Concierge for {rest_name}. Status: {status_str}.
RULES: Fact-based only. Use [DATABASE] for facts. If unsure, COMPLAINTS -> {mgr_contact}.
{tone_instruction}

ABOUT: {safe_get(kb, 'about_us') or f'Welcome to {rest_name}.'}
LOCATION: {address}. {safe_get(client_model, 'direction_note', '')}
CONTACT: {safe_get(client_model, 'public_phone', '-')} | {safe_get(client_model, 'public_email', '-')}
WIFI: {wifi}
FACILITIES: {facilities} | Family: {family}

OPS (Hours in {tz_name}):
{operating_hours_text}

POLICIES: {safe_get(kb, 'policy_info', 'Standard')} | Dep: {safe_get(client_model, 'deposit_policy', '-')} | Late: {safe_get(client_model, 'late_arrival_policy', '-')}
PAYMENT: {safe_get(kb, 'payment_methods', 'Cash/Cards')} | Tax: {safe_get(kb, 'tax_info', 'Inc')}

DATABASE (Relevant Items):
{full_database_context}

ACTIONS:
1. Check Status ({status_str}).
2. Menu Button: [BUTTON:View Menu|open_menu]
3. Map/Link: [BUTTON:Google Maps|link:{safe_get(client_model, 'maps_url', '#')}]
"""
