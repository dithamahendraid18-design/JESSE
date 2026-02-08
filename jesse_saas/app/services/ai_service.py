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
    def generate_smart_reply(user_message, client_model, kb, history=None):
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
    
            # 2a. Fetch Menu Data (RAG Implementation)
            from app.services.vector_service import VectorService
            client_id = getattr(client_model, 'id', None)
            
            # Search relevant items based on user message
            menu_items = VectorService.search_menu(client_id, user_message, limit=7)
            
            menu_text = "No relevant menu items found for this query."
            if menu_items:
                items_list = []
                for item in menu_items:
                    price = f"${item.price}"
                    desc = f": {item.description}" if item.description else ""
                    items_list.append(f"- {item.name} ({price}){desc}")
                menu_text = "\n".join(items_list)
            
            # Fallback: If user asked for "Menu" generally (without specific food), 
            # and search returned nothing (e.g. query "show me menu"), 
            # we might want to show categories Top items?
            # For now, rely on RAG. If "show menu" embeds to nothing, we have a problem.
            # "show menu" usually matches everything or nothing? 
            # "Menu" vector vs "Burger" vector.
            # IMPROVEMENT: If query is very short/generic "Menu", maybe fetch popular items?
            # Leaving as RAG-only for now as requested.
            
            # 2b. Construct Final System Prompt
            
            # Social Media Links & Website
            social_links = []
            if safe_get(client_model, 'website_url'): social_links.append(f"Website: {client_model.website_url}")
            if safe_get(client_model, 'instagram_url'): social_links.append(f"Instagram: {client_model.instagram_url}")
            if safe_get(client_model, 'whatsapp_url'): social_links.append(f"WhatsApp: {client_model.whatsapp_url}")
            if safe_get(client_model, 'tiktok_url'): social_links.append(f"TikTok: {client_model.tiktok_url}")
            if safe_get(client_model, 'youtube_url'): social_links.append(f"YouTube: {client_model.youtube_url}")
            social_media_text = ", ".join(social_links) if social_links else "No social links listed."
    
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
                    # Promo price check
                    if item.original_price and item.original_price > item.price:
                        price_str = f"{currency}{item.price} (Special Promo! Was {currency}{item.original_price})"
                    
                    labels = item.labels if item.labels else ""
                    
                    # Extra metadata
                    meta = []
                    if item.spiciness_level and item.spiciness_level > 0:
                        meta.append(f"Spiciness: {item.spiciness_level}/3")
                    if item.prep_time:
                        meta.append(f"Prep Time: {item.prep_time}")
                    if item.portion_size:
                        meta.append(f"Portion: {item.portion_size}")
                    
                    meta_str = f" [{', '.join(meta)}]" if meta else ""
                    
                    allergens = f"Allergens: {item.allergy_info}" if item.allergy_info else "No allergens reported"
                    
                    # Format: "- Truffle Risotto ($28): Vegetarian, Contains Dairy. [Spiciness: 1/3, Prep Time: 15 mins]"
                    menu_items_detailed.append(
                        f"- {item.name} ({price_str}): {labels}{', ' if labels and allergens else ''}{allergens}.{meta_str}"
                    )
                full_database_context = "\n".join(menu_items_detailed)
            else:
                full_database_context = "Menu is currently being updated. Please ask staff for details."
    
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
                if isinstance(hours_json, dict) and len(hours_json) > 0:
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
            try:
                tz = pytz.timezone(tz_name)
            except pytz.UnknownTimeZoneError:
                # Fallback to UTC if timezone is invalid
                print(f"Invalid Timezone '{tz_name}' for client {client_model.restaurant_name}. Defaulting to UTC.")
                tz = pytz.utc
            
            now_in_tz = datetime.now(tz)
            is_open_now = AIService.check_restaurant_status(client_model, now_in_tz)
            status_str = "OPEN" if is_open_now else "CLOSED"



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
            family_facilities = safe_get(client_model, 'family_facilities_list') or 'None listed'

            # Special Holidays & Buffers
            holiday_text = "Standard schedule applies."
            try:
                holidays = safe_get(kb, 'holiday_dates')
                if holidays:
                    h_list = json.loads(holidays)
                    if h_list:
                        holiday_text = "\n".join([f"- {h['date']}: {h['name']}" for h in h_list])
            except: pass

            buffer_text = "None"
            if safe_get(kb, 'use_last_order_buffer'):
                buffer_text = f"{safe_get(kb, 'last_order_buffer', 30)} minutes before closing."

            # Policies
            dep_pol = safe_get(client_model, 'deposit_policy') or "No deposit required for standard bookings."
            late_pol = safe_get(client_model, 'late_arrival_policy') or "Tables are typically held for 15 minutes."

            # Dynamic Button Label Lookup
            menu_btn_label = "View Full Menu" # Default
            try:
                starters = safe_get(kb, 'conversation_starters')
                if starters:
                    s_list = json.loads(starters)
                    for s in s_list:
                        if s.get('action') == 'open_menu':
                            menu_btn_label = s.get('label', 'View Full Menu')
                            break
            except: pass

            # Final Template V3 (Token Optimized)
            rest_name = safe_get(client_model, 'restaurant_name', 'the restaurant')
            about_text = safe_get(kb, 'about_us') or f"Welcome to {rest_name}."
            
            system_prompt = f"""
### ROLE
You are JESSE, AI Concierge for {rest_name}.
- Goal: Answer queries & facilitate bookings. 
- Status: **{status_str}**.
- Currency: {safe_get(client_model, 'currency_code', 'USD')} ({currency})

### SAFETY RULES (ABSOLUTE)
1. **DANGER TRIGGERS:** If user mentions {TRIGGER_MUTLAK}:
   - STOP. Reply ONLY: "I apologize, but for safety reasons, please contact Management: {mgr_contact_info}"
2. **COMPLAINTS:** If user mentions {TRIGGER_KONTEKSTUAL} or is angry:
   - Empathize deeply. Reply: "{handoff_reply_custom}" & provide: {mgr_contact_info}.
3. **LIMITS:** No recipes, medical advice, or off-topic chat.
4. **NO HALLUCINATION:** Stick strictly to [MENU DATABASE].

### TONE
{tone_instruction} matches this persona. BE CONCISE.

### CONTEXT
- **About:** {about_text}
- **Location:** {safe_get(client_model, 'address') or 'N/A'}. {safe_get(client_model, 'direction_note') or ''}
- **Contact:** {safe_get(client_model, 'public_phone')} | {safe_get(client_model, 'public_email')}
- **Links:** {social_media_text}
- **WiFi:** SSID "{safe_get(client_model, 'wifi_ssid', '-')}" | Pass "{safe_get(client_model, 'wifi_password', '-')}"
- **Facilities:** {facilities_txt} | Family: {family_facilities} | Seating: {seating_data}

### OPERATIONS
- **Open:** {status_str}. (Server Time: {now_in_tz.strftime('%A %I:%M %p')})
- **Hours:**
{operating_hours_text}
- **Holidays:** {holiday_text}
- **Policy:** {safe_get(kb, 'policy_info', 'Standard rules.')} Deposit: {dep_pol}. Late: {late_pol}.
- **Payment:** {safe_get(kb, 'payment_methods', 'Cash/Cards')} | Tax: {safe_get(kb, 'tax_info', 'Included')}

### MENU DATABASE
{full_database_context}

### INSTRUCTIONS
1. Check **Status** ({status_str}) before inviting.
2. Allergens: Check [MENU DATABASE] tags. If unsure, say "Please ask staff".
3. **MENU:** If asked "Show menu", use button: [BUTTON:{menu_btn_label}|open_menu]
4. **LINKS:** Share links as buttons: [BUTTON:Label|link:URL]
5. End with a helpful closing/CTA.
            """

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
                # Handle None values explicitly (safe_get returns None if DB field is null)
                raw_temp = safe_get(kb, 'temperature')
                temp = float(raw_temp) if raw_temp is not None else 0.7
                
                raw_tokens = safe_get(kb, 'max_tokens')
                max_tokens = int(raw_tokens) if raw_tokens is not None else 1024
            except:
                temp, max_tokens = 0.7, 1024
    
            # 6. Dispatch
            try:
                if provider == 'openai':
                    return AIService._call_openai(api_key, model, system_prompt, user_message, temp, max_tokens, history)
                elif provider == 'anthropic':
                    return AIService._call_anthropic(api_key, model, system_prompt, user_message, temp, max_tokens, history)
                elif provider == 'openai_compatible':
                     base_url = os.environ.get('LLM_BASE_URL', "https://api.groq.com/openai/v1")
                     return AIService._call_openai_compatible(api_key, base_url, model, system_prompt, user_message, temp, max_tokens, history)
                else:
                    return AIService._call_groq(api_key, model, system_prompt, user_message, temp, max_tokens, history)
            except Exception as e:
                print(f"AI Provider Error ({provider}): {e}")
                return "I'm having trouble connecting to my brain right now. Please try again later."
        except Exception as e:
            print(f"AI Service Critical Error: {e}")
            import traceback
            traceback.print_exc()
            return "I'm having a technical issue processing your request. Please contact support."

    @staticmethod
    def _call_groq(api_key, model, system, user, temp, tokens, history):
        return AIService._call_openai_compatible(api_key, "https://api.groq.com/openai/v1", model, system, user, temp, tokens, history)

    @staticmethod
    def _call_openai(api_key, model, system, user, temp, tokens, history):
        return AIService._call_openai_compatible(api_key, "https://api.openai.com/v1", model, system, user, temp, tokens, history)

    @staticmethod
    def _call_openai_compatible(api_key, base_url, model, system, user, temp, tokens, history):
        if base_url.endswith('/chat/completions'): base_url = base_url.replace('/chat/completions', '')
        target_url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Build Messages: System -> History -> Current User Message
        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})
        
        payload = {"model": model, "messages": messages, "temperature": temp, "max_tokens": tokens}
        resp = requests.post(target_url, headers=headers, json=payload, timeout=25)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    @staticmethod
    def _call_anthropic(api_key, model, system, user, temp, tokens, history):
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        
        # Build Messages: History -> Current User Message
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})

        payload = {"model": model, "system": system, "messages": messages, "max_tokens": tokens, "temperature": temp}
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()['content'][0]['text']

def generate_smart_reply(user_message, client_model, kb, history=None):
    return AIService.generate_smart_reply(user_message, client_model, kb, history)
