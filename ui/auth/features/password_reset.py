"""
Passwort-Reset-Feature: UI und Logik für Passwort zurücksetzen.
"""

from __future__ import annotations

from typing import Optional

import flet as ft

from utils.validators import validate_email
from utils.logging_config import get_logger
from services.account import AuthService
from ui.components import show_success_dialog, show_error_dialog
from ui.constants import MESSAGE_TYPE_ERROR, MESSAGE_COLOR_ERROR
from ..components import create_password_reset_dialog

logger = get_logger(__name__)


def show_password_reset_dialog_feature(
    page: ft.Page,
    auth_service: AuthService,
    initial_email: Optional[str] = None,
) -> None:
    """Zeigt den Dialog zum Zurücksetzen des Passworts.
    
    Args:
        page: Flet Page-Instanz
        auth_service: AuthService-Instanz
        initial_email: Optional E-Mail zum Vorausfüllen
    """
    email_field = ft.TextField(
        label="E-Mail-Adresse",
        prefix_icon=ft.Icons.EMAIL,
        keyboard_type=ft.KeyboardType.EMAIL,
        width=300,
        hint_text="Ihre registrierte E-Mail",
        value=initial_email or "",
    )

    error_text = ft.Text("", color=MESSAGE_COLOR_ERROR, size=12, visible=False)

    def on_send(e):
        email = (email_field.value or "").strip()

        try:
            # Validierung (UI-Ebene für besseres Feedback)
            is_valid, error_msg = validate_email(email)
            if not is_valid:
                error_text.value = error_msg or "Bitte gültige E-Mail eingeben."
                error_text.visible = True
                page.update()
                return

            # Service-Aufruf
            result = auth_service.reset_password(email)
            if result.success:
                page.close(dialog)
                show_success_dialog(
                    page,
                    "E-Mail gesendet",
                    result.message or "Eine E-Mail zum Zurücksetzen wurde gesendet.",
                )
            else:
                error_text.value = result.message or "Fehler beim Senden der E-Mail."
                error_text.visible = True
                page.update()
        except Exception as e:
            logger.error(f"Fehler bei Password Reset: {e}", exc_info=True)
            error_text.value = "Ein unerwarteter Fehler ist aufgetreten."
            error_text.visible = True
            page.update()

    def on_cancel(e):
        page.close(dialog)

    dialog = create_password_reset_dialog(
        email_field=email_field,
        error_text=error_text,
        on_send=on_send,
        on_cancel=on_cancel,
    )
    page.open(dialog)
