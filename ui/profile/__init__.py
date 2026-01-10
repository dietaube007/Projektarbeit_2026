"""
Profile Modul - Benutzer-Profil und Einstellungen.

Dieses Modul enthält die ProfileView-Klasse für die Anzeige des Benutzerprofils,
Favoriten und eigener Meldungen.

Struktur:
- view.py: Hauptklasse ProfileView (UI-Komposition und Koordination)
- components/: UI-Komponenten für Profile
- features/: Feature-Module
  - my_favorites.py: Favoriten-Verwaltung
  - my_posts.py: Eigene Meldungen-Verwaltung
  - edit_post.py: Meldung-Bearbeitung
  - profile_image.py: Profilbild-Upload/Verwaltung
  - my_account.py: Passwort ändern & Konto löschen
  - my_saved_searches.py: Gespeicherte Suchaufträge
"""

from ui.profile.view import ProfileView

__all__ = ["ProfileView"]
