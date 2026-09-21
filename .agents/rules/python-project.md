# Reguły projektu Python

- Python >= 3.10.
- Styl: PEP 8, ruff.
- Zmiany powinny być modularne i testowalne.
- Zachowaj kompatybilność Windows.
- GUI nie może blokować wątku interfejsu podczas researchu sieciowego lub wywołań Gemini.
- Każda funkcja pobierająca dane z Internetu musi mieć obsługę błędów.
- Klucze API wyłącznie przez zmienne środowiskowe lub lokalne pole GUI; nigdy nie commituj sekretów.
- Po zmianach uruchom `python -m pytest` oraz `ruff check .`.
