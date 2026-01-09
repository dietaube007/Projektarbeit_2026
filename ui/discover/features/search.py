"""
Search-Feature: UI und Logik für Post-Suche und Rendering.
"""

from __future__ import annotations

from typing import Callable, Optional, List, Dict, Any
import flet as ft

from utils.logging_config import get_logger
from services.posts import SearchService, FavoritesService
from ui.theme import soft_card
from ui.components import create_loading_indicator, create_no_results_card
from ..post_card_components import build_small_card, build_big_card

logger = get_logger(__name__)


def handle_load_posts(
    search_service: SearchService,
    favorites_service: FavoritesService,
    filters: Dict[str, Any],
    search_query: Optional[str],
    selected_colors: List[int],
    sort_option: str,
    current_user_id: Optional[str],
    list_view: ft.Column,
    grid_view: ft.ResponsiveRow,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_render: Callable[[List[Dict[str, Any]]], None],
) -> None:
    """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen + Favoritenstatus.
    
    Args:
        search_service: SearchService-Instanz
        favorites_service: FavoritesService-Instanz
        filters: Dictionary mit Filterwerten (typ, art, geschlecht, rasse)
        search_query: Optionaler Suchbegriff
        selected_colors: Liste der ausgewählten Farb-IDs
        sort_option: Sortier-Option
        current_user_id: Aktuelle User-ID (None wenn nicht eingeloggt)
        list_view: Column für Listen-Ansicht
        grid_view: ResponsiveRow für Grid-Ansicht
        empty_state_card: Container für Empty-State
        page: Flet Page-Instanz
        on_render: Callback zum Rendern der Items
    """
    loading_indicator = create_loading_indicator()
    list_view.controls = [loading_indicator]
    grid_view.controls = []
    list_view.visible = True
    grid_view.visible = False
    page.update()

    try:
        # Favoriten-IDs laden (für Markierung)
        favorite_ids = favorites_service.get_favorite_ids(current_user_id) if current_user_id else set()

        # Posts über SearchService laden
        items = search_service.search_posts(
            filters=filters,
            search_query=search_query,
            selected_colors=set(selected_colors) if selected_colors else None,
            sort_option=sort_option,
            favorite_ids=favorite_ids,
        )

        on_render(items)

    except Exception as ex:
        logger.error(f"Fehler beim Laden der Daten: {ex}", exc_info=True)
        list_view.controls = [empty_state_card]
        grid_view.controls = []
        list_view.visible = True
        grid_view.visible = False
        page.update()


def handle_render_items(
    items: List[Dict[str, Any]],
    view_mode: str,
    list_view: ft.Column,
    grid_view: ft.ResponsiveRow,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.IconButton], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
) -> None:
    """Rendert Post-Items in List- oder Grid-Ansicht.
    
    Args:
        items: Liste von Post-Dictionaries
        view_mode: "list" oder "grid"
        list_view: Column für Listen-Ansicht
        grid_view: ResponsiveRow für Grid-Ansicht
        empty_state_card: Container für Empty-State
        page: Flet Page-Instanz
        on_favorite_click: Callback für Favoriten-Klick
        on_card_click: Callback für Card-Klick
        on_contact_click: Optional Callback für Kontakt-Klick
        supabase: Optional Supabase-Client für Kommentare
        profile_service: Optional ProfileService für Kommentare
    """
    try:
        if not items:
            no_results = create_no_results_card()
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
                    supabase=supabase,
                    profile_service=profile_service,
                )
                for it in items
            ]
            grid_view.controls = []
            list_view.visible = True
            grid_view.visible = False

        page.update()
    except Exception as e:
        logger.error(f"Fehler in handle_render_items: {e}", exc_info=True)
        list_view.controls = [empty_state_card]
        page.update()
