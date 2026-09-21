from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from research_core.config import Settings
from research_core.exporter import export_markdown
from research_core.history import HistoryStore
from research_core.pipeline import ResearchPipeline


class ResearchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wikipedia Research AI 2.0")
        self.geometry("1250x820")
        self.minsize(950, 650)
        self.result = None
        self.history = HistoryStore()
        self._build_ui()

    def _build_ui(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            header, text="Wikipedia Research AI",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(
            header,
            text="Wikipedia + Web + Gemini • źródła • cytowania • wieloetapowy research",
        ).pack(anchor="w", padx=18, pady=(0, 12))

        row = ctk.CTkFrame(header, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=5)

        self.query = ctk.CTkEntry(
            row, placeholder_text="Co chcesz zbadać?", height=42,
            font=ctk.CTkFont(size=14)
        )
        self.query.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.query.bind("<Return>", lambda _: self.start())

        self.lang = ctk.CTkOptionMenu(row, values=["pl", "en", "de", "fr", "es"], width=70)
        self.lang.set("pl")
        self.lang.pack(side="left", padx=5)

        self.mode = ctk.CTkOptionMenu(
            row, values=["fast", "standard", "deep"], width=105
        )
        self.mode.set("standard")
        self.mode.pack(side="left", padx=5)

        self.start_btn = ctk.CTkButton(
            row, text="🔎 BADAJ", width=125, height=42, command=self.start
        )
        self.start_btn.pack(side="left", padx=(8, 0))

        keyrow = ctk.CTkFrame(header, fg_color="transparent")
        keyrow.pack(fill="x", padx=14, pady=(5, 12))
        ctk.CTkLabel(keyrow, text="Gemini API:").pack(side="left", padx=(0, 6))
        self.key = ctk.CTkEntry(keyrow, show="*", placeholder_text="GEMINI_API_KEY")
        self.key.insert(0, os.getenv("GEMINI_API_KEY", ""))
        self.key.pack(side="left", fill="x", expand=True)

        self.status = ctk.CTkLabel(self, text="Gotowy.", anchor="w")
        self.status.pack(fill="x", padx=20, pady=(0, 4))
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=(0, 10))
        self.progress.stop()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.answer_tab = self.tabs.add("Odpowiedź")
        self.sources_tab = self.tabs.add("Źródła")
        self.conflicts_tab = self.tabs.add("Weryfikacja")
        self.searches_tab = self.tabs.add("Zapytania")

        self.answer = ctk.CTkTextbox(self.answer_tab, wrap="word", font=ctk.CTkFont(size=14))
        self.answer.pack(fill="both", expand=True, padx=8, pady=8)
        self.sources = ctk.CTkTextbox(self.sources_tab, wrap="word")
        self.sources.pack(fill="both", expand=True, padx=8, pady=8)
        self.conflicts = ctk.CTkTextbox(self.conflicts_tab, wrap="word")
        self.conflicts.pack(fill="both", expand=True, padx=8, pady=8)
        self.searches = ctk.CTkTextbox(self.searches_tab, wrap="word")
        self.searches.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(bottom, text="Eksportuj raport Markdown", command=self.export).pack(side="left")
        ctk.CTkButton(bottom, text="Wyczyść", command=self.clear).pack(side="left", padx=8)

    def set_status(self, text: str):
        self.after(0, lambda: self.status.configure(text=text))

    def start(self):
        query = self.query.get().strip()
        if not query:
            self.set_status("Wpisz pytanie.")
            return
        api_key = self.key.get().strip()
        if not api_key:
            self.set_status("Brak GEMINI_API_KEY.")
            return

        self.start_btn.configure(state="disabled")
        self.progress.start()
        self.clear()
        settings = Settings.from_env()
        settings = Settings(
            gemini_api_key=api_key,
            gemini_model=settings.gemini_model,
            language=self.lang.get(),
            user_agent=settings.user_agent,
            max_web_results=settings.max_web_results,
            max_sources=settings.max_sources,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            timeout_seconds=settings.timeout_seconds,
        )
        mode = self.mode.get()

        def worker():
            try:
                result = ResearchPipeline(settings).run(
                    query, mode=mode, progress=self.set_status
                )
                self.result = result
                self.history.save(result)
                self.after(0, self.show_result)
            except Exception as exc:
                self.set_status(f"Błąd: {exc}")
                self.after(0, lambda: messagebox.showerror("Research AI", str(exc)))
            finally:
                self.after(0, self.finish)

        threading.Thread(target=worker, daemon=True).start()

    def show_result(self):
        self.answer.insert("1.0", self.result.answer)
        source_text = "\n\n".join(
            f"[{s.id}] {s.title}\n{ s.url }\nOcena źródła: {s.score:.1f}\n"
            f"Typ: {s.kind}\n"
            for s in self.result.sources
        )
        self.sources.insert("1.0", source_text or "Brak źródeł.")
        self.conflicts.insert("1.0", self.result.conflicts or "Tryb standard/fast: analiza sprzeczności nie była uruchamiana.")
        self.searches.insert("1.0", "\n".join(self.result.subqueries))

    def finish(self):
        self.progress.stop()
        self.start_btn.configure(state="normal")

    def clear(self):
        for box in (self.answer, self.sources, self.conflicts, self.searches):
            box.delete("1.0", tk.END)

    def export(self):
        if not self.result:
            messagebox.showinfo("Eksport", "Najpierw wykonaj badanie.")
            return
        path = filedialog.asksaveasfilename(
            title="Zapisz raport",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Wszystkie pliki", "*.*")],
        )
        if path:
            export_markdown(self.result, path)
            messagebox.showinfo("Eksport", f"Zapisano raport:\n{path}")


if __name__ == "__main__":
    ResearchApp().mainloop()
