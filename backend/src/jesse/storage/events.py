from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class EventStore:
    """
    Simple file-based analytics:
    - Simpan event ke JSONL per bulan:
      clients/<id>/analytics/events-YYYY-MM.jsonl
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def write(self, event: dict) -> None:
        analytics_dir = self.base_dir / "analytics"
        analytics_dir.mkdir(parents=True, exist_ok=True)

        month = datetime.utcnow().strftime("%Y-%m")
        path = analytics_dir / f"events-{month}.jsonl"

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
