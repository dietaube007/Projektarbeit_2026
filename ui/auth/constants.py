"""
ui/auth/constants.py
Konstanten für die Login-Ansicht.
"""

import flet as ft

# ─────────────────────────────────────────────────────────────────
# Validierung
# ─────────────────────────────────────────────────────────────────

MIN_PASSWORD_LENGTH = 8
MAX_DISPLAY_NAME_LENGTH = 30
SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# ─────────────────────────────────────────────────────────────────
# Farben - Minimalistisches Design
# ─────────────────────────────────────────────────────────────────

PRIMARY_COLOR = "#5B6EE1"       # Blau für Buttons
BACKGROUND_COLOR = "#F5F7FA"    # Heller grauer Hintergrund
CARD_COLOR = ft.Colors.WHITE     # Weiße Card
TEXT_PRIMARY = "#1F2937"         # Dunkler Text
TEXT_SECONDARY = "#6B7280"       # Grauer Text
BORDER_COLOR = "#E5E7EB"         # Hellgrauer Rahmen
