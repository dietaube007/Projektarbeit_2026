"""
ui/profile/edit_profile.py
Profil-Bearbeiten-Ansicht und Logik.
"""

import flet as ft

from ui.theme import soft_card
from .components import build_section_title, SECTION_PADDING, CARD_ELEVATION
from utils.logging_config import get_logger

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
    on_save=None,
) -> ft.Container:
    """Erstellt den Anzeigenamen-Abschnitt."""
    name_field = ft.TextField(
        value=current_name,
        width=300,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
    )
    
    return soft_card(
        ft.Column(
            [
                build_section_title("Anzeigename"),
                ft.Container(height=8),
                name_field,
                ft.Container(height=8),
                ft.FilledButton(
                    "Speichern",
                    icon=ft.Icons.SAVE,
                    on_click=on_save or (lambda _: print("Name speichern")),
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


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
    """Aktualisiert den Anzeigenamen in der Datenbank."""
    try:
        sb.table("user").update({"display_name": new_name}).eq("id", user_id).execute()
        return True
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Namens (User {user_id}): {e}", exc_info=True)
        return False


async def send_password_reset(sb, email: str) -> bool:
    """Sendet eine Passwort-Zurücksetzen-E-Mail."""
    try:
        sb.auth.reset_password_email(email)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der Reset-E-Mail ({email}): {e}", exc_info=True)
        return False
