from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Source:
    id: str
    title: str
    url: str
    text: str
    kind: str = "web"
    publisher: str = ""
    score: float = 0.0
    snippet: str = ""

    @property
    def label(self) -> str:
        return self.publisher or self.title or self.url


@dataclass
class ResearchResult:
    query: str
    answer: str
    sources: List[Source] = field(default_factory=list)
    subqueries: List[str] = field(default_factory=list)
    conflicts: str = ""
    mode: str = "standard"
    elapsed_seconds: float = 0.0

    def markdown(self) -> str:
        lines = [
            f"# Raport badawczy: {self.query}",
            "",
            f"**Tryb:** {self.mode}",
            f"**Czas:** {self.elapsed_seconds:.1f} s",
            "",
            "## Odpowiedź",
            "",
            self.answer,
        ]
        if self.conflicts:
            lines += ["", "## Sprzeczności / kwestie wymagające weryfikacji", "", self.conflicts]
        if self.subqueries:
            lines += ["", "## Zapytania pomocnicze", ""]
            lines += [f"- {q}" for q in self.subqueries]
        lines += ["", "## Źródła", ""]
        for s in self.sources:
            lines.append(f"- **[{s.id}] {s.title}** — {s.url}")
        return "\n".join(lines)
