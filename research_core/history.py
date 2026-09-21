from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import ResearchResult


class HistoryStore:
    def __init__(self, path: str = "data/history.json"):
        self.path = Path(path)

    def save(self, result: ResearchResult) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = []
        if self.path.exists():
            try:
                records = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                records = []
        records.insert(0, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query": result.query,
            "mode": result.mode,
            "answer": result.answer,
            "markdown": result.markdown(),
        })
        self.path.write_text(
            json.dumps(records[:50], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
