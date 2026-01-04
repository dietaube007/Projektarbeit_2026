"""
Photo Manager - Foto-Upload und Bildkomprimierung.

Enthält Funktionen für:
- Bildkomprimierung mit PIL
- Datei-Upload zu Supabase Storage
- Foto-Entfernung aus Storage
"""

from __future__ import annotations

import os
import io
import base64
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

from supabase import Client

from PIL import Image

from ui.post_form.constants import (
    MAX_IMAGE_SIZE,
    IMAGE_QUALITY,
    STORAGE_BUCKET,
    UPLOAD_DIR,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


def compress_image(file_path: str) -> Tuple[bytes, str]:
    """Komprimiert ein Bild für schnelleres Laden.
    
    Konvertiert das Bild zu JPEG und passt die Größe an.
    Behält das Seitenverhältnis bei.
    
    Args:
        file_path: Pfad zur Bilddatei
    
    Returns:
        Tuple mit (komprimierte Bytes, Dateiendung)
    """
    with Image.open(file_path) as img:
        # EXIF-Orientierung beibehalten, zu RGB konvertieren
        img = img.convert("RGB")
        
        # Größe anpassen wenn nötig (behält Seitenverhältnis)
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Als JPEG komprimieren
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
        buffer.seek(0)
        
        return buffer.read(), "jpeg"


def upload_to_storage(
    sb: Client,
    file_path: str,
    original_filename: str
) -> Dict[str, Optional[str]]:
    """Komprimiert und lädt ein Bild zu Supabase Storage hoch.
    
    Args:
        sb: Supabase Client-Instanz
        file_path: Pfad zur lokalen Bilddatei
        original_filename: Original-Dateiname
    
    Returns:
        Dictionary mit:
        - path: Storage-Pfad
        - base64: Base64-kodierte Bilddaten
        - url: Öffentliche URL
        - name: Original-Dateiname
        Alle Werte sind None bei Fehler
    """
    try:
        # Bild komprimieren
        compressed_bytes, file_ext = compress_image(file_path)
        image_data = base64.b64encode(compressed_bytes).decode()
        
        # Eindeutigen Dateinamen generieren
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = original_filename.rsplit(".", 1)[0]
        storage_filename = f"{timestamp}_{original_name}.jpg"
        
        # Zu Supabase Storage hochladen
        sb.storage.from_(STORAGE_BUCKET).upload(
            path=storage_filename,
            file=compressed_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        
        # Öffentliche URL abrufen
        public_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(storage_filename)
        
        return {
            "path": storage_filename,
            "base64": image_data,
            "url": public_url,
            "name": original_filename
        }
        
    except Exception as ex:
        logger.error(f"Fehler beim Upload von {original_filename}: {ex}", exc_info=True)
        return {"path": None, "base64": None, "url": None, "name": None}


def remove_from_storage(sb: Client, storage_path: Optional[str]) -> bool:
    """Entfernt ein Bild aus Supabase Storage.
    
    Args:
        sb: Supabase Client-Instanz
        storage_path: Pfad zum Bild im Storage (oder None)
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not storage_path:
        return True
        
    try:
        sb.storage.from_(STORAGE_BUCKET).remove([storage_path])
        return True
    except Exception as ex:
        logger.error(f"Fehler beim Löschen aus Storage ({storage_path}): {ex}", exc_info=True)
        return False


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


def get_upload_path(filename: str) -> str:
    """Erstellt den lokalen Upload-Pfad für eine Datei.
    
    Args:
        filename: Dateiname
    
    Returns:
        Vollständiger Pfad im Upload-Verzeichnis
    """
    return f"{UPLOAD_DIR}/{filename}"
