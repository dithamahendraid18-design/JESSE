import os
import requests
import json
from flask import current_app
from app.models import MenuItem

class AIService:
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
                    original_price_str = f" (Original: {currency}{item.original_price})" if item.original_price else ""
                    spicy = f" | Spiciness: {item.spiciness_level}/3" if item.spiciness_level > 0 else ""
                    allergens = f" | ALLERGENS: {item.allergy_info}" if item.allergy_info else " | Allergens: None reported"
                    labels = f" | Tags: {item.labels}" if item.labels else ""
                    portion = f" | Portion: {item.portion_size}" if item.portion_size else ""
                    
                    menu_items_detailed.append(
                        f"[{item.category}] {item.name}: {price_str}{original_price_str}{portion}{spicy}{labels}{allergens} - {item.description or 'No description'}"
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
    
            # Operating Hours
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
    
            # Holidays
            holiday_text = "No upcoming special holidays."
            try:
                h_dates = safe_get(kb, 'holiday_dates')
                holidays = json.loads(h_dates or '[]')
                if holidays:
                    holiday_text = "\n".join([f"- {h['date']}: {h['name']}" for h in holidays if h.get('date')])
            except: pass
    
            # Last Order Buffer
            use_buf = safe_get(kb, 'use_last_order_buffer', False)
            buf_min = safe_get(kb, 'last_order_buffer', 0)
            buffer_info = f"Last order is {buf_min} minutes before closing time." if (use_buf and buf_min) else "Last order is at closing time."
    
            # Final Template
            rest_name = safe_get(client_model, 'restaurant_name', 'the restaurant')
            system_prompt = f"""### ROLE & IDENTITY
    You are JESSE, the AI Concierge for {rest_name}.
    Currency Used: {safe_get(client_model, 'currency_code', 'USD')} ({currency})
    {f"IMPORTANT: Start your very first interaction with: 'I am an AI assistant for {rest_name}.'" if safe_get(client_model, 'show_ai_disclaimer') else ""}
    
    ### TONE OF VOICE
    - Your personality settings: {tone_instruction}
    - Adjust your vocabulary and sentence structure to match this persona strictly.
    
    Your goal is to assist guests with accurate information based ONLY on the context below.
    
    ### [1] REGIONAL & CONTACT CONTEXT
    - Address: {safe_get(client_model, 'address') or safe_get(kb, 'location_address') or 'Contact restaurant for address'}
    - Landmark/Directions: {safe_get(client_model, 'direction_note') or 'Located in the area'}
    - Google Maps: {safe_get(client_model, 'maps_url') or 'Search for ' + rest_name}
    - Parking: {safe_get(kb, 'parking_info') or safe_get(client_model, 'parking_info') or 'Available nearby'}
    - Website: {safe_get(client_model, 'website_url') or 'Coming soon'}
    - Contact: Phone {safe_get(client_model, 'public_phone') or safe_get(kb, 'contact_phone') or 'Not specified'} | Email {safe_get(client_model, 'public_email', 'Not specified')}
    - Social Media: {social_media_text}
    - Operating Hours:
    {operating_hours_text}
    - Special Holidays:
    {holiday_text}
    - Last Order Policy: {buffer_info}
    - Delivery Partners: {delivery_partners_txt}
    
    ### [2] GUEST EXPERIENCE & RULES
    - WiFi: SSID "{safe_get(client_model, 'wifi_ssid', 'Ask Staff')}" | Pass "{safe_get(client_model, 'wifi_password') or safe_get(kb, 'wifi_password') or 'Ask Staff'}"
    - Payment Methods: {safe_get(kb, 'payment_methods') or 'Cash and Major Cards'}
    - Review Link: {safe_get(client_model, 'review_url') or 'Google/Social Media'}
    - Reservations: {safe_get(client_model, 'booking_url') or safe_get(kb, 'reservation_url') or 'Walk-ins only'}
    - Booking Policy: {safe_get(kb, 'deposit_policy') or 'No deposit required'} | {safe_get(kb, 'late_arrival_policy') or '15-min grace period'}
    - House Rules: {safe_get(kb, 'policy_info') or 'Standard etiquette'} | {safe_get(kb, 'dietary_info') or 'Dietary needs accommodated'}
    - Legal: Terms ({safe_get(client_model, 'tos_url', 'Ask staff')})
    
    ### [3] FACILITIES & CAPACITY
    - Seating: {seating_data or 'Various options'}
    - Amenities: {safe_get(client_model, 'facilities_list') or 'Standard dining facilities'}
    - Family & Kids: {safe_get(client_model, 'family_facilities_list', 'Family-friendly')}
    
    ### [4] MENU DATABASE
    {full_menu_database}
    
    ### INSTRUCTIONS
    1. Answer queries based on the database.
    2. Suggest booking via {safe_get(client_model, 'booking_url') or safe_get(kb, 'reservation_url') or 'the website'} if applicable.
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
