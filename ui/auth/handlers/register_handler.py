"""
Registrierungs-Handler: UI-Handler für neue Benutzer-Registrierung.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from utils.validators import validate_email, validate_password
from services.account import AuthService
from ui.shared_components import show_success_dialog
from ui.constants import MESSAGE_TYPE_INFO, MESSAGE_TYPE_ERROR
from .error_handler import handle_auth_error


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
        if not email or not email.strip():
            show_message_callback(
                "Bitte E-Mail-Adresse eingeben.",
                MESSAGE_TYPE_ERROR
            )
            return
        
        # E-Mail-Format validieren
        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            show_message_callback(
                email_error or "Ungültige E-Mail-Adresse.",
                MESSAGE_TYPE_ERROR
            )
            return
        
        if not password:
            show_message_callback(
                "Bitte Passwort eingeben.",
                MESSAGE_TYPE_ERROR
            )
            return
        
        # Passwort-Validierung:
        is_valid_password, password_error = validate_password(password)
        if not is_valid_password:
            show_message_callback(
                "Das Passwort muss mindestens 8 Zeichen haben, einen Groß- und Kleinbuchstaben, eine Zahl und ein Sonderzeichen enthalten.",
                MESSAGE_TYPE_ERROR
            )
            return
        
        if not password_confirm:
            show_message_callback(
                "Bitte Passwort bestätigen.",
                MESSAGE_TYPE_ERROR
            )
            return
        
        if password != password_confirm:
            show_message_callback(
                "Passwörter stimmen nicht überein.",
                MESSAGE_TYPE_ERROR
            )
            return

        if not username or not username.strip():
            show_message_callback(
                "Bitte Anzeigename eingeben.",
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