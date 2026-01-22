import os
import requests
import json
from flask import current_app

class AIService:
    @staticmethod
    def generate_smart_reply(user_message, client_model, kb):
        """
        Generates a response using the configured AI provider.
        Supports: Groq, OpenAI, Anthropic, and Generic OpenAI-Compatible (e.g. LocalLLM, Custom Groq).
        """
        
        # 1. Determine Provider (DB -> Env -> Default)
        provider = kb.ai_provider
        if not provider:
            provider = os.environ.get('LLM_PROVIDER', 'groq')
        
        provider = provider.lower()
        
        # 2. Construction System Prompt
        system_prompt = kb.system_prompt
        if not system_prompt:
             # Fallback default prompt
             system_prompt = f"""
You are the AI Concierge for {client_model.restaurant_name}.
Your job is to answer guest questions strictly based on the provided context.
Be polite, concise, and helpful. Keep responses under 50 words.

CONTEXT:
- About Us: {kb.about_us or 'Not specified'}
- Opening Hours: {kb.opening_hours or 'Not specified'}
- Address: {kb.location_address or 'Not specified'}
- WiFi Password: {kb.wifi_password or 'Ask staff'}
- Contact Phone: {kb.contact_phone or 'Not specified'}
- Menu Link: {kb.menu_url or 'Ask staff'}
- Reservation Link: {kb.reservation_url or 'Walk-ins welcome'}
- Payment Methods: {kb.payment_methods or 'Not specified'}
- Parking Info: {kb.parking_info or 'Not specified'}
- Dietary Options: {kb.dietary_info or 'Not specified'}
- Policy/Rules: {kb.policy_info or 'Standard restaurant rules apply'}

GUIDELINES:
- If the answer is in the context, provide it.
- If the answer is NOT in the context, apologize and suggest calling {kb.contact_phone or 'the restaurant'}.
- Do NOT make up facts.
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
            max_tokens = int(kb.max_tokens) if kb.max_tokens else 150
        except:
            temp = 0.7
            max_tokens = 150

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
        # Normalize URL (remove /chat/completions if present to avoid doubling)
        if base_url.endswith('/chat/completions'):
             base_url = base_url.replace('/chat/completions', '')
        
        # Ensure no trailing slash
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

# Legacy Alias for backward compatibility if imported directly
def generate_smart_reply(user_message, client_model, kb):
    return AIService.generate_smart_reply(user_message, client_model, kb)
