"""
ui/profile/settings.py
Einstellungen-Ansicht und Logik.
"""

import flet as ft

from ui.theme import soft_card
from .components import build_section_title, build_setting_row, SECTION_PADDING, CARD_ELEVATION


def build_notifications_section(
    push_enabled: bool = True,
    email_enabled: bool = False,
    on_push_change=None,
    on_email_change=None,
) -> ft.Container:
    """Erstellt den Benachrichtigungs-Abschnitt."""
    return soft_card(
        ft.Column(
            [
                build_section_title("Benachrichtigungen"),
                ft.Container(height=12),
                build_setting_row(
                    ft.Icons.NOTIFICATIONS_OUTLINED,
                    "Push-Benachrichtigungen",
                    "Erhalte Updates zu deinen Meldungen",
                    ft.Switch(
                        value=push_enabled,
                        on_change=on_push_change or (lambda _: print("Push geändert")),
                    ),
                ),
                ft.Divider(height=20),
                build_setting_row(
                    ft.Icons.EMAIL_OUTLINED,
                    "E-Mail-Benachrichtigungen",
                    "Erhalte wichtige Updates per E-Mail",
                    ft.Switch(
                        value=email_enabled,
                        on_change=on_email_change or (lambda _: print("E-Mail geändert")),
                    ),
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


def build_appearance_section(
    dark_mode: bool = False,
    on_theme_change=None,
) -> ft.Container:
    """Erstellt den Erscheinungsbild-Abschnitt."""
    return soft_card(
        ft.Column(
            [
                build_section_title("Erscheinungsbild"),
                ft.Container(height=12),
                build_setting_row(
                    ft.Icons.DARK_MODE_OUTLINED,
                    "Dunkelmodus",
                    "Wechsle zwischen hellem und dunklem Design",
                    ft.Switch(
                        value=dark_mode,
                        on_change=on_theme_change or (lambda _: print("Theme geändert")),
                    ),
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


def build_privacy_section(on_delete_account=None) -> ft.Container:
    """Erstellt den Datenschutz-Abschnitt."""
    return soft_card(
        ft.Column(
            [
                build_section_title("Datenschutz & Daten"),
                ft.Container(height=12),
                ft.Text(
                    "Hier kannst du dein Konto und alle damit verbundenen Daten löschen.",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=12),
                ft.OutlinedButton(
                    "Konto löschen",
                    icon=ft.Icons.DELETE_FOREVER,
                    on_click=on_delete_account or (lambda _: print("Konto löschen")),
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED,
                        side=ft.BorderSide(1, ft.Colors.RED),
                    ),
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )
