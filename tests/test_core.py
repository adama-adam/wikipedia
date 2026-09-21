from research_core.models import ResearchResult, Source
from research_core.rag import chunk_text, rank_sources


def test_chunk_text():
    text = "A" * 3000
    chunks = chunk_text(text, size=1000, overlap=100)
    assert len(chunks) >= 3
    assert all(chunks)


def test_rank_sources_prefers_relevant_text():
    sources = [
        Source("S1", "TSDZ8", "https://example.com/1", "silnik centralny TSDZ8 moment 120 Nm"),
        Source("S2", "Pogoda", "https://example.com/2", "dzisiaj będzie deszcz"),
    ]
    ranked = rank_sources("TSDZ8 moment", sources, 2)
    assert ranked[0].id == "S1"


def test_markdown_report():
    result = ResearchResult(
        query="test",
        answer="Odpowiedź [S1]",
        sources=[Source("S1", "Źródło", "https://example.com", "tekst")],
    )
    md = result.markdown()
    assert "# Raport badawczy: test" in md
    assert "[S1]" in md
