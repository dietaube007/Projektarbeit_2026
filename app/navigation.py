"""
Navigation - Navigationskomponenten für PetBuddy.

Enthaelt Funktionen zum Erstellen von:
- AppBar (Top Bar)
- NavigationDrawer (Seitennavigation)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import flet as ft


# Tab-Indices als Konstanten
TAB_START = 0
TAB_MELDEN = 1
TAB_PROFIL = 2

# Drawer-Keys als Konstanten
DRAWER_KEY_START = "start"
DRAWER_KEY_MELDEN = "melden"
DRAWER_KEY_PROFILE_EDIT = "profile_edit"
DRAWER_KEY_MY_POSTS = "my_posts"
DRAWER_KEY_FAVORITES = "favorites"
DRAWER_KEY_SAVED_SEARCHES = "saved_searches"
DRAWER_KEY_SETTINGS = "settings"
DRAWER_KEY_LOGOUT = "logout"
DRAWER_KEY_LOGIN = "login"


def create_app_bar(
    is_logged_in: bool,
    on_logout: Callable[[ft.ControlEvent], None],
    theme_toggle_button: ft.Control,
    on_menu: Optional[Callable[[ft.ControlEvent], None]] = None,
    page: Optional[ft.Page] = None,  # Page-Instanz hinzufügen
    on_title_click: Optional[Callable[[ft.ControlEvent], None]] = None,
    on_login: Optional[Callable[[ft.ControlEvent], None]] = None,
) -> ft.Control:
    """Erstellt die App-Bar."""
    from ui.theme import get_theme_color
    
    actions = [theme_toggle_button]
    
    if is_logged_in:
        actions.insert(0, ft.IconButton(
            ft.Icons.LOGOUT,
            tooltip="Abmelden",
            on_click=on_logout
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
    
    actions_row = ft.Row(actions, spacing=4)
    title_row = ft.Row([title_content], alignment=ft.MainAxisAlignment.CENTER)

    menu_button = ft.IconButton(
        icon=ft.Icons.MENU,
        tooltip="Menü",
        on_click=on_menu,
    )
    menu_slot = ft.Container(
        content=menu_button if on_menu is not None else None,
        width=40,
        alignment=ft.alignment.center_left,
    )

    return ft.Container(
        content=ft.Row(
            [
                menu_slot,
                ft.Container(content=title_row, expand=True),
                actions_row,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
    )


@dataclass(frozen=True)
class DrawerItem:
    key: str
    label: str
    icon: ft.IconData
    action: Callable[[], None]


def create_navigation_drawer(
    items: list[DrawerItem],
    selected_index: int,
    on_change: Callable[[ft.ControlEvent], None],
) -> tuple[ft.NavigationDrawer, dict[str, int], list[Callable[[], None]]]:
    """Erstellt den NavigationDrawer inklusive Aktionen und Index-Mapping."""
    drawer_controls: list[ft.Control] = []
    drawer_actions: list[Callable[[], None]] = []
    drawer_index_map: dict[str, int] = {}

    for item in items:
        drawer_controls.append(
            ft.NavigationDrawerDestination(icon=item.icon, label=item.label)
        )
        drawer_actions.append(item.action)
        drawer_index_map[item.key] = len(drawer_controls) - 1

    drawer = ft.NavigationDrawer(
        selected_index=selected_index,
        on_change=on_change,
        controls=drawer_controls,
    )

    return drawer, drawer_index_map, drawer_actions


def build_drawer_items(
    is_logged_in: bool,
    actions: dict[str, Callable[[], None]],
) -> list[DrawerItem]:
    """Erstellt die Drawer-Items anhand des Login-Status und Actions."""
    items: list[DrawerItem] = [
        DrawerItem(
            key=DRAWER_KEY_START,
            label="Start",
            icon=ft.Icons.HOME_OUTLINED,
            action=actions[DRAWER_KEY_START],
        )
    ]

    if is_logged_in:
        items.extend(
            [
                DrawerItem(
                    key=DRAWER_KEY_MELDEN,
                    label="Melden",
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    action=actions[DRAWER_KEY_MELDEN],
                ),
                DrawerItem(
                    key=DRAWER_KEY_PROFILE_EDIT,
                    label="Profil bearbeiten",
                    icon=ft.Icons.PERSON_OUTLINE,
                    action=actions[DRAWER_KEY_PROFILE_EDIT],
                ),
                DrawerItem(
                    key=DRAWER_KEY_MY_POSTS,
                    label="Meine Meldungen",
                    icon=ft.Icons.ARTICLE_OUTLINED,
                    action=actions[DRAWER_KEY_MY_POSTS],
                ),
                DrawerItem(
                    key=DRAWER_KEY_FAVORITES,
                    label="Favoritenlisten",
                    icon=ft.Icons.FAVORITE_BORDER,
                    action=actions[DRAWER_KEY_FAVORITES],
                ),
                DrawerItem(
                    key=DRAWER_KEY_SAVED_SEARCHES,
                    label="Gespeicherte Suche",
                    icon=ft.Icons.BOOKMARK_BORDER,
                    action=actions[DRAWER_KEY_SAVED_SEARCHES],
                ),
                DrawerItem(
                    key=DRAWER_KEY_SETTINGS,
                    label="Einstellungen",
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    action=actions[DRAWER_KEY_SETTINGS],
                ),
                DrawerItem(
                    key=DRAWER_KEY_LOGOUT,
                    label="Abmelden",
                    icon=ft.Icons.LOGOUT,
                    action=actions[DRAWER_KEY_LOGOUT],
                ),
            ]
        )
    else:
        items.append(
            DrawerItem(
                key=DRAWER_KEY_LOGIN,
                label="Anmelden",
                icon=ft.Icons.LOGIN,
                action=actions[DRAWER_KEY_LOGIN],
            )
        )

    return items


def get_profile_drawer_key(current_view: Optional[str]) -> Optional[str]:
    """Mappt die aktuelle Profil-View auf den Drawer-Key."""
    if not current_view:
        return None
    from ui.profile import ProfileView

    return {
        ProfileView.VIEW_EDIT_PROFILE: DRAWER_KEY_PROFILE_EDIT,
        ProfileView.VIEW_MY_POSTS: DRAWER_KEY_MY_POSTS,
        ProfileView.VIEW_FAVORITES: DRAWER_KEY_FAVORITES,
        ProfileView.VIEW_SAVED_SEARCHES: DRAWER_KEY_SAVED_SEARCHES,
        ProfileView.VIEW_SETTINGS: DRAWER_KEY_SETTINGS,
    }.get(current_view)


def get_drawer_key_for_tab(tab: int, profile_key: Optional[str]) -> Optional[str]:
    """Mappt Tab-Index auf Drawer-Key."""
    if tab == TAB_START:
        return DRAWER_KEY_START
    if tab == TAB_MELDEN:
        return DRAWER_KEY_MELDEN
    if tab == TAB_PROFIL:
        return profile_key or DRAWER_KEY_PROFILE_EDIT
    return None


def set_drawer_selection(
    drawer: Optional[ft.NavigationDrawer],
    index_map: dict[str, int],
    index_or_key: int | str,
    profile_key: Optional[str],
) -> None:
    """Setzt den selektierten Drawer-Index anhand von Tab oder Key."""
    if drawer is None:
        return
    if isinstance(index_or_key, int):
        key = get_drawer_key_for_tab(index_or_key, profile_key)
    else:
        key = index_or_key
    if key is None:
        return
    index = index_map.get(key)
    if index is not None:
        drawer.selected_index = index