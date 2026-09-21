from __future__ import annotations

import time

from .config import Settings
from .llm import GeminiEngine
from .models import ResearchResult, Source
from .rag import rank_sources
from .sources import WikipediaSource, WebSource, deduplicate


class ResearchPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.wiki = WikipediaSource(settings.language, settings.user_agent)
        self.web = WebSource(settings.user_agent, settings.timeout_seconds)
        self.llm = GeminiEngine(settings.gemini_api_key, settings.gemini_model)

    def run(self, query: str, mode: str = "standard", progress=None) -> ResearchResult:
        started = time.perf_counter()
        if not query.strip():
            raise ValueError("Zapytanie nie może być puste.")
        self.settings.validate()

        def status(msg: str):
            if progress:
                progress(msg)

        status("Planowanie badania...")
        subqueries = self.llm.plan_queries(query, mode)

        raw = []
        for i, q in enumerate(subqueries, 1):
            status(f"Wyszukiwanie {i}/{len(subqueries)}: {q}")
            raw.extend(self.web.search(q, self.settings.max_web_results))
            raw.extend(self.wiki.search(q, 2))

        raw = deduplicate(raw)
        status(f"Pobrano {len(raw)} kandydatów. Pobieranie treści źródeł...")

        sources: list[Source] = []
        for idx, item in enumerate(raw, 1):
            text = item.get("text", "")
            if not text and item.get("kind") == "web":
                try:
                    text = self.web.fetch(item["url"])
                except Exception as exc:
                    text = f"[Nie udało się pobrać strony: {exc}]"
            if not text:
                text = item.get("snippet", "")
            if text:
                sources.append(
                    Source(
                        id=f"S{idx}",
                        title=item.get("title", "Bez tytułu"),
                        url=item.get("url", ""),
                        text=text,
                        kind=item.get("kind", "web"),
                        publisher=item.get("publisher", ""),
                        snippet=item.get("snippet", ""),
                    )
                )

        sources = rank_sources(query, sources, self.settings.max_sources)
        sources = [
            Source(id=f"S{i}", title=s.title, url=s.url, text=s.text,
                   kind=s.kind, publisher=s.publisher, score=s.score, snippet=s.snippet)
            for i, s in enumerate(sources, 1)
        ]

        status(f"Wybrano {len(sources)} źródeł. Generowanie odpowiedzi...")
        answer = self.llm.synthesize(query, sources, mode)

        conflicts = ""
        if mode == "deep":
            status("Sprawdzanie sprzeczności między źródłami...")
            conflicts = self.llm.detect_conflicts(query, sources)

        elapsed = time.perf_counter() - started
        status("Gotowe.")
        return ResearchResult(
            query=query,
            answer=answer,
            sources=sources,
            subqueries=subqueries,
            conflicts=conflicts,
            mode=mode,
            elapsed_seconds=elapsed,
        )
