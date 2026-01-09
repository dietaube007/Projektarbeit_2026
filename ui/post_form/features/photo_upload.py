"""
Photo Upload-Feature: UI und Logik für Foto-Upload und -Verwaltung.
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, Callable

import flet as ft

from utils.logging_config import get_logger
from services.posts import PostStorageService
from ui.constants import VALID_IMAGE_TYPES

logger = get_logger(__name__)


def cleanup_local_file(file_path: str) -> bool:
    """Löscht eine lokale temporäre Datei.
    
    Args:
        file_path: Pfad zur zu löschenden Datei
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as ex:
        logger.warning(f"Fehler beim Löschen der lokalen Datei {file_path}: {ex}", exc_info=True)
        return False


def get_upload_path(filename: str, session_id: Optional[str] = None) -> str:
    """Erstellt den lokalen Upload-Pfad für eine Datei.
    
    Args:
        filename: Dateiname
        session_id: Optional Session-ID für Unterordner
    
    Returns:
        Vollständiger Pfad zur Datei
    """
    upload_dir = os.getenv("UPLOAD_DIR", "image_uploads")
    if session_id:
        return f"{upload_dir}/{session_id}/{filename}"
    return f"{upload_dir}/{filename}"


async def handle_pick_photo(
    page: ft.Page,
    post_storage_service: PostStorageService,
    selected_photo: Dict[str, Any],
    photo_preview: ft.Image,
    show_status_callback: Callable[[str, bool, bool], None],
) -> None:
    """Öffnet Dateiauswahl und lädt Bild zu Supabase Storage hoch.
    
    Args:
        page: Flet Page-Instanz
        post_storage_service: PostStorageService-Instanz
        selected_photo: Dictionary mit Foto-Informationen (wird modifiziert)
        photo_preview: Image-Widget für Vorschau
        show_status_callback: Callback für Status-Nachrichten (message, is_error, is_loading)
    """
    def on_result(ev: ft.FilePickerResultEvent):
        if ev.files:
            f = ev.files[0]
            selected_photo["name"] = f.name
            
            fp.upload([ft.FilePickerUploadFile(
                f.name,
                upload_url=page.get_upload_url(f.name, 60)
            )])
    
    def on_upload(ev: ft.FilePickerUploadEvent):
        if ev.progress == 1.0:
            try:
                # Versuche beide mögliche Pfade (mit und ohne Session-ID)
                upload_path_with_session = get_upload_path(ev.file_name, page.session_id)
                upload_path_direct = get_upload_path(ev.file_name, None)
                
                # Wähle den Pfad der existiert
                if os.path.exists(upload_path_with_session):
                    upload_path = upload_path_with_session
                elif os.path.exists(upload_path_direct):
                    upload_path = upload_path_direct
                else:
                    show_status_callback(f"Datei nicht gefunden: {ev.file_name}", is_error=True, is_loading=False)
                    return
                
                # Bild hochladen und komprimieren über Service
                result = post_storage_service.upload_post_image(upload_path, ev.file_name)
                
                if result["url"]:
                    selected_photo["path"] = result["path"]
                    selected_photo["base64"] = result["base64"]
                    selected_photo["url"] = result["url"]
                    
                    photo_preview.src_base64 = result["base64"]
                    photo_preview.visible = True
                    show_status_callback(f"Bild hochgeladen: {ev.file_name}", is_error=False, is_loading=False)
                else:
                    show_status_callback("Fehler beim Hochladen", is_error=True, is_loading=False)
                
                # Lokale Datei aufräumen
                cleanup_local_file(upload_path)
                
            except Exception as ex:
                show_status_callback(f"Fehler: {ex}", is_error=True, is_loading=False)
    
    fp = ft.FilePicker(on_result=on_result, on_upload=on_upload)
    page.overlay.append(fp)
    page.update()
    fp.pick_files(allow_multiple=False, allowed_extensions=VALID_IMAGE_TYPES)


def handle_remove_photo(
    post_storage_service: PostStorageService,
    selected_photo: Dict[str, Any],
    photo_preview: ft.Image,
    status_text: ft.Text,
    page: ft.Page,
) -> None:
    """Entfernt das Foto aus der Vorschau und aus Supabase Storage.
    
    Args:
        post_storage_service: PostStorageService-Instanz
        selected_photo: Dictionary mit Foto-Informationen (wird zurückgesetzt)
        photo_preview: Image-Widget für Vorschau
        status_text: Text-Widget für Status-Nachrichten
        page: Flet Page-Instanz
    """
    post_storage_service.remove_post_image(selected_photo.get("path"))
    
    selected_photo.update({"path": None, "name": None, "url": None, "base64": None})
    photo_preview.visible = False
    status_text.value = ""
    page.update()
