"""Service für die vollständige Löschung von Benutzerkonten und zugehörigen Daten."""

from __future__ import annotations

import os
from typing import Tuple, Optional, Any

import httpx
from supabase import Client

from utils.logging_config import get_logger
from services.account.profile import ProfileService
from services.account.profile_image import ProfileImageService
from services.posts.post_image import PostStorageService

logger = get_logger(__name__)


class AccountDeletionService:
    """Service für das vollständige Löschen eines Benutzerkontos."""

    PET_IMAGES_BUCKET: str = "pet-images"
    EDGE_FUNCTION_TIMEOUT: float = 30.0

    def __init__(
        self,
        sb: Client,
        profile_service: Optional[ProfileService] = None,
        profile_image_service: Optional[ProfileImageService] = None,
        post_storage_service: Optional[PostStorageService] = None,
    ) -> None:
        """Initialisiert den AccountDeletionService.
        
        Args:
            sb: Supabase Client-Instanz
            profile_service: Optional ProfileService (wird bei Bedarf erstellt)
            profile_image_service: Optional ProfileImageService (wird bei Bedarf erstellt)
            post_storage_service: Optional PostStorageService (wird bei Bedarf erstellt)
        """
        self.sb = sb
        self._profile_service = profile_service or ProfileService(sb)
        self._profile_image_service = profile_image_service or ProfileImageService(sb)
        self._post_storage_service = post_storage_service or PostStorageService(sb)

    def _delete_pet_images(self, user_id: str, post_ids: list[str]) -> None:
        """Löscht alle Tierbilder des Benutzers aus Storage.
        
        Args:
            user_id: ID des Benutzers
            post_ids: Liste der Post-IDs des Benutzers
        """
        try:
            for post_id in post_ids:
                images_res = (
                    self.sb.table("post_image")
                    .select("url")
                    .eq("post_id", post_id)
                    .execute()
                )
                for img in (images_res.data or []):
                    url = img.get("url", "")
                    if url:
                        try:
                            # Verwende PostStorageService für konsistente Pfad-Extraktion
                            file_path = self._post_storage_service.extract_storage_path_from_url(url)
                            if file_path:
                                self._post_storage_service.remove_post_image(file_path)
                                logger.debug(f"Tierbild gelöscht: {file_path}")
                        except Exception as e:  # noqa: BLE001
                            logger.warning(f"Fehler beim Löschen des Tierbilds ({url}): {e}")
            logger.info(f"Tierbilder gelöscht für User {user_id}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Fehler beim Löschen der Tierbilder: {e}")

    def _delete_user_via_edge_function(self, user_id: str) -> bool:
        """Löscht den Benutzer über die Edge Function.
        
        Args:
            user_id: ID des Benutzers
        
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            session = self.sb.auth.get_session()
            if not session or not session.access_token:
                logger.warning("Keine Session gefunden für Edge Function Aufruf")
                return False

            supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
            if not supabase_url:
                logger.error("SUPABASE_URL nicht gesetzt")
                return False

            edge_function_url = f"{supabase_url}/functions/v1/delete-user"

            response = httpx.post(
                edge_function_url,
                headers={
                    "Authorization": f"Bearer {session.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=self.EDGE_FUNCTION_TIMEOUT,
            )

            if response.status_code == 200:
                logger.info(f"Benutzer {user_id} erfolgreich über Edge Function gelöscht")
                return True
            else:
                logger.warning(
                    f"Edge Function Fehler: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Fehler beim Aufruf der Edge Function: {e}")
            return False

    def delete_account(self) -> Tuple[bool, str]:
        """Löscht das Konto des aktuellen Benutzers und alle zugehörigen Daten.
        
        Hinweis: Viele Daten werden automatisch durch CASCADE DELETE gelöscht,
        wenn der Benutzer gelöscht wird:
        - Posts und verknüpfte Daten (post.user_id → CASCADE)
          - Post-Images (post_image.post_id → CASCADE)
          - Post-Farben (post_color.post_id → CASCADE)
          - Kommentare (comment.post_id → CASCADE)
          - Kontakt-Nachrichten (contact_message.post_id → CASCADE)
        - Favoriten (favorite.user_id → CASCADE)
        - Gespeicherte Suchaufträge (saved_search.user_id → CASCADE)
        - Kommentare (comment.user_id → CASCADE)
        - Notifications (notification.user_id → CASCADE)
        - User-Einstellungen (user_notification_setting.user_id → CASCADE)
        
        Storage-Dateien (Bilder) müssen jedoch explizit gelöscht werden,
        bevor die Datenbank-Einträge durch CASCADE entfernt werden.
        
        Returns:
            Tuple (success, error_message)
        """
        user = self._profile_service.get_current_user()
        if not user:
            return False, "Nicht eingeloggt."

        user_id = user.id

        try:
            # Post-IDs abfragen (für Storage-Löschung)
            posts_res = self.sb.table("post").select("id").eq("user_id", user_id).execute()
            post_ids = [p["id"] for p in (posts_res.data or [])]

            # 1. Profilbild löschen (Storage + DB)
            success, error_msg = self._profile_image_service.delete_profile_image()
            if not success:
                logger.warning(f"Fehler beim Löschen des Profilbilds: {error_msg}")

            # 2. Tierbilder aus Storage löschen (BEVOR Posts durch CASCADE gelöscht werden)
            # Wichtig: Storage-Dateien müssen gelöscht werden, bevor die DB-Einträge
            # durch CASCADE entfernt werden, sonst haben wir die URLs nicht mehr.
            self._delete_pet_images(user_id, post_ids)

            # 3. Benutzer über Edge Function löschen
            # Dies löst CASCADE DELETE für alle verknüpften Daten:
            # - Posts, Favoriten, Saved Searches, Comments, Notifications, etc.
            self._delete_user_via_edge_function(user_id)

            # 4. Ausloggen (falls noch nicht durch Edge Function geschehen)
            try:
                self.sb.auth.sign_out()
            except Exception:
                pass

            logger.info(f"Konto gelöscht für User {user_id}")
            return True, ""

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Löschen des Kontos: {e}", exc_info=True)
            return False, str(e)

