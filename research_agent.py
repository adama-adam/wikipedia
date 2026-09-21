from __future__ import annotations

import argparse

from research_core.config import Settings
from research_core.pipeline import ResearchPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Wikipedia Research AI — wieloźródłowy agent researchowy"
    )
    parser.add_argument("query", nargs="?", help="Pytanie badawcze")
    parser.add_argument("--lang", default="pl", help="Język Wikipedii, np. pl/en")
    parser.add_argument(
        "--mode", choices=["fast", "standard", "deep"], default="standard",
        help="Tryb: szybki, standardowy lub głęboki"
    )
    args = parser.parse_args()

    query = args.query or input("Co chcesz zbadać? ").strip()
    if not query:
        parser.error("Zapytanie nie może być puste.")

    settings = Settings.from_env()
    settings = Settings(
        gemini_api_key=settings.gemini_api_key,
        gemini_model=settings.gemini_model,
        language=args.lang,
        user_agent=settings.user_agent,
        max_web_results=settings.max_web_results,
        max_sources=settings.max_sources,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        timeout_seconds=settings.timeout_seconds,
    )

    def progress(msg: str):
        print(f"[Research] {msg}")

    result = ResearchPipeline(settings).run(query, mode=args.mode, progress=progress)
    print("\n" + "=" * 90)
    print(result.answer)
    print("=" * 90)
    print("\nŹródła:")
    for s in result.sources:
        print(f"[{s.id}] {s.title} — {s.url}")
    if result.conflicts:
        print("\nWERYFIKACJA / SPRZECZNOŚCI:")
        print(result.conflicts)


if __name__ == "__main__":
    main()
