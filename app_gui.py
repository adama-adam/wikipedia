import os
import sys
import threading
from typing import List, Dict, Any

import customtkinter as ctk
import wikipediaapi
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

# Konfiguracja motywu CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RAGApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Wikipedia & Web RAG Research Agent")
        self.geometry("1000rollback" if False else "1050x750")
        self.minsize(800, 600)

        self._build_ui()

    def _build_ui(self):
        # Nagłówek i Sekcja Konfiguracyjna
        top_frame = ctk.CTkFrame(self, corner_radius=10)
        top_frame.pack(fill="x", padx=15, pady=15)

        title_label = ctk.CTkLabel(
            top_frame,
            text=" Wikipedia & Web RAG Research Agent",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_label.pack(anchor="w", padx=15, pady=(10, 5))

        # Klucz API
        api_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        api_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(api_frame, text="Klucz GEMINI_API_KEY:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 5))
        
        default_key = os.environ.get("GEMINI_API_KEY", "")
        self.api_key_entry = ctk.CTkEntry(api_frame, placeholder_text="Wklej klucz GEMINI_API_KEY...", show="*", width=450)
        self.api_key_entry.insert(0, default_key)
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Sekcja Wyszukiwania
        search_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=10)

        self.query_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Wpisz hasło / temat do analizy RAG...", font=ctk.CTkFont(size=14), height=40
        )
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.query_entry.bind("<Return>", lambda event: self.start_analysis())

        self.lang_option = ctk.CTkOptionMenu(search_frame, values=["pl", "en", "de", "fr", "es"], width=70, height=40)
        self.lang_option.set("pl")
        self.lang_option.pack(side="left", padx=(0, 10))

        self.search_btn = ctk.CTkButton(
            search_frame, text="Analizuj (RAG)", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.start_analysis
        )
        self.search_btn.pack(side="left")

        # Pasek postępu i status
        self.status_label = ctk.CTkLabel(self, text="Gotowy do działania.", font=ctk.CTkFont(size=12), anchor="w")
        self.status_label.pack(fill="x", padx=20, pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_bar.stop()

        # Karty Wyników (Tabs)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tab_synthesis = self.tabview.add("Synteza LLM (Gemini)")
        self.tab_wiki = self.tabview.add("Kontekst Wikipedia")
        self.tab_web = self.tabview.add("Kontekst DuckDuckGo")

        # Pola tekstowe w kartach
        self.txt_synthesis = ctk.CTkTextbox(self.tab_synthesis, font=ctk.CTkFont(size=13), wrap="word")
        self.txt_synthesis.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_wiki = ctk.CTkTextbox(self.tab_wiki, font=ctk.CTkFont(size=12), wrap="word")
        self.txt_wiki.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_web = ctk.CTkTextbox(self.tab_web, font=ctk.CTkFont(size=12), wrap="word")
        self.txt_web.pack(fill="both", expand=True, padx=5, pady=5)

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def start_analysis(self):
        query = self.query_entry.get().strip()
        if not query:
            self.set_status(" Błąd: Wprowadź temat do wyszukania.")
            return

        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.set_status(" Błąd: Brak klucza GEMINI_API_KEY. Uzupełnij pole klucza.")
            return

        self.search_btn.configure(state="disabled")
        self.progress_bar.start()
        self.set_status(" Processing: Pobieranie danych z Wikipedii i DuckDuckGo...")

        # Czyszczenie pól tekstowych
        self._clear_textbox(self.txt_synthesis)
        self._clear_textbox(self.txt_wiki)
        self._clear_textbox(self.txt_web)

        # Uruchomienie w osobnym wątku, aby nie blokować GUI
        threading.Thread(target=self._run_rag_pipeline, args=(query, self.lang_option.get(), api_key), daemon=True).start()

    def _clear_textbox(self, textbox: ctk.CTkTextbox):
        textbox.delete("1.0", ctk.END)

    def _write_textbox(self, textbox: ctk.CTkTextbox, text: str):
        textbox.delete("1.0", ctk.END)
        textbox.insert("1.0", text)

    def _run_rag_pipeline(self, query: str, lang: str, api_key: str):
        try:
            # 1. Wikipedia
            self.after(0, lambda: self.set_status("[1/3] Pobieranie danych z Wikipedii..."))
            wiki_ctx = self._get_wiki_context(query, lang)
            self.after(0, lambda: self._write_textbox(self.txt_wiki, wiki_ctx))

            # 2. DuckDuckGo
            self.after(0, lambda: self.set_status("[2/3] Pobieranie najnowszych wyników z DuckDuckGo..."))
            web_ctx = self._get_web_context(query)
            self.after(0, lambda: self._write_textbox(self.txt_web, web_ctx))

            # 3. Gemini LLM Synthesis
            self.after(0, lambda: self.set_status("[3/3] Generowanie syntezy przez model Gemini..."))
            synthesis_result = self._synthesize(query, wiki_ctx, web_ctx, api_key)
            self.after(0, lambda: self._write_textbox(self.txt_synthesis, synthesis_result))

            self.after(0, lambda: self.set_status(" Gotowe! Odpowiedź została wygenerowana."))
        except Exception as e:
            err_msg = f" Wystąpił błąd podczas analizy: {str(e)}"
            self.after(0, lambda: self.set_status(err_msg))
            self.after(0, lambda: self._write_textbox(self.txt_synthesis, err_msg))
        finally:
            self.after(0, self._finish_processing)

    def _finish_processing(self):
        self.progress_bar.stop()
        self.search_btn.configure(state="normal")

    def _get_wiki_context(self, query: str, lang: str) -> str:
        user_agent = "ResearchAgentGUI/1.0 (contact@example.com)"
        wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language=lang)
        page = wiki.page(query)

        if not page.exists():
            return f"[WIKIPEDIA]: Brak strony dla zapytania '{query}' w języku '{lang}'."

        title_lower = page.title.lower()
        summary_lower = page.summary.lower()
        is_disambiguation = "ujednoznacznienie" in title_lower or "disambiguation" in title_lower or "strona ujednoznaczniająca" in summary_lower

        if not is_disambiguation:
            for cat in page.categories.keys():
                if "ujednoznacznienie" in cat.lower() or "disambiguation" in cat.lower():
                    is_disambiguation = True
                    break

        if is_disambiguation:
            links = list(page.links.keys())[:12]
            links_str = ", ".join(links) if links else "brak linków"
            return f"[WIKIPEDIA]: Strona ujednoznaczniająca dla '{query}'. Możliwe tematy: {links_str}."

        snippet = page.text[:4000] if page.text else page.summary
        return f"TYTUŁ: {page.title}\n\nPODSUMOWANIE:\n{page.summary}\n\nFRAGMENT TREŚCI:\n{snippet}"

    def _get_web_context(self, query: str) -> str:
        try:
            results = []
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=4)
                if ddg_gen:
                    results = list(ddg_gen)

            if not results:
                return f"[WEB SEARCH]: Brak wyników dla '{query}'."

            out = []
            for i, r in enumerate(results, 1):
                out.append(f"{i}. {r.get('title', '')}\n   URL: {r.get('href', '')}\n   Opis: {r.get('body', '')}")
            return "\n\n".join(out)
        except Exception as e:
            return f"[WEB SEARCH ERROR]: {str(e)}"

    def _synthesize(self, query: str, wiki_ctx: str, web_ctx: str, api_key: str) -> str:
        client = genai.Client(api_key=api_key)

        sys_instruction = (
            "Jesteś obiektywnym, profesjonalnym analitykiem RAG.\n"
            "Twoim zadaniem jest synteza odpowiedzi wyłącznie na podstawie wstrzykniętych danych z Wikipedii i Wyszukiwarki Internetowej.\n"
            "BEZWZGLĘDNY ZAKAZ KONFABULACJI i wymyślania faktów spoza tekstu kontekstu.\n"
            "Formatuj odpowiedź przejrzyście w Markdown z nagłówkami i punktami."
        )

        prompt = (
            f"ZAPYTANIE: {query}\n\n"
            f"=== KONTEKST WIKIPEDIA ===\n{wiki_ctx}\n\n"
            f"=== KONTEKST DUCKDUCKGO ===\n{web_ctx}\n\n"
            "SYNTEZA ODPOWIEDZI:"
        )

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                temperature=0.1,
            ),
        )

        return resp.text if resp.text else "Brak odpowiedzi z modelu."


if __name__ == "__main__":
    app = RAGApp()
    app.mainloop()
