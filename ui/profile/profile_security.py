from __future__ import annotations

from typing import Any

import flet as ft

from utils.logging_config import get_logger
from utils.validators import validate_password
from ui.components import show_success_dialog, show_error_dialog

logger = get_logger(__name__)


def show_change_password_dialog(view: Any) -> None:
    """Zeigt einen Dialog zum Ändern des Passworts."""
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

        # Erst mit aktuellem Passwort authentifizieren
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
            from services.account import AuthService
            auth_service = AuthService(view.sb)
            result = auth_service.change_password(new_pw)

            if result.success:
                view.page.close(dialog)
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
        view.page.close(dialog)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Passwort ändern", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(
                [
                    current_password_field,
                    ft.Divider(height=16),
                    new_password_field,
                    confirm_password_field,
                    error_text,
                ],
                spacing=8,
                tight=True,
            ),
            width=320,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton("Speichern", icon=ft.Icons.SAVE, on_click=on_save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    view.page.open(dialog)


def confirm_delete_account(view: Any) -> None:
    """Zeigt Bestätigungsdialog zum Löschen des Kontos."""
    confirm_field = ft.TextField(
        label="Zur Bestätigung 'LÖSCHEN' eingeben",
        width=300,
    )
    error_text = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

    def on_confirm(e: ft.ControlEvent) -> None:
        if confirm_field.value != "LÖSCHEN":
            error_text.value = "Bitte geben Sie 'LÖSCHEN' ein, um fortzufahren."
            error_text.visible = True
            view.page.update()
            return

        view.page.close(dialog)
        delete_account(view)

    def on_cancel(e: ft.ControlEvent) -> None:
        view.page.close(dialog)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=28),
                ft.Text("Konto wirklich löschen?", weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Diese Aktion kann nicht rückgängig gemacht werden!\n\n"
                        "Folgende Daten werden gelöscht:\n"
                        "• Ihr Profilbild\n"
                        "• Ihre Favoriten\n"
                        "• Ihre Meldungen",
                        size=14,
                    ),
                    ft.Container(height=16),
                    confirm_field,
                    error_text,
                ],
                spacing=8,
                tight=True,
            ),
            width=350,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton(
                "Endgültig löschen",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=on_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    view.page.open(dialog)


def delete_account(view: Any) -> None:
    """Löscht das Benutzerkonto."""
    from services.account import AccountDeletionService
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


