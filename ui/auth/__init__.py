"""
Auth Modul - Authentifizierung (Login/Registrierung).

Dieses Modul enthält die AuthView-Klasse und zugehörige Komponenten
für die Benutzer-Authentifizierung.

Struktur:
- view.py: Hauptklasse AuthView
- forms.py: Formular-Komponenten (Login/Register)
- validators.py: Validierungsfunktionen
- constants.py: Konstanten (Farben, Limits)
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from ui.auth import AuthView
from ui.auth.view import AuthView

__all__ = ["AuthView"]
