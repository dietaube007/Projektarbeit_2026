"""Post/Meldungs-Verwaltung.

Dieses Modul verwaltet alle Datenbankoperationen für Posts/Tier-Meldungen:
- Erstellen neuer Posts
- Aktualisieren bestehender Posts
- Verknüpfung von Posts mit Farben
- Foto-Upload zum Storage

"""

from supabase import Client
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class PostService:
    # Service-Klasse für Post-Operationen.
    #     
    STORAGE_BUCKET = "pet-images"
    
    def __init__(self, sb: Client):
        # Initialisiert den Service mit dem Supabase-Client.
        self.sb = sb
    
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt einen neuen Post und gibt ihn zurück."""
        try:
            res = self.sb.table("post").insert(payload).execute()
            
            if not res.data:
                raise RuntimeError("Keine Daten in der Response")
            return res.data[0]
        except Exception as ex:
            raise RuntimeError(f"Fehler beim Erstellen der Meldung: {str(ex)}")
    
    def update(self, post_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Aktualisiert einen bestehenden Post.
        try:
            res = self.sb.table("post").update(payload).eq("id", post_id).execute()
            if not res.data:
                raise RuntimeError("Keine Daten in der Response")
            return res.data[0]
        except Exception as ex:
            raise RuntimeError(f"Fehler beim Aktualisieren der Meldung: {str(ex)}")
    
    def delete(self, post_id: str) -> bool:
        # Löscht einen Post komplett inkl. Bilder und verknüpfter Daten.
        try:
            # 1. Hole die Bild-URLs
            images_res = self.sb.table("post_image").select("url").eq("post_id", post_id).execute()
            image_urls = [img["url"] for img in (images_res.data or [])]
            
            # 2. Lösche Bilder aus Storage
            for url in image_urls:
                try:
                    if self.STORAGE_BUCKET in url:
                        parts = url.split(f"{self.STORAGE_BUCKET}/")
                        if len(parts) > 1:
                            file_path = parts[1].split("?")[0]
                            self.sb.storage.from_(self.STORAGE_BUCKET).remove([file_path])
                except Exception:
                    pass
            
            # 3. Lösche verknüpfte Daten
            self.sb.table("post_image").delete().eq("post_id", post_id).execute()
            self.sb.table("post_color").delete().eq("post_id", post_id).execute()
            
            # 4. Lösche den Post
            self.sb.table("post").delete().eq("id", post_id).execute()
            
            return True
        except Exception:
            return False
    
    def get_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        # Holt einen Post anhand seiner ID.
        try:
            res = self.sb.table("post").select("*, post_image(url)").eq("id", post_id).execute()
            return res.data[0] if res.data else None
        except Exception as ex:
            logger.error(f"Fehler beim Laden des Posts {post_id}: {ex}", exc_info=True)
            return None
    
    def get_all(self, limit: int = 200) -> List[Dict[str, Any]]:
        # Holt alle Posts mit Relationen.
        try:
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
    
    def add_color(self, post_id: str, color_id: int) -> None:
        # Fügt eine Farbe zu einem Post hinzu.
        try:
            self.sb.table("post_color").insert({
                "post_id": post_id,
                "color_id": color_id,
            }).execute()
        except Exception as ex:
            logger.error(f"Fehler beim Hinzufügen der Farbe {color_id} zu Post {post_id}: {ex}", exc_info=True)
    
    def update_colors(self, post_id: str, color_ids: List[int]) -> None:
        """Aktualisiert die Farben eines Posts (löscht alte, fügt neue hinzu)."""
        try:
            # Alte Farben löschen
            self.sb.table("post_color").delete().eq("post_id", post_id).execute()
            
            # Neue Farben hinzufügen
            for color_id in color_ids:
                self.sb.table("post_color").insert({
                    "post_id": post_id,
                    "color_id": color_id,
                }).execute()
        except Exception as ex:
            logger.error(f"Fehler beim Aktualisieren der Farben für Post {post_id}: {ex}", exc_info=True)
    
    def add_photo(self, post_id: str, photo_url: str) -> None:
        # Speichert eine Foto-URL für einen Post.
        try:
            self.sb.table("post_image").insert({
                "post_id": post_id,
                "url": photo_url,
            }).execute()
        except Exception as ex:
            logger.error(f"Fehler beim Speichern der Foto-URL für Post {post_id}: {ex}", exc_info=True)

