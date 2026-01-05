"""
Konstanten für das Post-Formular.

Enthält Konfigurationswerte für:
- Bildverarbeitung (Größe, Qualität, Formate)
- Formularlayout (Feldbreiten)
- Speicher-Konfiguration
- Datumsformate
"""

from typing import Tuple

# BILDVERARBEITUNG

VALID_IMAGE_TYPES: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]
"""Erlaubte Bildformate für Uploads."""

MAX_IMAGE_SIZE: Tuple[int, int] = (800, 800)
"""Maximale Bildgröße nach Komprimierung (Breite, Höhe)."""

IMAGE_QUALITY: int = 85
"""JPEG-Kompressionsqualität (0-100)."""

PLACEHOLDER_IMAGE: str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
"""1x1 transparentes Platzhalter-Bild als Base64."""

# SPEICHER-KONFIGURATION

STORAGE_BUCKET: str = "pet-images"
"""Supabase Storage Bucket für Tierbilder."""

UPLOAD_DIR: str = "image_uploads"
"""Lokaler Upload-Ordner für temporäre Dateien."""

# FORMULARLAYOUT

FIELD_WIDTH_SMALL: int = 250
"""Breite für kleine Formularfelder (z.B. Dropdowns)."""

FIELD_WIDTH_MEDIUM: int = 400
"""Breite für mittlere Formularfelder (z.B. Name)."""

FIELD_WIDTH_LARGE: int = 500
"""Breite für große Formularfelder (z.B. Beschreibung)."""

# MELDUNGSARTEN

ALLOWED_POST_STATUSES: list[str] = ["vermisst", "fundtier"]
"""Erlaubte Meldungsarten (von Post-Statuses in der DB)."""

# FORMULARWERTE

DATE_FORMAT: str = "%d.%m.%Y"
"""Datumsformat für Eingabe (TT.MM.YYYY)."""

NO_SELECTION_VALUE: str = "none"
"""Wert für "Keine Angabe" in Dropdowns."""

NO_SELECTION_LABEL: str = "— Keine Angabe —"
"""Anzeigetext für "Keine Angabe" in Dropdowns."""
