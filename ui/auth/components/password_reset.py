"""
Password Reset-Komponenten: UI-Komponenten für Passwort-Reset.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional

from ui.constants import PRIMARY_COLOR, TEXT_SECONDARY
from .common import create_base_textfield


def create_password_reset_email_field(
    initial_email: Optional[str] = None,
) -> ft.TextField:
    """Erstellt das E-Mail-Feld für Passwort-Reset."""
    field = create_base_textfield(
        label="E-Mail-Adresse",
        hint_text="Ihre registrierte E-Mail",
        keyboard_type=ft.KeyboardType.EMAIL,
        value=initial_email or "",
        width=300,
    )
    # prefix_icon direkt setzen (nach der Erstellung)
    field.prefix_icon = ft.Icons.EMAIL
    return field


def create_forgot_password_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den 'Passwort vergessen?' Button."""
    return ft.TextButton(
        "Passwort vergessen?",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_password_reset_dialog(
    email_field: ft.TextField,
    error_text: ft.Text,
    on_send: Callable[[ft.ControlEvent], None],
    on_cancel: Callable[[ft.ControlEvent], None],
) -> ft.AlertDialog:
    """Erstellt den Dialog zum Zurücksetzen des Passworts."""
    return ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.LOCK_RESET, color=PRIMARY_COLOR),
            ft.Text("Passwort vergessen?", weight=ft.FontWeight.BOLD),
        ], spacing=8),
        content=ft.Container(
            content=ft.Column([
                ft.Text(
                    "Bitte E-Mail-Adresse eingeben:",
                    size=14,
                    color=TEXT_SECONDARY,
                ),
                ft.Container(height=8),
                email_field,
                error_text,
            ], spacing=8, tight=True),
            width=320,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton(
                "Link senden",
                icon=ft.Icons.SEND,
                bgcolor=PRIMARY_COLOR,
                color=ft.Colors.WHITE,
                on_click=on_send,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
