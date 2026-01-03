"""
ui/auth/constants.py
Konstanten für die Login-Ansicht.
"""

# Farben aus zentraler Stelle importieren
from ui.constants import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    CARD_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
)

# ─────────────────────────────────────────────────────────────────
# Validierung
# ─────────────────────────────────────────────────────────────────

MIN_PASSWORD_LENGTH = 8
MAX_DISPLAY_NAME_LENGTH = 30
SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Re-export für Abwärtskompatibilität
__all__ = [
    "PRIMARY_COLOR",
    "BACKGROUND_COLOR",
    "CARD_COLOR",
    "TEXT_PRIMARY",
    "TEXT_SECONDARY",
    "BORDER_COLOR",
    "MIN_PASSWORD_LENGTH",
    "MAX_DISPLAY_NAME_LENGTH",
    "SPECIAL_CHARS",
    "EMAIL_REGEX",
]
