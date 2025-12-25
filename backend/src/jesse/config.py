from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    port: int
    clients_dir: Path
    global_api_key: str | None
    rate_limit_per_minute: int

    llm_provider: str
    llm_base_url: str | None
    llm_api_key: str | None
    llm_model: str | None
    llm_timeout_seconds: int


def load_settings() -> Settings:
    port = int(os.getenv("PORT", "5000"))

    backend_dir = Path(__file__).resolve().parents[2]
    clients_dir = Path(os.getenv("CLIENTS_DIR", str(backend_dir / "clients"))).resolve()

    global_api_key = os.getenv("GLOBAL_API_KEY") or None
    rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    llm_provider = os.getenv("LLM_PROVIDER", "mock")
    llm_base_url = os.getenv("LLM_BASE_URL") or None
    llm_api_key = os.getenv("LLM_API_KEY") or None
    llm_model = os.getenv("LLM_MODEL") or None
    llm_timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "25"))

    return Settings(
        port=port,
        clients_dir=clients_dir,
        global_api_key=global_api_key,
        rate_limit_per_minute=rate_limit,
        llm_provider=llm_provider,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        llm_timeout_seconds=llm_timeout,
    )
