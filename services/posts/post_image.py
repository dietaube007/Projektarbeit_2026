"""Post Image Storage - Upload, Download, Komprimierung."""

from __future__ import annotations

import os
import base64
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from supabase import Client
from PIL import Image
import io

from utils.logging_config import get_logger

logger = get_logger(__name__)


class PostStorageService:
    """Service für Post-Image Storage-Operationen."""

    MAX_IMAGE_SIZE: Tuple[int, int] = (1920, 1920)
    IMAGE_QUALITY: int = 85
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    IMAGE_CONTENT_TYPE: str = "image/jpeg"
    IMAGE_FORMAT: str = "jpeg"
    STORAGE_BUCKET: str = "pet-images"

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.
        
        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb
    
    def extract_storage_path_from_url(self, url: str) -> Optional[str]:
        """Extrahiert den Storage-Pfad aus einer vollständigen URL.
        
        Args:
            url: Vollständige URL zum Bild
        
        Returns:
            Storage-Pfad oder None wenn URL ungültig oder nicht gefunden
        """
        if not url or not isinstance(url, str):
            return None
        
        url = url.strip()
        if not url or self.STORAGE_BUCKET not in url:
            return None
        
        try:
            parts = url.split(f"{self.STORAGE_BUCKET}/")
            if len(parts) > 1:
                path = parts[1].split("?")[0]
                return path if path else None
        except (AttributeError, IndexError, ValueError) as e:
            logger.warning(f"Fehler beim Extrahieren des Storage-Pfads aus URL: {e}")
        
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Bereinigt einen Dateinamen für sichere Speicherung.
        
        Args:
            filename: Original-Dateiname
        
        Returns:
            Bereinigter Dateiname (nur alphanumerische Zeichen, Bindestrich, Unterstrich)
        """
        # Entferne Dateiendung
        name_without_ext = filename.rsplit(".", 1)[0] if "." in filename else filename
        
        # Ersetze Sonderzeichen und Leerzeichen
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name_without_ext)
        
        # Begrenze Länge
        return sanitized[:50] if len(sanitized) > 50 else sanitized

    def _compress_image(self, file_path: str) -> Tuple[bytes, str]:
        """Komprimiert ein Bild für schnelleres Laden.
        
        Args:
            file_path: Pfad zur Bilddatei
        
        Returns:
            Tuple mit (komprimierte Bytes, Dateiendung)
        
        Raises:
            OSError: Wenn Datei nicht gelesen werden kann
            ValueError: Wenn Datei kein gültiges Bild ist
        """
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.IMAGE_QUALITY, optimize=True)
            buffer.seek(0)
            
            return buffer.read(), self.IMAGE_FORMAT
    
    def _create_error_response(self) -> Dict[str, Optional[str]]:
        """Erstellt ein Fehler-Response-Dictionary.
        
        Returns:
            Dictionary mit allen Werten als None
        """
        return {"path": None, "base64": None, "url": None, "name": None}

    def upload_post_image(
        self,
        file_path: str,
        original_filename: str
    ) -> Dict[str, Optional[str]]:
        """Komprimiert und lädt ein Bild zu Supabase Storage hoch.
        
        Args:
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
        # Input-Validierung
        if not file_path or not isinstance(file_path, str):
            logger.error("Ungültiger file_path")
            return self._create_error_response()
        
        if not original_filename or not isinstance(original_filename, str):
            logger.error("Ungültiger original_filename")
            return self._create_error_response()
        
        try:
            if not os.path.exists(file_path):
                logger.error(f"Datei nicht gefunden: {file_path}")
                return self._create_error_response()
            
            # Dateigröße prüfen
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                logger.error(f"Datei zu groß: {file_size} bytes (Max: {self.MAX_FILE_SIZE} bytes)")
                return self._create_error_response()
            
            # Bild komprimieren
            compressed_bytes, file_ext = self._compress_image(file_path)
            image_data = base64.b64encode(compressed_bytes).decode()
            
            # Eindeutigen Dateinamen generieren
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_name = self._sanitize_filename(original_filename)
            storage_filename = f"{timestamp}_{sanitized_name}.jpg"
            
            # Zu Supabase Storage hochladen
            self.sb.storage.from_(self.STORAGE_BUCKET).upload(
                path=storage_filename,
                file=compressed_bytes,
                file_options={"content-type": self.IMAGE_CONTENT_TYPE}
            )
            
            # Öffentliche URL abrufen
            public_url = self.sb.storage.from_(self.STORAGE_BUCKET).get_public_url(storage_filename)
            
            logger.debug(f"Bild erfolgreich hochgeladen: {storage_filename}")
            return {
                "path": storage_filename,
                "base64": image_data,
                "url": public_url,
                "name": original_filename
            }
            
        except (OSError, ValueError, IOError) as e:
            logger.error(f"Fehler beim Verarbeiten des Bildes: {e}", exc_info=True)
            return self._create_error_response()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Upload des Bildes: {e}", exc_info=True)
            return self._create_error_response()
    
    def remove_post_image(self, storage_path: Optional[str]) -> bool:
        """Entfernt ein Bild aus Supabase Storage.
        
        Args:
            storage_path: Pfad zum Bild im Storage (oder None)
        
        Returns:
            True bei Erfolg oder wenn storage_path None/leer ist, False bei Fehler
        """
        if not storage_path or not isinstance(storage_path, str) or not storage_path.strip():
            return True
            
        try:
            self.sb.storage.from_(self.STORAGE_BUCKET).remove([storage_path.strip()])
            logger.debug(f"Bild aus Storage gelöscht: {storage_path}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Löschen aus Storage ({storage_path}): {e}", exc_info=True)
            return False
    
    def download_post_image(self, storage_path: str) -> Optional[bytes]:
        """Lädt ein Bild aus Supabase Storage herunter.
        
        Args:
            storage_path: Pfad zum Bild im Storage
        
        Returns:
            Bilddaten als Bytes oder None bei Fehler oder ungültigem storage_path
        """
        if not storage_path or not isinstance(storage_path, str) or not storage_path.strip():
            logger.warning("Ungültiger storage_path für Download")
            return None
        
        try:
            response = self.sb.storage.from_(self.STORAGE_BUCKET).download(storage_path.strip())
            return response
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Download des Bildes ({storage_path}): {e}", exc_info=True)
            return None
