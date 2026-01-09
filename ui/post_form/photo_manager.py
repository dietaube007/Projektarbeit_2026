"""
Photo Manager - Lokale Datei-Verwaltung und Helper-Funktionen.

Enthält Funktionen für:
- Lokale Datei-Verwaltung (Upload-Pfade, Cleanup)
- Hinweis: Storage-Operationen sind jetzt in PostService
"""

from __future__ import annotations

import os
from typing import Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


def cleanup_local_file(file_path: str) -> bool:
    """Löscht eine lokale temporäre Datei.
    
    Args:
        file_path: Pfad zur zu löschenden Datei
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as ex:
        logger.warning(f"Fehler beim Löschen der lokalen Datei {file_path}: {ex}", exc_info=True)
        return False


def get_upload_path(filename: str, session_id: Optional[str] = None) -> str:
    """Erstellt den lokalen Upload-Pfad für eine Datei.
    
    Args:
        filename: Dateiname
        session_id: Optional Session-ID für Unterordner
    
    Returns:
        Vollständiger Pfad zur Datei
    """
    upload_dir = os.getenv("UPLOAD_DIR", "image_uploads")
    if session_id:
        return f"{upload_dir}/{session_id}/{filename}"
    return f"{upload_dir}/{filename}"
