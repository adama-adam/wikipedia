from __future__ import annotations

import re
from dataclasses import replace

from .models import Source


STOPWORDS = {
    "jest", "jestem", "czy", "jak", "jaki", "jaka", "jakie", "dla", "oraz",
    "tego", "też", "się", "z", "na", "do", "w", "i", "a", "o", "to", "co",
    "the", "and", "for", "with", "from", "what", "how", "is", "are",
}


def tokenize(text: str) -> set[str]:
    return {
        x for x in re.findall(r"[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{3,}", text.lower())
        if x not in STOPWORDS
    }


def chunk_text(text: str, size: int = 1400, overlap: int = 220) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def rank_sources(query: str, sources: list[Source], top_k: int = 10) -> list[Source]:
    q = tokenize(query)
    ranked = []
    for source in sources:
        haystack = f"{source.title} {source.snippet} {source.text[:6000]}"
        tokens = tokenize(haystack)
        overlap = len(q & tokens)
        authority = 0.0
        url = source.url.lower()
        if "wikipedia.org" in url:
            authority += 1.0
        if ".gov" in url or ".edu" in url:
            authority += 1.5
        if "britannica.com" in url or "nature.com" in url or "sciencedirect.com" in url:
            authority += 1.5
        score = overlap + authority
        ranked.append(replace(source, score=score))
    return sorted(ranked, key=lambda s: s.score, reverse=True)[:top_k]
