"""
Discover-View mit Listen- und Kartendarstellung.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft
from supabase import Client

from services.posts.references import ReferenceService
from services.posts import SavedSearchService, FavoritesService, SearchService
from services.account import ProfileService
from utils.logging_config import get_logger
from ui.theme import soft_card
from ui.shared_components import show_error_dialog, show_login_required_snackbar, create_empty_state_card

from .components import (
    create_search_field,
    create_dropdown,
    create_farben_header,
    create_reset_button,
    create_view_toggle,
    create_sort_dropdown,
)
from .handlers import (
    handle_view_toggle_favorite,
    handle_view_load_posts,
    handle_view_render_items,
    handle_view_show_detail_dialog,
    handle_view_reset_filters,
    handle_view_apply_saved_search,
    handle_view_show_save_search_dialog,
    handle_view_filter_change,
    handle_view_get_filter_value,
    handle_view_toggle_farben_panel,
    handle_view_load_references,
    handle_view_tierart_change,
    handle_view_update_rassen_dropdown,
    handle_view_view_change,
)

logger = get_logger(__name__)


class DiscoverView:
    """Discover-View mit Listen- und Kartendarstellung."""

    def __init__(
        self,
        page: ft.Page,
        sb: Client,
        on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_melden_click: Optional[Callable[[], None]] = None,
        on_login_required: Optional[Callable[[], None]] = None,
        on_save_search_login_required: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialisiert die DiscoverView."""
        self.page = page
        self.sb = sb
        self.on_contact_click = on_contact_click
        self.on_melden_click = on_melden_click
        self.on_login_required = on_login_required
        self.on_save_search_login_required = on_save_search_login_required

        # Services
        self.ref_service = ReferenceService(self.sb)
        self.saved_search_service = SavedSearchService(self.sb)
        self.favorites_service = FavoritesService(self.sb)
        self.search_service = SearchService(self.sb)
        self.profile_service = ProfileService(self.sb)

        # Filter-Status (als dict für Mutability in Handlern)
        self.selected_farben: list[int] = []
        self.farben_panel_visible = {"visible": False}
        self.view_mode = {"mode": "list"}
        self.current_items = {"items": []}

        # User
        self.current_user_id: Optional[str] = None
        self.refresh_user()

        # UI-Komponenten
        self._search_q: Optional[ft.TextField] = None
        self._filter_typ: Optional[ft.Dropdown] = None
        self._filter_art: Optional[ft.Dropdown] = None
        self._filter_geschlecht: Optional[ft.Dropdown] = None
        self._filter_rasse: Optional[ft.Dropdown] = None
        self._farben_filter_container: Optional[ft.ResponsiveRow] = None
        self._farben_toggle_icon: Optional[ft.Icon] = None
        self._farben_panel: Optional[ft.Container] = None
        self._farben_header: Optional[ft.Container] = None
        self._sort_dropdown: Optional[ft.Dropdown] = None
        self._reset_btn: Optional[ft.TextButton] = None
        self._save_search_btn: Optional[ft.TextButton] = None
        self._view_toggle: Optional[ft.SegmentedButton] = None
        self._list_view: Optional[ft.Column] = None
        self._grid_view: Optional[ft.ResponsiveRow] = None
        self._empty_state_card: Optional[ft.Container] = None
        self.search_row = ft.ResponsiveRow(controls=[], spacing=10, run_spacing=10) 

        self._all_breeds = {"breeds": {}}

        self._init_ui_elements()
        self.page.run_task(self._load_references)

    # ─────────────────────────────────────────────────────────────
    # User / Auth
    # ─────────────────────────────────────────────────────────────

    def refresh_user(self) -> str:
        """Aktualisiert die aktuelle User-ID und gibt sie zurück.
        
        Kann von außen (z.B. nach Login) aufgerufen werden, um den User-Status
        zu aktualisieren.
        
        Returns:
            Aktuelle User-ID oder None
        """
        self.current_user_id = self.profile_service.get_user_id()
        return self.current_user_id

    # ─────────────────────────────────────────────────────────────
    # Init UI Elements
    # ─────────────────────────────────────────────────────────────

    def _init_ui_elements(self) -> None:
        """Initialisiert alle UI-Elemente."""
        # Callbacks für Filter-Änderungen
        def on_filter_change(_: Optional[ft.ControlEvent] = None) -> None:
            handle_view_filter_change(
                page=self.page,
                load_posts_callback=self.load_posts,
            )
        
        def on_tierart_change(e: ft.ControlEvent) -> None:
            handle_view_tierart_change(
                filter_art=self._filter_art,
                filter_rasse=self._filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
                update_breeds_callback=lambda: handle_view_update_rassen_dropdown(
                    filter_art=self._filter_art,
                    filter_rasse=self._filter_rasse,
                    all_breeds=self._all_breeds,
                    page=self.page,
                ),
            )
        
        def on_reset_filters(_: Optional[ft.ControlEvent] = None) -> None:
            handle_view_reset_filters(
                search_field=self._search_q,
                filter_typ=self._filter_typ,
                filter_art=self._filter_art,
                filter_geschlecht=self._filter_geschlecht,
                filter_rasse=self._filter_rasse,
                sort_dropdown=self._sort_dropdown,
                selected_colors=self.selected_farben,
                color_checkboxes_container=self._farben_filter_container,
                page=self.page,
                on_reset=on_filter_change,
            )
        
        def on_toggle_farben_panel(_: Optional[ft.ControlEvent] = None) -> None:
            handle_view_toggle_farben_panel(
                farben_panel=self._farben_panel,
                farben_toggle_icon=self._farben_toggle_icon,
                farben_panel_visible=self.farben_panel_visible,
                page=self.page,
            )
        
        def on_view_change(e: ft.ControlEvent) -> None:
            handle_view_view_change(
                e=e,
                view_mode=self.view_mode,
                current_items=self.current_items,
                list_view=self._list_view,
                grid_view=self._grid_view,
                empty_state_card=self._empty_state_card,
                page=self.page,
                on_favorite_click=self._toggle_favorite,
                on_card_click=self._show_detail_dialog,
                on_contact_click=self.on_contact_click,
                supabase=self.sb,
                profile_service=self.profile_service,
            )
        
        def on_show_save_search_dialog(e: Optional[ft.ControlEvent] = None) -> None:
            handle_view_show_save_search_dialog(
                page=self.page,
                saved_search_service=self.saved_search_service,
                search_field=self._search_q,
                filter_typ=self._filter_typ,
                filter_art=self._filter_art,
                filter_geschlecht=self._filter_geschlecht,
                filter_rasse=self._filter_rasse,
                selected_colors=self.selected_farben,
                current_user_id=self.current_user_id,
                on_save_search_login_required=self.on_save_search_login_required,
                on_login_required=self.on_login_required,
            )
        
        self._search_q = create_search_field(
            on_change=on_filter_change
        )

        self._filter_typ = create_dropdown(
            label="Kategorie",
            on_change=on_filter_change,
        )

        self._filter_art = create_dropdown(
            label="Tierart",
            on_change=on_tierart_change,
        )

        self._filter_geschlecht = create_dropdown(
            label="Geschlecht",
            on_change=on_filter_change,
            initial_options=[
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ],
        )

        self._filter_rasse = create_dropdown(
            label="Rasse",
            on_change=on_filter_change,
        )

        self._farben_filter_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self._farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
        self._farben_panel = ft.Container(
            content=self._farben_filter_container,
            padding=12,
            visible=self.farben_panel_visible["visible"],
        )

        self._farben_header = create_farben_header(
            toggle_icon=self._farben_toggle_icon,
            on_click=on_toggle_farben_panel,
        )

        self._sort_dropdown = create_sort_dropdown(
            on_change=on_filter_change
        )

        self._reset_btn = create_reset_button(on_click=on_reset_filters)
        self._save_search_btn = ft.TextButton(
            "Suche speichern",
            icon=ft.Icons.BOOKMARK_ADD_OUTLINED,
            on_click=on_show_save_search_dialog,
        )

        self._view_toggle = create_view_toggle(on_change=on_view_change)

        self._list_view = ft.Column(spacing=14, expand=True)
        self._grid_view = ft.ResponsiveRow(spacing=12, run_spacing=12, visible=False)
        
        self._empty_state_card = create_empty_state_card(
            message="Noch keine Meldungen",
            subtitle="",
        )
        
        self._list_view.controls = [self._empty_state_card]
        self._list_view.visible = True

        if all([
            self._search_q is not None,
            self._filter_typ is not None,
            self._filter_art is not None,
            self._filter_geschlecht is not None,
            self._filter_rasse is not None,
            self._reset_btn is not None,
            self._save_search_btn is not None,
            self._farben_header is not None,
            self._farben_panel is not None,
        ]):
            self.search_row = ft.ResponsiveRow(
                controls=[
                    ft.Container(self._search_q, col={"xs": 12, "md": 5}),
                    ft.Container(self._filter_typ, col={"xs": 6, "md": 2}),
                    ft.Container(self._filter_art, col={"xs": 6, "md": 2}),
                    ft.Container(self._filter_geschlecht, col={"xs": 6, "md": 2}),
                    ft.Container(self._filter_rasse, col={"xs": 6, "md": 1}),
                    ft.Container(
                        ft.Row([self._reset_btn, self._save_search_btn], spacing=8),
                        col={"xs": 12, "md": 12},
                    ),
                    ft.Container(self._farben_header, col={"xs": 12, "md": 12}),
                    ft.Container(self._farben_panel, col={"xs": 12, "md": 12}),
                ],
                spacing=10,
                run_spacing=10,
            )
        else:
            self.search_row = ft.ResponsiveRow(controls=[], spacing=10, run_spacing=10)
    
    # ─────────────────────────────────────────────────────────────
    # Private Methoden für Handler-Callbacks
    # ─────────────────────────────────────────────────────────────
    
    async def _load_references(self) -> None:
        """Lädt alle Referenzen und befüllt die Dropdowns."""
        def on_color_change_callback() -> None:
            handle_view_filter_change(
                page=self.page,
                load_posts_callback=self.load_posts,
            )
        
        def update_breeds_callback() -> None:
            handle_view_update_rassen_dropdown(
                filter_art=self._filter_art,
                filter_rasse=self._filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
            )
        
        await handle_view_load_references(
            ref_service=self.ref_service,
            filter_typ=self._filter_typ,
            filter_art=self._filter_art,
            filter_geschlecht=self._filter_geschlecht,
            filter_rasse=self._filter_rasse,
            farben_filter_container=self._farben_filter_container,
            selected_colors=self.selected_farben,
            all_breeds=self._all_breeds,
            page=self.page,
            on_color_change_callback=on_color_change_callback,
            update_breeds_callback=update_breeds_callback,
        )
    
    async def load_posts(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen."""
        self.refresh_user()
        
        await handle_view_load_posts(
            search_service=self.search_service,
            favorites_service=self.favorites_service,
            search_field=self._search_q,
            filter_typ=self._filter_typ,
            filter_art=self._filter_art,
            filter_geschlecht=self._filter_geschlecht,
            filter_rasse=self._filter_rasse,
            sort_dropdown=self._sort_dropdown,
            selected_colors=self.selected_farben,
            current_user_id=self.current_user_id,
            list_view=self._list_view,
            grid_view=self._grid_view,
            empty_state_card=self._empty_state_card,
            page=self.page,
            on_render=self._render_items,
            get_filter_value=handle_view_get_filter_value,
        )
    
    def _render_items(self, items: list[dict]) -> None:
        """Rendert die geladenen Items in der aktuellen View-Mode."""
        handle_view_render_items(
            items=items,
            view_mode=self.view_mode["mode"],
            current_items=self.current_items,
            list_view=self._list_view,
            grid_view=self._grid_view,
            empty_state_card=self._empty_state_card,
            page=self.page,
            on_favorite_click=self._toggle_favorite,
            on_card_click=self._show_detail_dialog,
            on_contact_click=self.on_contact_click,
            supabase=self.sb,
            profile_service=self.profile_service,
        )
    
    def _show_detail_dialog(self, item: Dict[str, Any]) -> None:
        """Zeigt den Detail-Dialog für eine Meldung."""
        handle_view_show_detail_dialog(
            item=item,
            page=self.page,
            on_contact_click=self.on_contact_click,
            on_favorite_click=self._toggle_favorite,
            profile_service=self.profile_service,
        )
    
    def _toggle_favorite(self, item: Dict[str, Any], icon_button: ft.IconButton) -> None:
        """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie."""
        handle_view_toggle_favorite(
            favorites_service=self.favorites_service,
            item=item,
            icon_button=icon_button,
            page=self.page,
            current_user_id=self.current_user_id,
            on_login_required=self.on_login_required,
            refresh_user_callback=self.refresh_user,
        )
    
    def apply_saved_search(self, search: Dict[str, Any]) -> None:
        """Wendet einen gespeicherten Suchauftrag auf die Filter an."""
        def update_breeds_callback() -> None:
            handle_view_update_rassen_dropdown(
                filter_art=self._filter_art,
                filter_rasse=self._filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
            )
        
        handle_view_apply_saved_search(
            search=search,
            search_field=self._search_q,
            filter_typ=self._filter_typ,
            filter_art=self._filter_art,
            filter_geschlecht=self._filter_geschlecht,
            filter_rasse=self._filter_rasse,
            selected_colors=self.selected_farben,
            color_checkboxes_container=self._farben_filter_container,
            update_breeds_callback=update_breeds_callback,
            load_posts_callback=self.load_posts,
            page=self.page,
        )

    # ─────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────

    def build(self) -> ft.Column:
        """Erstellt und gibt die komplette Discover-UI zurück."""

        view_toggle_row = ft.Container(
            content=ft.Row([self._view_toggle], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.only(left=4, top=12, bottom=8),
        )

        content_container = ft.Container(
            padding=4,
            content=ft.Column([
                view_toggle_row,
                self._list_view,
                self._grid_view,
            ], spacing=8),
        )

        map_placeholder = ft.Column(
            [
                ft.Container(height=50),
                ft.Icon(ft.Icons.MAP_OUTLINED, size=64, color=ft.Colors.GREY_400),
                ft.Text("Kartenansicht", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_600),
                ft.Text("Kommt bald!", color=ft.Colors.GREY_500),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        map_container = ft.Container(padding=4, content=map_placeholder, expand=True)

        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Meldungen", icon=ft.Icons.PETS, content=content_container),
                ft.Tab(text="Karte", icon=ft.Icons.MAP, content=map_container),
            ],
            expand=True,
            animation_duration=250,
        )

        self.page.run_task(self.load_posts)

        return ft.Column([tabs], spacing=14, expand=True)
