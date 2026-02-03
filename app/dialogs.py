"""
Dialoge - Login-Dialoge und Banner für PetBuddy.

Enthält Funktionen zum Erstellen von:
- Login-Required Dialoge
- Favoriten-Login-Dialoge
- Suche-speichern-Login-Dialoge
- Kommentar-Login-Dialoge
- Login-Banner für Gäste
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from ui.constants import PRIMARY_COLOR



def create_login_required_dialog(
    page: ft.Page,
    target_tab: int,
    on_login_click: Callable[[ft.ControlEvent], None],
    on_cancel_click: Callable[[ft.ControlEvent], None]
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
    on_login_click: Callable[[ft.ControlEvent], None],
    on_cancel_click: Callable[[ft.ControlEvent], None]
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


def create_saved_search_login_dialog(
    page: ft.Page,
    on_login_click: Callable[[ft.ControlEvent], None],
    on_cancel_click: Callable[[ft.ControlEvent], None]
) -> ft.AlertDialog:
    """Erstellt einen Dialog wenn Gast eine Suche speichern möchte."""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Anmeldung erforderlich"),
        content=ft.Text(
            "Bitte melden Sie sich an, um Suchen zu speichern."
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_click),
            ft.ElevatedButton("Anmelden", on_click=on_login_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


def create_comment_login_dialog(
    page: ft.Page,
    on_login_click: Callable[[ft.ControlEvent], None],
    on_cancel_click: Callable[[ft.ControlEvent], None]
) -> ft.AlertDialog:
    """Erstellt einen Dialog wenn Gast kommentieren möchte."""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text("Anmeldung erforderlich"),
        content=ft.Text(
            "Bitte melden Sie sich an, um zu kommentieren."
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_click),
            ft.ElevatedButton("Anmelden", on_click=on_login_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


def create_login_banner(on_login_click: Callable) -> ft.Container:
    """Erstellt ein Banner für nicht eingeloggte Benutzer."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
                ft.Text(
                    "Melden Sie sich an, um Tiere zu melden oder Ihr Profil zu verwalten.",
                    color=ft.Colors.BLUE_900,
                    size=14,
                    expand=True,
                ),
                ft.TextButton(
                    "Anmelden",
                    icon=ft.Icons.LOGIN,
                    on_click=on_login_click,
                    style=ft.ButtonStyle(
                        color=PRIMARY_COLOR,  # Oder PRIMARY_COLOR verwenden
                    )
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        bgcolor=ft.Colors.BLUE_50,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.BLUE_200),
    )
