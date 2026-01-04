"""
Photo Manager - Foto-Upload und Bildkomprimierung.

Enthält Funktionen für:
- Bildkomprimierung mit PIL
- Datei-Upload zu Supabase Storage
- Foto-Entfernung aus Storage
"""

import os
import io
import base64
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

from PIL import Image

from ui.post_form.constants import (
    MAX_IMAGE_SIZE,
    IMAGE_QUALITY,
    STORAGE_BUCKET,
    UPLOAD_DIR,
)


def compress_image(file_path: str) -> Tuple[bytes, str]:
    """
    Komprimiert ein Bild für schnelleres Laden.
    Konvertiert das Bild zu JPEG und passt die Größe an.
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
    sb,
    file_path: str,
    original_filename: str
) -> Dict[str, Optional[str]]:
    """Komprimiert und lädt ein Bild zu Supabase Storage hoch."""
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
        print(f"Fehler beim Upload: {ex}")
        return {"path": None, "base64": None, "url": None, "name": None}


def remove_from_storage(sb, storage_path: Optional[str]) -> bool:
    """Entfernt ein Bild aus Supabase Storage."""
    if not storage_path:
        return True
        
    try:
        sb.storage.from_(STORAGE_BUCKET).remove([storage_path])
        return True
    except Exception as ex:
        print(f"Fehler beim Löschen aus Storage: {ex}")
        return False


def cleanup_local_file(file_path: str) -> bool:
    """Löscht eine lokale temporäre Datei."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as ex:
        print(f"Fehler beim Löschen der lokalen Datei: {ex}")
        return False


def get_upload_path(filename: str) -> str:
    """Erstellt den lokalen Upload-Pfad für eine Datei."""
    return f"{UPLOAD_DIR}/{filename}"
