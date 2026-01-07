"""Post/Meldungs-Verwaltung.

Dieses Modul verwaltet alle Datenbankoperationen für Posts/Tier-Meldungen:
- Erstellen neuer Posts
- Aktualisieren bestehender Posts
- Verknüpfung von Posts mit Farben
- Foto-Upload zum Storage

"""

from __future__ import annotations

from supabase import Client
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Konstante hier definiert um Circular Import zu vermeiden
DEFAULT_POSTS_LIMIT: int = 200


class PostService:
    """Service-Klasse für Post-Operationen."""

    STORAGE_BUCKET: str = "pet-images"

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb
    
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt einen neuen Post und gibt ihn zurück.

        Args:
            payload: Dictionary mit Post-Daten

        Returns:
            Erstellter Post als Dictionary

        Raises:
            RuntimeError: Bei Fehler beim Erstellen
        """
        try:
            res = self.sb.table("post").insert(payload).execute()

            if not res.data:
                raise RuntimeError("Keine Daten in der Response")
            return res.data[0]
        except Exception as ex:
            raise RuntimeError(f"Fehler beim Erstellen der Meldung: {str(ex)}")
    
    def update(self, post_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert einen bestehenden Post.

        Args:
            post_id: ID des zu aktualisierenden Posts
            payload: Dictionary mit aktualisierten Daten

        Returns:
            Aktualisierter Post als Dictionary

        Raises:
            RuntimeError: Bei Fehler beim Aktualisieren
        """
        try:
            res = self.sb.table("post").update(payload).eq("id", post_id).execute()
            if not res.data:
                raise RuntimeError("Keine Daten in der Response")
            return res.data[0]
        except Exception as ex:
            raise RuntimeError(f"Fehler beim Aktualisieren der Meldung: {str(ex)}")
    
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
        if not post_id:
            logger.warning("Versuch, Post ohne ID zu löschen")
            return False
        
        # Prüfe ob Post existiert
        try:
            post_check = self.sb.table("post").select("id").eq("id", post_id).execute()
            if not post_check.data:
                logger.warning(f"Post {post_id} existiert nicht")
                return False
        except Exception as ex:
            logger.error(f"Fehler beim Prüfen der Post-Existenz {post_id}: {ex}", exc_info=True)
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
                    if self.STORAGE_BUCKET in url:
                        parts = url.split(f"{self.STORAGE_BUCKET}/")
                        if len(parts) > 1:
                            file_path = parts[1].split("?")[0]
                            self.sb.storage.from_(self.STORAGE_BUCKET).remove([file_path])
                            deleted_storage_files.append(file_path)
                            logger.debug(f"Storage-Datei gelöscht: {file_path}")
                except Exception as ex:
                    # Storage-Löschung ist nicht kritisch, weitermachen
                    logger.warning(f"Konnte Storage-Datei nicht löschen ({url}): {ex}")
            
            # 3. Lösche verknüpfte Daten aus der Datenbank
            # Reihenfolge: Zuerst abhängige Tabellen, dann Haupttabelle
            try:
                self.sb.table("post_image").delete().eq("post_id", post_id).execute()
                deleted_images = True
                logger.debug(f"Post-Images für Post {post_id} gelöscht")
            except Exception as ex:
                logger.error(f"Fehler beim Löschen der Post-Images für Post {post_id}: {ex}", exc_info=True)
                raise
            
            try:
                self.sb.table("post_color").delete().eq("post_id", post_id).execute()
                deleted_colors = True
                logger.debug(f"Post-Farben für Post {post_id} gelöscht")
            except Exception as ex:
                logger.error(f"Fehler beim Löschen der Post-Farben für Post {post_id}: {ex}", exc_info=True)
                raise
            
            # 4. Lösche den Post selbst (zuletzt, da andere Tabellen davon abhängen)
            try:
                self.sb.table("post").delete().eq("id", post_id).execute()
                logger.info(f"Post {post_id} erfolgreich gelöscht")
                return True
            except Exception as ex:
                logger.error(f"Fehler beim Löschen des Posts {post_id}: {ex}", exc_info=True)
                # Post konnte nicht gelöscht werden, aber abhängige Daten wurden bereits gelöscht
                # Dies ist ein inkonsistenter Zustand, sollte aber selten vorkommen
                raise
            
        except Exception as ex:
            # Bei Fehler: Logge den inkonsistenten Zustand
            logger.error(
                f"Fehler beim Löschen von Post {post_id}. "
                f"Status: Images={deleted_images}, Colors={deleted_colors}, "
                f"Storage={len(deleted_storage_files)} Dateien gelöscht. "
                f"Fehler: {ex}",
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
        try:
            res = self.sb.table("post").select("*, post_image(url)").eq("id", post_id).execute()
            return res.data[0] if res.data else None
        except Exception as ex:
            logger.error(f"Fehler beim Laden des Posts {post_id}: {ex}", exc_info=True)
            return None
    
    def get_all(self, limit: int = DEFAULT_POSTS_LIMIT) -> List[Dict[str, Any]]:
        """Holt alle Posts mit Relationen.
        
        Optimiert: Lädt alle Relationen in einer einzigen Query (kein N+1 Problem).

        Args:
            limit: Maximale Anzahl zu ladender Posts

        Returns:
            Liste von Posts als Dictionaries, leere Liste bei Fehler
        """
        try:
            # Optimierte Query: Alle Relationen in einem Select (kein N+1 Problem)
            # Supabase PostgREST unterstützt verschachtelte Selects für Relationen
            res = self.sb.table("post").select("""
                *,
                post_status(id, name),
                species(id, name),
                breed(id, name),
                post_image(url),
                post_color(color(id, name))
            """).limit(limit).execute()
            return res.data or []
        except Exception as ex:
            logger.error(f"Fehler beim Laden der Posts (Limit: {limit}): {ex}", exc_info=True)
            return []

    def get_my_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """Lädt alle Meldungen eines bestimmten Benutzers."""
        if not user_id:
            return []

        try:
            res = (
                self.sb.table("post")
                .select(
                    """
                    id,
                    headline,
                    description,
                    location_text,
                    event_date,
                    created_at,
                    is_active,
                    post_status(id, name),
                    species(id, name),
                    breed(id, name),
                    sex(id, name),
                    post_image(url),
                    post_color(color(id, name))
                    """
                )
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as ex:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der eigenen Meldungen für User {user_id}: {ex}", exc_info=True)
            return []
    
    def add_color(self, post_id: str, color_id: int) -> None:
        """Fügt eine Farbe zu einem Post hinzu.

        Args:
            post_id: ID des Posts
            color_id: ID der hinzuzufügenden Farbe
        """
        try:
            self.sb.table("post_color").insert({
                "post_id": post_id,
                "color_id": color_id,
            }).execute()
        except Exception as ex:
            logger.error(f"Fehler beim Hinzufügen der Farbe {color_id} zu Post {post_id}: {ex}", exc_info=True)
    
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
            except Exception as ex:
                logger.error(f"Fehler beim Löschen alter Farben für Post {post_id}: {ex}", exc_info=True)
                raise
            
            # Neue Farben hinzufügen (nur wenn Liste nicht leer)
            if color_ids:
                try:
                    # Batch-Insert für bessere Performance
                    color_data = [
                        {"post_id": post_id, "color_id": color_id}
                        for color_id in color_ids
                    ]
                    self.sb.table("post_color").insert(color_data).execute()
                    logger.debug(f"{len(color_ids)} neue Farben für Post {post_id} hinzugefügt")
                except Exception as ex:
                    logger.error(f"Fehler beim Hinzufügen neuer Farben für Post {post_id}: {ex}", exc_info=True)
                    # Bei Fehler: Alte Farben wurden bereits gelöscht, aber neue konnten nicht hinzugefügt werden
                    # Dies ist ein inkonsistenter Zustand
                    raise
            else:  
                logger.debug(f"Keine neuen Farben für Post {post_id}, nur alte gelöscht")
                
        except Exception as ex:
            logger.error(f"Fehler beim Aktualisieren der Farben für Post {post_id}: {ex}", exc_info=True)
            raise
    
    def add_photo(self, post_id: str, photo_url: str) -> None:
        """Speichert eine Foto-URL für einen Post.

        Args:
            post_id: ID des Posts
            photo_url: URL des hochgeladenen Fotos
        """
        try:
            self.sb.table("post_image").insert({
                "post_id": post_id,
                "url": photo_url,
            }).execute()
        except Exception as ex:
            logger.error(f"Fehler beim Speichern der Foto-URL für Post {post_id}: {ex}", exc_info=True)

