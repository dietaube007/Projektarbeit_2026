from __future__ import annotations

from typing import Any, Dict, List

from supabase import Client

from utils.logging_config import get_logger

logger = get_logger(__name__)


class FavoritesService:
    """Service-Klasse für das Verwalten von Favoriten."""

    def __init__(self, sb: Client) -> None:
        self.sb = sb

    # ─────────────────────────────────────────────────────────────
    # Hilfsmethoden
    # ─────────────────────────────────────────────────────────────

    def _get_current_user(self) -> Any | None:
        """Lädt den aktuellen Benutzer über Supabase."""
        try:
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                return user_response.user
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden des Benutzers (Favoriten): {e}", exc_info=True)
            return None

    # ─────────────────────────────────────────────────────────────
    # Öffentliche API
    # ─────────────────────────────────────────────────────────────

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Lädt alle favorisierten Meldungen des aktuellen Benutzers."""
        user = self._get_current_user()
        if not user:
            return []

        try:
            # Favoriten-IDs laden
            fav_res = (
                self.sb.table("favorite")
                .select("post_id")
                .eq("user_id", user.id)
                .execute()
            )
            fav_rows = fav_res.data or []
            post_ids = [row["post_id"] for row in fav_rows if row.get("post_id")]

            if not post_ids:
                return []

            # Posts laden
            posts_res = (
                self.sb.table("post")
                .select(
                    """
                    id,
                    headline,
                    location_text,
                    event_date,
                    created_at,
                    is_active,
                    post_status(id, name),
                    species(id, name),
                    breed(id, name),
                    post_image(url),
                    post_color(color(id, name))
                    """
                )
                .in_("id", post_ids)
                .order("created_at", desc=True)
                .execute()
            )

            return posts_res.data or []

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der Favoriten: {e}", exc_info=True)
            return []

    def add_favorite(self, post_id: int) -> bool:
        """Fügt einen Post zu den Favoriten hinzu."""
        user = self._get_current_user()
        if not user:
            return False

        try:
            self.sb.table("favorite").insert(
                {
                    "user_id": user.id,
                    "post_id": post_id,
                }
            ).execute()
            logger.info(f"Favorit hinzugefügt: User {user.id}, Post {post_id}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Hinzufügen zu Favoriten: {e}", exc_info=True)
            return False

    def remove_favorite(self, post_id: int) -> bool:
        """Entfernt einen Post aus den Favoriten."""
        user = self._get_current_user()
        if not user:
            return False

        try:
            (
                self.sb.table("favorite")
                .delete()
                .eq("user_id", user.id)
                .eq("post_id", post_id)
                .execute()
            )
            logger.info(f"Favorit entfernt: User {user.id}, Post {post_id}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Entfernen aus Favoriten: {e}", exc_info=True)
            return False

    def is_favorite(self, post_id: int) -> bool:
        """Prüft ob ein Post in den Favoriten ist."""
        user = self._get_current_user()
        if not user:
            return False

        try:
            res = (
                self.sb.table("favorite")
                .select("id")
                .eq("user_id", user.id)
                .eq("post_id", post_id)
                .maybe_single()
                .execute()
            )
            return res.data is not None
        except Exception:
            return False


