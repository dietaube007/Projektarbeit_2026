"""
Settings Components: UI-Komponenten für Einstellungen.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from ui.theme import soft_card
from .menu_components import create_section_title, create_setting_row

# Konstanten
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


def create_settings_view(
    on_notification_change: Callable[[bool], None],
    on_email_notification_change: Callable[[bool], None],
    on_change_password: Optional[Callable] = None,
    on_delete_account: Optional[Callable] = None,
) -> list[ft.Control]:
    """Erstellt die Einstellungen-Ansicht.

    Args:
        on_notification_change: Callback beim Ändern der Push-Benachrichtigungen
        on_email_notification_change: Callback beim Ändern der E-Mail-Benachrichtigungen
        on_change_password: Callback zum Ändern des Passworts
        on_delete_account: Callback zum Löschen des Kontos

    Returns:
        Liste von Controls für Settings-View
    """
    sections: list[ft.Control] = []

    if on_change_password:
        password_section = soft_card(
            ft.Column([
                create_section_title("Passwort"),
                ft.Container(height=8),
                ft.Text("Ändern Sie Ihr Passwort", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=8),
                ft.FilledButton(
                    "Passwort ändern",
                    icon=ft.Icons.LOCK,
                    on_click=on_change_password,
                ),
            ], spacing=8),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )
        sections.append(password_section)

    if on_delete_account:
        delete_account_section = soft_card(
            ft.Column([
                create_section_title("Konto löschen"),
                ft.Container(height=8),
                ft.Text(
                    "Wenn Sie Ihr Konto löschen, werden alle Ihre Daten unwiderruflich entfernt.",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=8),
                ft.OutlinedButton(
                    "Konto löschen",
                    icon=ft.Icons.DELETE_FOREVER,
                    on_click=on_delete_account,
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED,
                        side=ft.BorderSide(1, ft.Colors.RED),
                    ),
                ),
            ], spacing=8),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )
        sections.append(delete_account_section)

    return sections
