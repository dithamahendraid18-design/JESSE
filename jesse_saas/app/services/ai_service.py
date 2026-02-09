import os
import json
from datetime import datetime
from app.models import ChatMessage, MenuItem
from app.extensions import db
from app.services.vector_service import VectorService
from app.services.ai import utils, providers, context_builder

class AIService:
    @staticmethod
    def generate_smart_reply(user_message, client_model, kb, history=None, session_id=None):
        """
        Orchestrates AI response generation using modular components.
        """
        try:
            # 1. Memory Retrieval (if not provided)
            if not history and session_id:
                recent_msgs = ChatMessage.query.filter_by(
                    session_id=session_id, 
                    client_id=client_model.id
                ).order_by(ChatMessage.timestamp.desc()).limit(6).all()
                history = [{"role": "user" if m.sender == "user" else "assistant", "content": m.content} for m in reversed(recent_msgs)]

            # 2. Reflex Check (Deterministic Safety Layer)
            is_triggered, safety_response = utils.check_reflex_triggers(user_message, client_model, kb)
            if is_triggered:
                AIService._save_history(session_id, client_model.id, user_message, safety_response)
                return safety_response

            # 3. RAG: Search Menu Items
            menu_items = VectorService.search_menu(client_model.id, user_message, limit=7)

            # 4. Context & Prompt Building
            system_prompt = context_builder.build_system_prompt(client_model, kb, menu_items)
            
            # 5. Determine Provider & Parameters
            provider = utils.safe_get(kb, 'ai_provider') or os.environ.get('LLM_PROVIDER', 'groq')
            temp = float(utils.safe_get(kb, 'temperature', 0.7))
            max_tokens = int(utils.safe_get(kb, 'max_tokens', 1024))
            
            # Provider fallback list
            providers_to_try = [provider.lower()]
            for backup in ['groq', 'openai', 'anthropic']:
                if backup not in providers_to_try: providers_to_try.append(backup)

            # 6. Provider Loop (Execution)
            ai_response = None
            for p in providers_to_try:
                try:
                    # Resolve Auth & Model
                    api_key = os.environ.get(f"{p.upper()}_API_KEY") or os.environ.get('LLM_API_KEY')
                    if p == provider.lower() and utils.safe_get(kb, 'ai_api_key'):
                        api_key = kb.ai_api_key
                    
                    if not api_key: continue
                    
                    model = utils.safe_get(kb, 'ai_model') if p == provider.lower() else None
                    if not model:
                        model = {'openai': 'gpt-4o-mini', 'anthropic': 'claude-3-haiku-20240307', 'groq': 'llama-3.1-8b-instant'}.get(p)

                    # Call Provider
                    if p == 'openai':
                        ai_response = providers.call_openai(api_key, model, system_prompt, user_message, temp, max_tokens, history)
                    elif p == 'anthropic':
                        ai_response = providers.call_anthropic(api_key, model, system_prompt, user_message, temp, max_tokens, history)
                    else:
                        ai_response = providers.call_groq(api_key, model, system_prompt, user_message, temp, max_tokens, history)
                    
                    if ai_response: break
                except Exception as e:
                    print(f"AI Provider '{p}' failed: {e}")
                    continue

            # 7. Post-Processing & Persistence
            if not ai_response:
                ai_response = "I'm having trouble connecting right now. Please try again or contact us directly."
            
            ai_response = utils.sanitize_response(ai_response)
            AIService._save_history(session_id, client_model.id, user_message, ai_response)
            
            return ai_response

        except Exception as e:
            print(f"AI Service Error: {e}")
            return "I'm temporarily unavailable. Please check back later."

    @staticmethod
    def _save_history(session_id, client_id, user_msg, ai_msg):
        if session_id:
            try:
                db.session.add(ChatMessage(session_id=session_id, client_id=client_id, sender="user", content=user_msg))
                db.session.add(ChatMessage(session_id=session_id, client_id=client_id, sender="assistant", content=ai_msg))
                db.session.commit()
            except:
                db.session.rollback()

# Compatibility helper
def generate_smart_reply(user_message, client_model, kb, history=None, session_id=None):
    return AIService.generate_smart_reply(user_message, client_model, kb, history, session_id=session_id)
