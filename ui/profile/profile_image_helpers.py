from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Optional

import flet as ft

from utils.logging_config import get_logger
from ui.components import show_success_dialog, show_error_dialog
from services.account import ProfileImageService

logger = get_logger(__name__)


async def handle_profile_image_upload(view: Any, e: ft.FilePickerResultEvent) -> None:
    """Behandelt den Upload eines Profilbilds (Desktop & Web)."""
    logger.info(f"_handle_profile_image_upload aufgerufen, files: {e.files}")

    if not e.files:
        logger.info("Keine Dateien ausgewählt")
        return

    try:
        selected_file = e.files[0]
        logger.info(
            f"Datei: name={selected_file.name}, path={selected_file.path}, size={selected_file.size}"
        )

        if selected_file.path:
            # Desktop-Modus
            await process_profile_image(view, selected_file.path)
        else:
            # Web-Modus
            if selected_file.size and selected_file.size > 5 * 1024 * 1024:
                show_error_dialog(view.page, "Fehler", "Die Datei ist zu groß. Max. 5 MB.")
                return

            upload_name = f"profile_{uuid.uuid4().hex}_{selected_file.name}"
            view.profile_image_picker.upload(
                [
                    ft.FilePickerUploadFile(
                        selected_file.name,
                        upload_url=view.page.get_upload_url(upload_name, 600),
                    )
                ]
            )

            await asyncio.sleep(1)
            upload_dir = os.path.join(os.getcwd(), "image_uploads")
            file_path = os.path.join(upload_dir, upload_name)

            for _ in range(20):
                if os.path.exists(file_path):
                    break
                await asyncio.sleep(0.5)

            if os.path.exists(file_path):
                await process_profile_image(view, file_path)
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            else:
                show_error_dialog(
                    view.page,
                    "Fehler",
                    "Upload fehlgeschlagen. Bitte erneut versuchen.",
                )

    except Exception as ex:
        logger.error(f"Fehler beim Upload: {ex}", exc_info=True)
        show_error_dialog(view.page, "Fehler", f"Fehler: {str(ex)}")


async def process_profile_image(view: Any, file_path: str) -> None:
    """Verarbeitet und lädt ein Profilbild hoch."""
    image_service = ProfileImageService(view.sb)
    success, image_url, error_msg = image_service.upload_profile_image(file_path)

    if success and image_url:
        update_avatar_image(view, image_url)
        await view._load_user_data()
        show_success_dialog(view.page, "Erfolg", "Profilbild aktualisiert.")
    else:
        show_error_dialog(view.page, "Fehler", error_msg or "Upload fehlgeschlagen.")


def update_avatar_image(view: Any, image_url: Optional[str]) -> None:
    """Aktualisiert den Avatar des Views."""
    if image_url:
        # Cache-Busting: Timestamp anhängen um Browser-Caching zu vermeiden
        from time import time as _time

        cache_buster = f"?t={int(_time() * 1000)}"
        view.avatar.foreground_image_src = image_url + cache_buster
        view.avatar.content = None
    else:
        view.avatar.foreground_image_src = None
        view.avatar.content = ft.Icon(ft.Icons.PERSON, size=50, color=ft.Colors.WHITE)
    view.page.update()


def confirm_delete_profile_image(view: Any) -> None:
    """Zeigt Bestätigungsdialog zum Löschen des Profilbilds."""

    def on_confirm(e: ft.ControlEvent) -> None:
        view.page.close(dialog)
        view.page.run_task(view._delete_profile_image)

    def on_cancel(e: ft.ControlEvent) -> None:
        view.page.close(dialog)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Profilbild löschen?"),
        content=ft.Text("Möchten Sie Ihr Profilbild wirklich löschen?"),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton(
                "Löschen",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=on_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    view.page.open(dialog)


async def delete_profile_image(view: Any) -> None:
    """Löscht das Profilbild des Benutzers."""
    try:
        image_service = ProfileImageService(view.sb)
        success, error_msg = image_service.delete_profile_image()
        
        if success:
            # Avatar zurücksetzen
            update_avatar_image(view, None)

            # View neu laden um Button zu aktualisieren
            view._rebuild()

            show_success_dialog(view.page, "Erfolg", "Profilbild wurde gelöscht.")
        else:
            show_error_dialog(
                view.page, "Fehler", error_msg or "Profilbild konnte nicht gelöscht werden."
            )
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Profilbilds: {e}", exc_info=True)
        show_error_dialog(view.page, "Fehler", f"Fehler: {str(e)}")


