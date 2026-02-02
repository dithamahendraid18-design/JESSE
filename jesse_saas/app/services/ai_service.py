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
        
        # 1. Determine Provider (DB -> Env -> Default)
        provider = kb.ai_provider
        if not provider:
            provider = os.environ.get('LLM_PROVIDER', 'groq')
        
        provider = provider.lower()

        # 2a. Fetch Menu Data
        menu_items = MenuItem.query.filter_by(client_id=client_model.id, is_available=True).all()
        menu_text = "No menu items available."
        if menu_items:
            items_list = []
            for item in menu_items:
                price = f"${item.price}" # Assuming generic currency symbol or stored in client setting
                desc = f": {item.description}" if item.description else ""
                items_list.append(f"- {item.name} ({price}){desc}")
            menu_text = "\n".join(items_list)
        
        # 2b. Construct Final System Prompt (New Structured Template)
        
        # Helper: Gather Social Media Links
        social_links = []
        if client_model.instagram_url: social_links.append(f"Instagram: {client_model.instagram_url}")
        if client_model.whatsapp_url: social_links.append(f"WhatsApp: {client_model.whatsapp_url}")
        if client_model.tiktok_url: social_links.append(f"TikTok: {client_model.tiktok_url}")
        if client_model.youtube_url: social_links.append(f"YouTube: {client_model.youtube_url}")
        social_media_text = ", ".join(social_links) if social_links else "Follow us on social media for updates."

        # Helper: Delivery Partners JSON
        delivery_partners_txt = "Not currently listed."
        try:
            if client_model.delivery_partners:
                partners = json.loads(client_model.delivery_partners)
                if isinstance(partners, list):
                    delivery_partners_txt = ", ".join([f"{p.get('platform', 'Partner')}: {p.get('url', '')}" for p in partners])
                else:
                    delivery_partners_txt = str(client_model.delivery_partners)
        except:
             delivery_partners_txt = client_model.delivery_partners or 'Not currently listed.'

        # Helper: Seating & Privacy
        seating_data = client_model.seating_configuration or ""
        if client_model.has_private_room:
            seating_data += f" | Private Room Available (Capacity: {client_model.private_room_capacity or 'Unknown'})"
        
        # Helper: Menu Formatting (Detailed with Allergens)
        menu_items_detailed = []
        if menu_items:
            for item in menu_items:
                price_str = f"{client_model.currency_symbol}{item.price}"
                original_price_str = f" (Original: {client_model.currency_symbol}{item.original_price})" if item.original_price else ""
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

        # Helper: Personality Tone
        tone_map = {
            'professional': "Professional & Formal. Use polite language, avoid slang, and do not use emojis. Ideal for fine dining.",
            'friendly': "Friendly & Casual. Be warm, welcoming, and helpful. Use a conversational tone.",
            'energetic': "Enthusiastic & Energetic. Be upbeat, positive, and exciting. Use active verbs.",
            'luxury': "Luxury & Elegant. Be extremely polite, sophisticated, and polished. Use high-end vocabulary and no emojis.",
            'funny': "Funny & Witty. Be clever, humorous, and lighthearted while still being helpful."
        }
        emoji_map = {
            'none': "Do not use any emojis in your response.",
            'minimal': "Use emojis sparingly (maximum 1 per response).",
            'expressive': "Use emojis freely to add personality and warmth (multiple emojis allowed)."
        }
        length_map = {
            'concise': "Be concise and brief. To the point, respect the guest's time.",
            'detailed': "Be detailed and descriptive. Use storytelling to explain menu items and the experience."
        }
        
        tone_instruction = f"{tone_map.get(kb.personality_tone, tone_map['friendly'])} {emoji_map.get(kb.personality_emoji, emoji_map['minimal'])} {length_map.get(kb.personality_length, length_map['concise'])}"

        # Helper: Smart Operating Hours Parsing
        try:
            hours_json = json.loads(client_model.operating_hours or '{}')
            operating_hours_text = ""
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
                operating_hours_text = str(client_model.operating_hours or 'Open daily')
        except:
            operating_hours_text = str(client_model.operating_hours or 'Open daily')

        # Helper: Holidays Parsing
        holiday_text = "No upcoming special holidays."
        try:
            holidays = json.loads(kb.holiday_dates or '[]')
            if holidays:
                holiday_text = "\n".join([f"- {h['date']}: {h['name']}" for h in holidays if h.get('date')])
        except: pass

        # Helper: Last Order Buffer
        buffer_info = f"Last order is {kb.last_order_buffer} minutes before closing time." if (kb.use_last_order_buffer and kb.last_order_buffer) else "Last order is at closing time."

        # The Template Requested by User
        system_prompt = f"""### ROLE & IDENTITY
You are JESSE, the AI Concierge for {client_model.restaurant_name}.
Currency Used: {client_model.currency_code} ({client_model.currency_symbol})
{f"IMPORTANT: Start your very first interaction with: 'I am an AI assistant for {client_model.restaurant_name}.'" if client_model.show_ai_disclaimer else ""}

### TONE OF VOICE
- Your personality settings: {tone_instruction}
- Adjust your vocabulary and sentence structure to match this persona strictly.

Your goal is to assist guests with accurate information based ONLY on the context below.

### [1] REGIONAL & CONTACT CONTEXT
- Address: {client_model.address or kb.location_address or 'Contact restaurant for address'}
- Landmark/Directions: {client_model.direction_note or 'Located in ' + (client_model.address or 'the area')}
- Google Maps: {client_model.maps_url or 'Search for ' + client_model.restaurant_name}
- Parking: {kb.parking_info or client_model.parking_info or 'Available nearby'}
- Website: {client_model.website_url or 'Coming soon'}
- Contact: Phone {client_model.public_phone or kb.contact_phone or 'Not specified'} | Email {client_model.public_email or 'Not specified'}
- Social Media: {social_media_text}
- Operating Hours:
{operating_hours_text}
- Special Holidays (CLOSED on these dates):
{holiday_text}
- Last Order Policy: {buffer_info}
- Current Status: Check operating hours for current status (Timezone: {client_model.timezone})
- Delivery Partners: {delivery_partners_txt}

### [2] GUEST EXPERIENCE & RULES
- WiFi: SSID "{client_model.wifi_ssid or 'Ask Staff'}" | Pass "{client_model.wifi_password or kb.wifi_password or 'Ask Staff'}"
- Payment Methods: {kb.payment_methods or 'Cash and Major Cards'}
- Review Link: {client_model.review_url or 'Google/Social Media'}
- Reservations: {client_model.booking_url or kb.reservation_url or 'Walk-ins only'}
- Booking Policy: {kb.deposit_policy or 'No deposit required'} | {kb.late_arrival_policy or '15-min grace period'}
- House Rules & Context: {kb.policy_info or 'Standard dining etiquette'} | {kb.dietary_info or 'We accommodate major dietary needs'}
- Legal: Privacy Policy ({client_model.privacy_policy_url or 'Ask staff'}) | Terms of Service ({client_model.tos_url or 'Ask staff'})

### [3] FACILITIES & CAPACITY
- Seating Configuration: {seating_data or 'Various seating options'}
- Amenities: {client_model.facilities_list or 'Standard dining facilities'}
- Family & Kids: {client_model.family_facilities_list or 'Family-friendly environment'}

### [4] MENU DATABASE (TRUTH SOURCE)
Rules: You can ONLY recommend items listed here. Check ALLERGENS strictly.
{full_menu_database}

### INSTRUCTIONS
1. Use the [MENU DATABASE] to answer questions about food, price, portion, and allergens.
2. If a user asks to book a table, provide the {client_model.booking_url or kb.reservation_url or 'the reservation link'} and mention the {kb.deposit_policy or 'any deposit requirements'} if applicable.
3. If asked about location, combine the Address with the Landmark Note for clarity.
4. If asked about WiFi, provide the details immediately.
"""


        # 3. Determine API Key (DB first, then Env)
        api_key = kb.ai_api_key
        if not api_key:
            # Fallback to Env Vars based on provider
            if provider == 'openai':
                api_key = os.environ.get('OPENAI_API_KEY')
            elif provider == 'anthropic':
                api_key = os.environ.get('ANTHROPIC_API_KEY')
            elif provider == 'groq':
                api_key = os.environ.get('GROQ_API_KEY') or os.environ.get('LLM_API_KEY')
            elif provider == 'openai_compatible':
                api_key = os.environ.get('LLM_API_KEY')

        if not api_key:
            return f"System Error: AI API Key not configured for provider '{provider}'."

        # 4. Determine Model (DB -> Env -> Default)
        model = kb.ai_model
        if not model:
            if provider == 'openai':
                model = 'gpt-4o-mini'
            elif provider == 'anthropic':
                model = 'claude-3-haiku-20240307'
            elif provider == 'groq':
                model = 'llama-3.1-8b-instant'
            else:
                 # Generic Fallback
                 model = os.environ.get('LLM_MODEL', 'llama-3.1-8b-instant')

        # 5. Settings
        try:
            temp = float(kb.temperature) if kb.temperature is not None else 0.7
            max_tokens = int(kb.max_tokens) if kb.max_tokens else 300 # Increased for menu listing
        except:
            temp = 0.7
            max_tokens = 300

        # 6. Dispatch Request
        try:
            if provider == 'openai':
                return AIService._call_openai(api_key, model, system_prompt, user_message, temp, max_tokens)
            elif provider == 'anthropic':
                return AIService._call_anthropic(api_key, model, system_prompt, user_message, temp, max_tokens)
            elif provider == 'openai_compatible':
                 base_url = os.environ.get('LLM_BASE_URL', "https://api.groq.com/openai/v1")
                 return AIService._call_openai_compatible(api_key, base_url, model, system_prompt, user_message, temp, max_tokens)
            else:
                # Default to Groq
                return AIService._call_groq(api_key, model, system_prompt, user_message, temp, max_tokens)
                
        except Exception as e:
            print(f"AI Service Error ({provider}): {e}")
            return "I'm having trouble connecting to my brain right now. Please try again later."

    @staticmethod
    def _call_groq(api_key, model, system, user, temp, tokens):
        return AIService._call_openai_compatible(
            api_key, 
            "https://api.groq.com/openai/v1", 
            model, system, user, temp, tokens
        )

    @staticmethod
    def _call_openai(api_key, model, system, user, temp, tokens):
        return AIService._call_openai_compatible(
            api_key, 
            "https://api.openai.com/v1", 
            model, system, user, temp, tokens
        )

    @staticmethod
    def _call_openai_compatible(api_key, base_url, model, system, user, temp, tokens):
        # Normalize URL
        if base_url.endswith('/chat/completions'):
             base_url = base_url.replace('/chat/completions', '')
        base_url = base_url.rstrip('/')
        target_url = f"{base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temp,
            "max_tokens": tokens
        }
        resp = requests.post(target_url, headers=headers, json=payload, timeout=25)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    @staticmethod
    def _call_anthropic(api_key, model, system, user, temp, tokens):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "system": system,
            "messages": [
                {"role": "user", "content": user}
            ],
            "max_tokens": tokens,
            "temperature": temp
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()['content'][0]['text']

# Legacy Alias
def generate_smart_reply(user_message, client_model, kb):
    return AIService.generate_smart_reply(user_message, client_model, kb)
