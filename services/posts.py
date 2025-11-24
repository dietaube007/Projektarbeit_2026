"""Post/Meldungs-Verwaltung.

Dieses Modul verwaltet alle Datenbankoperationen für Posts/Tier-Meldungen:
- Erstellen neuer Posts
- Aktualisieren bestehender Posts
- Verknüpfung von Posts mit Farben
- Foto-Upload zum Storage

"""

import os
from supabase import Client
from typing import Dict, Any, List
from pathlib import Path


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


def upload_photo(sb: Client, post_id: str, photo_path: str) -> str:
    """
    Lädt ein Foto zu Supabase Storage hoch.
    
    Args:
        sb: Supabase Client
        post_id: ID der Meldung (für Dateiorganisation)
        photo_path: Lokaler Pfad zum Foto
    
    Returns:
        URL des hochgeladenen Fotos in Supabase Storage
    
    Raises:
        RuntimeError: Bei Fehler beim Upload
    """
    try:
        # Validiere dass Datei existiert
        if not os.path.exists(photo_path):
            raise RuntimeError(f"Foto nicht gefunden: {photo_path}")
        
        # Erstelle eindeutigen Dateinamen: post_id/filename
        file_name = Path(photo_path).name
        file_path = f"{post_id}/{file_name}"
        
        # Lese Datei
        with open(photo_path, "rb") as f:
            file_data = f.read()
        
        # Lade zu Storage hoch
        res = sb.storage.from_(STORAGE_BUCKET).upload(
            file=file_data,
            path=file_path,
            file_options={"cacheControl": "3600", "upsert": "false"},
        )
        
        # Konstruiere Public URL
        public_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(file_path)
        
        return public_url
        
    except Exception as ex:
        raise RuntimeError(f"Fehler beim Hochladen des Fotos: {str(ex)}")


def add_photo_to_post(sb: Client, post_id: str, photo_url: str) -> None:
    """Speichert die Foto-URL in der post_image Tabelle."""
    try:
        print(f"DEBUG - Speichere Bild: post_id={post_id}, url={photo_url}")
        result = sb.table("post_image").insert({
            "post_id": post_id,
            "url": photo_url,
        }).execute()
        print(f"DEBUG - Result: {result}")
    except Exception as ex:
        print(f"Fehler beim Speichern der Foto-URL: {ex}")