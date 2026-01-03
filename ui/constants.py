"""
UI Konstanten - Zentrale Definition aller Farben, Größen und Limits.
"""

import flet as ft

# ══════════════════════════════════════════════════════════════════════
# PRIMÄRFARBEN (App-weit verwendet)
# ══════════════════════════════════════════════════════════════════════

PRIMARY_COLOR = "#5B6EE1"          # Blau für Buttons und Akzente
PRIMARY_SEED = "#4C6FFF"           # Material 3 Seed-Farbe
BACKGROUND_COLOR = "#F5F7FA"       # Heller grauer Hintergrund
CARD_COLOR = ft.Colors.WHITE        # Weiße Card
TEXT_PRIMARY = "#1F2937"            # Dunkler Text
TEXT_SECONDARY = "#6B7280"          # Grauer Text
BORDER_COLOR = "#E5E7EB"            # Hellgrauer Rahmen

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
