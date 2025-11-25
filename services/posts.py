"""Post/Meldungs-Verwaltung.

Dieses Modul verwaltet alle Datenbankoperationen für Posts/Tier-Meldungen:
- Erstellen neuer Posts
- Aktualisieren bestehender Posts
- Verknüpfung von Posts mit Farben
- Foto-Upload zum Storage

"""

from supabase import Client
from typing import Dict, Any


STORAGE_BUCKET = "pet-images"  # Name des Storage Buckets in Supabase

def create_post(sb: Client, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Insert ohne select
        sb.table("post").insert(payload).execute()
        
        # Dann separat den erstellten Post holen
        res = sb.table("post").select("*").eq("user_id", payload["user_id"]).order("created_at", desc=True).limit(1).execute()
        
        if not res.data:
            raise RuntimeError("Keine Daten in der Response")
        return res.data[0]
    except Exception as ex:
        raise RuntimeError(f"Fehler beim Erstellen der Meldung: {str(ex)}")


def update_post(sb: Client, post_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:

    # Aktualisiert eine existierende Post-Meldung.
    
    try:
        res = sb.table("post").update(payload).eq("id", post_id).select("*").execute()
        if not res.data:
            raise RuntimeError("Keine Daten in der Response")
        return res.data[0]
    except Exception as ex:
        raise RuntimeError(f"Fehler beim Aktualisieren der Meldung: {str(ex)}")


def add_color_to_post(sb: Client, post_id: str, color_id: int) -> None:
    
    # Fügt eine Farbe zu einer Post-Meldung hinzu.
    
    try:
        sb.table("post_color").insert({
            "post_id": post_id,
            "color_id": color_id,
        }).execute()
    except Exception as ex:
        # Fehler werden nur geloggt, nicht geworfen
        print(f"Fehler beim Hinzufügen der Farbe {color_id} zu Post {post_id}: {ex}")


def add_photo_to_post(sb: Client, post_id: str, photo_url: str) -> None:
    """Speichert die Foto-URL in der post_image Tabelle."""
    try:
        sb.table("post_image").insert({
            "post_id": post_id,
            "url": photo_url,
        }).execute()
    except Exception as ex:
        print(f"Fehler beim Speichern der Foto-URL: {ex}")


def delete_post(sb: Client, post_id: str) -> bool:
    # Löscht einen Post komplett aus der Datenbank UND das zugehörige Bild aus dem Storage.

    try:
        # 1. Hole die Bild-URLs aus post_image Tabelle
        images_res = sb.table("post_image").select("url").eq("post_id", post_id).execute()
        image_urls = [img["url"] for img in (images_res.data or [])]
        
        # 2. Lösche Bilder aus Supabase Storage
        for url in image_urls:
            try:
                if STORAGE_BUCKET in url:
                    parts = url.split(f"{STORAGE_BUCKET}/")
                    if len(parts) > 1:
                        file_path = parts[1].split("?")[0]
                        sb.storage.from_(STORAGE_BUCKET).remove([file_path])
            except Exception:
                pass  # Fehler beim Bild-Löschen ignorieren
        
        # 3. Lösche verknüpfte Daten
        sb.table("post_image").delete().eq("post_id", post_id).execute()
        sb.table("post_color").delete().eq("post_id", post_id).execute()
        
        # 4. Lösche den Post selbst
        sb.table("post").delete().eq("id", post_id).execute()
        
        return True
        
    except Exception:
        return False


def get_post_by_id(sb: Client, post_id: str) -> Dict[str, Any] | None:
    """Holt einen einzelnen Post anhand seiner ID."""
    try:
        res = sb.table("post").select("*, post_image(url)").eq("id", post_id).execute()
        return res.data[0] if res.data else None
    except Exception as ex:
        print(f"Fehler beim Laden des Posts: {ex}")
        return None