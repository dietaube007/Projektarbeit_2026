"""
Search & Filter-Komponenten für die Discover-View.
"""

from __future__ import annotations

from typing import Callable, Optional, List, Dict, Any
import flet as ft

from ui.constants import BORDER_COLOR, PRIMARY_COLOR, DROPDOWN_MENU_HEIGHT


def create_search_field(on_change: Optional[Callable[[ft.ControlEvent], None]] = None) -> ft.TextField:
    """Erstellt das Suchfeld.
    
    Args:
        on_change: Optional Callback-Funktion die bei Eingabe aufgerufen wird
    
    Returns:
        TextField für Suchbegriff-Eingabe
    """
    return ft.TextField(
        label="Suche",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=on_change,
        border_radius=12,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_dropdown(
    label: str,
    on_change: Optional[Callable[[ft.ControlEvent], None]] = None,
    initial_options: Optional[List[ft.dropdown.Option]] = None
) -> ft.Dropdown:
    """Erstellt ein Dropdown-Menü.
    
    Args:
        label: Label-Text für das Dropdown
        on_change: Optional Callback-Funktion die bei Auswahl aufgerufen wird
        initial_options: Optionale initiale Optionen (Standard: ["Alle"])
    
    Returns:
        Konfiguriertes Dropdown-Widget
    """
    if initial_options is None:
        initial_options = [ft.dropdown.Option("alle", "Alle")]
    
    dropdown = ft.Dropdown(
        label=label,
        options=initial_options,
        value="alle",
        expand=True,
        on_change=on_change,
    )
    if hasattr(dropdown, "max_menu_height"):
        dropdown.max_menu_height = DROPDOWN_MENU_HEIGHT
    return dropdown


def populate_dropdown(
    dropdown: ft.Dropdown,
    items: List[Dict[str, Any]],
    id_key: str = "id",
    name_key: str = "name",
    include_all: bool = True
) -> None:
    """Befüllt ein Dropdown mit Optionen.
    
    Args:
        dropdown: Dropdown-Widget das befüllt werden soll
        items: Liste von Dictionaries mit den Daten
        id_key: Schlüssel für die ID im Dictionary (Standard: "id")
        name_key: Schlüssel für den Namen im Dictionary (Standard: "name")
        include_all: Ob "Alle"-Option hinzugefügt werden soll
    """
    if include_all:
        dropdown.options = [ft.dropdown.Option("alle", "Alle")]
    else:
        dropdown.options = []
    
    for it in items or []:
        dropdown.options.append(
            ft.dropdown.Option(str(it.get(id_key)), it.get(name_key, ""))
        )


def create_farben_header(toggle_icon: ft.Icon, on_click: Callable, page: Optional[ft.Page] = None) -> ft.Container:
    """Erstellt den Header für das Farben-Panel.

    Args:
        toggle_icon: Icon für Toggle-Button
        on_click: Callback für Klick
        page: Optional Page-Instanz für Theme-Erkennung

    Returns:
        Container mit Farben-Header (verwendet Material-3 Farben für automatische Theme-Anpassung)
    """
    # Theme-Farben für Light/Dark Mode mit Fallback
    if page:
        from ui.theme import get_theme_color
        is_dark = page.theme_mode == ft.ThemeMode.DARK
        text_color = get_theme_color("text_primary", is_dark)
        icon_color = get_theme_color("text_secondary", is_dark)
    else:
        # Fallback wenn keine Page verfügbar
        text_color = ft.Colors.GREY_800
        icon_color = ft.Colors.GREY_600
    
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18, color=icon_color),
                ft.Text("Farben wählen", size=14, color=text_color),
                ft.Container(expand=True),
                toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=on_click,
        border_radius=8,
    )


def create_view_toggle(on_change: Callable[[ft.ControlEvent], None]) -> ft.SegmentedButton:
    """Erstellt den View-Toggle (Liste/Kacheln).
    
    Args:
        on_change: Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        SegmentedButton für View-Auswahl (Liste/Grid)
    """
    return ft.SegmentedButton(
        selected={"list"},
        segments=[
            ft.Segment(value="list", label=ft.Text("Liste"), icon=ft.Icon(ft.Icons.VIEW_AGENDA)),
            ft.Segment(value="grid", label=ft.Text("Kacheln"), icon=ft.Icon(ft.Icons.GRID_VIEW)),
        ],
        on_change=on_change,
    )


def create_sort_dropdown(
    on_change: Optional[Callable[[ft.ControlEvent], None]] = None
) -> ft.Dropdown:
    """Erstellt das Sortier-Dropdown.
    
    Args:
        on_change: Optional Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        Dropdown für Sortier-Optionen
    """
    dropdown = ft.Dropdown(
        label="Sortieren",
        options=[
            ft.dropdown.Option("created_at_desc", "Erstellungsdatum (neueste)"),
            ft.dropdown.Option("created_at_asc", "Erstellungsdatum (älteste)"),
            ft.dropdown.Option("event_date_desc", "Event-Datum (neueste)"),
            ft.dropdown.Option("event_date_asc", "Event-Datum (älteste)"),
        ],
        value="created_at_desc",
        expand=True,
        on_change=on_change,
    )
    if hasattr(dropdown, "max_menu_height"):
        dropdown.max_menu_height = DROPDOWN_MENU_HEIGHT
    return dropdown


def create_reset_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den Filter-Reset-Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        TextButton zum Zurücksetzen der Filter
    """
    return ft.TextButton(
        "Filter zurücksetzen",
        icon=ft.Icons.RESTART_ALT,
        on_click=on_click,
    )
