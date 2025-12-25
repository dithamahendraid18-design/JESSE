from __future__ import annotations

import requests

from ..config import Settings


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

        if self.settings.llm_provider in ("openai_compatible", "groq"):
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
        if self.settings.llm_provider in ("openai_compatible", "groq"):
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
            "temperature": 0.3,
        }

        try:
            r = self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=getattr(self.settings, "llm_timeout_seconds", 30),
            )
        except requests.RequestException:
            # Jangan bocorin detail error ke user (lebih aman untuk produk)
            return "Sorry — the AI service is temporarily unavailable. Please use the menu buttons 😊"

        if r.status_code >= 400:
            # Optional: kamu bisa log r.text di server untuk debugging
            return "Sorry — the AI service returned an error. Please try again or use the menu buttons 😊"

        try:
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            return "Sorry — I couldn't parse the AI response. Please use the menu buttons 😊"
