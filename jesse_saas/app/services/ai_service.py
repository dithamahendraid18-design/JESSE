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
        
        # 2b. Construct Final System Prompt
        # Strategy: Combine User Persona (or Default) + Data Context + Menu + Guidelines
        
        # A. Persona (Role & Tone)
        persona = kb.system_prompt
        if not persona:
             persona = f"""You are the AI Concierge for {client_model.restaurant_name}.
Your job is to answer guest questions strictly based on the provided context.
Be polite, concise, and helpful. Keep responses under 50 words."""

        # Helper: Try to parse JSON starters if flow fields are missing
        c_starters = []
        try:
            if kb.conversation_starters:
                c_starters = json.loads(kb.conversation_starters)
        except:
            c_starters = []

        # Map actions to field names for fallback
        # action_name -> (kb_field_value, context_label)
        # We only need to extract text if the explicit field is empty
        
        def get_flow_text(field_val, action_target):
            if field_val: return field_val
            # Find in starters
            for btn in c_starters:
                if btn.get('action') == action_target:
                    return btn.get('response_text') or btn.get('payload') or ''
            return ''

        about_txt = get_flow_text(kb.flow_about, 'about')
        hours_txt = get_flow_text(kb.flow_hours, 'hours')
        loc_txt = get_flow_text(kb.flow_location, 'location')
        contact_txt = get_flow_text(kb.flow_contact, 'contact')
        # Menu intro often in 'menu' action or just explicit
        menu_intro = get_flow_text(kb.flow_menu, 'menu') or get_flow_text(None, 'main_menu')

        # B. Data Context (Auto-injected from Client Hub)
        context_data = f"""
CONTEXT (Read-Only):
- About Us: {kb.about_us or about_txt or 'Not specified'}
- Opening Hours: {kb.opening_hours or hours_txt or 'Not specified'}
- Address/Location: {kb.location_address or 'Not specified'}
- Location Details: {loc_txt or ''}
- WiFi Password: {kb.wifi_password or 'Ask staff'}
- Contact Phone: {kb.contact_phone or 'Not specified'}
- Contact Details: {contact_txt or ''}
- Reservation Link: {kb.reservation_url or 'Walk-ins welcome'}
- Menu Introduction: {menu_intro or ''}
- Payment Methods: {kb.payment_methods or 'Not specified'}
- Parking Info: {kb.parking_info or 'Not specified'}
- Dietary Options: {kb.dietary_info or 'Not specified'}
- Policy: {kb.policy_info or 'Standard rules'}
"""

        # C. Menu Context (Already fetched above)
        menu_context = f"\nMENU ITEMS (Live Database):\n{menu_text}\n"

        # D. Functional Guidelines
        guidelines = f"""
GUIDELINES:
- You represent {client_model.restaurant_name}. Use the tone defined in the persona above.
- Use the CONTEXT and MENU ITEMS to answer questions.
- If specific ingredients are not listed in the menu, do not make them up.
- If the answer is NOT in the context, apologize and suggest calling {kb.contact_phone or 'the restaurant'}.
- If the user asks to see the menu, answer politely AND append: [BUTTON:View Menu|open_menu]
- If the user asks for a reservation, answer polite AND append: [BUTTON:Book a Table|link:{kb.reservation_url or '#'}]
"""

        # Combine All
        system_prompt = f"{persona}\n{context_data}\n{menu_context}\n{guidelines}"

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
