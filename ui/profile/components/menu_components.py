"""
Common Profile Components: Wiederverwendbare Basis-Komponenten.
"""

from __future__ import annotations

import flet as ft

from ui.constants import PRIMARY_COLOR


def create_section_title(title: str) -> ft.Text:
    """Erstellt einen Abschnitts-Titel.

    Args:
        title: Titel-Text

    Returns:
        Text-Widget für Abschnitts-Titel
    """
    return ft.Text(title, size=18, weight=ft.FontWeight.W_600)


def create_setting_row(icon: str, title: str, subtitle: str, control: ft.Control) -> ft.Row:
    """Erstellt eine Einstellungs-Zeile.

    Args:
        icon: Icon-Name
        title: Titel
        subtitle: Untertitel
        control: Kontrollelement (z.B. Switch, Button)

    Returns:
        Row mit Einstellungs-Zeile
    """
    return ft.Row(
        [
            ft.Icon(icon, color=PRIMARY_COLOR),
            ft.Column(
                [
                    ft.Text(title, size=14),
                    ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                ],
                spacing=2,
                expand=True,
            ),
            control,
        ],
        spacing=12,
    )

