"""
Zentrale Validierungsfunktionen für User-Input.

Dieses Modul stellt wiederverwendbare Validierungsfunktionen bereit,
um konsistente Input-Validierung im gesamten Projekt zu gewährleisten.
"""

from typing import Optional, List
import re
from utils.logging_config import get_logger

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════════
# STRING-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_not_empty(value: Optional[str], field_name: str = "Feld") -> tuple[bool, Optional[str]]:
    """Validiert, dass ein String-Wert nicht leer ist.
    
    Args:
        value: Zu validierender Wert
        field_name: Name des Feldes für Fehlermeldungen
    
    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True wenn gültig, False wenn ungültig
        - error_message: Fehlermeldung oder None wenn gültig
    """
    if value is None:
        return False, f"{field_name} darf nicht leer sein"
    
    if not isinstance(value, str):
        return False, f"{field_name} muss ein Text sein"
    
    stripped = value.strip()
    if not stripped:
        return False, f"{field_name} darf nicht leer sein"
    
    return True, None


def validate_length(
    value: Optional[str],
    min_length: int = 0,
    max_length: Optional[int] = None,
    field_name: str = "Feld"
) -> tuple[bool, Optional[str]]:
    """Validiert die Länge eines Strings.
    
    Args:
        value: Zu validierender Wert
        min_length: Minimale Länge (Standard: 0)
        max_length: Maximale Länge (None = unbegrenzt)
        field_name: Name des Feldes für Fehlermeldungen
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if value is None:
        value = ""
    
    if not isinstance(value, str):
        return False, f"{field_name} muss ein Text sein"
    
    length = len(value.strip())
    
    if length < min_length:
        return False, f"{field_name} muss mindestens {min_length} Zeichen lang sein"
    
    if max_length is not None and length > max_length:
        return False, f"{field_name} darf maximal {max_length} Zeichen lang sein"
    
    return True, None


def sanitize_string(value: Optional[str], max_length: Optional[int] = None) -> str:
    """Bereinigt und normalisiert einen String.
    
    Args:
        value: Zu bereinigender Wert
        max_length: Maximale Länge (wird abgeschnitten wenn überschritten)
    
    Returns:
        Bereinigter String (leer wenn None)
    """
    if value is None:
        return ""
    
    if not isinstance(value, str):
        return str(value).strip()
    
    # Whitespace normalisieren
    sanitized = " ".join(value.split())
    
    # Länge begrenzen
    if max_length is not None and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


# ════════════════════════════════════════════════════════════════════
# E-MAIL-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

from utils.constants import EMAIL_REGEX


def validate_email(email: Optional[str]) -> tuple[bool, Optional[str]]:
    """Validiert eine E-Mail-Adresse.
    
    Args:
        email: Zu validierende E-Mail-Adresse
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not email:
        return False, "E-Mail-Adresse ist erforderlich"
    
    if not isinstance(email, str):
        return False, "E-Mail-Adresse muss ein Text sein"
    
    email = email.strip().lower()
    
    if not email:
        return False, "E-Mail-Adresse ist erforderlich"
    
    if not EMAIL_REGEX.match(email):
        return False, "Ungültige E-Mail-Adresse"
    
    # Zusätzliche Längenprüfung
    if len(email) > 254:  # RFC 5321 Limit
        return False, "E-Mail-Adresse ist zu lang"
    
    return True, None


