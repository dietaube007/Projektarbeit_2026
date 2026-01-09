"""
Auth Modul - Authentifizierung (Login/Registrierung).

Dieses Modul enthält die AuthView-Klasse und zugehörige Komponenten
für die Benutzer-Authentifizierung.

Struktur:
- view.py: Hauptklasse AuthView (UI-Komposition)
- components.py: Gemeinsame UI-Komponenten (statische Builder)
- features/: Feature-Module (Login, Register, Password Reset)
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.auth import AuthView
from ui.auth.view import AuthView

__all__ = ["AuthView"]
