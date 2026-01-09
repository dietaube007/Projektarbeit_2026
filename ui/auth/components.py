"""
Gemeinsame UI-Komponenten für Login, Registrierung und Auth-Bereich.

Enthält statische Komponenten-Builder-Funktionen.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional

from ui.constants import (
    PRIMARY_COLOR,
    CARD_COLOR,
    TEXT_SECONDARY,
    BORDER_COLOR,
    DARK_CARD,
    LOGOUT_BUTTON_COLOR,
)
from utils.constants import MAX_DISPLAY_NAME_LENGTH


# ══════════════════════════════════════════════════════════════════════
# TEXTFIELD-BASE-FUNKTIONEN
# ══════════════════════════════════════════════════════════════════════

def _create_base_textfield(
    label: str,
    hint_text: str = "",
    password: bool = False,
    keyboard_type: Optional[ft.KeyboardType] = None,
    border_radius: int = 12,
    max_length: Optional[int] = None,
    prefix_icon: Optional[str] = None,
    value: Optional[str] = None,
    width: Optional[int] = None,
) -> ft.TextField:
    """Erstellt ein TextField mit konsistentem Styling.
    
    Args:
        label: Feld-Label
        hint_text: Platzhalter-Text
        password: Ob es ein Passwort-Feld ist
        keyboard_type: Optionaler Keyboard-Typ (z.B. EMAIL)
        border_radius: Border-Radius (Standard: 12)
        max_length: Maximale Textlänge
        prefix_icon: Optionales Icon
        value: Optionaler Vorbelegungswert
        width: Optionale Breite
    
    Returns:
        TextField mit konsistentem Styling
    """
    field = ft.TextField(
        label=label,
        hint_text=hint_text,
        password=password,
        can_reveal_password=password,
        keyboard_type=keyboard_type,
        border_radius=border_radius,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )
    
    if max_length:
        field.max_length = max_length
    if prefix_icon:
        field.prefix_icon = prefix_icon
    if value is not None:
        field.value = value
    if width:
        field.width = width
    
    return field


# ══════════════════════════════════════════════════════════════════════
# LOGIN-FELDER
# ══════════════════════════════════════════════════════════════════════

def create_login_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Login."""
    return _create_base_textfield(
        label="E-Mail",
        hint_text="beispiel@mail.com",
        keyboard_type=ft.KeyboardType.EMAIL,
    )


def create_login_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Login."""
    return _create_base_textfield(
        label="Passwort",
        hint_text="Ihr Passwort",
        password=True,
    )


def create_register_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Registrierung."""
    return _create_base_textfield(
        label="E-Mail",
        hint_text="beispiel@email.de",
        keyboard_type=ft.KeyboardType.EMAIL,
    )


def create_register_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Registrierung."""
    return _create_base_textfield(
        label="Passwort",
        hint_text="Mind. 8 Zeichen, Ziffer & Sonderzeichen",
        password=True,
    )


def create_register_password_confirm_field() -> ft.TextField:
    """Erstellt das Passwort-Bestätigungs-Feld für Registrierung."""
    return _create_base_textfield(
        label="Passwort wiederholen",
        hint_text="Passwort bestätigen",
        password=True,
    )


def create_register_username_field() -> ft.TextField:
    """Erstellt das Anzeigename-Feld für Registrierung."""
    return _create_base_textfield(
        label="Anzeigename",
        hint_text="Ihr Name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
    )


# ══════════════════════════════════════════════════════════════════════
# BUTTONS
# ══════════════════════════════════════════════════════════════════════

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


def create_register_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den Registrierungs-Link-Button."""
    return ft.TextButton(
        "Registrieren",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_continue_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den 'Ohne Account fortsetzen' Button."""
    return ft.TextButton(
        "Ohne Account fortsetzen",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_forgot_password_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den 'Passwort vergessen?' Button."""
    return ft.TextButton(
        "Passwort vergessen?",
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


# ══════════════════════════════════════════════════════════════════════
# COMPLEX COMPONENTS
# ══════════════════════════════════════════════════════════════════════

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
        bgcolor=DARK_CARD if is_dark else CARD_COLOR,
        width=400,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=3,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
        ),
    )


def create_password_reset_email_field(
    initial_email: Optional[str] = None,
) -> ft.TextField:
    """Erstellt das E-Mail-Feld für Passwort-Reset Dialog."""
    return _create_base_textfield(
        label="E-Mail-Adresse",
        hint_text="Ihre registrierte E-Mail",
        keyboard_type=ft.KeyboardType.EMAIL,
        prefix_icon=ft.Icons.EMAIL,
        value=initial_email or "",
        width=300,
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
    """Erstellt die Login-Card."""
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
    
    if is_logged_in and logout_btn:
        card_content.append(logout_btn)
    
    return ft.Container(
        content=ft.Column(card_content, tight=True, spacing=0),
        padding=40,
        border_radius=20,
        bgcolor=DARK_CARD if is_dark else CARD_COLOR,
        width=420,
        shadow=ft.BoxShadow(
            blur_radius=40,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )
