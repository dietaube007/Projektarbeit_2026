"""
UI Konstanten - Zentrale Definition aller Farben, Größen und Limits.
"""

import flet as ft

# ══════════════════════════════════════════════════════════════════════
# FARBEN FÜR BADGES
# ══════════════════════════════════════════════════════════════════════

STATUS_COLORS: dict[str, str] = {
    "vermisst": ft.Colors.RED_200,
    "fundtier": ft.Colors.INDIGO_300,
    "wiedervereint": ft.Colors.LIGHT_GREEN_200,
}

SPECIES_COLORS: dict[str, str] = {
    "hund": ft.Colors.PURPLE_200,
    "katze": ft.Colors.PINK_200,
    "kleintier": ft.Colors.TEAL_200,
}

# ══════════════════════════════════════════════════════════════════════
# GRÖSSSEN UND LIMITS
# ══════════════════════════════════════════════════════════════════════

MAX_POSTS_LIMIT = 30
CARD_IMAGE_HEIGHT = 160
LIST_IMAGE_HEIGHT = 220
DIALOG_IMAGE_HEIGHT = 280

# ══════════════════════════════════════════════════════════════════════
# PLATZHALTER
# ══════════════════════════════════════════════════════════════════════

DEFAULT_PLACEHOLDER = "—"
