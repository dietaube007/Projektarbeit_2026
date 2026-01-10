"""
Zentrale App-weite Konstanten.

Diese Datei enthält alle Konstanten, die app-weit verwendet werden:
- Validierungs-Konstanten
- Text-Längen-Limits
- Post-Limits

UI-spezifische Konstanten (Farben, Bildgrößen) bleiben in ui/constants.py
"""

import re

# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGS-KONSTANTEN
# ══════════════════════════════════════════════════════════════════════

MIN_PASSWORD_LENGTH = 8
"""Minimale Passwort-Länge."""

MAX_DISPLAY_NAME_LENGTH = 50
"""Maximale Länge für Anzeigename (Profil). Einheitlich 50 (nicht 30)."""

SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
"""Erlaubte Sonderzeichen für Passwörter."""

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)
"""Kompilierter Regex für E-Mail-Validierung."""

# ══════════════════════════════════════════════════════════════════════
# TEXT-LÄNGEN-LIMITS
# ══════════════════════════════════════════════════════════════════════

MAX_HEADLINE_LENGTH = 50
"""Maximale Länge für Post-Überschrift/Name."""

MAX_DESCRIPTION_LENGTH = 2000
"""Maximale Länge für Post-Beschreibung."""

MIN_DESCRIPTION_LENGTH = 10
"""Minimale Länge für Post-Beschreibung."""

MAX_LOCATION_LENGTH = 200
"""Maximale Länge für Ortsangabe."""

MAX_SEARCH_QUERY_LENGTH = 200
"""Maximale Länge für Suchbegriffe."""

MAX_COMMENT_LENGTH = 1000
"""Maximale Länge für Kommentar-Text."""

TRUNCATE_TEXT_LENGTH = 100
"""Standard-Länge für Text-Kürzung in Vorschauen."""

# ══════════════════════════════════════════════════════════════════════
# POST-LIMITS
# ══════════════════════════════════════════════════════════════════════

MAX_POSTS_LIMIT = 30
"""Maximale Anzahl von Posts die auf einmal geladen werden."""

DEFAULT_POSTS_LIMIT = 200
"""Standard-Limit für Post-Abfragen in der Datenbank."""
