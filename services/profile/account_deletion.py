from __future__ import annotations

import os
from typing import Tuple

import httpx
from supabase import Client

from utils.logging_config import get_logger

logger = get_logger(__name__)


class AccountDeletionService:
    """Service für das vollständige Löschen eines Benutzerkontos."""

    PET_IMAGES_BUCKET: str = "pet-images"

    def __init__(self, sb: Client) -> None:
        self.sb = sb

    def _get_current_user(self):
        try:
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                return user_response.user
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden des Benutzers (AccountDeletion): {e}", exc_info=True)
            return None

    def delete_account(self) -> Tuple[bool, str]:
        """Löscht das Konto des aktuellen Benutzers und alle zugehörigen Daten."""
        user = self._get_current_user()
        if not user:
            return False, "Nicht eingeloggt."

        user_id = user.id
        PET_IMAGES_BUCKET = self.PET_IMAGES_BUCKET

        try:
            # 1. Profilbild aus Storage löschen
            try:
                storage_path = f"{user_id}/avatar.jpg"
                self.sb.storage.from_("profile-images").remove([storage_path])
                logger.info(f"Profilbild gelöscht für User {user_id}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Fehler beim Löschen des Profilbilds: {e}")

            # 2. Tierbilder aus Storage löschen
            try:
                posts_res = self.sb.table("post").select("id").eq("user_id", user_id).execute()
                post_ids = [p["id"] for p in (posts_res.data or [])]

                for post_id in post_ids:
                    images_res = (
                        self.sb.table("post_image")
                        .select("url")
                        .eq("post_id", post_id)
                        .execute()
                    )
                    for img in (images_res.data or []):
                        url = img.get("url", "")
                        if PET_IMAGES_BUCKET in url:
                            try:
                                parts = url.split(f"{PET_IMAGES_BUCKET}/")
                                if len(parts) > 1:
                                    file_path = parts[1].split("?")[0]
                                    self.sb.storage.from_(PET_IMAGES_BUCKET).remove([file_path])
                                    logger.debug(f"Tierbild gelöscht: {file_path}")
                            except Exception as e:  # noqa: BLE001
                                logger.warning(f"Fehler beim Löschen des Tierbilds ({url}): {e}")
                logger.info(f"Tierbilder gelöscht für User {user_id}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Fehler beim Löschen der Tierbilder: {e}")

            # 3. Favoriten löschen
            try:
                self.sb.table("favorite").delete().eq("user_id", user_id).execute()
                logger.info(f"Favoriten gelöscht für User {user_id}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Fehler beim Löschen der Favoriten: {e}")

            # 4. Meldungen des Benutzers komplett löschen (inkl. verknüpfte Daten)
            try:
                posts_res = self.sb.table("post").select("id").eq("user_id", user_id).execute()
                post_ids = [p["id"] for p in (posts_res.data or [])]

                for post_id in post_ids:
                    self.sb.table("post_image").delete().eq("post_id", post_id).execute()
                    self.sb.table("post_color").delete().eq("post_id", post_id).execute()
                    self.sb.table("favorite").delete().eq("post_id", post_id).execute()

                self.sb.table("post").delete().eq("user_id", user_id).execute()
                logger.info(f"Meldungen gelöscht für User {user_id}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Fehler beim Löschen der Meldungen: {e}")

            # 5. Benutzer über Edge Function löschen
            try:
                session = self.sb.auth.get_session()
                if session and session.access_token:
                    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
                    edge_function_url = f"{supabase_url}/functions/v1/delete-user"

                    response = httpx.post(
                        edge_function_url,
                        headers={
                            "Authorization": f"Bearer {session.access_token}",
                            "Content-Type": "application/json",
                        },
                        timeout=30.0,
                    )

                    if response.status_code == 200:
                        logger.info(f"Benutzer {user_id} erfolgreich über Edge Function gelöscht")
                    else:
                        logger.warning(
                            f"Edge Function Fehler: {response.status_code} - {response.text}"
                        )
                else:
                    logger.warning("Keine Session gefunden für Edge Function Aufruf")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Fehler beim Aufruf der Edge Function: {e}")

            # 6. Ausloggen (falls noch nicht durch Edge Function geschehen)
            try:
                self.sb.auth.sign_out()
            except Exception:
                pass

            logger.info(f"Konto gelöscht für User {user_id}")
            return True, ""

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Löschen des Kontos: {e}", exc_info=True)
            return False, str(e)


