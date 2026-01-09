"""
ui/auth/validators.py
Validierungsfunktionen für E-Mail und Passwort.
"""

import re
from typing import Optional

from .constants import (
    EMAIL_REGEX,
    MIN_PASSWORD_LENGTH,
    SPECIAL_CHARS,
    MAX_DISPLAY_NAME_LENGTH,
)


def is_valid_email(email: str) -> bool:
    """Prüft ob die E-Mail-Adresse gültig ist."""
    return bool(re.match(EMAIL_REGEX, email))


def validate_password(password: str) -> Optional[str]:
    """Validiert das Passwort."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Passwort mind. {MIN_PASSWORD_LENGTH} Zeichen."
    if not any(c.isdigit() for c in password):
        return "Passwort muss mind. eine Ziffer enthalten."
    if not any(c in SPECIAL_CHARS for c in password):
        return "Passwort muss mind. ein Sonderzeichen enthalten."
    return None


def validate_display_name(name: str) -> Optional[str]:
    """Validiert den Anzeigenamen."""
    if not name or not name.strip():
        return "Bitte Anzeigename eingeben."
    if len(name) > MAX_DISPLAY_NAME_LENGTH:
        return f"Anzeigename max. {MAX_DISPLAY_NAME_LENGTH} Zeichen."
    return None


def validate_login_form(email: str, password: str) -> Optional[str]:
    """Validiert das Login-Formular."""
    if not email:
        return "Bitte E-Mail eingeben."
    if not is_valid_email(email):
        return "Bitte gültige E-Mail eingeben."
    if not password:
        return "Bitte Passwort eingeben."
    return None


def validate_register_form(email: str, password: str, username: str) -> Optional[str]:
    """Validiert das Registrierungs-Formular."""
    if not email:
        return "Bitte E-Mail eingeben."
    if not is_valid_email(email):
        return "Bitte gültige E-Mail eingeben."
    if not password:
        return "Bitte Passwort eingeben."
    
    password_error = validate_password(password)
    if password_error:
        return password_error
    
    name_error = validate_display_name(username)
    if name_error:
        return name_error
    
    return None
