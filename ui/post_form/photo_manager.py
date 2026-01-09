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
)

# Berechne absoluten Upload-Pfad relativ zum Projektverzeichnis
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(_PROJECT_ROOT, "image_uploads")


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
        print(f"[DEBUG upload_to_storage] file_path: {file_path}")
        print(f"[DEBUG upload_to_storage] Datei existiert: {os.path.exists(file_path)}")
        
        # Bild komprimieren
        print(f"[DEBUG upload_to_storage] Starte Komprimierung...")
        compressed_bytes, file_ext = compress_image(file_path)
        print(f"[DEBUG upload_to_storage] Komprimierung OK, Größe: {len(compressed_bytes)} bytes")
        image_data = base64.b64encode(compressed_bytes).decode()
        
        # Eindeutigen Dateinamen generieren
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = original_filename.rsplit(".", 1)[0]
        storage_filename = f"{timestamp}_{original_name}.jpg"
        print(f"[DEBUG upload_to_storage] Storage-Dateiname: {storage_filename}")
        
        # Zu Supabase Storage hochladen
        print(f"[DEBUG upload_to_storage] Starte Supabase Upload zu Bucket '{STORAGE_BUCKET}'...")
        sb.storage.from_(STORAGE_BUCKET).upload(
            path=storage_filename,
            file=compressed_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        print(f"[DEBUG upload_to_storage] Supabase Upload erfolgreich!")
        
        # Öffentliche URL abrufen
        public_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(storage_filename)
        print(f"[DEBUG upload_to_storage] Public URL: {public_url}")
        
        return {
            "path": storage_filename,
            "base64": image_data,
            "url": public_url,
            "name": original_filename
        }
        
    except Exception as ex:
        print(f"[ERROR upload_to_storage] Fehler beim Upload: {type(ex).__name__}: {ex}")
        import traceback
        traceback.print_exc()
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


def get_upload_path(filename: str, session_id: Optional[str] = None) -> str:
    """Erstellt den lokalen Upload-Pfad für eine Datei.

    Berücksichtigt den Flet-Session-Unterordner, wenn `session_id` angegeben ist.
    """
    # Stelle sicher, dass das Upload-Verzeichnis existiert
    if session_id:
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        return os.path.join(session_dir, filename)
    else:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        return os.path.join(UPLOAD_DIR, filename)
