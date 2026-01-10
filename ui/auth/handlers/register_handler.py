"""
Registrierungs-Handler: UI-Handler für neue Benutzer-Registrierung.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from utils.logging_config import get_logger
from services.account import AuthService, AuthResult
from ui.shared_components import show_success_dialog
from ui.constants import MESSAGE_TYPE_INFO, MESSAGE_TYPE_SUCCESS, MESSAGE_TYPE_ERROR
from .error_handler import handle_auth_error

logger = get_logger(__name__)


def handle_register(
    auth_service: AuthService,
    email: str,
    password: str,
    password_confirm: str,
    username: str,
    page: ft.Page,
    show_message_callback: Callable[[str, str], None],
    on_success_callback: Optional[Callable[[], None]] = None,
    on_close_modal_callback: Optional[Callable[[], None]] = None,
) -> None:
    """Führt Registrierung durch (Service-Aufruf + UI-Feedback)."""
    try:
        if password != password_confirm:
            show_message_callback(
                "Passwörter stimmen nicht überein.",
                MESSAGE_TYPE_ERROR
            )
            return
        
        show_message_callback("Registrierung läuft...", MESSAGE_TYPE_INFO)
        
        result = auth_service.register(
            email=email,
            password=password,
            username=username,
        )
        
        if result.success:
            if result.code == "confirm_email":
                show_success_dialog(
                    page,
                    "Erfolg",
                    result.message or "Bestätigungs-E-Mail gesendet! Bitte prüfen Sie Ihr Postfach.",
                    on_close=on_close_modal_callback,
                )
            else:
                show_success_dialog(
                    page,
                    "Erfolg",
                    "Registrierung erfolgreich.",
                    on_close=on_close_modal_callback,
                )
            if on_success_callback:
                on_success_callback()
        else:
            show_message_callback(
                result.message or "Fehler bei der Registrierung.",
                MESSAGE_TYPE_ERROR
            )
    except Exception as e:
        handle_auth_error(e, "Registrierung", show_message_callback)
