"""
Discover Modul - Startseite mit Meldungsübersicht.

Dieses Modul enthält die DiscoverView-Klasse und zugehörige Komponenten
für die Anzeige und Filterung von Tiermeldungen.

Struktur:
- view.py: Hauptklasse DiscoverView (UI-Komposition und Koordinierung)
- filter_components.py: Filter-UI-Komponenten (Suchfeld, Dropdowns, Buttons)
- post_card_components.py: Post-Karten-Komponenten (Small/Big Card, Detail-Dialog)
- comment_components.py: Kommentar-Komponente (CommentSection)
- features/: Feature-Module (Favorites, Search, Filters, References, SavedSearch)
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.discover import DiscoverView
from ui.discover.view import DiscoverView

__all__ = ["DiscoverView"]
