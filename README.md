# Wikipedia Research AI 2.0

Wieloźródłowy agent researchowy w Pythonie: **Wikipedia + Web + Gemini**.

## Uruchomienie w Google Antigravity

Projekt jest przygotowany do pracy jako lokalny workspace w Google Antigravity. Antigravity obsługuje workspace rules w `.agents/rules/` oraz workflows w `.agents/workflows/`.

1. Sklonuj repozytorium:
   `git clone https://github.com/adama-adam/wikipedia.git`
2. Otwórz folder `wikipedia` w Antigravity jako workspace.
3. W terminalu utwórz środowisko:
   `python -m venv .venv`
4. Windows:
   `.venv\\Scripts\\activate`
5. Zainstaluj zależności:
   `python -m pip install -r requirements.txt`
6. Skopiuj `.env.example` jako `.env` i wpisz swój `GEMINI_API_KEY`.
7. Uruchom GUI:
   `python app_gui.py`
8. Albo CLI:
   `python research_agent.py "Co to jest TSDZ8?" --mode standard`

### Szybka kontrola projektu

```
python -m pytest
ruff check .
```

W Antigravity możesz też używać workflowów zapisanych w `.agents/workflows/`.

## Funkcje

- wieloetapowe planowanie zapytań,
- Wikipedia + wyszukiwarka WWW,
- pobieranie rzeczywistej treści stron,
- ranking źródeł,
- cytowania `[S1]`, `[S2]`,
- tryby **fast / standard / deep**,
- wykrywanie sprzeczności w trybie deep,
- historia lokalna,
- eksport Markdown,
- GUI i CLI,
- testy automatyczne,
- konfiguracja przez `.env`.

## Architektura

```
app_gui.py
research_agent.py
research_core/
  config.py
  models.py
  sources.py
  rag.py
  llm.py
  pipeline.py
  history.py
  exporter.py
tests/
.agents/
  rules/
  workflows/
```

## Bezpieczeństwo

Nie zapisuj klucza API w kodzie ani w Git. Plik `.env` jest ignorowany przez Git.

Cytowania pomagają zweryfikować odpowiedź, ale przy ważnych decyzjach należy otworzyć źródła i sprawdzić ich treść.

## Tryby

- **fast** — jedno zapytanie, najmniej wywołań LLM.
- **standard** — kilka zapytań pomocniczych, więcej źródeł.
- **deep** — standard + analiza sprzeczności między źródłami.
