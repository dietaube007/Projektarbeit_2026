"""UI-Builder für die Discover-View: Initialisierung aller UI-Elemente."""

from __future__ import annotations

from typing import Callable, Optional, Dict
import flet as ft

from ui.theme import soft_card
from .filters import (
    create_sort_dropdown,
    create_search_field,
    create_dropdown,
    create_farben_header,
    create_view_toggle,
    create_reset_button,
)


def build_discover_ui(
    on_search_click: Callable,
    on_tierart_change: Callable,
    on_reset_click: Callable,
    on_save_search_click: Callable,
    on_view_change: Callable,
    on_toggle_farben: Callable,
) -> Dict[str, ft.Control]:
    """Baut alle UI-Elemente für die Discover-View.

    Args:
        on_search_click: Callback für Suchen-Button-Klick
        on_tierart_change: Callback für Tierart-Änderung (aktualisiert Rassen-Dropdown)
        on_reset_click: Callback für Reset-Button
        on_save_search_click: Callback für Save-Search-Button
        on_view_change: Callback für View-Toggle-Änderung
        on_toggle_farben: Callback für Farben-Panel-Toggle

    Returns:
        Dictionary mit allen UI-Elementen
    """
    # Suche - ohne on_change (keine automatische Suche)
    search_q = create_search_field(on_change=None)

    # Filter Dropdowns - ohne on_change (keine automatische Suche)
    filter_typ = create_dropdown(
        label="Kategorie",
        on_change=None,
    )

    filter_art = create_dropdown(
        label="Tierart",
        on_change=on_tierart_change,  # Nur für Rassen-Dropdown-Update
    )

    filter_geschlecht = create_dropdown(
        label="Geschlecht",
        on_change=None,
        initial_options=[
            ft.dropdown.Option("alle", "Alle"),
            ft.dropdown.Option("keine_angabe", "Keine Angabe"),
        ],
    )

    filter_rasse = create_dropdown(
        label="Rasse",
        on_change=None,
    )

    # Farben Panel
    farben_filter_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
    farben_panel = ft.Container(
        content=farben_filter_container,
        padding=12,
        visible=False,
    )

    farben_header = create_farben_header(
        toggle_icon=farben_toggle_icon,
        on_click=on_toggle_farben,
    )

    # Sortier-Dropdown - ohne on_change (keine automatische Suche)
    sort_dropdown = create_sort_dropdown(on_change=None)

    # Buttons
    search_btn = ft.ElevatedButton(
        "Suchen",
        icon=ft.Icons.SEARCH,
        on_click=on_search_click,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PRIMARY,
            color=ft.Colors.ON_PRIMARY,
        ),
    )
    reset_btn = create_reset_button(on_click=on_reset_click)
    save_search_btn = ft.TextButton(
        "Suche speichern",
        icon=ft.Icons.BOOKMARK_ADD_OUTLINED,
        on_click=on_save_search_click,
    )

    search_row = ft.ResponsiveRow(
        controls=[
            ft.Container(search_q, col={"xs": 12, "md": 4}),
            ft.Container(filter_typ, col={"xs": 6, "md": 1.5}),
            ft.Container(filter_art, col={"xs": 6, "md": 1.5}),
            ft.Container(filter_geschlecht, col={"xs": 6, "md": 2}),
            ft.Container(filter_rasse, col={"xs": 6, "md": 1}),
            ft.Container(sort_dropdown, col={"xs": 12, "md": 2}),
            ft.Container(farben_header, col={"xs": 12, "md": 12}),
            ft.Container(farben_panel, col={"xs": 12, "md": 12}),
            ft.Container(
                ft.Row([search_btn, reset_btn, save_search_btn], spacing=8),
                col={"xs": 12, "md": 12},
            ),
        ],
        spacing=10,
        run_spacing=10,
    )

    # View toggle
    view_toggle = create_view_toggle(on_change=on_view_change)

    # Ergebnisbereiche
    list_view = ft.Column(spacing=14, expand=True)
    grid_view = ft.ResponsiveRow(spacing=12, run_spacing=12, visible=False)

    empty_state_card = soft_card(
        ft.Column(
            [
                ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
                ft.Text("Noch keine Meldungen", weight=ft.FontWeight.W_600),
                ft.Text("Passen Sie Ihre Filter an oder melden Sie ein Tier.", color=ft.Colors.GREY_700),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        elev=1,
        pad=24,
    )

    return {
        "search_q": search_q,
        "filter_typ": filter_typ,
        "filter_art": filter_art,
        "filter_geschlecht": filter_geschlecht,
        "filter_rasse": filter_rasse,
        "farben_filter_container": farben_filter_container,
        "farben_toggle_icon": farben_toggle_icon,
        "farben_panel": farben_panel,
        "farben_header": farben_header,
        "sort_dropdown": sort_dropdown,
        "search_btn": search_btn,
        "reset_btn": reset_btn,
        "save_search_btn": save_search_btn,
        "search_row": search_row,
        "view_toggle": view_toggle,
        "list_view": list_view,
        "grid_view": grid_view,
        "empty_state_card": empty_state_card,
    }

