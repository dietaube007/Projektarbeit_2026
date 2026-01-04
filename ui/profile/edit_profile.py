"""
ui/profile/edit_profile.py
Profil-Bearbeiten-Ansicht und Logik.
"""

from __future__ import annotations

import flet as ft
from typing import Tuple, Optional, Callable

from ui.theme import soft_card
from .components import build_section_title, SECTION_PADDING, CARD_ELEVATION
from ui.constants import MAX_DISPLAY_NAME_LENGTH
from utils.logging_config import get_logger
from utils.validators import validate_not_empty, validate_length, sanitize_string, validate_email

logger = get_logger(__name__)


def build_change_image_section(
    avatar: ft.CircleAvatar,
    on_change_image=None,
) -> ft.Container:
    """Erstellt den Profilbild-Abschnitt."""
    return soft_card(
        ft.Column(
            [
                build_section_title("Profilbild"),
                ft.Container(height=8),
                ft.Row(
                    [
                        avatar,
                        ft.FilledButton(
                            "Bild ändern",
                            icon=ft.Icons.CAMERA_ALT,
                            on_click=on_change_image or (lambda _: print("Bild ändern")),
                        ),
                    ],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.START,
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


def build_change_name_section(
    current_name: str,
    on_save: Optional[Callable[[ft.TextField], None]] = None,
) -> Tuple[ft.Container, ft.TextField]:
    """Erstellt den Anzeigenamen-Abschnitt.
    
    Args:
        current_name: Aktueller Anzeigename
        on_save: Callback-Funktion die mit (name_field) aufgerufen wird
    
    Returns:
        Tuple mit (Container, TextField) - TextField für Zugriff auf den Wert
    """
    name_field = ft.TextField(
        value=current_name,
        width=300,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        label="Anzeigename",
        hint_text=f"Max. {MAX_DISPLAY_NAME_LENGTH} Zeichen",
        max_length=MAX_DISPLAY_NAME_LENGTH,
    )
    
    def handle_save(_):
        if on_save:
            on_save(name_field)
    
    container = soft_card(
        ft.Column(
            [
                build_section_title("Anzeigename"),
                ft.Container(height=8),
                name_field,
                ft.Container(height=8),
                ft.FilledButton(
                    "Speichern",
                    icon=ft.Icons.SAVE,
                    on_click=handle_save,
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )
    
    return container, name_field


def build_password_section(on_reset=None) -> ft.Container:
    """Erstellt den Passwort-Abschnitt."""
    return soft_card(
        ft.Column(
            [
                build_section_title("Passwort"),
                ft.Container(height=8),
                ft.Text(
                    "Setze dein Passwort zurück",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=8),
                ft.OutlinedButton(
                    "Passwort zurücksetzen",
                    icon=ft.Icons.LOCK_RESET,
                    on_click=on_reset or (lambda _: print("Passwort zurücksetzen")),
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


async def update_display_name(sb, user_id: str, new_name: str) -> bool:
    """Aktualisiert den Anzeigenamen in beiden Tabellen (auth.users und user).
    
    Aktualisiert:
    - auth.users.user_metadata.display_name (über Supabase Auth)
    - user.display_name (in der eigenen user Tabelle)
    
    Args:
        sb: Supabase Client-Instanz
        user_id: ID des Benutzers
        new_name: Neuer Anzeigename
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    # Validierung
    name_valid, name_error = validate_not_empty(new_name, "Anzeigename")
    if not name_valid:
        logger.warning(f"Ungültiger Anzeigename: {name_error}")
        return False
    
    # Länge validieren (max. MAX_DISPLAY_NAME_LENGTH Zeichen)
    length_valid, length_error = validate_length(new_name, max_length=MAX_DISPLAY_NAME_LENGTH, field_name="Anzeigename")
    if not length_valid:
        logger.warning(f"Anzeigename zu lang: {length_error}")
        return False
    
    try:
        # Input sanitizen
        sanitized_name = sanitize_string(new_name, max_length=MAX_DISPLAY_NAME_LENGTH)
        
        # 1. Aktualisiere auth.users.user_metadata.display_name
        # Hinweis: Supabase Auth API aktualisiert user_metadata über update_user()
        try:
            # Hole aktuelles user_metadata um bestehende Daten zu behalten
            current_user = sb.auth.get_user()
            current_metadata = {}
            if current_user and current_user.user and current_user.user.user_metadata:
                current_metadata = dict(current_user.user.user_metadata)  # Kopie erstellen
            
            # Füge/aktualisiere display_name in user_metadata
            current_metadata["display_name"] = sanitized_name
            
            # Aktualisiere user_metadata über Supabase Auth API
            # Die update_user() Methode erwartet ein Dictionary mit "data" für user_metadata
            sb.auth.update_user({
                "data": current_metadata
            })
            logger.info(f"Auth user_metadata.display_name aktualisiert für User {user_id}")
        except Exception as auth_error:
            logger.warning(f"Fehler beim Aktualisieren von auth.users (User {user_id}): {auth_error}", exc_info=True)
            # Weiter mit user Tabelle, auch wenn auth Update fehlschlägt
        
        # 2. Aktualisiere user.display_name in der eigenen Tabelle
        sb.table("user").update({"display_name": sanitized_name}).eq("id", user_id).execute()
        logger.info(f"User.display_name aktualisiert für User {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Namens (User {user_id}): {e}", exc_info=True)
        return False


async def send_password_reset(sb, email: str) -> bool:
    """Sendet eine Passwort-Zurücksetzen-E-Mail.
    
    Args:
        sb: Supabase Client-Instanz
        email: E-Mail-Adresse des Benutzers
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    # E-Mail validieren
    email_valid, email_error = validate_email(email)
    if not email_valid:
        logger.warning(f"Ungültige E-Mail-Adresse: {email_error}")
        return False
    
    try:
        # E-Mail normalisieren (lowercase)
        normalized_email = email.strip().lower()
        sb.auth.reset_password_email(normalized_email)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der Reset-E-Mail ({email}): {e}", exc_info=True)
        return False
