"""
Registrierungs-Komponenten: UI-Komponenten für die Registrierung.
"""

from __future__ import annotations

import flet as ft
from typing import Callable

from ui.constants import PRIMARY_COLOR
from ui.theme import get_theme_color
from utils.constants import MAX_DISPLAY_NAME_LENGTH
from .common import create_base_textfield


def create_register_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Registrierung."""
    return create_base_textfield(
        label="E-Mail",
        hint_text="beispiel@email.de",
        keyboard_type=ft.KeyboardType.EMAIL,
    )


def create_register_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Registrierung."""
    return create_base_textfield(
        label="Passwort",
        hint_text="Mind. 8 Zeichen, Ziffer & Sonderzeichen",
        password=True,
    )


def create_register_password_confirm_field() -> ft.TextField:
    """Erstellt das Passwort-Bestätigungs-Feld für Registrierung."""
    return create_base_textfield(
        label="Passwort wiederholen",
        hint_text="Passwort bestätigen",
        password=True,
    )


def create_register_username_field() -> ft.TextField:
    """Erstellt das Anzeigename-Feld für Registrierung."""
    return create_base_textfield(
        label="Anzeigename",
        hint_text="Ihr Name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
    )


def create_register_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den Registrierungs-Link-Button."""
    return ft.TextButton(
        "Registrieren",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_registration_modal(
    email_field: ft.TextField,
    password_field: ft.TextField,
    password_confirm_field: ft.TextField,
    username_field: ft.TextField,
    info_text: ft.Text,
    on_register: Callable[[ft.ControlEvent], None],
    on_close: Callable[[ft.ControlEvent], None],
    is_dark: bool = False,
) -> ft.Container:
    """Erstellt das Registrierungs-Modal."""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Registrieren", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.CLOSE, on_click=on_close)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            email_field,
            password_field,
            password_confirm_field,
            username_field,
            info_text,
            ft.Row([
                ft.TextButton("Abbrechen", on_click=on_close),
                ft.ElevatedButton(
                    "Registrieren",
                    on_click=on_register,
                    bgcolor=PRIMARY_COLOR,
                    color=ft.Colors.WHITE,
                ),
            ], alignment=ft.MainAxisAlignment.END),
        ], tight=True, spacing=12),
        padding=24,
        border_radius=16,
        bgcolor=get_theme_color("card", is_dark),
        width=400,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=3,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
        ),
    )
