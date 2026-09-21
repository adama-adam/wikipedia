import os
import sys
import argparse
from typing import List, Dict, Any

import wikipediaapi
from duckduckgo_search import DDGS
from google import genai
from google.genai import types


def get_wiki_context(query: str, lang: str = "pl") -> str:
    """
    Pobiera podsumowanie oraz treść artykułu z Wikipedii.
    Obsługuje brak strony oraz strony ujednoznaczniające (Disambiguation).
    """
    user_agent = "ResearchAgentRAG/1.0 (contact@example.com)"
    wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language=lang)
    page = wiki.page(query)

    if not page.exists():
        return f"[WIKIPEDIA]: Brak strony dla zapytania '{query}'."

    # Wykrywanie stron ujednoznaczniających
    # W wikipedia-api strony ujednoznaczniające często mają specjalną kategorię lub krótki opis wskazujący na ujednoznacznienie
    is_disambiguation = False
    title_lower = page.title.lower()
    summary_lower = page.summary.lower()
    
    if "ujednoznacznienie" in title_lower or "disambiguation" in title_lower:
        is_disambiguation = True
    elif "strona ujednoznaczniająca" in summary_lower or "refer to:" in summary_lower:
        is_disambiguation = True
    else:
        for cat in page.categories.keys():
            if "ujednoznacznienie" in cat.lower() or "disambiguation" in cat.lower():
                is_disambiguation = True
                break

    if is_disambiguation:
        # Pobranie dostępnych opcji ujednoznacznienia z linków wewnętrznych strony
        links = list(page.links.keys())[:10]
        links_str = ", ".join(links) if links else "brak szczegółowych odnośników"
        return (
            f"[WIKIPEDIA]: Wykryto stronę ujednoznaczniającą dla '{query}'. "
            f"Możliwe znaczenia/tematy: {links_str}."
        )

    # Ograniczenie długości treści, aby uniknąć przekroczenia optymalnego okna kontekstu
    content_snippet = page.text[:4000] if page.text else page.summary
    return f"[WIKIPEDIA - {page.title}]\nPodsumowanie:\n{page.summary}\n\nTreść (fragment):\n{content_snippet}"


def get_web_context(query: str, max_results: int = 4) -> str:
    """
    Pobiera czołowe wyniki wyszukiwania z DuckDuckGo (tytuł, URL, snippet).
    """
    try:
        results: List[Dict[str, Any]] = []
        with DDGS() as ddgs:
            ddg_gen = ddgs.text(query, max_results=max_results)
            if ddg_gen:
                results = list(ddg_gen)

        if not results:
            return f"[WEB SEARCH]: Brak wyników wyszukiwania dla zapytania '{query}'."

        formatted_results = []
        for idx, res in enumerate(results, 1):
            title = res.get("title", "Brak tytułu")
            url = res.get("href", "Brak URL")
            body = res.get("body", "Brak opisu")
            formatted_results.append(f"{idx}. Tytuł: {title}\n   URL: {url}\n   Snippet: {body}")

        return "[WEB SEARCH RESULTS]\n" + "\n\n".join(formatted_results)
    except Exception as e:
        return f"[WEB SEARCH ERROR]: Nie udało się pobrać danych z wyszukiwarki: {str(e)}"


def synthesize(query: str, wiki_context: str, web_context: str) -> str:
    """
    Łączy wyekstrahowane dane i syntetyzuje odpowiedź przy użyciu Gemini (google-genai SDK).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Brak zmiennej środowiskowej GEMINI_API_KEY. Ustaw klucz API przed uruchomieniem.")

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "Jesteś obiektywnym, precyzyjnym analitykiem danych i architektem wiedzy RAG.\n"
        "Twoim zadaniem jest stworzenie wyczerpującej, ustrukturyzowanej odpowiedzi na zapytanie użytkownika.\n\n"
        "ZASADY KRYTYCZNE:\n"
        "1. BEZWZGLĘDNY ZAKAZ KONFABULACJI I HALUCYNACJI. Odpowiedź MUSI opierać się wyłącznie na dostarczonym poniżej kontekście (Wikipedia i Web Search).\n"
        "2. Jeśli kontekst nie zawiera odpowiedzi na pytanie lub zawiera informację o braku strony/wieloznaczności, wyraźnie to zaznacz w analizie.\n"
        "3. Odpowiedź ma być ustrukturyzowana (użyj jasnych nagłówków, punktów i logicznej hierarchii).\n"
        "4. Podaj źródła informacji, odnosząc się do sekcji Wikipedii oraz wyników Web Search."
    )

    prompt = (
        f"ZAPYTANIE UŻYTKOWNIKA: {query}\n\n"
        f"=== KONTEKST 1: WIKIPEDIA ===\n{wiki_context}\n\n"
        f"=== KONTEKST 2: INTERNET (DUCKDUCKGO) ===\n{web_context}\n\n"
        "SYNTEZA ODPOWIEDZI:"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
        ),
    )

    return response.text if response.text else "Brak odpowiedzi z modelu."


def main():
    parser = argparse.ArgumentParser(description="CLI Agent RAG: Wikipedia + DuckDuckGo + Gemini LLM")
    parser.add_argument("query", type=str, nargs="?", help="Zapytanie badawcze dla agenta")
    parser.add_argument("--lang", type=str, default="pl", help="Kod języka dla Wikipedii (domyślnie: pl)")
    args = parser.parse_args()

    query = args.query
    if not query:
        query = input("Wprowadź zapytanie badawcze: ").strip()

    if not query:
        print("Błąd: Zapytanie nie może być puste.")
        sys.exit(1)

    print(f"\n[1/3] Pobieranie danych z Wikipedii ({args.lang})...")
    wiki_ctx = get_wiki_context(query, lang=args.lang)

    print("[2/3] Wyszukiwanie aktualnych informacji w internecie (DuckDuckGo)...")
    web_ctx = get_web_context(query, max_results=4)

    print("[3/3] Generowanie syntezy LLM (Gemini)...")
    try:
        result = synthesize(query, wiki_ctx, web_ctx)
        print("\n" + "=" * 80)
        print(f" WYNIK ANALIZY RAG: {query}")
        print("=" * 80 + "\n")
        print(result)
        print("\n" + "=" * 80)
    except Exception as err:
        print(f"\nBłąd podczas syntezy LLM: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
