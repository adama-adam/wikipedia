from __future__ import annotations

import json
import re

from google import genai
from google.genai import types

from .models import Source


class GeminiEngine:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("Brak GEMINI_API_KEY.")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _generate(self, prompt: str, system: str, temperature: float = 0.1) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
            ),
        )
        return response.text or ""

    def plan_queries(self, query: str, mode: str) -> list[str]:
        if mode == "fast":
            return [query]
        prompt = (
            f"Użytkownik chce zbadać: {query}\n"
            "Wygeneruj 3 krótkie, różne zapytania wyszukiwawcze po polsku. "
            "Każde w osobnej linii. Bez numeracji i komentarzy."
        )
        text = self._generate(
            prompt,
            "Jesteś planistą researchu. Twórz precyzyjne zapytania, nie odpowiadaj na pytanie.",
        )
        queries = [re.sub(r"^[-*\d. )]+", "", x).strip() for x in text.splitlines() if x.strip()]
        return list(dict.fromkeys([query] + queries[:4]))

    def synthesize(self, query: str, sources: list[Source], mode: str) -> str:
        context = "\n\n".join(
            f"[{s.id}] {s.title}\nURL: {s.url}\nTREŚĆ:\n{s.text[:5000]}"
            for s in sources
        )
        system = (
            "Jesteś precyzyjnym analitykiem researchu. "
            "Odpowiadasz WYŁĄCZNIE na podstawie podanego kontekstu. "
            "Nie wymyślaj faktów ani źródeł. Każde istotne twierdzenie opatrz cytowaniem "
            "w formacie [S1], [S2] itd. Jeśli źródła sobie przeczą, wyraźnie to zaznacz. "
            "Jeżeli danych brakuje, powiedz to wprost. Odpowiedź ma być po polsku i w Markdown."
        )
        prompt = (
            f"PYTANIE: {query}\n\n"
            f"TRYB BADANIA: {mode}\n\n"
            f"ŹRÓDŁA:\n{context}\n\n"
            "Przygotuj rzeczową odpowiedź. Nie dodawaj informacji spoza źródeł."
        )
        return self._generate(prompt, system)

    def detect_conflicts(self, query: str, sources: list[Source]) -> str:
        if len(sources) < 2:
            return "Za mało niezależnych źródeł do analizy sprzeczności."
        context = "\n\n".join(
            f"[{s.id}] {s.title}: {s.text[:2500]}" for s in sources[:8]
        )
        return self._generate(
            f"Pytanie: {query}\n\n{context}\n\n"
            "Wskaż tylko istotne sprzeczności między źródłami. "
            "Jeśli ich nie ma, napisz: Brak istotnych sprzeczności.",
            "Jesteś audytorem faktów. Nie rozstrzygaj sporu bez podstawy. Cytuj identyfikatory źródeł.",
        )
