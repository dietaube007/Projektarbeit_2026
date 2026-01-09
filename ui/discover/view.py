"""
Discover-View mit Listen- und Kartendarstellung.

Enthält UI-Komposition und koordiniert Discover-Features.
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
from ui.components import show_error_dialog, show_login_required_snackbar, create_empty_state_card

from .filter_components import (
    create_search_field,
    create_dropdown,
    create_farben_header,
    create_reset_button,
    create_view_toggle,
    create_sort_dropdown,
)
from .post_card_components import show_detail_dialog
from .features.favorites import handle_toggle_favorite
from .features.search import handle_load_posts, handle_render_items
from .features.filters import reset_filters, apply_saved_search_filters, collect_current_filters
from .features.references import load_and_populate_references, update_breeds_dropdown
from .features.saved_search import show_save_search_dialog

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

        # Filter-Status
        self.selected_farben: list[int] = []
        self.farben_panel_visible = False
        self.view_mode = "list"
        self.current_items: list[dict] = []

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

        self._all_breeds: Dict[int, list] = {}

        self._init_ui_elements()
        self.page.run_task(self._load_references)

    # ─────────────────────────────────────────────────────────────
    # User / Auth
    # ─────────────────────────────────────────────────────────────

    def refresh_user(self) -> None:
        """Aktualisiert die aktuelle User-ID.
        
        Kann von außen (z.B. nach Login) aufgerufen werden, um den User-Status
        zu aktualisieren.
        """
        self.current_user_id = self.profile_service.get_user_id()

    # ─────────────────────────────────────────────────────────────
    # Favoriten
    # ─────────────────────────────────────────────────────────────

    def _toggle_favorite(self, item: Dict[str, Any], icon_button: ft.IconButton) -> None:
        """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie.
        
        Args:
            item: Post-Dictionary
            icon_button: IconButton-Widget das aktualisiert werden soll
        """
        self.refresh_user()
        handle_toggle_favorite(
            favorites_service=self.favorites_service,
            item=item,
            icon_button=icon_button,
            page=self.page,
            current_user_id=self.current_user_id,
            on_login_required=self.on_login_required,
        )

    # ─────────────────────────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────────────────────────

    async def load_posts(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen + Favoritenstatus.
        
        Sammelt alle aktiven Filterwerte und ruft handle_load_posts auf.
        """
        # Sicherstellen, dass UI-Elemente initialisiert sind
        if self._filter_typ is None:
            return
        
        self.refresh_user()

        filters = {
            "typ": self._get_filter_value(self._filter_typ),
            "art": self._get_filter_value(self._filter_art),
            "geschlecht": self._get_filter_value(self._filter_geschlecht),
            "rasse": self._get_filter_value(self._filter_rasse),
        }

        sort_option = self._get_filter_value(self._sort_dropdown, "created_at_desc")

        handle_load_posts(
            search_service=self.search_service,
            favorites_service=self.favorites_service,
            filters=filters,
            search_query=self._search_q.value.strip() if self._search_q.value else None,
            selected_colors=self.selected_farben,
            sort_option=sort_option,
            current_user_id=self.current_user_id,
            list_view=self._list_view,
            grid_view=self._grid_view,
            empty_state_card=self._empty_state_card,
            page=self.page,
            on_render=self._render_items,
        )

    def _render_items(self, items: list[dict]) -> None:
        """Rendert die geladenen Items in der aktuellen View-Mode.
        
        Args:
            items: Liste von Post-Dictionaries die gerendert werden sollen
        """
        self.current_items = items
        handle_render_items(
            items=items,
            view_mode=self.view_mode,
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
        """Zeigt den Detail-Dialog für eine Meldung.
        
        Args:
            item: Post-Dictionary mit allen Daten
        """
        show_detail_dialog(
            item=item,
            page=self.page,
            on_contact_click=self.on_contact_click,
            on_favorite_click=self._toggle_favorite,
            profile_service=self.profile_service,
        )

    # ─────────────────────────────────────────────────────────────
    # References
    # ─────────────────────────────────────────────────────────────

    async def _load_references(self) -> None:
        """Lädt alle Referenzen und befüllt die Dropdowns."""
        try:
            self._all_breeds = load_and_populate_references(
                ref_service=self.ref_service,
                filter_typ=self._filter_typ,
                filter_art=self._filter_art,
                filter_geschlecht=self._filter_geschlecht,
                filter_rasse=self._filter_rasse,
                farben_filter_container=self._farben_filter_container,
                selected_colors=self.selected_farben,
                on_color_change_callback=self._on_filter_change,
                page=self.page,
            )
            self._update_rassen_dropdown()
            self.page.update()
        except Exception as ex:
            logger.error(f"Fehler beim Laden der Referenzen: {ex}", exc_info=True)
            show_error_dialog(
                self.page,
                "Fehler beim Laden",
                "Die Filteroptionen konnten nicht geladen werden. Bitte versuchen Sie es später erneut."
            )

    def _on_tierart_change(self, e: ft.ControlEvent) -> None:
        """Wird aufgerufen wenn die Tierart geändert wird."""
        self._update_rassen_dropdown()

    def _update_rassen_dropdown(self) -> None:
        """Aktualisiert das Rassen-Dropdown basierend auf der ausgewählten Tierart."""
        if self._all_breeds:
            update_breeds_dropdown(
                filter_art=self._filter_art,
                filter_rasse=self._filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
            )

    def _toggle_farben_panel(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Öffnet oder schließt das Farben-Panel."""
        self.farben_panel_visible = not self.farben_panel_visible
        self._farben_panel.visible = self.farben_panel_visible
        self._farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()

    # ─────────────────────────────────────────────────────────────
    # Filter
    # ─────────────────────────────────────────────────────────────

    def _reset_filters(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Setzt alle Filter zurück."""
        reset_filters(
            search_field=self._search_q,
            filter_typ=self._filter_typ,
            filter_art=self._filter_art,
            filter_geschlecht=self._filter_geschlecht,
            filter_rasse=self._filter_rasse,
            sort_dropdown=self._sort_dropdown,
            selected_colors=self.selected_farben,
            color_checkboxes_container=self._farben_filter_container,
            page=self.page,
            on_reset=self._on_filter_change,
        )

    def apply_saved_search(self, search: Dict[str, Any]) -> None:
        """Wendet einen gespeicherten Suchauftrag auf die Filter an."""
        apply_saved_search_filters(
            search=search,
            search_field=self._search_q,
            filter_typ=self._filter_typ,
            filter_art=self._filter_art,
            filter_geschlecht=self._filter_geschlecht,
            filter_rasse=self._filter_rasse,
            selected_colors=self.selected_farben,
            color_checkboxes_container=self._farben_filter_container,
            update_breeds_callback=self._update_rassen_dropdown,
            page=self.page,
        )
        self.page.run_task(self.load_posts)

    def _show_save_search_dialog(self, e: Optional[ft.ControlEvent] = None) -> None:
        """Zeigt Dialog zum Speichern der aktuellen Suche."""
        if not self.current_user_id:
            if self.on_save_search_login_required:
                self.on_save_search_login_required()
            elif self.on_login_required:
                self.on_login_required()
            else:
                show_login_required_snackbar(
                    self.page,
                    "Bitte melden Sie sich an, um Suchaufträge zu speichern."
                )
            return

        current_filters = collect_current_filters(
            search_field=self._search_q,
            filter_typ=self._filter_typ,
            filter_art=self._filter_art,
            filter_geschlecht=self._filter_geschlecht,
            filter_rasse=self._filter_rasse,
            selected_colors=self.selected_farben,
        )

        show_save_search_dialog(
            page=self.page,
            saved_search_service=self.saved_search_service,
            current_filters=current_filters,
        )

    # ─────────────────────────────────────────────────────────────
    # UI-Hilfsmethoden
    # ─────────────────────────────────────────────────────────────

    def _on_filter_change(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Wird aufgerufen wenn ein Filter geändert wird.
        
        Lädt die Posts neu mit aktualisierten Filterwerten.
        """
        self.page.run_task(self.load_posts)

    def _get_filter_value(self, dropdown: ft.Dropdown, default: str = "alle") -> str:
        """Holt den Wert aus einem Dropdown mit Fallback.
        
        Args:
            dropdown: Dropdown-Widget
            default: Standard-Wert wenn None oder leer
        
        Returns:
            Dropdown-Wert oder default
        """
        return dropdown.value if dropdown.value else default

    def _on_view_change(self, e: ft.ControlEvent) -> None:
        """Wird aufgerufen wenn die View-Ansicht geändert wird.
        
        Wechselt zwischen Listen- und Grid-Ansicht und rendert die aktuellen
        Items in der neuen Ansicht.
        
        Args:
            e: ControlEvent vom View-Toggle
        """
        val = next(iter(e.control.selected), "list")
        self.view_mode = val
        self._render_items(self.current_items)

    # ─────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────

    def _init_ui_elements(self) -> None:
        """Initialisiert alle UI-Elemente."""
        self._search_q = create_search_field(
            on_change=self._on_filter_change
        )

        self._filter_typ = create_dropdown(
            label="Kategorie",
            on_change=self._on_filter_change,
        )

        self._filter_art = create_dropdown(
            label="Tierart",
            on_change=self._on_tierart_change,
        )

        self._filter_geschlecht = create_dropdown(
            label="Geschlecht",
            on_change=self._on_filter_change,
            initial_options=[
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ],
        )

        self._filter_rasse = create_dropdown(
            label="Rasse",
            on_change=self._on_filter_change,
        )

        self._farben_filter_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self._farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
        self._farben_panel = ft.Container(
            content=self._farben_filter_container,
            padding=12,
            visible=False,
        )

        self._farben_header = create_farben_header(
            toggle_icon=self._farben_toggle_icon,
            on_click=self._toggle_farben_panel,
        )

        self._sort_dropdown = create_sort_dropdown(
            on_change=self._on_filter_change
        )

        self._reset_btn = create_reset_button(on_click=self._reset_filters)
        self._save_search_btn = ft.TextButton(
            "Suche speichern",
            icon=ft.Icons.BOOKMARK_ADD_OUTLINED,
            on_click=self._show_save_search_dialog,
        )

        self._view_toggle = create_view_toggle(on_change=self._on_view_change)

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
