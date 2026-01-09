"""
Dialoge - Login-Dialoge und Banner für PetBuddy.

Enthält Funktionen zum Erstellen von:
- Login-Required Dialoge
- Favoriten-Login-Dialoge
- Login-Banner für Gäste
"""

from typing import Callable

import flet as ft



def create_login_required_dialog(
    page: ft.Page,
    target_tab: int,
    on_login_click: Callable,
    on_cancel_click: Callable
) -> ft.AlertDialog:
    """Erstellt einen Dialog für nicht eingeloggte Benutzer."""
    tab_name = "Melden" if target_tab == 1 else "Profil"
    
    if target_tab == 1:
        message = "Bitte melden Sie sich an, um Meldungen zu erstellen."
    else:
        message = "Bitte melden Sie sich an, um auf Profilbereich zuzugreifen."
    
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Anmeldung erforderlich"),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_click),
            ft.ElevatedButton("Anmelden", on_click=on_login_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


def create_favorite_login_dialog(
    page: ft.Page,
    on_login_click: Callable,
    on_cancel_click: Callable
) -> ft.AlertDialog:
    """Erstellt einen Dialog wenn Gast auf Favorit klickt."""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Anmeldung erforderlich"),
        content=ft.Text(
            "Bitte melden Sie sich an, um Meldungen zu favorisieren."
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_click),
            ft.ElevatedButton("Anmelden", on_click=on_login_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


def create_login_banner(on_login_click: Callable, theme_mode=None) -> ft.Container:
    """Erstellt ein Banner für nicht eingeloggte Benutzer (hell/dunkel)."""
    is_dark = theme_mode != ft.ThemeMode.LIGHT  # alles außer LIGHT als dunkel behandeln

    if is_dark:
        icon_color = ft.Colors.BLUE_100
        text_color = ft.Colors.WHITE
        bg_color = ft.Colors.with_opacity(0.18, ft.Colors.BLUE_900)
        border_color = ft.Colors.with_opacity(0.32, ft.Colors.BLUE_700)
        link_color = ft.Colors.WHITE
    else:
        icon_color = ft.Colors.BLUE_700
        text_color = ft.Colors.BLUE_900
        bg_color = ft.Colors.BLUE_50
        border_color = ft.Colors.BLUE_200
        link_color = ft.Colors.BLUE_700

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=icon_color, size=20),
                ft.Text(
                    "Melden Sie sich an, um Tiere zu melden oder Ihr Profil zu verwalten.",
                    color=text_color,
                    size=14,
                    expand=True,
                ),
                ft.TextButton(
                    "Anmelden",
                    icon=ft.Icons.LOGIN,
                    on_click=on_login_click,
                    style=ft.ButtonStyle(color=link_color),
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=bg_color,
        border_radius=10,
        border=ft.border.all(1, border_color),
    )
