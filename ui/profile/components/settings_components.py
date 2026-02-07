"""
Settings Components: UI-Komponenten für Einstellungen.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from ui.theme import soft_card
from .menu_components import create_section_title, create_setting_row

# Konstanten
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


def create_settings_view(
    on_notification_change: Callable[[bool], None],
    on_email_notification_change: Callable[[bool], None],
) -> list[ft.Control]:
    """Erstellt die Einstellungen-Ansicht.
    
    Args:
        on_notification_change: Callback beim Ändern der Push-Benachrichtigungen
        on_email_notification_change: Callback beim Ändern der E-Mail-Benachrichtigungen
    
    Returns:
        Liste von Controls für Settings-View
    """
    notifications_section = soft_card(
        ft.Column([
            create_section_title("Benachrichtigungen"),
            ft.Container(height=12),
            create_setting_row(
                ft.Icons.NOTIFICATIONS_OUTLINED,
                "Push-Benachrichtigungen",
                "Erhalten Sie Updates zu Ihren Meldungen",
                ft.Switch(value=True, on_change=lambda e: on_notification_change(e.control.value)),
            ),
            ft.Divider(height=20),
            create_setting_row(
                ft.Icons.EMAIL_OUTLINED,
                "E-Mail-Benachrichtigungen",
                "Erhalte wichtige Updates per E-Mail",
                ft.Switch(value=False, on_change=lambda e: on_email_notification_change(e.control.value)),
            ),
        ], spacing=8),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )

    return [notifications_section]
