"""
Filter-Komponenten für die Discover View.

Enthält Funktionen zum Erstellen und Verwalten der Filter-UI.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, List, Dict, Any, Tuple, Optional


def create_search_field(on_change: Callable[[ft.ControlEvent], None]) -> ft.TextField:
    """Erstellt das Suchfeld.
    
    Args:
        on_change: Callback-Funktion die bei Eingabe aufgerufen wird
    
    Returns:
        TextField für Suchbegriff-Eingabe
    """
    return ft.TextField(
        label="Suche",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=on_change,
    )


def create_dropdown(
    label: str,
    on_change: Callable[[ft.ControlEvent], None],
    initial_options: Optional[List[ft.dropdown.Option]] = None
) -> ft.Dropdown:
    """Erstellt ein Dropdown-Menü.
    
    Args:
        label: Label-Text für das Dropdown
        on_change: Callback-Funktion die bei Auswahl aufgerufen wird
        initial_options: Optionale initiale Optionen (Standard: ["Alle"])
    
    Returns:
        Konfiguriertes Dropdown-Widget
    """
    if initial_options is None:
        initial_options = [ft.dropdown.Option("alle", "Alle")]
    
    return ft.Dropdown(
        label=label,
        options=initial_options,
        value="alle",
        expand=True,
        on_change=on_change,
    )


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


def create_farben_panel(
    colors: List[Dict[str, Any]],
    selected_farben: List[int],
    on_color_change: Callable[[], None]
) -> Tuple[ft.ResponsiveRow, ft.Icon, ft.Container]:
    """Erstellt das Farben-Filter-Panel.
    
    Args:
        colors: Liste von Farb-Dictionaries mit 'id' und 'name'
        selected_farben: Liste mit IDs der bereits ausgewählten Farben
        on_color_change: Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        Tuple mit:
        - ResponsiveRow mit Checkboxes
        - Toggle-Icon
        - Container für Panel
    """
    farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
    
    for c in colors or []:
        c_id = c["id"]
        
        def make_on_change(color_id):
            def handler(e):
                if e.control.value:
                    if color_id not in selected_farben:
                        selected_farben.append(color_id)
                else:
                    if color_id in selected_farben:
                        selected_farben.remove(color_id)
                on_color_change()
            return handler
        
        cb = ft.Checkbox(
            label=c["name"],
            value=c_id in selected_farben,
            on_change=make_on_change(c_id)
        )
        farben_container.controls.append(
            ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
        )
    
    # Theme-Farben für Light/Dark Mode (sicherer Zugriff mit Fallback)
    surface_color = getattr(ft.Colors, "SURFACE_VARIANT", None)
    outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
    
    panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=False,
        bgcolor=surface_color,
        border_radius=8,
        border=ft.border.all(1, outline_color) if outline_color else None,
    )
    
    return farben_container, toggle_icon, panel


def create_farben_header(
    toggle_icon: ft.Icon,
    on_click: Callable[[ft.ControlEvent], None]
) -> ft.Container:
    """Erstellt den Header für das Farben-Panel.
    
    Args:
        toggle_icon: Icon-Widget für Toggle-Button
        on_click: Callback-Funktion für Klick auf Header
    
    Returns:
        Container mit Header-Layout
    """
    # Theme-Farben für Light/Dark Mode (sicherer Zugriff mit Fallback)
    surface_color = getattr(ft.Colors, "SURFACE_VARIANT", None)
    outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
    
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18),
                ft.Text("Farben wählen", size=14),
                ft.Container(expand=True),
                toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=on_click,
        border_radius=8,
        bgcolor=surface_color,
        border=ft.border.all(1, outline_color) if outline_color else None,
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
