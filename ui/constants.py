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
# FENSTERGRÖSSEN
# ══════════════════════════════════════════════════════════════════════

WINDOW_MIN_WIDTH = 420
"""Minimale Fensterbreite in Pixeln."""

WINDOW_DEFAULT_WIDTH = 1100
"""Standard-Fensterbreite in Pixeln."""

WINDOW_DEFAULT_HEIGHT = 820
"""Standard-Fensterhöhe in Pixeln."""

# ══════════════════════════════════════════════════════════════════════
# GRÖSSSEN UND LIMITS
# ══════════════════════════════════════════════════════════════════════

MAX_POSTS_LIMIT = 30
"""Maximale Anzahl von Posts die auf einmal geladen werden."""

DEFAULT_POSTS_LIMIT = 200
"""Standard-Limit für Post-Abfragen in der Datenbank."""

CARD_IMAGE_HEIGHT = 160
"""Höhe von Bildern in Karten-Ansicht (Grid)."""

LIST_IMAGE_HEIGHT = 220
"""Höhe von Bildern in Listen-Ansicht."""

DIALOG_IMAGE_HEIGHT = 280
"""Höhe von Bildern in Detail-Dialogen."""

# ══════════════════════════════════════════════════════════════════════
# TEXT-LÄNGEN-LIMITS
# ══════════════════════════════════════════════════════════════════════

MAX_HEADLINE_LENGTH = 200
"""Maximale Länge für Post-Überschrift/Name."""

MAX_DESCRIPTION_LENGTH = 2000
"""Maximale Länge für Post-Beschreibung."""

MAX_LOCATION_LENGTH = 200
"""Maximale Länge für Ortsangabe."""

MAX_DISPLAY_NAME_LENGTH = 50
"""Maximale Länge für Anzeigename (Profil)."""

MAX_SEARCH_QUERY_LENGTH = 200
"""Maximale Länge für Suchbegriffe."""

MIN_DESCRIPTION_LENGTH = 10
"""Minimale Länge für Post-Beschreibung."""

TRUNCATE_TEXT_LENGTH = 100
"""Standard-Länge für Text-Kürzung in Vorschauen."""

# ══════════════════════════════════════════════════════════════════════
# PLATZHALTER
# ══════════════════════════════════════════════════════════════════════

DEFAULT_PLACEHOLDER = "—"
