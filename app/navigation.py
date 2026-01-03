"""
Navigation - Navigationskomponenten für PetBuddy.

Enthält Funktionen zum Erstellen von:
- NavigationBar (Bottom Navigation)
- AppBar (Top Bar)
"""

from typing import Callable, List

import flet as ft


# Tab-Indices als Konstanten
TAB_START = 0
TAB_MELDEN = 1
TAB_PROFIL = 2


def create_navigation_bar(
    current_tab: int,
    on_change: Callable
) -> ft.NavigationBar:
    """Erstellt die Navigationsleiste."""
    return ft.NavigationBar(
        selected_index=current_tab,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Start"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                selected_icon=ft.Icons.ADD_CIRCLE,
                label="Melden"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.PERSON,
                label="Profil"
            ),
        ],
        on_change=on_change,
    )


def create_app_bar(
    is_logged_in: bool,
    on_logout: Callable,
    theme_toggle_button: ft.Control
) -> ft.AppBar:
    """Erstellt die App-Bar."""
    actions = [theme_toggle_button]
    
    if is_logged_in:
        actions.insert(0, ft.IconButton(
            ft.Icons.LOGOUT,
            tooltip="Abmelden",
            on_click=on_logout
        ))
    
    return ft.AppBar(
        title=ft.Text("PetBuddy", size=20, weight=ft.FontWeight.W_600),
        center_title=True,
        actions=actions,
    )
