from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    language: str = "pl"
    user_agent: str = "WikipediaResearchAI/2.0 (https://github.com/adama-adam/wikipedia)"
    max_web_results: int = 8
    max_sources: int = 10
    chunk_size: int = 1400
    chunk_overlap: int = 220
    timeout_seconds: int = 15

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            language=os.getenv("WIKI_LANGUAGE", "pl"),
            user_agent=os.getenv(
                "WIKI_USER_AGENT",
                "WikipediaResearchAI/2.0 (https://github.com/adama-adam/wikipedia)",
            ),
            max_web_results=int(os.getenv("MAX_WEB_RESULTS", "8")),
            max_sources=int(os.getenv("MAX_SOURCES", "10")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1400")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "220")),
            timeout_seconds=int(os.getenv("REQUEST_TIMEOUT", "15")),
        )

    def validate(self) -> None:
        if not self.gemini_api_key:
            raise ValueError(
                "Brak GEMINI_API_KEY. Ustaw zmienną środowiskową lub użyj pola API w GUI."
            )
