import json
import re
from datetime import datetime
import pytz

def safe_get(obj, attr, default=None):
    return getattr(obj, attr, default) if obj else default

def check_restaurant_status(client_model, current_time):
    """Checks if the restaurant is open based on operating_hours JSON and current_time."""
    try:
        op_hours = getattr(client_model, "operating_hours", None)
        if not op_hours:
            return True

        hours_json = json.loads(op_hours)
        day_name = current_time.strftime("%A").lower()

        if day_name not in hours_json:
            return False

        day_data = hours_json[day_name]
        if day_data.get("is_closed"):
            return False

        current_hhmm = current_time.strftime("%H:%M")
        shifts = day_data.get("shifts", [])

        for shift in shifts:
            start = shift.get("start")
            end = shift.get("end")
            if start and end:
                if start <= current_hhmm <= end:
                    return True
        return False
    except:
        return True

def sanitize_response(text):
    """Fixes common AI hallucinations in button syntax."""
    if not text: return text
    
    # 1. Fix Brackets: (BUTTON:...) -> [BUTTON:...]
    text = re.sub(r'\(BUTTON:', '[BUTTON:', text, flags=re.IGNORECASE)
    text = re.sub(r'\{BUTTON:', '[BUTTON:', text, flags=re.IGNORECASE)
    
    # 2. Fix Spacing in Tag: [ BUTTON : ... ] -> [BUTTON:...]
    text = re.sub(r'\[\s*BUTTON\s*:', '[BUTTON:', text, flags=re.IGNORECASE)
    
    # 3. Fix pipe spacing: | link: -> |link:
    text = re.sub(r'\|\s*link\s*:', '|link:', text, flags=re.IGNORECASE)
    text = re.sub(r'\|\s*open_menu', '|open_menu', text, flags=re.IGNORECASE)
    
    return text

TRIGGER_MUTLAK = [
    "poison", "racun", "police", "polisi", "suicide", "bunuh diri", "scam", "penipuan", 
    "illegal", "narkoba", "drugs", "assault", "emergency", "darurat", "fire", "kebakaran",
    "medical", "medis", "injury", "luka", "allergic reaction", "alergi parah", "hospital",
    "sexual harassment", "pelecehan", "theft", "pencurian", "robbery", "rampok", "threat", "ancaman"
]

def check_reflex_triggers(user_message, client_model, kb):
    """Deterministic Layer: Checks for high-risk keywords BEFORE calling AI."""
    msg_lower = user_message.lower()
    
    for keyword in TRIGGER_MUTLAK:
        if keyword in msg_lower:
            mgr_email = "management"
            mgr_phone = getattr(client_model, 'public_phone', 'staff') or "staff"
            try:
                handoff = getattr(kb, 'handoff_notifications', None)
                if handoff:
                    h_json = json.loads(handoff)
                    if h_json.get('email_address'): mgr_email = h_json['email_address']
                    if h_json.get('wa_number'): mgr_phone = h_json['wa_number']
            except: pass
            
            mgr_info = f"Email: {mgr_email} | WhatsApp: {mgr_phone}"
            return True, f"I apologize, but for safety and security reasons, I cannot process this request. Please contact Management immediately: {mgr_info}"

    return False, None
