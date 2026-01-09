"""
Profile Modul - Benutzer-Profil und Einstellungen.

Dieses Modul enthält die ProfileView-Klasse für die Anzeige des Benutzerprofils,
Favoriten und eigener Meldungen.

Struktur:
- view.py: Hauptklasse ProfileView (inkl. Profil bearbeiten, Einstellungen, Profilbild)
- favorites.py: Favoriten-Logik (Mixin)
- my_posts.py: Eigene Meldungen (Mixin)
"""

from ui.profile.view import ProfileView

__all__ = ["ProfileView"]
