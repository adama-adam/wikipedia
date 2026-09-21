from pathlib import Path

from .models import ResearchResult


def export_markdown(result: ResearchResult, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result.markdown(), encoding="utf-8")
    return target
