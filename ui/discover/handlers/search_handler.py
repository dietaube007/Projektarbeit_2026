"""
Search-Handler: UI-Handler für Post-Suche und Rendering.
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional, List, Dict, Any
import flet as ft

from utils.logging_config import get_logger
from services.posts import SearchService, FavoritesService
from ui.shared_components import create_loading_indicator, create_no_results_card

logger = get_logger(__name__)

LOADING_MELDUNGEN_TEXT = "Meldungen werden geladen…"


def _fetch_posts_sync(
    search_service: SearchService,
    favorites_service: FavoritesService,
    filters: Dict[str, Any],
    search_query: Optional[str],
    selected_colors: List[int],
    sort_option: str,
    current_user_id: Optional[str],
    location_lat: Optional[float] = None,
    location_lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    location_text_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lädt Meldungen synchron (für asyncio.to_thread). Gibt Items zurück."""
    favorite_ids = favorites_service.get_favorite_ids(current_user_id) if current_user_id else set()
    return search_service.search_posts(
        filters=filters,
        search_query=search_query,
        selected_colors=set(selected_colors) if selected_colors else None,
        sort_option=sort_option,
        favorite_ids=favorite_ids,
        location_lat=location_lat,
        location_lon=location_lon,
        radius_km=radius_km,
        location_text_filter=location_text_filter,
    )


def handle_render_items(
    items: List[Dict[str, Any]],
    list_view: ft.Column,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.IconButton], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Rendert Post-Items in der Listen-Ansicht.
    
    Args:
        items: Liste von Post-Dictionaries
        list_view: Column für Listen-Ansicht
        empty_state_card: Container für Empty-State
        page: Flet Page-Instanz
        on_favorite_click: Callback für Favoriten-Klick
        on_card_click: Callback für Card-Klick
        on_contact_click: Optional Callback für Kontakt-Klick
        supabase: Optional Supabase-Client für Kommentare
        profile_service: Optional ProfileService für Kommentare
        on_comment_login_required: Optional Callback wenn Login zum Kommentieren erforderlich
    """
    try:
        if getattr(page, "_theme_listeners", None) is not None:
            page._theme_listeners.clear()
        if not items:
            no_results = create_no_results_card()
            list_view.controls = [no_results]
            list_view.visible = True
            page.update()
            return

        # Lazy import um Circular Import zu vermeiden
        from ..components.post_card_components import build_big_card
        
        list_view.controls = [
            build_big_card(
                item=it,
                page=page,
                on_favorite_click=on_favorite_click,
                on_card_click=on_card_click,
                on_contact_click=on_contact_click,
                supabase=supabase,
                profile_service=profile_service,
                on_comment_login_required=on_comment_login_required,
            )
            for it in items
        ]
        list_view.visible = True

        page.update()
    except Exception as e:
        logger.error(f"Fehler in handle_render_items: {e}", exc_info=True)
        list_view.controls = [empty_state_card]
        page.update()


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler
# ─────────────────────────────────────────────────────────────

async def handle_view_load_posts(
    search_service: SearchService,
    favorites_service: FavoritesService,
    search_field: ft.TextField,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    sort_dropdown: ft.Dropdown,
    selected_colors: list[int],
    current_user_id: Optional[str],
    list_view: ft.Column,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_render: Callable[[list[dict]], None],
    get_filter_value: Callable[[ft.Dropdown, str], str],
    location_lat: Optional[float] = None,
    location_lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    location_text_filter: Optional[str] = None,
) -> None:
    """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen (View-Wrapper).
    
    Args:
        search_service: SearchService-Instanz
        favorites_service: FavoritesService-Instanz
        search_field: Suchfeld
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        sort_dropdown: Sortier-Dropdown
        selected_colors: Liste der ausgewählten Farb-IDs
        current_user_id: Aktuelle User-ID (None wenn nicht eingeloggt)
        list_view: Column für Listen-Ansicht
        empty_state_card: Container für Empty-State
        page: Flet Page-Instanz
        on_render: Callback zum Rendern der Items
        get_filter_value: Funktion zum Abrufen von Dropdown-Werten
        location_lat: Optional Breitengrad des Suchzentrums
        location_lon: Optional Laengengrad des Suchzentrums
        radius_km: Optional Umkreis in Kilometern
        location_text_filter: Optional Stadtname fuer "Ganzer Ort"-Filter
    """
    if filter_typ is None:
        return

    filters = {
        "typ": get_filter_value(filter_typ),
        "art": get_filter_value(filter_art),
        "geschlecht": get_filter_value(filter_geschlecht),
        "rasse": get_filter_value(filter_rasse),
    }
    sort_option = get_filter_value(sort_dropdown, "created_at_desc")
    search_query = search_field.value.strip() if search_field.value else None

    loading_indicator = create_loading_indicator(text=LOADING_MELDUNGEN_TEXT)
    list_view.controls = [loading_indicator]
    list_view.visible = True
    page.update()
    await asyncio.sleep(0)

    try:
        items = await asyncio.to_thread(
            _fetch_posts_sync,
            search_service=search_service,
            favorites_service=favorites_service,
            filters=filters,
            search_query=search_query,
            selected_colors=selected_colors,
            sort_option=sort_option,
            current_user_id=current_user_id,
            location_lat=location_lat,
            location_lon=location_lon,
            radius_km=radius_km,
            location_text_filter=location_text_filter,
        )
        on_render(items)
    except Exception as ex:
        logger.error(f"Fehler beim Laden der Meldungen: {ex}", exc_info=True)
        list_view.controls = [empty_state_card]
        list_view.visible = True
        page.update()


def handle_view_render_items(
    items: list[dict],
    current_items: dict,  
    list_view: ft.Column,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.IconButton], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Rendert die geladenen Items in der Listen-Ansicht (View-Wrapper).
    
    Args:
        items: Liste von Post-Dictionaries die gerendert werden sollen
        current_items: Dictionary mit "items" key (wird aktualisiert)
        list_view: Column für Listen-Ansicht
        empty_state_card: Container für Empty-State
        page: Flet Page-Instanz
        on_favorite_click: Callback für Favoriten-Klick
        on_card_click: Callback für Card-Klick
        on_contact_click: Optional Callback für Kontakt-Klick
        supabase: Optional Supabase-Client für Kommentare
        profile_service: Optional ProfileService für Kommentare
        on_comment_login_required: Optional Callback wenn Login zum Kommentieren erforderlich
    """
    current_items["items"] = items
    handle_render_items(
        items=items,
        list_view=list_view,
        empty_state_card=empty_state_card,
        page=page,
        on_favorite_click=on_favorite_click,
        on_card_click=on_card_click,
        on_contact_click=on_contact_click,
        supabase=supabase,
        profile_service=profile_service,
        on_comment_login_required=on_comment_login_required,
    )


def handle_view_show_detail_dialog(
    item: Dict[str, Any],
    page: ft.Page,
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_favorite_click: Optional[Callable[[Dict[str, Any], ft.IconButton], None]] = None,
    profile_service=None,
    supabase=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Zeigt den Detail-Dialog für eine Meldung inkl. Kommentare (View-Wrapper)."""
    from ..components.post_card_components import show_detail_dialog
    show_detail_dialog(
        item=item,
        page=page,
        on_contact_click=on_contact_click,
        on_favorite_click=on_favorite_click,
        profile_service=profile_service,
        supabase=supabase,
        on_comment_login_required=on_comment_login_required,
    )


