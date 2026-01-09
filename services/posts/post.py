"""Post CRUD-Operationen - Erstellen, Lesen, Aktualisieren, Löschen."""

from __future__ import annotations

from typing import Dict, Any, List, Optional, TYPE_CHECKING

from supabase import Client

from utils.logging_config import get_logger
from utils.constants import DEFAULT_POSTS_LIMIT
from .queries import POST_SELECT_FULL, POST_SELECT_MY_POSTS

if TYPE_CHECKING:
    from .post_image import PostStorageService

logger = get_logger(__name__)


class PostService:
    """Service-Klasse für Post CRUD-Operationen."""

    def __init__(
        self,
        sb: Client,
        storage_service: Optional["PostStorageService"] = None,
    ) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
            storage_service: Optional PostStorageService (wird bei Bedarf erstellt)
        """
        self.sb = sb
        if storage_service is None:
            from .post_image import PostStorageService
            self._storage_service = PostStorageService(sb)
        else:
            self._storage_service = storage_service
    
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt einen neuen Post und gibt ihn zurück.

        Args:
            payload: Dictionary mit Post-Daten

        Returns:
            Erstellter Post als Dictionary

        Raises:
            ValueError: Wenn payload ungültig ist
            RuntimeError: Bei Fehler beim Erstellen
        """
        if not payload or not isinstance(payload, dict):
            raise ValueError("Payload darf nicht leer sein und muss ein Dictionary sein.")

        try:
            res = self.sb.table("post").insert(payload).execute()

            if not res.data:
                raise RuntimeError("Keine Daten in der Response")
            return res.data[0]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Fehler beim Erstellen der Meldung: {str(e)}")
    
    def update(self, post_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert einen bestehenden Post.

        Args:
            post_id: ID des zu aktualisierenden Posts
            payload: Dictionary mit aktualisierten Daten

        Returns:
            Aktualisierter Post als Dictionary

        Raises:
            ValueError: Wenn post_id oder payload ungültig sind
            RuntimeError: Bei Fehler beim Aktualisieren
        """
        if not post_id or not isinstance(post_id, str) or not post_id.strip():
            raise ValueError("post_id darf nicht leer sein.")
        if not payload or not isinstance(payload, dict):
            raise ValueError("Payload darf nicht leer sein und muss ein Dictionary sein.")

        try:
            res = self.sb.table("post").update(payload).eq("id", post_id).execute()
            if not res.data:
                raise RuntimeError("Keine Daten in der Response")
            return res.data[0]
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Fehler beim Aktualisieren der Meldung: {str(e)}")
    
    def delete(self, post_id: str) -> bool:
        """Löscht einen Post komplett inkl. Bilder und verknüpfter Daten.
        
        Hinweis: Da Supabase Python Client keine expliziten Transaktionen unterstützt,
        werden die Operationen sequenziell ausgeführt. Bei Fehlern wird versucht,
        einen konsistenten Zustand zu gewährleisten.

        Args:
            post_id: ID des zu löschenden Posts

        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not post_id or not isinstance(post_id, str) or not post_id.strip():
            logger.warning("Versuch, Post ohne gültige ID zu löschen")
            return False
        
        # Prüfe ob Post existiert
        try:
            post_check = self.sb.table("post").select("id").eq("id", post_id).execute()
            if not post_check.data:
                logger.warning(f"Post {post_id} existiert nicht")
                return False
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Prüfen der Post-Existenz {post_id}: {e}", exc_info=True)
            return False
        
        # Sammle Informationen für Rollback (falls nötig)
        deleted_storage_files = []
        deleted_images = False
        deleted_colors = False
        
        try:
            # 1. Hole die Bild-URLs vor dem Löschen
            images_res = self.sb.table("post_image").select("url").eq("post_id", post_id).execute()
            image_urls = [img["url"] for img in (images_res.data or [])]
            
            # 2. Lösche Bilder aus Storage (kann fehlschlagen, ist aber nicht kritisch)
            for url in image_urls:
                try:
                    file_path = self._storage_service.extract_storage_path_from_url(url)
                    if file_path:
                        self._storage_service.remove_post_image(file_path)
                        deleted_storage_files.append(file_path)
                        logger.debug(f"Storage-Datei gelöscht: {file_path}")
                except Exception as e:  # noqa: BLE001
                    # Storage-Löschung ist nicht kritisch, weitermachen
                    logger.warning(f"Konnte Storage-Datei nicht löschen ({url}): {e}")
            
            # 3. Lösche verknüpfte Daten aus der Datenbank
            # Reihenfolge: Zuerst abhängige Tabellen, dann Haupttabelle
            try:
                self.sb.table("post_image").delete().eq("post_id", post_id).execute()
                deleted_images = True
                logger.debug(f"Post-Images für Post {post_id} gelöscht")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Fehler beim Löschen der Post-Images für Post {post_id}: {e}", exc_info=True)
                raise
            
            try:
                self.sb.table("post_color").delete().eq("post_id", post_id).execute()
                deleted_colors = True
                logger.debug(f"Post-Farben für Post {post_id} gelöscht")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Fehler beim Löschen der Post-Farben für Post {post_id}: {e}", exc_info=True)
                raise
            
            # 4. Lösche den Post selbst (zuletzt, da andere Tabellen davon abhängen)
            try:
                self.sb.table("post").delete().eq("id", post_id).execute()
                logger.info(f"Post {post_id} erfolgreich gelöscht")
                return True
            except Exception as e:  # noqa: BLE001
                logger.error(f"Fehler beim Löschen des Posts {post_id}: {e}", exc_info=True)
                # Post konnte nicht gelöscht werden, aber abhängige Daten wurden bereits gelöscht
                # Dies ist ein inkonsistenter Zustand, sollte aber selten vorkommen
                raise
            
        except Exception as e:  # noqa: BLE001
            # Bei Fehler: Logge den inkonsistenten Zustand
            logger.error(
                f"Fehler beim Löschen von Post {post_id}. "
                f"Status: Images={deleted_images}, Colors={deleted_colors}, "
                f"Storage={len(deleted_storage_files)} Dateien gelöscht. "
                f"Fehler: {e}",
                exc_info=True
            )
            return False
    
    def get_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Holt einen Post anhand seiner ID.

        Args:
            post_id: ID des gesuchten Posts

        Returns:
            Post als Dictionary oder None bei Fehler
        """
        if not post_id or not isinstance(post_id, str) or not post_id.strip():
            logger.warning("Ungültige post_id beim Laden eines Posts")
            return None

        try:
            res = self.sb.table("post").select(POST_SELECT_FULL).eq("id", post_id).execute()
            return res.data[0] if res.data else None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden des Posts {post_id}: {e}", exc_info=True)
            return None
    
    def get_all(self, limit: int = DEFAULT_POSTS_LIMIT) -> List[Dict[str, Any]]:
        """Holt alle Posts mit Relationen.

        Args:
            limit: Maximale Anzahl zu ladender Posts

        Returns:
            Liste von Posts als Dictionaries, leere Liste bei Fehler
        """
        if not isinstance(limit, int) or limit <= 0:
            logger.warning(f"Ungültiges Limit für get_all: {limit}. Verwende Standardlimit.")
            limit = DEFAULT_POSTS_LIMIT

        try:
            res = self.sb.table("post").select(POST_SELECT_FULL).limit(limit).execute()
            return res.data or []
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der Posts (Limit: {limit}): {e}", exc_info=True)
            return []

    def get_my_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """Lädt alle Meldungen eines bestimmten Benutzers.
        
        Args:
            user_id: ID des Benutzers
        
        Returns:
            Liste von Posts als Dictionaries, leere Liste bei Fehler oder wenn user_id leer ist
        """
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            logger.warning("Ungültige user_id beim Laden eigener Meldungen")
            return []

        try:
            res = (
                self.sb.table("post")
                .select(POST_SELECT_MY_POSTS)
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der eigenen Meldungen für User {user_id}: {e}", exc_info=True)
            return []
    
