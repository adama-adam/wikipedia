from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import wikipediaapi

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


class WikipediaSource:
    def __init__(self, language: str, user_agent: str):
        self.api = wikipediaapi.Wikipedia(
            user_agent=user_agent,
            language=language,
        )

    def search(self, query: str, limit: int = 3) -> list[dict]:
        # wikipedia-api resolves exact pages; link search is intentionally conservative.
        page = self.api.page(query)
        if not page.exists():
            return []
        return [{
            "title": page.title,
            "url": f"https://{self.api.language}.wikipedia.org/wiki/{page.title.replace(' ', '_')}",
            "text": page.text or page.summary,
            "snippet": page.summary,
            "kind": "wikipedia",
            "publisher": f"Wikipedia ({self.api.language})",
        }][:limit]


class WebSource:
    def __init__(self, user_agent: str, timeout: int = 15):
        self.user_agent = user_agent
        self.timeout = timeout

    def search(self, query: str, max_results: int = 8) -> list[dict]:
        if DDGS is None:
            raise RuntimeError("Brak pakietu ddgs. Zainstaluj zależności z requirements.txt.")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", "Bez tytułu"),
                "url": r.get("href", ""),
                "text": "",
                "snippet": r.get("body", ""),
                "kind": "web",
                "publisher": urlparse(r.get("href", "")).netloc,
            }
            for r in results
            if r.get("href")
        ]

    def fetch(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""
        response = requests.get(
            url,
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            return ""
        return _clean_html(response.text)[:20000]


def deduplicate(items: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for item in items:
        url = item.get("url", "").split("#")[0].rstrip("/")
        title = item.get("title", "").strip().lower()
        key = url or title
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out
