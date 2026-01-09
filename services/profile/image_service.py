from __future__ import annotations

import io
import os
from typing import Any, Optional, Tuple

from PIL import Image
from supabase import Client

from utils.logging_config import get_logger

logger = get_logger(__name__)


# Profilbild-Konstanten (bewusst getrennt von anderen Profil-Konstanten)
PROFILE_IMAGE_BUCKET: str = "profile-images"
PROFILE_IMAGE_SIZE: Tuple[int, int] = (400, 400)
IMAGE_QUALITY: int = 85
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB


class ProfileImageService:
    """Service für alle Profilbild-bezogenen Operationen."""

    def __init__(self, sb: Client) -> None:
        self.sb = sb

    # ─────────────────────────────────────────────────────────────
    # Hilfsmethoden
    # ─────────────────────────────────────────────────────────────

    def _get_current_user(self) -> Optional[Any]:
        """Hilfsmethode um den aktuell eingeloggten Benutzer zu laden."""
        try:
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                return user_response.user
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden des Benutzers (Profilbild): {e}", exc_info=True)
            return None

    def _compress_profile_image(self, file_path: str) -> bytes:
        """Komprimiert ein Profilbild auf die gewünschte Größe und Qualität."""
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.thumbnail(PROFILE_IMAGE_SIZE, Image.LANCZOS)

            # Quadratisches Bild erstellen
            square_img = Image.new("RGB", PROFILE_IMAGE_SIZE, (255, 255, 255))
            paste_x = (PROFILE_IMAGE_SIZE[0] - img.width) // 2
            paste_y = (PROFILE_IMAGE_SIZE[1] - img.height) // 2
            square_img.paste(img, (paste_x, paste_y))

            buffer = io.BytesIO()
            square_img.save(buffer, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
            buffer.seek(0)
            return buffer.read()

    def _update_profile_image_url(self, image_url: Optional[str]) -> bool:
        """Aktualisiert die Profilbild-URL in user_metadata."""
        try:
            user = self._get_current_user()
            if not user:
                return False

            current_metadata = dict(user.user_metadata) if user.user_metadata else {}

            if image_url:
                current_metadata["profile_image_url"] = image_url
            else:
                current_metadata.pop("profile_image_url", None)

            self.sb.auth.update_user({"data": current_metadata})
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Aktualisieren der Profilbild-URL: {e}", exc_info=True)
            return False

    # ─────────────────────────────────────────────────────────────
    # Öffentliche API
    # ─────────────────────────────────────────────────────────────

    def upload_profile_image(self, file_path: str) -> Tuple[bool, Optional[str], str]:
        """Lädt ein Profilbild zu Supabase Storage hoch und aktualisiert user_metadata."""
        # Validierungen
        if not os.path.exists(file_path):
            return False, None, "Datei nicht gefunden."

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            return False, None, "Datei zu groß. Max. 5 MB."

        user = self._get_current_user()
        if not user:
            return False, None, "Nicht eingeloggt."

        try:
            # Altes Bild aus Storage löschen (Metadaten werden beim Setzen der neuen URL überschrieben)
            self.delete_profile_image()

            # Bild komprimieren
            compressed_bytes = self._compress_profile_image(file_path)
            storage_path = f"{user.id}/avatar.jpg"

            # Hochladen
            self.sb.storage.from_(PROFILE_IMAGE_BUCKET).upload(
                path=storage_path,
                file=compressed_bytes,
                file_options={"content-type": "image/jpeg", "upsert": "true"},
            )

            # Public URL holen
            public_url = self.sb.storage.from_(PROFILE_IMAGE_BUCKET).get_public_url(storage_path)

            # URL in Metadaten speichern
            success = self._update_profile_image_url(public_url)
            if not success:
                return False, None, "Konnte Profilbild-URL nicht speichern."

            logger.info(f"Profilbild hochgeladen für User {user.id}")
            return True, public_url, ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Upload des Profilbilds: {e}", exc_info=True)
            return False, None, str(e)

    def delete_profile_image(self) -> Tuple[bool, str]:
        """Löscht das Profilbild aus Storage und user_metadata."""
        user = self._get_current_user()
        if not user:
            return False, "Nicht eingeloggt."

        try:
            storage_path = f"{user.id}/avatar.jpg"
            self.sb.storage.from_(PROFILE_IMAGE_BUCKET).remove([storage_path])

            # URL aus Metadaten entfernen
            self._update_profile_image_url(None)

            logger.info(f"Profilbild gelöscht für User {user.id}")
            return True, ""
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Fehler beim Löschen des Profilbilds: {e}", exc_info=True)
            return False, str(e)


