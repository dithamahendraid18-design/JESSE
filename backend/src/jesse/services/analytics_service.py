from __future__ import annotations

from datetime import datetime

from ..core.client_loader import ClientContext
from ..storage.events import EventStore


class AnalyticsService:
    def __init__(self) -> None:
        pass

    def track(self, ctx: ClientContext, user_id: str | None, kind: str, payload: dict) -> None:
        store = EventStore(ctx.base_dir)
        store.write(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
                "client_id": ctx.id,
                "user_id": user_id,
                "kind": kind,
                "payload": payload,
            }
        )
