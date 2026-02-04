import os
import requests
import json
from datetime import datetime
import pytz
from flask import current_app
from app.models import MenuItem

class AIService:
    @staticmethod
    def check_restaurant_status(client_model, current_time):
        """
        Checks if the restaurant is open based on operating_hours JSON and current_time.
        """
        try:
            op_hours = getattr(client_model, "operating_hours", None)
            if not op_hours:
                return True  # Default to open if no hours set

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
            return True  # Fallback to avoid breaking things

    @staticmethod
    def generate_smart_reply(user_message, client_model, kb):
        """
        Generates a response using the configured AI provider.
        Supports: Groq, OpenAI, Anthropic, and Generic OpenAI-Compatible.
        Injects MENU DATA into context.
        """
        try:
            # Helper to get attributes safely from kb or client_model
            def safe_get(obj, attr, default=None):
                return getattr(obj, attr, default) if obj else default

            # 1. Determine Provider (DB -> Env -> Default)
            provider = safe_get(kb, 'ai_provider')
            if not provider:
                provider = os.environ.get('LLM_PROVIDER', 'groq')
            
            provider = provider.lower()
    
            # 2a. Fetch Menu Data
            client_id = getattr(client_model, 'id', None)
            menu_items = MenuItem.query.filter_by(client_id=client_id, is_available=True).all() if client_id else []
            menu_text = "No menu items available."
            if menu_items:
                items_list = []
                for item in menu_items:
                    price = f"${item.price}"
                    desc = f": {item.description}" if item.description else ""
                    items_list.append(f"- {item.name} ({price}){desc}")
                menu_text = "\n".join(items_list)
            
            # 2b. Construct Final System Prompt
            
            # Social Media Links
            social_links = []
            if safe_get(client_model, 'instagram_url'): social_links.append(f"Instagram: {client_model.instagram_url}")
            if safe_get(client_model, 'whatsapp_url'): social_links.append(f"WhatsApp: {client_model.whatsapp_url}")
            if safe_get(client_model, 'tiktok_url'): social_links.append(f"TikTok: {client_model.tiktok_url}")
            if safe_get(client_model, 'youtube_url'): social_links.append(f"YouTube: {client_model.youtube_url}")
            social_media_text = ", ".join(social_links) if social_links else "Follow us on social media for updates."
    
            # Delivery Partners
            delivery_partners_txt = "Not currently listed."
            try:
                dp = safe_get(client_model, 'delivery_partners')
                if dp:
                    partners = json.loads(dp)
                    if isinstance(partners, list):
                        delivery_partners_txt = ", ".join([f"{p.get('platform', 'Partner')}: {p.get('url', '')}" for p in partners])
                    else:
                        delivery_partners_txt = str(dp)
            except:
                  delivery_partners_txt = safe_get(client_model, 'delivery_partners') or 'Not currently listed.'
    
            # Seating & Privacy
            seating_data = safe_get(client_model, 'seating_configuration') or ""
            if safe_get(client_model, 'has_private_room'):
                seating_data += f" | Private Room Available (Capacity: {safe_get(client_model, 'private_room_capacity') or 'Unknown'})"
            
            # Menu Formatting
            menu_items_detailed = []
            currency = safe_get(client_model, 'currency_symbol', '$')
            if menu_items:
                for item in menu_items:
                    price_str = f"{currency}{item.price}"
                    labels = item.labels if item.labels else ""
                    allergens = f"Allergens: {item.allergy_info}" if item.allergy_info else "No allergens reported"
                    
                    # Format: "- Truffle Risotto ($28): Vegetarian, Contains Dairy."
                    menu_items_detailed.append(
                        f"- {item.name} ({price_str}): {labels}{', ' if labels and allergens else ''}{allergens}."
                    )
                full_menu_database = "\n".join(menu_items_detailed)
            else:
                full_menu_database = "Menu is currently being updated. Please ask staff for details."
    
            # Personality Tone
            tone_map = {
                'professional': "Professional & Formal. Use polite language, avoid slang, and do not use emojis.",
                'friendly': "Friendly & Casual. Be warm, welcoming, and helpful.",
                'energetic': "Enthusiastic & Energetic. Be upbeat, positive, and exciting.",
                'luxury': "Luxury & Elegant. Be extremely polite, sophisticated, and polished.",
                'funny': "Funny & Witty. Be clever, humorous, and lighthearted."
            }
            emoji_map = {'none': "No emojis.", 'minimal': "Max 1 emoji.", 'expressive': "Emojis allowed."}
            length_map = {'concise': "Be concise.", 'detailed': "Be detailed."}
            
            p_tone = safe_get(kb, 'personality_tone', 'friendly')
            p_emoji = safe_get(kb, 'personality_emoji', 'minimal')
            p_length = safe_get(kb, 'personality_length', 'concise')
            tone_instruction = f"{tone_map.get(p_tone, tone_map['friendly'])} {emoji_map.get(p_emoji, emoji_map['minimal'])} {length_map.get(p_length, length_map['concise'])}"
    
        # --- [1] LOGIKA WAKTU (Backend Calculation) ---
        operating_hours_text = "Open daily"
        try:
            op_hours = safe_get(client_model, 'operating_hours')
            hours_json = json.loads(op_hours or '{}')
            if isinstance(hours_json, dict) and 'monday' in hours_json:
                h_lines = []
                for day, data in hours_json.items():
                    if data.get('is_closed'):
                        h_lines.append(f"- {day.capitalize()}: CLOSED")
                    else:
                        shifts = data.get('shifts', [])
                        shift_str = ", ".join([f"{s['start']}-{s['end']}" for s in shifts])
                        h_lines.append(f"- {day.capitalize()}: {shift_str}")
                operating_hours_text = "\n".join(h_lines)
            else:
                operating_hours_text = str(op_hours or 'Open daily')
        except: pass

        tz_name = safe_get(client_model, 'timezone', 'UTC')
        now_in_tz = datetime.now(pytz.timezone(tz_name))
        is_open_now = AIService.check_restaurant_status(client_model, now_in_tz)
        status_str = "OPEN" if is_open_now else "CLOSED"

        # --- [2] LOGIKA EKSTRA (Social & Delivery) ---
        social_links = []
        if safe_get(client_model, 'instagram_url'): social_links.append(f"Instagram: {client_model.instagram_url}")
        if safe_get(client_model, 'whatsapp_url'): social_links.append(f"WhatsApp: {client_model.whatsapp_url}")
        if safe_get(client_model, 'tiktok_url'): social_links.append(f"TikTok: {client_model.tiktok_url}")
        if safe_get(client_model, 'youtube_url'): social_links.append(f"YouTube: {client_model.youtube_url}")
        social_media_text = ", ".join(social_links) if social_links else "Follow us on social media for updates."

        delivery_partners_txt = "Not currently listed."
        try:
            dp = safe_get(client_model, 'delivery_partners')
            if dp:
                partners = json.loads(dp)
                if isinstance(partners, list):
                    delivery_partners_txt = ", ".join([f"{p.get('platform', 'Partner')}: {p.get('url', '')}" for p in partners])
        except: pass

        # --- [3] CONTACT INFO HANDOFF (Manager) ---
        mgr_email = "the manager"
        mgr_phone = safe_get(client_model, 'public_phone') or "staff"
        
        try:
            handoff = safe_get(kb, 'handoff_notifications')
            if handoff:
                h_json = json.loads(handoff)
                if h_json.get('email_address'): mgr_email = h_json['email_address']
                if h_json.get('wa_number'): mgr_phone = h_json['wa_number']
        except: pass

        mgr_contact_info = f"Email: {mgr_email} | WhatsApp: {mgr_phone}"
        handoff_reply_custom = safe_get(kb, 'handoff_reply', 'I will connect you to our manager immediately to resolve this.')
        
        # Replace placeholders for better UI/UX sync
        handoff_reply_custom = handoff_reply_custom.replace('{{public_phone}}', safe_get(client_model, 'public_phone', 'staff contact'))
        handoff_reply_custom = handoff_reply_custom.replace('{{public_email}}', safe_get(client_model, 'public_email', 'management email'))
        handoff_reply_custom = handoff_reply_custom.replace('{{mgr_contact}}', mgr_contact_info)

        # --- [4] HARDCODED TRIGGERS (Absolute vs Contextual) ---
        # TRIGGER_MUTLAK: High-risk/Illegal/Emergency. AI MUST provide contact politely but immediately.
        TRIGGER_MUTLAK = [
            "poison", "racun", "police", "polisi", "suicide", "bunuh diri", "scam", "penipuan", 
            "illegal", "narkoba", "drugs", "assault", "emergency", "darurat", "fire", "kebakaran",
            "medical", "medis", "injury", "luka", "allergic reaction", "alergi parah", "hospital",
            "sexual harassment", "pelecehan", "theft", "pencurian", "robbery", "rampok", "threat", "ancaman"
        ]
        # TRIGGER_KONTEKSTUAL: Service issues/Feedback. AI speaks with empathy then hands off.
        TRIGGER_KONTEKSTUAL = [
            "complaint", "komplain", "kecewa", "angry", "marah", "rude", "kasar", "refund", 
            "pengembalian", "manager", "atasan", "owner", "bad service", "pelayanan buruk",
            "hair in food", "rambut di makanan", "cold food", "makanan dingin", "dirty", "kotor",
            "wrong order", "salah pesanan", "overcharged", "mahal sekali", "disappointed",
            "unprofessional", "slow service", "lama sekali", "terrible", "buruk"
        ]

        # --- [5] DATA REFINEMENT (Internationalization) ---
        facilities_txt = safe_get(client_model, 'facilities_list') or 'Not specified'
        facilities_txt = facilities_txt.replace('Mushola', 'Prayer Room')

        # Final Template V2 (Optimized)
        rest_name = safe_get(client_model, 'restaurant_name', 'the restaurant')
        system_prompt = f"""
### IDENTITY & ROLE
You are JESSE, the specialized AI Concierge for {rest_name}.
- Your Goal: Serve guests, answer questions about the menu/venue, and facilitate bookings.
- Current Status: The restaurant is currently **{status_str}**.
- Currency: {safe_get(client_model, 'currency_code', 'USD')} ({currency})

### CRITICAL RULES (SAFETY & BEHAVIOR)
1. **TRIGGER MUTLAK (ABSOLUTE):** If user mentions keywords from this list: {TRIGGER_MUTLAK}.
   - **ACTION:** STOP all other tasks. 
   - **REPLY ONLY WITH:** "I apologize, but for safety and legal reasons, I cannot handle this request directly. Please contact our Management immediately at: {mgr_contact_info}"
2. **TRIGGER KONTEKSTUAL (CONTEXTUAL):** If user mentions keywords from this list: {TRIGGER_KONTEKSTUAL} or shows frustration/anger.
   - **ACTION:** Show high empathy. Apologize sincerely.
   - **REPLY:** Use this specific message provided by management: "{handoff_reply_custom}". Then, ensure they have the contact info: {mgr_contact_info}.
3. **SCOPE LIMIT:** - You are a Concierge, NOT a Chef. Do NOT provide recipes.
   - You are NOT a Doctor. Do NOT give medical advice.
   - If asked about topics outside the restaurant (politics, math, etc.), politely decline.
4. **NO HALLUCINATION:** If an item is NOT in the [MENU DATABASE], say it is unavailable. Do NOT invent menu items.

### TONE & STYLE
- Tone Instruction: {tone_instruction}
- Adjust vocabulary to match this persona strictly.
- Keep answers concise and helpful.

### [1] CONTEXT: LOCATION & OPS
- Address: {safe_get(client_model, 'address') or 'Please contact us for address'}
- Directions: {safe_get(client_model, 'direction_note') or 'Nearby'}
- Parking: {safe_get(client_model, 'parking_info') or 'Public parking available'}
- Contact: {safe_get(client_model, 'public_phone')} | {safe_get(client_model, 'public_email')}
- Social Media: {social_media_text}
- Delivery Partners: {delivery_partners_txt}
- WiFi: SSID "{safe_get(client_model, 'wifi_ssid', 'Ask Staff')}" | Pass "{safe_get(client_model, 'wifi_password', 'Ask Staff')}"
- **Operating Hours:**
{operating_hours_text}
- **Current Time (Server):** {now_in_tz.strftime('%A, %Y-%m-%d %I:%M %p')}
- **Open Status:** {status_str} (Trust this status over the hours list).

### [2] GUEST POLICIES
- Payment: {safe_get(kb, 'payment_methods', 'Cash & Cards')}
- Reservation: {safe_get(client_model, 'booking_url') or 'Walk-ins welcome'}
- Policy: {safe_get(kb, 'policy_info', 'Standard rules apply')}
- Tax/Gratuity Info: {safe_get(kb, 'tax_info', 'Included in prices unless specified')}

### [3] FACILITIES
- Seating: {seating_data}
- Facilities: {facilities_txt} (e.g., Wheelchair access, Prayer room)

### [4] MENU DATABASE
(Use this data strictly for food queries. Check allergens carefully.)
{full_menu_database}

### RESPONSE INSTRUCTIONS
1. Check the **Current Status** ({status_str}) before inviting guests.
2. If asked about allergens (Vegan, Nut-free), CHECK the tags in [MENU DATABASE]. If unsure, say "I cannot guarantee, please ask staff."
3. End with a helpful question or Call-to-Action (e.g., "Would you like to book a table?").
"""
    
            # 3. API Key
            api_key = safe_get(kb, 'ai_api_key')
            if not api_key:
                if provider == 'openai': api_key = os.environ.get('OPENAI_API_KEY')
                elif provider == 'anthropic': api_key = os.environ.get('ANTHROPIC_API_KEY')
                elif provider == 'groq': api_key = os.environ.get('GROQ_API_KEY') or os.environ.get('LLM_API_KEY')
                elif provider == 'openai_compatible': api_key = os.environ.get('LLM_API_KEY')
    
            if not api_key: return f"System Error: API Key missing for '{provider}'."
    
            # 4. Model
            model = safe_get(kb, 'ai_model')
            if not model:
                if provider == 'openai': model = 'gpt-4o-mini'
                elif provider == 'anthropic': model = 'claude-3-haiku-20240307'
                else: model = 'llama-3.1-8b-instant'
    
            # 5. Settings
            try:
                temp = float(safe_get(kb, 'temperature', 0.7))
                max_tokens = int(safe_get(kb, 'max_tokens', 300))
            except:
                temp, max_tokens = 0.7, 300
    
            # 6. Dispatch
            try:
                if provider == 'openai':
                    return AIService._call_openai(api_key, model, system_prompt, user_message, temp, max_tokens)
                elif provider == 'anthropic':
                    return AIService._call_anthropic(api_key, model, system_prompt, user_message, temp, max_tokens)
                elif provider == 'openai_compatible':
                     base_url = os.environ.get('LLM_BASE_URL', "https://api.groq.com/openai/v1")
                     return AIService._call_openai_compatible(api_key, base_url, model, system_prompt, user_message, temp, max_tokens)
                else:
                    return AIService._call_groq(api_key, model, system_prompt, user_message, temp, max_tokens)
            except Exception as e:
                print(f"AI Provider Error ({provider}): {e}")
                return "I'm having trouble connecting to my brain right now. Please try again later."
        except Exception as e:
            print(f"AI Service Critical Error: {e}")
            import traceback
            traceback.print_exc()
            return "I'm having a technical issue processing your request. Please contact support."

    @staticmethod
    def _call_groq(api_key, model, system, user, temp, tokens):
        return AIService._call_openai_compatible(api_key, "https://api.groq.com/openai/v1", model, system, user, temp, tokens)

    @staticmethod
    def _call_openai(api_key, model, system, user, temp, tokens):
        return AIService._call_openai_compatible(api_key, "https://api.openai.com/v1", model, system, user, temp, tokens)

    @staticmethod
    def _call_openai_compatible(api_key, base_url, model, system, user, temp, tokens):
        if base_url.endswith('/chat/completions'): base_url = base_url.replace('/chat/completions', '')
        target_url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": temp, "max_tokens": tokens}
        resp = requests.post(target_url, headers=headers, json=payload, timeout=25)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    @staticmethod
    def _call_anthropic(api_key, model, system, user, temp, tokens):
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        payload = {"model": model, "system": system, "messages": [{"role": "user", "content": user}], "max_tokens": tokens, "temperature": temp}
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()['content'][0]['text']

def generate_smart_reply(user_message, client_model, kb):
    return AIService.generate_smart_reply(user_message, client_model, kb)
