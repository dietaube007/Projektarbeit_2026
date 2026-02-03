"""
Search-Handler: UI-Handler für Post-Suche und Rendering.
"""

from __future__ import annotations

from typing import Callable, Optional, List, Dict, Any
import flet as ft

from utils.logging_config import get_logger
from services.posts import SearchService, FavoritesService
from ui.shared_components import create_loading_indicator, create_no_results_card

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
    on_comment_login_required: Optional[Callable[[], None]] = None,
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
        on_comment_login_required: Optional Callback wenn Login zum Kommentieren erforderlich
    """
    try:
        if getattr(page, "_theme_listeners", None) is not None:
            page._theme_listeners.clear()
        if not items:
            no_results = create_no_results_card()
            list_view.controls = [no_results]
            grid_view.controls = []
            list_view.visible = True
            grid_view.visible = False
            page.update()
            return

        # Lazy import um Circular Import zu vermeiden
        from ..components.post_card_components import build_small_card, build_big_card
        
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
                    on_comment_login_required=on_comment_login_required,
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
    grid_view: ft.ResponsiveRow,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_render: Callable[[list[dict]], None],
    get_filter_value: Callable[[ft.Dropdown, str], str],
) -> None:
    """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen (View-Wrapper).
    
    Sammelt alle aktiven Filterwerte und ruft handle_load_posts auf.
    
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
        grid_view: ResponsiveRow für Grid-Ansicht
        empty_state_card: Container für Empty-State
        page: Flet Page-Instanz
        on_render: Callback zum Rendern der Items
        get_filter_value: Funktion zum Abrufen von Dropdown-Werten
    """
    # Sicherstellen, dass UI-Elemente initialisiert sind
    if filter_typ is None:
        return

    filters = {
        "typ": get_filter_value(filter_typ),
        "art": get_filter_value(filter_art),
        "geschlecht": get_filter_value(filter_geschlecht),
        "rasse": get_filter_value(filter_rasse),
    }

    sort_option = get_filter_value(sort_dropdown, "created_at_desc")

    handle_load_posts(
        search_service=search_service,
        favorites_service=favorites_service,
        filters=filters,
        search_query=search_field.value.strip() if search_field.value else None,
        selected_colors=selected_colors,
        sort_option=sort_option,
        current_user_id=current_user_id,
        list_view=list_view,
        grid_view=grid_view,
        empty_state_card=empty_state_card,
        page=page,
        on_render=on_render,
    )


def handle_view_render_items(
    items: list[dict],
    view_mode: str,
    current_items: dict,  
    list_view: ft.Column,
    grid_view: ft.ResponsiveRow,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.IconButton], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Rendert die geladenen Items in der aktuellen View-Mode (View-Wrapper).
    
    Args:
        items: Liste von Post-Dictionaries die gerendert werden sollen
        view_mode: "list" oder "grid"
        current_items: Dictionary mit "items" key (wird aktualisiert)
        list_view: Column für Listen-Ansicht
        grid_view: ResponsiveRow für Grid-Ansicht
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
        view_mode=view_mode,
        list_view=list_view,
        grid_view=grid_view,
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


def handle_view_view_change(
    e: ft.ControlEvent,
    view_mode: dict,  # dict mit "mode" key für Mutability
    current_items: dict,  # dict mit "items" key
    list_view: ft.Column,
    grid_view: ft.ResponsiveRow,
    empty_state_card: ft.Container,
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.IconButton], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Wird aufgerufen wenn die View-Ansicht geändert wird (View-Wrapper).
    
    Wechselt zwischen Listen- und Grid-Ansicht und rendert die aktuellen
    Items in der neuen Ansicht.
    
    Args:
        e: ControlEvent vom View-Toggle
        view_mode: Dictionary mit "mode" key (wird aktualisiert)
        current_items: Dictionary mit "items" key
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
    val = next(iter(e.control.selected), "list")
    view_mode["mode"] = val
    
    items = current_items.get("items", [])
    handle_view_render_items(
        items=items,
        view_mode=val,
        current_items=current_items,
        list_view=list_view,
        grid_view=grid_view,
        empty_state_card=empty_state_card,
        page=page,
        on_favorite_click=on_favorite_click,
        on_card_click=on_card_click,
        on_contact_click=on_contact_click,
        supabase=supabase,
        profile_service=profile_service,
        on_comment_login_required=on_comment_login_required,
    )
