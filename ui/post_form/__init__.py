"""
Post Form Modul - Meldungsformular für Haustiere.

Dieses Modul enthält die PostForm-Klasse und zugehörige Komponenten
für das Erstellen von Tier-Meldungen (vermisst/gefunden).

Struktur:
- view.py: Hauptklasse PostForm (UI-Komposition und Koordinierung)
- components.py: Gemeinsame UI-Komponenten (statische Builder)
- features/: Feature-Module (AI Recognition, Photo Upload, Post Upload, Validation, References)
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.post_form import PostForm
from ui.post_form.view import PostForm

__all__ = ["PostForm"]
