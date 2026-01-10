"""
Edit Profile Handler: Logik für Profil-Bearbeitung (Profilbild, Display Name, Passwort, Konto löschen).
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Optional

import flet as ft

from utils.logging_config import get_logger
from ui.shared_components import show_success_dialog, show_error_dialog
from services.account import ProfileImageService, AccountDeletionService, AuthService
from ..components.edit_profile_components import (
    create_change_password_dialog,
    create_delete_account_dialog,
    create_delete_profile_image_dialog,
)

logger = get_logger(__name__)


def handle_change_password(view: Any) -> None:
    """Zeigt einen Dialog zum Ändern des Passworts (Handler mit Logik).
    
    Args:
        view: ProfileView-Instanz
    """
    from utils.validators import validate_password
    
    current_password_field = ft.TextField(
        label="Aktuelles Passwort",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        width=300,
    )

    new_password_field = ft.TextField(
        label="Neues Passwort",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK,
        hint_text="Min. 8 Zeichen, Groß/Klein, Zahl, Sonderzeichen",
        width=300,
    )

    confirm_password_field = ft.TextField(
        label="Neues Passwort bestätigen",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK,
        width=300,
    )

    error_text = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

    def on_save(e: ft.ControlEvent) -> None:
        current_pw = current_password_field.value
        new_pw = new_password_field.value
        confirm_pw = confirm_password_field.value

        # Validierung
        if not current_pw:
            error_text.value = "Bitte aktuelles Passwort eingeben."
            error_text.visible = True
            view.page.update()
            return

        # Passwort-Anforderungen prüfen
        is_valid, pw_error = validate_password(new_pw)
        if not is_valid:
            error_text.value = pw_error or "Passwort ungültig."
            error_text.visible = True
            view.page.update()
            return

        if new_pw != confirm_pw:
            error_text.value = "Passwörter stimmen nicht überein."
            error_text.visible = True
            view.page.update()
            return

        # Business-Logik: Erst mit aktuellem Passwort authentifizieren
        try:
            email = view.profile_service.get_email()
            if not email:
                error_text.value = "E-Mail nicht gefunden."
                error_text.visible = True
                view.page.update()
                return

            # Re-Authentifizierung mit aktuellem Passwort
            auth_result = view.sb.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": current_pw,
                }
            )

            if not auth_result or not auth_result.user:
                error_text.value = "Aktuelles Passwort ist falsch."
                error_text.visible = True
                view.page.update()
                return

            # Neues Passwort setzen
            auth_service = AuthService(view.sb)
            result = auth_service.change_password(new_pw)

            if result.success:
                view.page.close(password_dialog)
                show_success_dialog(view.page, "Erfolg", "Passwort wurde geändert!")
            else:
                error_text.value = result.message or "Fehler beim Ändern."
                error_text.visible = True
                view.page.update()

        except Exception as ex:
            logger.error(f"Fehler beim Passwort ändern: {ex}", exc_info=True)
            error_text.value = "Aktuelles Passwort ist falsch."
            error_text.visible = True
            view.page.update()

    def on_cancel(e: ft.ControlEvent) -> None:
        view.page.close(password_dialog)

    password_dialog = create_change_password_dialog(
        page=view.page,
        on_save=on_save,
        on_cancel=on_cancel,
    )
    
    # Fields zum Dialog hinzufügen (für Validierung)
    password_dialog.content.content.controls = [
        current_password_field,
        ft.Divider(height=16),
        new_password_field,
        confirm_password_field,
        error_text,
    ]
    
    view.page.open(password_dialog)


def handle_delete_account_confirmation(view: Any) -> None:
    """Zeigt Bestätigungsdialog zum Löschen des Kontos (Handler mit Logik).
    
    Args:
        view: ProfileView-Instanz
    """
    def on_confirm(confirmation_text: str) -> None:
        """Business-Logik für Konto-Löschung."""
        deletion_service = AccountDeletionService(view.sb)
        success, error_msg = deletion_service.delete_account()

        if success:
            show_success_dialog(
                view.page,
                "Konto gelöscht",
                "Ihr Konto wurde erfolgreich gelöscht.",
                on_close=lambda: view.page.go("/login") if view.on_logout else None,
            )
            if view.on_logout:
                view.on_logout()
        else:
            show_error_dialog(
                view.page,
                "Fehler",
                error_msg or "Konto konnte nicht gelöscht werden.",
            )

    delete_dialog = create_delete_account_dialog(
        page=view.page,
        on_confirm=on_confirm,
    )
    view.page.open(delete_dialog)


async def handle_profile_image_upload(view: Any, e: ft.FilePickerResultEvent) -> None:
    """Behandelt den Upload eines Profilbilds (Desktop & Web).
    
    Args:
        view: ProfileView-Instanz
        e: FilePickerResultEvent
    """
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
    """Verarbeitet und lädt ein Profilbild hoch.
    
    Args:
        view: ProfileView-Instanz
        file_path: Pfad zur hochzuladenden Datei
    """
    image_service = ProfileImageService(view.sb)
    success, image_url, error_msg = image_service.upload_profile_image(file_path)

    if success and image_url:
        update_avatar_image(view, image_url)
        await view._load_user_data()
        show_success_dialog(view.page, "Erfolg", "Profilbild aktualisiert.")
    else:
        show_error_dialog(view.page, "Fehler", error_msg or "Upload fehlgeschlagen.")


def update_avatar_image(view: Any, image_url: Optional[str]) -> None:
    """Aktualisiert den Avatar des Views.
    
    Args:
        view: ProfileView-Instanz
        image_url: Optional URL des Profilbilds
    """
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


def handle_delete_profile_image_confirmation(view: Any) -> None:
    """Zeigt Bestätigungsdialog zum Löschen des Profilbilds (Handler mit Logik).
    
    Args:
        view: ProfileView-Instanz
    """
    def on_confirm() -> None:
        """Business-Logik für Profilbild-Löschung."""
        view.page.run_task(view._delete_profile_image)

    delete_dialog = create_delete_profile_image_dialog(
        page=view.page,
        on_confirm=on_confirm,
    )
    view.page.open(delete_dialog)


async def handle_delete_profile_image(view: Any) -> None:
    """Löscht das Profilbild des Benutzers.
    
    Args:
        view: ProfileView-Instanz
    """
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


async def handle_save_display_name(
    view: Any,
    name_field: ft.TextField,
) -> None:
    """Speichert den neuen Anzeigenamen.
    
    Args:
        view: ProfileView-Instanz
        name_field: TextField mit dem neuen Anzeigenamen
    """
    new_name = name_field.value
    if not new_name or not new_name.strip():
        show_error_dialog(view.page, "Fehler", "Der Anzeigename darf nicht leer sein.")
        return

    success, error_msg = view.profile_service.update_display_name(new_name)

    if success:
        view.display_name.value = new_name.strip()
        view.page.update()
        show_success_dialog(view.page, "Erfolg", "Der Anzeigename wurde aktualisiert.")
    else:
        show_error_dialog(view.page, "Fehler", error_msg or "Unbekannter Fehler.")
