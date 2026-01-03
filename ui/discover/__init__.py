"""
Discover Modul - Startseite mit Meldungsübersicht.

Dieses Modul enthält die DiscoverView-Klasse und zugehörige Komponenten
für die Anzeige und Filterung von Tiermeldungen.

Struktur:
- view.py: Hauptklasse DiscoverView (orchestriert alles)
- cards.py: Card-Komponenten (Small/Big Card, Detail-Dialog)
- filters.py: Filter-UI-Komponenten (Dropdowns, Suche, Farben)
- data.py: Daten-Logik (Query-Builder, Filter-Funktionen)
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.discover import DiscoverView
from ui.discover.view import DiscoverView

__all__ = ["DiscoverView"]
