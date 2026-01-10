"""
Common Profile Components: Wiederverwendbare Basis-Komponenten.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from ui.theme import soft_card
from ui.constants import PRIMARY_COLOR

# Konstanten
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


def create_back_button(on_click: Callable) -> ft.Container:
    """Erstellt einen Zurück-Button.
    
    Args:
        on_click: Callback-Funktion die beim Klick aufgerufen wird
    
    Returns:
        Container mit Zurück-Button
    """
    return ft.Container(
        content=ft.TextButton("← Zurück", on_click=on_click),
        padding=ft.padding.only(bottom=8),
    )


def create_section_title(title: str) -> ft.Text:
    """Erstellt einen Abschnitts-Titel.
    
    Args:
        title: Titel-Text
    
    Returns:
        Text-Widget für Abschnitts-Titel
    """
    return ft.Text(title, size=18, weight=ft.FontWeight.W_600)


def create_menu_item(
    icon: str,
    title: str,
    subtitle: str = "",
    on_click: Optional[Callable] = None,
) -> ft.Container:
    """Erstellt einen Menüpunkt.
    
    Args:
        icon: Icon-Name (z.B. ft.Icons.EDIT_OUTLINED)
        title: Titel des Menüpunkts
        subtitle: Optionaler Untertitel
        on_click: Optionaler Callback beim Klick
    
    Returns:
        Container mit Menüpunkt
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, size=24, color=PRIMARY_COLOR),
                    padding=12,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
                ),
                ft.Column(
                    [
                        ft.Text(title, size=16, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=12, color=ft.Colors.GREY_600) if subtitle else ft.Container(),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400),
            ],
            spacing=16,
        ),
        padding=12,
        border_radius=12,
        on_click=on_click,
        ink=True,
    )


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


def create_profile_header(
    avatar: ft.CircleAvatar,
    display_name: ft.Text,
    email_text: ft.Text,
) -> ft.Control:
    """Erstellt den Profil-Header im Hauptmenü.
    
    Args:
        avatar: CircleAvatar-Widget
        display_name: Text-Widget für Anzeigename
        email_text: Text-Widget für E-Mail
    
    Returns:
        Container mit Profil-Header
    """
    return soft_card(
        ft.Column([
            ft.Row([
                avatar,
                ft.Column([display_name, email_text], spacing=4, expand=True),
            ], spacing=20),
        ], spacing=16),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


def create_main_menu(
    on_edit_profile: Callable,
    on_my_posts: Callable,
    on_favorites: Callable,
    on_saved_searches: Callable,
    on_settings: Callable,
) -> ft.Control:
    """Erstellt das Hauptmenü.
    
    Args:
        on_edit_profile: Callback für "Profil bearbeiten"
        on_my_posts: Callback für "Meine Meldungen"
        on_favorites: Callback für "Favorisierte Meldungen"
        on_saved_searches: Callback für "Gespeicherte Suchaufträge"
        on_settings: Callback für "Einstellungen"
    
    Returns:
        Container mit Hauptmenü
    """
    return soft_card(
        ft.Column([
            create_menu_item(ft.Icons.EDIT_OUTLINED, "Profil bearbeiten", on_click=on_edit_profile),
            ft.Divider(height=1),
            create_menu_item(ft.Icons.ARTICLE_OUTLINED, "Meine Meldungen", on_click=on_my_posts),
            ft.Divider(height=1),
            create_menu_item(ft.Icons.FAVORITE_BORDER, "Favorisierte Meldungen", on_click=on_favorites),
            ft.Divider(height=1),
            create_menu_item(ft.Icons.BOOKMARK_BORDER, "Gespeicherte Suchaufträge", on_click=on_saved_searches),
            ft.Divider(height=1),
            create_menu_item(ft.Icons.SETTINGS_OUTLINED, "Einstellungen", on_click=on_settings),
        ], spacing=0),
        pad=12,
        elev=2,
    )


def create_logout_button(on_logout: Callable) -> ft.Container:
    """Erstellt den Logout-Button.
    
    Args:
        on_logout: Callback beim Klick auf Logout
    
    Returns:
        Container mit Logout-Button
    """
    return ft.Container(
        content=ft.OutlinedButton(
            "Abmelden",
            icon=ft.Icons.LOGOUT,
            on_click=on_logout,
            style=ft.ButtonStyle(color=ft.Colors.RED, side=ft.BorderSide(1, ft.Colors.RED)),
            width=200,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=8, bottom=24),
    )
