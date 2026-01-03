"""
Post Form Modul - Meldungsformular für Haustiere.

Dieses Modul enthält die PostForm-Klasse und zugehörige Komponenten
für das Erstellen von Tier-Meldungen (vermisst/gefunden).

Struktur:
- view.py: Hauptklasse PostForm
- photo_manager.py: Foto-Upload und Komprimierung
- form_fields.py: UI-Komponenten für das Formular
- constants.py: Konstanten (Bildgrößen, Limits)
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.post_form import PostForm
from ui.post_form.view import PostForm

__all__ = ["PostForm"]
