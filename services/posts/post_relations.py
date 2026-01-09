"""Post-Verknüpfungen - Farben und Fotos."""

from __future__ import annotations

from typing import List

from supabase import Client

from utils.logging_config import get_logger

logger = get_logger(__name__)


class PostRelationsService:
    """Service für Post-Verknüpfungen (Farben, Fotos)."""

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.
        
        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb
    
    def add_color(self, post_id: str, color_id: int) -> None:
        """Fügt eine Farbe zu einem Post hinzu.

        Args:
            post_id: ID des Posts
            color_id: ID der hinzuzufügenden Farbe
        
        Raises:
            ValueError: Wenn post_id oder color_id ungültig sind
        """
        if not post_id:
            raise ValueError("post_id darf nicht leer sein")
        if not color_id or color_id <= 0:
            raise ValueError("color_id muss eine positive Zahl sein")
        
        try:
            self.sb.table("post_color").insert({
                "post_id": post_id,
                "color_id": color_id,
            }).execute()
            logger.debug(f"Farbe {color_id} zu Post {post_id} hinzugefügt")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Hinzufügen der Farbe {color_id} zu Post {post_id}: {e}", exc_info=True)
            raise
    
    def update_colors(self, post_id: str, color_ids: List[int]) -> None:
        """Aktualisiert die Farben eines Posts (löscht alte, fügt neue hinzu).
        
        Hinweis: Da Supabase Python Client keine expliziten Transaktionen unterstützt,
        werden die Operationen sequenziell ausgeführt. Bei Fehlern wird versucht,
        einen konsistenten Zustand zu gewährleisten.

        Args:
            post_id: ID des Posts
            color_ids: Liste mit IDs der neuen Farben
        """
        if not post_id:
            logger.warning("Versuch, Farben für Post ohne ID zu aktualisieren")
            return
        
        try:
            # Prüfe ob Post existiert
            post_check = self.sb.table("post").select("id").eq("id", post_id).execute()
            if not post_check.data:
                logger.warning(f"Post {post_id} existiert nicht, kann Farben nicht aktualisieren")
                return
            
            # Alte Farben löschen
            try:
                self.sb.table("post_color").delete().eq("post_id", post_id).execute()
                logger.debug(f"Alte Farben für Post {post_id} gelöscht")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Fehler beim Löschen alter Farben für Post {post_id}: {e}", exc_info=True)
                raise
            
            # Neue Farben hinzufügen (nur wenn Liste nicht leer)
            if color_ids:
                try:
                    color_data = [
                        {"post_id": post_id, "color_id": color_id}
                        for color_id in color_ids
                    ]
                    self.sb.table("post_color").insert(color_data).execute()
                    logger.debug(f"{len(color_ids)} neue Farben für Post {post_id} hinzugefügt")
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Fehler beim Hinzufügen neuer Farben für Post {post_id}: {e}", exc_info=True)
                    raise
            else:  
                logger.debug(f"Keine neuen Farben für Post {post_id}, nur alte gelöscht")
                
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Aktualisieren der Farben für Post {post_id}: {e}", exc_info=True)
            raise
    
    def add_photo(self, post_id: str, photo_url: str) -> None:
        """Speichert eine Foto-URL für einen Post.

        Args:
            post_id: ID des Posts
            photo_url: URL des hochgeladenen Fotos
        
        Raises:
            ValueError: Wenn post_id oder photo_url ungültig sind
        """
        if not post_id:
            raise ValueError("post_id darf nicht leer sein")
        if not photo_url or not photo_url.strip():
            raise ValueError("photo_url darf nicht leer sein")
        
        try:
            self.sb.table("post_image").insert({
                "post_id": post_id,
                "url": photo_url.strip(),
            }).execute()
            logger.debug(f"Foto-URL für Post {post_id} gespeichert")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Speichern der Foto-URL für Post {post_id}: {e}", exc_info=True)
            raise
