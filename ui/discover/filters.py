"""
Filter-Komponenten für die Discover View.

Enthält Funktionen zum Erstellen und Verwalten der Filter-UI.
"""

import flet as ft
from typing import Callable, List


def create_search_field(on_change: Callable) -> ft.TextField:
    """Erstellt das Suchfeld."""
    return ft.TextField(
        label="Suche",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=on_change,
    )


def create_dropdown(
    label: str,
    on_change: Callable,
    initial_options: List[ft.dropdown.Option] = None
) -> ft.Dropdown:
    """Erstellt ein Dropdown-Menü."""
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
    items: List[dict],
    id_key: str = "id",
    name_key: str = "name",
    include_all: bool = True
):
    """Befüllt ein Dropdown mit Optionen."""
    if include_all:
        dropdown.options = [ft.dropdown.Option("alle", "Alle")]
    else:
        dropdown.options = []
    
    for it in items or []:
        dropdown.options.append(
            ft.dropdown.Option(str(it.get(id_key)), it.get(name_key, ""))
        )


def create_farben_panel(
    colors: List[dict],
    selected_farben: List[int],
    on_color_change: Callable
) -> tuple[ft.ResponsiveRow, ft.Icon, ft.Container]:
    """Erstellt das Farben-Filter-Panel."""
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
    
    panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=False,
    )
    
    return farben_container, toggle_icon, panel


def create_farben_header(toggle_icon: ft.Icon, on_click: Callable) -> ft.Container:
    """Erstellt den Header für das Farben-Panel."""
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
        bgcolor=ft.Colors.GREY_50,
        border=ft.border.all(1, ft.Colors.GREY_200),
    )


def create_view_toggle(on_change: Callable) -> ft.SegmentedButton:
    """Erstellt den View-Toggle (Liste/Kacheln)."""
    return ft.SegmentedButton(
        selected={"list"},
        segments=[
            ft.Segment(value="list", label=ft.Text("Liste"), icon=ft.Icon(ft.Icons.VIEW_AGENDA)),
            ft.Segment(value="grid", label=ft.Text("Kacheln"), icon=ft.Icon(ft.Icons.GRID_VIEW)),
        ],
        on_change=on_change,
    )


def create_reset_button(on_click: Callable) -> ft.TextButton:
    """Erstellt den Filter-Reset-Button."""
    return ft.TextButton(
        "Filter zurücksetzen",
        icon=ft.Icons.RESTART_ALT,
        on_click=on_click,
    )
