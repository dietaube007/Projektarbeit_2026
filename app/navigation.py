"""
Navigation - Navigationskomponenten für PetBuddy.

Enthält Funktionen zum Erstellen von:
- NavigationBar (Bottom Navigation)
- AppBar (Top Bar)
"""

from __future__ import annotations

from typing import Callable, List, Optional

import flet as ft


# Tab-Indices als Konstanten
TAB_START = 0
TAB_MELDEN = 1
TAB_PROFIL = 2


def create_navigation_bar(
    current_tab: int,
    on_change: Callable[[ft.ControlEvent], None]
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
    on_logout: Callable[[ft.ControlEvent], None],
    theme_toggle_button: ft.Control,
    page: Optional[ft.Page] = None,  # Page-Instanz hinzufügen
    on_title_click: Optional[Callable[[ft.ControlEvent], None]] = None,
    on_login: Optional[Callable[[ft.ControlEvent], None]] = None,
) -> ft.AppBar:
    """Erstellt die App-Bar."""
    from ui.theme import get_theme_color
    
    actions = [theme_toggle_button]
    
    if is_logged_in:
        actions.insert(0, ft.IconButton(
            ft.Icons.LOGOUT,
            tooltip="Abmelden",
            on_click=on_logout
        ))
    elif on_login is not None:
        actions.insert(0, ft.IconButton(
            ft.Icons.LOGIN,
            tooltip="Anmelden",
            on_click=on_login,
        ))
    
    bgcolor = None
    if page:
        bgcolor = get_theme_color("background", page=page)
    else:
        bgcolor = get_theme_color("background", is_dark=False)
    
    title_content = ft.Text("PetBuddy", size=20, weight=ft.FontWeight.W_600)
    if on_title_click is not None:
        title_content = ft.GestureDetector(
            content=title_content,
            on_tap=on_title_click,
            mouse_cursor=ft.MouseCursor.CLICK,
        )
    
    return ft.AppBar(
        title=title_content,
        center_title=True,
        actions=actions,
        bgcolor=bgcolor,  
        elevation=0,
        surface_tint_color=ft.Colors.TRANSPARENT,
    )