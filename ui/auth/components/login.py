"""
Login-Komponenten: UI-Komponenten für die Login-Funktionalität.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional

from ui.constants import (
    PRIMARY_COLOR,
    TEXT_SECONDARY,
    LOGOUT_BUTTON_COLOR,
)
from ui.theme import get_theme_color
from .common import create_base_textfield


def create_login_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Login."""
    return create_base_textfield(
        label="E-Mail",
        hint_text="beispiel@mail.com",
        keyboard_type=ft.KeyboardType.EMAIL,
    )


def create_login_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Login."""
    return create_base_textfield(
        label="Passwort",
        hint_text="Ihr Passwort",
        password=True,
    )


def create_login_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.ElevatedButton:
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


def create_continue_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den 'Ohne Account fortsetzen' Button."""
    return ft.TextButton(
        "Ohne Account fortsetzen",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_logout_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den Logout-Button."""
    return ft.TextButton(
        "Abmelden",
        icon=ft.Icons.LOGOUT,
        on_click=on_click,
        style=ft.ButtonStyle(color=LOGOUT_BUTTON_COLOR),
    )


def create_login_card(
    email_field: ft.TextField,
    password_field: ft.TextField,
    info_text: ft.Text,
    login_btn: ft.ElevatedButton,
    register_btn: ft.TextButton,
    continue_btn: ft.TextButton,
    is_logged_in: bool = False,
    logout_btn: Optional[ft.TextButton] = None,
    forgot_password_btn: Optional[ft.TextButton] = None,
    is_dark: bool = False,
) -> ft.Container:
    """Erstellt die Login-Card.
    
    Wenn is_logged_in=True, wird das Login-Formular versteckt und nur
    eine Erfolgs-Nachricht mit Logout-Button angezeigt.
    """
    if is_logged_in and logout_btn:
        # Eingeloggt: Nur Logout-Button anzeigen
        card_content = [
            ft.Text(
                "Sie sind eingeloggt",
                size=18,
                weight=ft.FontWeight.W_600,
                color=get_theme_color("text_secondary", is_dark),
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=24),
            ft.Row([logout_btn], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=16),
            info_text,
        ]
    else:
        # Nicht eingeloggt: Login-Formular anzeigen
        card_content = [
            email_field,
            ft.Container(height=16),
            password_field,
        ]
        
        if forgot_password_btn:
            card_content.append(
                ft.Row([forgot_password_btn], alignment=ft.MainAxisAlignment.END)
            )
            card_content.append(ft.Container(height=8))
        else:
            card_content.append(ft.Container(height=24))
        
        card_content.extend([
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
        ])
    
    return ft.Container(
        content=ft.Column(card_content, tight=True, spacing=0),
        padding=40,
        border_radius=20,
        bgcolor=get_theme_color("card", is_dark),
        width=420,
        shadow=ft.BoxShadow(
            blur_radius=40,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )
