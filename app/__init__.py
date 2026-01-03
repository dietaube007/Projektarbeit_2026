"""
App Modul - PetBuddy Hauptanwendung.

Dieses Modul enthält die Hauptklasse der Anwendung und Dialoge.

Struktur:
- app.py: PetBuddyApp Hauptklasse
- dialogs.py: Login-Dialoge und Banner
- navigation.py: Navigationskomponenten
"""

# Re-export der Hauptklasse für einfachen Import
# Verwendung: from app import PetBuddyApp
from app.app import PetBuddyApp

__all__ = ["PetBuddyApp"]
