"""
Profile Modul - Benutzer-Profil und Einstellungen.

Dieses Modul enthält die ProfileView-Klasse und zugehörige Komponenten
für die Anzeige des Benutzerprofils, Favoriten und eigener Meldungen.

Struktur:
- view.py: Hauptklasse ProfileView (orchestriert alles)
- favorites.py: Favoriten-Tab Logik und Karten
- my_posts.py: Eigene Meldungen Ansicht
- edit_post.py: Dialog zum Bearbeiten einer Meldung
- edit_profile.py: Profil-Bearbeiten Ansicht
- settings.py: Einstellungen Ansicht
- components.py: Gemeinsame UI-Komponenten
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.profile import ProfileView
from ui.profile.view import ProfileView

__all__ = ["ProfileView"]
