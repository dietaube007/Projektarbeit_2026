"""Service für Favoriten-Verwaltung.

Ermöglicht Benutzern das Hinzufügen, Entfernen und Abfragen von favorisierten Posts.
"""

from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING, Optional

from supabase import Client

from utils.logging_config import get_logger
from .queries import POST_SELECT_FAVORITES

if TYPE_CHECKING:
    from services.account.profile import ProfileService

logger = get_logger(__name__)


class FavoritesService:
    """Service-Klasse für das Verwalten von Favoriten."""

    def __init__(
        self,
        sb: Client,
        profile_service: Optional["ProfileService"] = None,
    ) -> None:
        """Initialisiert den FavoritesService.
        
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

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Lädt alle favorisierten Meldungen des aktuellen Benutzers.
        
        Returns:
            Liste von Post-Dictionaries mit allen Relationen (Status, Art, Rasse, Bilder, Farben).
            Leere Liste wenn Benutzer nicht eingeloggt ist oder bei Fehler.
        """
        user = self._profile_service.get_current_user()
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
                .select(POST_SELECT_FAVORITES)
                .in_("id", post_ids)
                .order("created_at", desc=True)
                .execute()
            )

            return posts_res.data or []

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der Favoriten: {e}", exc_info=True)
            return []

    def _get_current_user_id(self) -> Optional[str]:
        """Hilfsmethode: Gibt die User-ID des aktuellen Benutzers zurück.
        
        Returns:
            User-ID oder None wenn nicht eingeloggt
        """
        user = self._profile_service.get_current_user()
        return user.id if user else None

    def add_favorite(self, post_id: str) -> bool:
        """Fügt einen Post zu den Favoriten hinzu.
        
        Args:
            post_id: ID des Posts (UUID als String), der zu den Favoriten hinzugefügt werden soll
        
        Returns:
            True bei Erfolg, False wenn Benutzer nicht eingeloggt ist, post_id ungültig ist oder bei Fehler
        """
        if not post_id or not isinstance(post_id, str) or not post_id.strip():
            logger.warning(f"Ungültige post_id beim Hinzufügen zu Favoriten: {post_id}")
            return False
        
        user_id = self._get_current_user_id()
        if not user_id:
            return False

        try:
            self.sb.table("favorite").insert(
                {
                    "user_id": user_id,
                    "post_id": post_id,
                }
            ).execute()
            logger.info(f"Favorit hinzugefügt: User {user_id}, Post {post_id}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Hinzufügen zu Favoriten: {e}", exc_info=True)
            return False

    def remove_favorite(self, post_id: str) -> bool:
        """Entfernt einen Post aus den Favoriten.
        
        Args:
            post_id: ID des Posts (UUID als String), der aus den Favoriten entfernt werden soll
        
        Returns:
            True bei Erfolg, False wenn Benutzer nicht eingeloggt ist, post_id ungültig ist oder bei Fehler
        """
        if not post_id or not isinstance(post_id, str) or not post_id.strip():
            logger.warning(f"Ungültige post_id beim Entfernen aus Favoriten: {post_id}")
            return False
        
        user_id = self._get_current_user_id()
        if not user_id:
            return False

        try:
            (
                self.sb.table("favorite")
                .delete()
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .execute()
            )
            logger.info(f"Favorit entfernt: User {user_id}, Post {post_id}")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Entfernen aus Favoriten: {e}", exc_info=True)
            return False

    def is_favorite(self, post_id: str) -> bool:
        """Prüft ob ein Post in den Favoriten ist.
        
        Args:
            post_id: ID des Posts (UUID als String), der geprüft werden soll
        
        Returns:
            True wenn der Post in den Favoriten ist, False sonst oder bei Fehler
        """
        if not post_id or not isinstance(post_id, str) or not post_id.strip():
            return False
        
        user_id = self._get_current_user_id()
        if not user_id:
            return False

        try:
            res = (
                self.sb.table("favorite")
                .select("id")
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .maybe_single()
                .execute()
            )
            return res.data is not None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Prüfen des Favoriten-Status für Post {post_id}: {e}", exc_info=True)
            return False

    def get_favorite_ids(self, user_id: str) -> set[str]:
        """Holt die Favoriten-IDs eines Benutzers.
        
        Optimiert: Lädt alle Favoriten in einer einzigen Query statt N+1 Queries.

        Args:
            user_id: ID des Benutzers

        Returns:
            Set mit Post-IDs (UUIDs als Strings) der Favoriten, leeres Set wenn user_id None
        """
        if not user_id:
            return set()
        
        try:
            # Optimierte Query: Nur post_id selektieren, keine unnötigen Daten
            fav_res = (
                self.sb.table("favorite")
                .select("post_id")
                .eq("user_id", user_id)
                .execute()
            )
            # Set-Comprehension für schnellen Lookup
            return {str(row["post_id"]) for row in (fav_res.data or []) if "post_id" in row}
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der Favoriten für User {user_id}: {e}", exc_info=True)
            return set()