# ════════════════════════════════════════════════════════════════════
# DATUMS-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_date_format(date_str: Optional[str], format_str: str = "%d.%m.%Y") -> tuple[bool, Optional[str]]:
    """Validiert ein Datum im angegebenen Format.
    
    Args:
        date_str: Zu validierender Datumsstring
        format_str: Erwartetes Format (Standard: TT.MM.YYYY)
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not date_str:
        return False, "Datum ist erforderlich"
    
    if not isinstance(date_str, str):
        return False, "Datum muss ein Text sein"
    
    date_str = date_str.strip()
    
    if not date_str:
        return False, "Datum ist erforderlich"
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, format_str)
        return True, None
    except ValueError:
        return False, f"Datum muss im Format {format_str} sein (z.B. 01.01.2025)"


# ════════════════════════════════════════════════════════════════════
# LISTEN-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_list_not_empty(
    value: Optional[List],
    field_name: str = "Liste",
    min_items: int = 1
) -> tuple[bool, Optional[str]]:
    """Validiert, dass eine Liste nicht leer ist.
    
    Args:
        value: Zu validierende Liste
        field_name: Name des Feldes für Fehlermeldungen
        min_items: Minimale Anzahl von Elementen
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} darf nicht leer sein"
    
    if not isinstance(value, list):
        return False, f"{field_name} muss eine Liste sein"
    
    if len(value) < min_items:
        return False, f"{field_name} muss mindestens {min_items} Element(e) enthalten"
    
    return True, None


# ════════════════════════════════════════════════════════════════════
# ID-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_id(value: Optional[str], field_name: str = "ID") -> tuple[bool, Optional[str]]:
    """Validiert eine ID (nicht leer, nicht None).
    
    Args:
        value: Zu validierende ID
        field_name: Name des Feldes für Fehlermeldungen
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} ist erforderlich"
    
    if isinstance(value, str):
        if not value.strip():
            return False, f"{field_name} ist erforderlich"
        return True, None
    
    # Für numerische IDs
    if value == 0 or value == "":
        return False, f"{field_name} ist erforderlich"
    
    return True, None


# ════════════════════════════════════════════════════════════════════
# PASSWORT-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """Validiert ein Passwort nach den Sicherheitsanforderungen.
    
    Args:
        password: Zu validierendes Passwort
    
    Returns:
        Tuple (is_valid, error_message)
    """
    from utils.constants import MIN_PASSWORD_LENGTH, SPECIAL_CHARS
    
    if not password:
        return False, "Passwort darf nicht leer sein."
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen haben."
    
    if not re.search(r"[A-Z]", password):
        return False, "Passwort muss mindestens einen Großbuchstaben enthalten."
    
    if not re.search(r"[a-z]", password):
        return False, "Passwort muss mindestens einen Kleinbuchstaben enthalten."
    
    if not re.search(r"[0-9]", password):
        return False, "Passwort muss mindestens eine Zahl enthalten."
    
    if not re.search(f"[{re.escape(SPECIAL_CHARS)}]", password):
        return False, "Passwort muss mindestens ein Sonderzeichen enthalten."
    
    return True, None


# ════════════════════════════════════════════════════════════════════
# ANZEIGENAME-VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_display_name(name: str) -> tuple[bool, Optional[str]]:
    """Validiert den Anzeigenamen.
    
    Args:
        name: Zu validierender Anzeigename
    
    Returns:
        Tuple (is_valid, error_message)
    """
    from utils.constants import MAX_DISPLAY_NAME_LENGTH
    
    if not name or not name.strip():
        return False, "Bitte Anzeigename eingeben."
    
    if len(name) > MAX_DISPLAY_NAME_LENGTH:
        return False, f"Anzeigename max. {MAX_DISPLAY_NAME_LENGTH} Zeichen."
    
    return True, None


# ════════════════════════════════════════════════════════════════════
# KOMBINIERTE VALIDIERUNG
# ════════════════════════════════════════════════════════════════════

def validate_multiple(
    validations: List[tuple[bool, Optional[str]]],
    field_name: str = "Feld"
) -> tuple[bool, Optional[str]]:
    """Validiert mehrere Bedingungen und gibt die erste Fehlermeldung zurück.
    
    Args:
        validations: Liste von (is_valid, error_message) Tuples
        field_name: Name des Feldes für Fehlermeldungen
    
    Returns:
        Tuple (is_valid, error_message)
    """
    for is_valid, error_message in validations:
        if not is_valid:
            return False, error_message or f"{field_name} ist ungültig"
    
    return True, None

