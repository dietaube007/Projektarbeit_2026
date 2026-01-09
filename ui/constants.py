"""
UI Konstanten - Zentrale Definition aller Farben, Größen und UI-spezifische Limits.

App-weite Konstanten (Validierung, Text-Limits) sind in utils/constants.py
"""

import flet as ft
from utils.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_DISPLAY_NAME_LENGTH,
    MAX_SEARCH_QUERY_LENGTH,
    TRUNCATE_TEXT_LENGTH,
    MAX_POSTS_LIMIT,
    DEFAULT_POSTS_LIMIT,
)

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
# FENSTERGRÖSSEN
# ══════════════════════════════════════════════════════════════════════

WINDOW_MIN_WIDTH = 420
"""Minimale Fensterbreite in Pixeln."""

WINDOW_DEFAULT_WIDTH = 1100
"""Standard-Fensterbreite in Pixeln."""

WINDOW_DEFAULT_HEIGHT = 820
"""Standard-Fensterhöhe in Pixeln."""

# ══════════════════════════════════════════════════════════════════════
# UI-GRÖSSEN (Bilder, Fenster)
# ══════════════════════════════════════════════════════════════════════

CARD_IMAGE_HEIGHT = 160
"""Höhe von Bildern in Karten-Ansicht (Grid)."""

LIST_IMAGE_HEIGHT = 220
"""Höhe von Bildern in Listen-Ansicht."""

DIALOG_IMAGE_HEIGHT = 280
"""Höhe von Bildern in Detail-Dialogen."""

# ══════════════════════════════════════════════════════════════════════
# PLATZHALTER
# ══════════════════════════════════════════════════════════════════════

DEFAULT_PLACEHOLDER = "—"

# ══════════════════════════════════════════════════════════════════════
# BILDFORMATE & UPLOAD
# ══════════════════════════════════════════════════════════════════════

VALID_IMAGE_TYPES: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]
"""Erlaubte Bildformate für Uploads."""

PLACEHOLDER_IMAGE: str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
"""1x1 transparentes Platzhalter-Bild als Base64."""

# ══════════════════════════════════════════════════════════════════════
# FORMULARLAYOUT
# ══════════════════════════════════════════════════════════════════════

FIELD_WIDTH_SMALL: int = 250
"""Breite für kleine Formularfelder (z.B. Dropdowns)."""

FIELD_WIDTH_MEDIUM: int = 400
"""Breite für mittlere Formularfelder (z.B. Name)."""

FIELD_WIDTH_LARGE: int = 500
"""Breite für große Formularfelder (z.B. Beschreibung)."""

# ══════════════════════════════════════════════════════════════════════
# DATUMSFORMATE
# ══════════════════════════════════════════════════════════════════════

DATE_FORMAT: str = "%d.%m.%Y"
"""Datumsformat für Eingabe (TT.MM.YYYY)."""

# ══════════════════════════════════════════════════════════════════════
# DROPDOWN-WERTE
# ══════════════════════════════════════════════════════════════════════

NO_SELECTION_VALUE: str = "none"
"""Wert für "Keine Angabe" in Dropdowns."""

NO_SELECTION_LABEL: str = "— Keine Angabe —"
"""Anzeigetext für "Keine Angabe" in Dropdowns."""

# ══════════════════════════════════════════════════════════════════════
# MELDUNGSARTEN
# ══════════════════════════════════════════════════════════════════════

ALLOWED_POST_STATUSES: list[str] = ["vermisst", "fundtier"]
"""Erlaubte Meldungsarten (von Post-Statuses in der DB)."""
