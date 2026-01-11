"""
Login-Handler: UI-Handler für Benutzer-Anmeldung.
"""

from __future__ import annotations

from typing import Callable, Optional

from utils.logging_config import get_logger
from utils.validators import validate_email
from services.account import AuthService, AuthResult
from ui.constants import MESSAGE_TYPE_INFO, MESSAGE_TYPE_SUCCESS, MESSAGE_TYPE_ERROR
from .error_handler import handle_auth_error

logger = get_logger(__name__)


def handle_login(
    auth_service: AuthService,
    email: str,
    password: str,
    show_message_callback: Callable[[str, str], None],
    on_success_callback: Optional[Callable[[], None]] = None,
) -> None:
    """Führt Login durch (Service-Aufruf + UI-Feedback)."""
    try:
        # E-Mail-Format clientseitig validieren
        if email and email.strip():
            is_valid_email, email_error = validate_email(email)
            if not is_valid_email:
                show_message_callback(
                    email_error or "Ungültige E-Mail-Adresse.",
                    MESSAGE_TYPE_ERROR
                )
                return
        
        result: AuthResult = auth_service.login(email, password)
        
        if result.success:
            show_message_callback("Erfolgreich!", MESSAGE_TYPE_SUCCESS)
            if on_success_callback:
                on_success_callback()
        else:
            show_message_callback(
                result.message or "Anmeldung fehlgeschlagen.",
                MESSAGE_TYPE_ERROR
            )
    except Exception as e:
        handle_auth_error(e, "Login", show_message_callback)


def handle_logout(
    auth_service: AuthService,
    show_message_callback: Callable[[str, str], None],
) -> None:
    """Führt Logout durch (Service-Aufruf + UI-Feedback)."""
    try:
        result = auth_service.logout()
        if result.success:
            show_message_callback(result.message or "Abgemeldet.", MESSAGE_TYPE_SUCCESS)
        else:
            show_message_callback(
                result.message or "Abmeldung fehlgeschlagen.",
                MESSAGE_TYPE_ERROR
            )
    except Exception as e:
        handle_auth_error(e, "Logout", show_message_callback)
