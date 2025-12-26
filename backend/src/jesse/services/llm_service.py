from __future__ import annotations

import requests
import logging 

from ..config import Settings

# Setup logger agar kita bisa lihat error di terminal Render jika ada masalah
logger = logging.getLogger(__name__)

class LLMService:
    """
    Abstraction untuk LLM (provider bisa diganti tanpa ubah logic HybridService).

    Cocok untuk Groq karena Groq menyediakan endpoint OpenAI-compatible:
    base_url: https://api.groq.com/openai/v1
    endpoint: /chat/completions
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session = requests.Session()

    def is_configured(self) -> bool:
        """
        Dipakai untuk cek apakah LLM siap dipanggil (api key + base_url + model lengkap).
        """
        if self.settings.llm_provider == "mock":
            return False

        if self.settings.llm_provider in ("openai_compatible", "groq", "openai"):
            return bool(
                (self.settings.llm_base_url or "").strip()
                and (self.settings.llm_api_key or "").strip()
                and (self.settings.llm_model or "").strip()
            )

        return False

    def answer(self, system_prompt: str, user_message: str) -> str:
        # Mode aman (default): tidak panggil API
        if self.settings.llm_provider == "mock":
            return (
                "Thanks! (LLM is disabled right now). "
                "Please use the buttons for menu, hours, location, or contact 😊"
            )

        # Groq kita treat sebagai openai_compatible
        if self.settings.llm_provider in ("openai_compatible", "groq", "openai"):
            return self._openai_compatible(system_prompt, user_message)

        return "LLM provider not configured."

    def _openai_compatible(self, system_prompt: str, user_message: str) -> str:
        # Validasi config
        base = (self.settings.llm_base_url or "").strip()
        key = (self.settings.llm_api_key or "").strip()
        model = (self.settings.llm_model or "").strip()

        if not base or not key or not model:
            return "LLM is not fully configured."

        url = base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_message or ""},
            ],
            # --- SETTINGAN OPTIMAL ---
            "temperature": 0.4,  # 0.2 = Cerdas tapi Stabil (Tidak Halusinasi, Tidak Kaku)
            "max_tokens": 450,   # Batasi panjang jawaban (agar tidak ngobrol kepanjangan)
            "top_p": 0.9,        # Variasi kosa kata yang natural
        }

        try:
            r = self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=getattr(self.settings, "llm_timeout_seconds", 30),
            )
            r.raise_for_status() # Cek jika ada error HTTP (4xx/5xx)
            
            data = r.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.HTTPError as e:
            # Log error asli ke terminal Render (biar Anda tau kenapa error)
            logger.error(f"LLM API Error: {e.response.text}")
            return "Sorry, I'm having trouble connecting to my brain right now. Please try again or check the menu buttons! 🧠✨"
            
        except Exception as e:
            logger.error(f"LLM General Error: {e}")
            return "Oops! Something went wrong. Please use the menu buttons for now. 🙏"