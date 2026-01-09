"""Rendering-Logik für Post-Items in der Discover-View."""

from __future__ import annotations

from typing import List, Dict, Any, Callable, Optional
import flet as ft

from ui.theme import soft_card
from .cards import build_small_card, build_big_card


def create_empty_state_card(message: str = "Noch keine Meldungen", subtitle: str = "") -> ft.Container:
    """Erstellt eine Empty-State-Karte.

    Args:
        message: Haupttext
        subtitle: Untertitel

    Returns:
        Container mit Empty-State
    """
    return soft_card(
        ft.Column(
            [
                ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
                ft.Text(message, weight=ft.FontWeight.W_600),
                ft.Text(subtitle, color=ft.Colors.GREY_700) if subtitle else ft.Container(),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        elev=1,
        pad=24,
    )


def create_no_results_card(on_reset: Optional[Callable] = None) -> ft.Container:
    """Erstellt eine "Keine Ergebnisse"-Karte.

    Args:
        on_reset: Optional Callback für Reset-Button

    Returns:
        Container mit No-Results-State
    """
    controls = [
        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY_400),
        ft.Text("Keine Meldungen gefunden", weight=ft.FontWeight.W_600),
        ft.Text("Versuche andere Suchkriterien", color=ft.Colors.GREY_700),
    ]
    
    if on_reset:
        controls.append(ft.TextButton("Filter zurücksetzen", on_click=on_reset))

    return soft_card(
        ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        elev=1,
        pad=24,
    )


def render_items(
    items: List[Dict[str, Any]],
    view_mode: str,
    list_view: ft.Column,
    grid_view: ft.ResponsiveRow,
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.IconButton], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_reset: Optional[Callable] = None,
) -> None:
    """Rendert Post-Items in List- oder Grid-Ansicht.

    Args:
        items: Liste von Post-Dictionaries
        view_mode: "list" oder "grid"
        list_view: Column für Listen-Ansicht
        grid_view: ResponsiveRow für Grid-Ansicht
        page: Flet Page-Instanz
        on_favorite_click: Callback für Favoriten-Klick
        on_card_click: Callback für Card-Klick
        on_contact_click: Optional Callback für Kontakt-Klick
        on_reset: Optional Callback für Reset-Button
    """
    if not items:
        no_results = create_no_results_card(on_reset=on_reset)
        list_view.controls = [no_results]
        grid_view.controls = []
        list_view.visible = True
        grid_view.visible = False
        page.update()
        return

    if view_mode == "grid":
        grid_view.controls = [
            build_small_card(
                item=it,
                page=page,
                on_favorite_click=on_favorite_click,
                on_card_click=on_card_click,
            )
            for it in items
        ]
        list_view.controls = []
        list_view.visible = False
        grid_view.visible = True
    else:
        list_view.controls = [
            build_big_card(
                item=it,
                page=page,
                on_favorite_click=on_favorite_click,
                on_card_click=on_card_click,
                on_contact_click=on_contact_click,
            )
            for it in items
        ]
        grid_view.controls = []
        list_view.visible = True
        grid_view.visible = False

    page.update()

