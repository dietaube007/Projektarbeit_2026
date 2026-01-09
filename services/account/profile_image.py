"""Service für Profilbild-Upload, -Komprimierung und -Löschung."""

from __future__ import annotations

import io
import os
from typing import Any, Optional, Tuple, TYPE_CHECKING

from PIL import Image
from supabase import Client

from utils.logging_config import get_logger

if TYPE_CHECKING:
    from services.account.profile import ProfileService

logger = get_logger(__name__)


class ProfileImageService:
    """Service für alle Profilbild-bezogenen Operationen."""

    PROFILE_IMAGE_BUCKET: str = "profile-images"
    PROFILE_IMAGE_SIZE: Tuple[int, int] = (400, 400)
    IMAGE_QUALITY: int = 85
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB

    def __init__(
        self,
        sb: Client,
        profile_service: Optional["ProfileService"] = None,
    ) -> None:
        """Initialisiert den ProfileImageService.
        
        Args:
            sb: Supabase Client-Instanz
            profile_service: Optional ProfileService (wird bei Bedarf erstellt)
        """
        self.sb = sb
        if profile_service is None:
            from services.account.profile import ProfileService
            self._profile_service = ProfileService(sb)
        else:
            self._profile_service = profile_service

    def _compress_profile_image(self, file_path: str) -> bytes:
        """Komprimiert ein Profilbild auf die gewünschte Größe und Qualität."""
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.thumbnail(self.PROFILE_IMAGE_SIZE, Image.LANCZOS)

            # Quadratisches Bild erstellen
            square_img = Image.new("RGB", self.PROFILE_IMAGE_SIZE, (255, 255, 255))
            paste_x = (self.PROFILE_IMAGE_SIZE[0] - img.width) // 2
            paste_y = (self.PROFILE_IMAGE_SIZE[1] - img.height) // 2
            square_img.paste(img, (paste_x, paste_y))

            buffer = io.BytesIO()
            square_img.save(buffer, format="JPEG", quality=self.IMAGE_QUALITY, optimize=True)
            buffer.seek(0)
            return buffer.read()

    def _update_profile_image_url(self, image_url: Optional[str], user: Optional[Any] = None) -> bool:
        """Aktualisiert die Profilbild-URL in user_metadata.
        
        Args:
            image_url: Neue Profilbild-URL oder None zum Löschen
            user: Optional User-Objekt (wird geladen falls nicht angegeben)
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            if user is None:
                user = self._profile_service.get_current_user()
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

    def upload_profile_image(self, file_path: str) -> Tuple[bool, Optional[str], str]:
        """Lädt ein Profilbild zu Supabase Storage hoch und aktualisiert user_metadata."""
        if not os.path.exists(file_path):
            return False, None, "Datei nicht gefunden."

        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
            return False, None, "Datei zu groß. Max. 5 MB."

        user = self._profile_service.get_current_user()
        if not user:
            return False, None, "Nicht eingeloggt."

        try:
            # Altes Bild aus Storage löschen (nur Storage, Metadaten werden später überschrieben)
            try:
                old_storage_path = f"{user.id}/avatar.jpg"
                self.sb.storage.from_(self.PROFILE_IMAGE_BUCKET).remove([old_storage_path])
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Altes Profilbild existiert nicht oder konnte nicht gelöscht werden: {e}")

            # Bild komprimieren
            compressed_bytes = self._compress_profile_image(file_path)
            storage_path = f"{user.id}/avatar.jpg"

            # Hochladen
            self.sb.storage.from_(self.PROFILE_IMAGE_BUCKET).upload(
                path=storage_path,
                file=compressed_bytes,
                file_options={"content-type": "image/jpeg", "upsert": "true"},
            )

            # Public URL holen
            public_url = self.sb.storage.from_(self.PROFILE_IMAGE_BUCKET).get_public_url(storage_path)

            # URL in Metadaten speichern (user bereits vorhanden)
            success = self._update_profile_image_url(public_url, user=user)
            if not success:
                return False, None, "Konnte Profilbild-URL nicht speichern."

            logger.info(f"Profilbild hochgeladen für User {user.id}")
            return True, public_url, ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Upload des Profilbilds: {e}", exc_info=True)
            return False, None, str(e)

    def delete_profile_image(self, user: Optional[Any] = None) -> Tuple[bool, str]:
        """Löscht das Profilbild aus Storage und user_metadata.
        
        Args:
            user: Optional User-Objekt (wird geladen falls nicht angegeben)
        
        Returns:
            Tuple (success, error_message)
        """
        if user is None:
            user = self._profile_service.get_current_user()
            if not user:
                return False, "Nicht eingeloggt."

        try:
            storage_path = f"{user.id}/avatar.jpg"
            self.sb.storage.from_(self.PROFILE_IMAGE_BUCKET).remove([storage_path])

            # URL aus Metadaten entfernen 
            self._update_profile_image_url(None, user=user)

            logger.info(f"Profilbild gelöscht für User {user.id}")
            return True, ""
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Fehler beim Löschen des Profilbilds: {e}", exc_info=True)
            return False, str(e)
