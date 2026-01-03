"""
ui/auth/forms.py
Formular-Komponenten für Login und Registrierung.
"""

import flet as ft
from typing import Callable

from .constants import (
    PRIMARY_COLOR,
    CARD_COLOR,
    TEXT_SECONDARY,
    BORDER_COLOR,
    MAX_DISPLAY_NAME_LENGTH,
)


def create_login_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Login."""
    return ft.TextField(
        label="E-Mail",
        hint_text="beispiel@mail.com",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=8,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_login_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Login."""
    return ft.TextField(
        label="Passwort",
        hint_text="Dein Passwort",
        password=True,
        can_reveal_password=True,
        border_radius=8,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_register_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Registrierung."""
    return ft.TextField(
        label="E-Mail",
        hint_text="deine@email.de",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=12,
    )


def create_register_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Registrierung."""
    return ft.TextField(
        label="Passwort",
        hint_text="Mind. 8 Zeichen, Ziffer & Sonderzeichen",
        password=True,
        can_reveal_password=True,
        border_radius=12,
    )


def create_register_username_field() -> ft.TextField:
    """Erstellt das Anzeigename-Feld für Registrierung."""
    return ft.TextField(
        label="Anzeigename",
        hint_text="Dein Name",
        border_radius=12,
        max_length=MAX_DISPLAY_NAME_LENGTH,
    )


def create_login_button(on_click: Callable) -> ft.ElevatedButton:
    """Erstellt den Login-Button."""
    return ft.ElevatedButton(
        "Einloggen",
        on_click=on_click,
        expand=True,
        height=48,
        bgcolor=PRIMARY_COLOR,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=24),
        ),
    )


def create_register_button(on_click: Callable) -> ft.TextButton:
    """Erstellt den Registrierungs-Link-Button."""
    return ft.TextButton(
        "Registrieren",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_continue_button(on_click: Callable) -> ft.TextButton:
    """Erstellt den 'Ohne Account fortsetzen' Button."""
    return ft.TextButton(
        "Ohne Account fortsetzen",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_logout_button(on_click: Callable) -> ft.TextButton:
    """Erstellt den Logout-Button."""
    return ft.TextButton(
        "Abmelden",
        icon=ft.Icons.LOGOUT,
        on_click=on_click,
        style=ft.ButtonStyle(color=ft.Colors.RED_400),
    )


def create_theme_toggle(is_dark: bool, on_click: Callable) -> ft.IconButton:
    """Erstellt den Theme-Toggle-Button."""
    return ft.IconButton(
        icon=ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE,
        on_click=on_click,
        tooltip="Theme wechseln",
        icon_color=ft.Colors.WHITE if is_dark else TEXT_SECONDARY,
    )


def create_registration_modal(
    email_field: ft.TextField,
    password_field: ft.TextField,
    username_field: ft.TextField,
    info_text: ft.Text,
    on_register: Callable,
    on_close: Callable,
    is_dark: bool = False,
) -> ft.Container:
    """Erstellt das Registrierungs-Modal."""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Registrierung", size=20, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.CLOSE, on_click=on_close)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            email_field,
            ft.Container(height=8),
            password_field,
            ft.Container(height=8),
            username_field,
            ft.Container(height=12),
            info_text,
            ft.Container(height=12),
            ft.Row([
                ft.TextButton("Abbrechen", on_click=on_close),
                ft.ElevatedButton(
                    "Registrieren",
                    on_click=on_register,
                    bgcolor=PRIMARY_COLOR,
                    color=ft.Colors.WHITE,
                ),
            ], alignment=ft.MainAxisAlignment.END),
        ], tight=True, spacing=0),
        padding=24,
        border_radius=16,
        bgcolor=ft.Colors.GREY_800 if is_dark else CARD_COLOR,
        width=400,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=3,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
        ),
    )


def create_login_card(
    email_field: ft.TextField,
    password_field: ft.TextField,
    info_text: ft.Text,
    login_btn: ft.ElevatedButton,
    register_btn: ft.TextButton,
    continue_btn: ft.TextButton,
    is_logged_in: bool = False,
    logout_btn: ft.TextButton = None,
    is_dark: bool = False,
) -> ft.Container:
    """Erstellt die Login-Card."""
    card_content = [
        email_field,
        ft.Container(height=16),
        password_field,
        ft.Container(height=24),
        login_btn,
        ft.Container(height=16),
        info_text,
        ft.Container(height=8),
        ft.Row(
            [ft.Text("Noch kein Konto?", color=TEXT_SECONDARY), register_btn], 
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Container(height=12),
        ft.Row([continue_btn], alignment=ft.MainAxisAlignment.CENTER),
    ]
    
    if is_logged_in and logout_btn:
        card_content.append(logout_btn)
    
    return ft.Container(
        content=ft.Column(card_content, tight=True, spacing=0),
        padding=40,
        border_radius=20,
        bgcolor=ft.Colors.GREY_800 if is_dark else CARD_COLOR,
        width=420,
        shadow=ft.BoxShadow(
            blur_radius=40,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )
