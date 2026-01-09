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
)
from utils.constants import MAX_DISPLAY_NAME_LENGTH


def create_login_email_field() -> ft.TextField:
    """Erstellt das E-Mail-Feld für Login.
    
    Returns:
        TextField für E-Mail-Eingabe mit Material-3 Styling
    """
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
    """Erstellt das Passwort-Feld für Login.
    
    Returns:
        TextField für Passwort-Eingabe mit Sichtbarkeits-Toggle
    """
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
    """Erstellt das E-Mail-Feld für Registrierung.
    
    Returns:
        TextField für E-Mail-Eingabe bei Registrierung
    """
    return ft.TextField(
        label="E-Mail",
        hint_text="beispiel@email.de",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=12,
    )


def create_register_password_field() -> ft.TextField:
    """Erstellt das Passwort-Feld für Registrierung.
    
    Returns:
        TextField für Passwort-Eingabe bei Registrierung
    """
    return ft.TextField(
        label="Passwort",
        hint_text="Mind. 8 Zeichen, Ziffer & Sonderzeichen",
        password=True,
        can_reveal_password=True,
        border_radius=12,
    )


def create_register_password_confirm_field() -> ft.TextField:
    """Erstellt das Passwort-Bestätigungs-Feld für Registrierung.
    
    Returns:
        TextField für Passwort-Bestätigung
    """
    return ft.TextField(
        label="Passwort wiederholen",
        hint_text="Passwort bestätigen",
        password=True,
        can_reveal_password=True,
        border_radius=12,
    )


def create_register_username_field() -> ft.TextField:
    """Erstellt das Anzeigename-Feld für Registrierung.
    
    Returns:
        TextField für Anzeigename mit Längenbegrenzung
    """
    return ft.TextField(
        label="Anzeigename",
        hint_text="Ihr Name",
        border_radius=12,
        max_length=MAX_DISPLAY_NAME_LENGTH,
    )


def create_login_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.ElevatedButton:
    """Erstellt den Login-Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        ElevatedButton mit Material-3 Styling
    """
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
    """Erstellt den Registrierungs-Link-Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        TextButton für Registrierungs-Link
    """
    return ft.TextButton(
        "Registrieren",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_continue_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den 'Ohne Account fortsetzen' Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        TextButton für Fortsetzen ohne Account
    """
    return ft.TextButton(
        "Ohne Account fortsetzen",
        on_click=on_click,
        style=ft.ButtonStyle(color=PRIMARY_COLOR),
    )


def create_logout_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den Logout-Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        TextButton mit rotem Styling für Logout
    """
    return ft.TextButton(
        "Abmelden",
        icon=ft.Icons.LOGOUT,
        on_click=on_click,
        style=ft.ButtonStyle(color=ft.Colors.RED_400),  # Logout-Button rot bleiben
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
    """Erstellt das Registrierungs-Modal.
    
    Args:
        email_field: TextField für E-Mail
        password_field: TextField für Passwort
        password_confirm_field: TextField für Passwort-Bestätigung
        username_field: TextField für Anzeigename
        info_text: Text-Widget für Fehlermeldungen/Info
        on_register: Callback für Registrierungs-Button
        on_close: Callback für Schließen-Button
        is_dark: Ob Dark-Modus aktiv ist
    
    Returns:
        Container mit Registrierungs-Modal
    """
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


def create_password_reset_dialog(
    email_field: ft.TextField,
    error_text: ft.Text,
    on_send: Callable[[ft.ControlEvent], None],
    on_cancel: Callable[[ft.ControlEvent], None],
) -> ft.AlertDialog:
    """Erstellt den Dialog zum Zurücksetzen des Passworts.
    
    Args:
        email_field: TextField für E-Mail-Eingabe
        error_text: Text-Widget für Fehlermeldungen
        on_send: Callback für "Link senden"-Button
        on_cancel: Callback für "Abbrechen"-Button
    
    Returns:
        AlertDialog für Passwort-Reset
    """
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
    """Erstellt die Login-Card.
    
    Args:
        email_field: TextField für E-Mail
        password_field: TextField für Passwort
        info_text: Text-Widget für Fehlermeldungen/Info
        login_btn: ElevatedButton für Login
        register_btn: TextButton für Registrierung
        continue_btn: TextButton für Fortsetzen ohne Account
        is_logged_in: Ob Benutzer eingeloggt ist
        logout_btn: Optionaler TextButton für Logout
        forgot_password_btn: Optionaler TextButton für Passwort vergessen
        is_dark: Ob Dark-Modus aktiv ist
    
    Returns:
        Container mit Login-Card
    """
    card_content = [
        email_field,
        ft.Container(height=16),
        password_field,
    ]
    
    # "Passwort vergessen?" Link
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
