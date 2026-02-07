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
from ui.theme import get_theme_color, soft_card
from ui.shared_components import (
    create_empty_state_card,
    create_loading_indicator,
)
from app.dialogs import create_login_banner
from utils.logging_config import get_logger

logger = get_logger(__name__)

from .components import (
    create_search_field,
    create_dropdown,
    create_farben_header,
    create_reset_button,
    create_sort_dropdown,
    create_location_filter_field,
    create_radius_dropdown,
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
)


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
        on_comment_login_required: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialisiert die DiscoverView."""
        self.page = page
        self.sb = sb
        self.on_contact_click = on_contact_click
        self.on_melden_click = on_melden_click
        self.on_login_required = on_login_required
        self.on_save_search_login_required = on_save_search_login_required
        self.on_comment_login_required = on_comment_login_required

        # Services
        self.ref_service = ReferenceService(self.sb)
        self.saved_search_service = SavedSearchService(self.sb)
        self.favorites_service = FavoritesService(self.sb)
        self.search_service = SearchService(self.sb)
        self.profile_service = ProfileService(self.sb)

        # Filter-Status (als dict für Mutability in Handlern)
        self.selected_farben: list[int] = []
        self.farben_panel_visible = {"visible": False}
        self.current_items = {"items": []}
        self._has_loaded_posts = False

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
        self._list_view: Optional[ft.Column] = None
        self._empty_state_card: Optional[ft.Container] = None
        self.search_row = ft.ResponsiveRow(controls=[], spacing=10, run_spacing=10) 

        # Ort/Umkreis-Filter
        self._location_field: Optional[ft.TextField] = None
        self._radius_dropdown: Optional[ft.Dropdown] = None
        self._location_suggestions_list: Optional[ft.Column] = None
        self._location_suggestions_box: Optional[ft.Container] = None
        self._location_selected: Dict[str, Any] = {"text": None, "lat": None, "lon": None}
        self._location_query_version: int = 0
        self._location_setting_value: bool = False  # Verhindert on_change bei programmatischer Aenderung

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
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
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
            on_filter_change(e)
        
        def on_reset_filters(_: Optional[ft.ControlEvent] = None) -> None:
            self._hide_distance_sort_option()
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
                update_breeds_callback=lambda: handle_view_update_rassen_dropdown(
                    filter_art=self._filter_art,
                    filter_rasse=self._filter_rasse,
                    all_breeds=self._all_breeds,
                    page=self.page,
                ),
                location_field=self._location_field,
                radius_dropdown=self._radius_dropdown,
                location_selected=self._location_selected,
            )
        
        def on_toggle_farben_panel(_: Optional[ft.ControlEvent] = None) -> None:
            handle_view_toggle_farben_panel(
                farben_panel=self._farben_panel,
                farben_toggle_icon=self._farben_toggle_icon,
                farben_panel_visible=self.farben_panel_visible,
                page=self.page,
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
                location_selected=self._location_selected,
                radius_dropdown=self._radius_dropdown,
            )
        
        self._search_q = create_search_field(
            on_change=on_filter_change
        )

        # Ort/Umkreis-Filter initialisieren
        self._location_field = create_location_filter_field(
            on_change=lambda _: self._on_location_input_change()
        )
        self._radius_dropdown = create_radius_dropdown(
            on_change=on_filter_change
        )
        self._location_suggestions_list = ft.Column(spacing=2)
        self._location_suggestions_box = ft.Container(
            content=self._location_suggestions_list,
            visible=False,
            padding=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
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
            border_radius=8,
        )

        self._farben_header = create_farben_header(
            toggle_icon=self._farben_toggle_icon,
            on_click=on_toggle_farben_panel,
            page=self.page,  # Page übergeben für Theme-Erkennung
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

        self._list_view = ft.ResponsiveRow(spacing=14, run_spacing=14)
        
        self._empty_state_card = create_empty_state_card(
            message="Noch keine Meldungen",
            subtitle="",
        )
        # Beim Start Ladekreis anzeigen
        self._list_view.controls = [
            create_loading_indicator(text="Meldungen werden geladen…"),
        ]
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
            # Ort-Feld + Vorschlaege zusammen in einer Column
            location_col = ft.Column(
                [self._location_field, self._location_suggestions_box],
                spacing=0,
            )

            self.search_row = ft.ResponsiveRow(
                controls=[
                    ft.Container(self._search_q, col={"xs": 12, "md": 4}),
                    ft.Container(self._filter_typ, col={"xs": 6, "md": 2}),
                    ft.Container(self._filter_art, col={"xs": 6, "md": 2}),
                    ft.Container(self._filter_geschlecht, col={"xs": 6, "md": 2}),
                    ft.Container(self._filter_rasse, col={"xs": 6, "md": 2}),
                    ft.Container(location_col, col={"xs": 8, "md": 4}),
                    ft.Container(self._radius_dropdown, col={"xs": 4, "md": 2}),
                    ft.Container(self._farben_header, col={"xs": 12, "md": 12}),
                    ft.Container(self._farben_panel, col={"xs": 12, "md": 12}),
                    ft.Container(
                        ft.Row([self._reset_btn, self._save_search_btn], spacing=8),
                        col={"xs": 12, "md": 12},
                    )
                ],
                spacing=10,
                run_spacing=10,
            )
        else:
            self.search_row = ft.ResponsiveRow(controls=[], spacing=10, run_spacing=10)
    
    def _update_farben_colors(self) -> None:
        """Aktualisiert die Farben des Farben-Panels basierend auf aktuellem Theme."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        if self._farben_header:
            # Text- und Icon-Farben aktualisieren
            if hasattr(self._farben_header.content, 'controls'):
                for control in self._farben_header.content.controls:
                    if isinstance(control, ft.Text):
                        control.color = get_theme_color("text_primary", is_dark)
                    elif isinstance(control, ft.Icon):
                        control.color = get_theme_color("text_secondary", is_dark)
    
    # ─────────────────────────────────────────────────────────────
    # Entfernungs-Sortierung dynamisch ein-/ausblenden
    # ─────────────────────────────────────────────────────────────

    _DISTANCE_OPTION_KEY = "distance"

    def _show_distance_sort_option(self) -> None:
        """Fuegt die 'Entfernung'-Option zum Sortier-Dropdown hinzu (falls nicht vorhanden)."""
        if self._sort_dropdown is None:
            return
        existing_keys = {o.key for o in self._sort_dropdown.options}
        if self._DISTANCE_OPTION_KEY not in existing_keys:
            self._sort_dropdown.options.append(
                ft.dropdown.Option(self._DISTANCE_OPTION_KEY, "Entfernung (nächste)")
            )

    def _hide_distance_sort_option(self) -> None:
        """Entfernt die 'Entfernung'-Option aus dem Sortier-Dropdown."""
        if self._sort_dropdown is None:
            return
        self._sort_dropdown.options = [
            o for o in self._sort_dropdown.options
            if o.key != self._DISTANCE_OPTION_KEY
        ]
        # Falls aktuell 'distance' gewaehlt war, auf Standard zuruecksetzen
        if self._sort_dropdown.value == self._DISTANCE_OPTION_KEY:
            self._sort_dropdown.value = "created_at_desc"

    # ─────────────────────────────────────────────────────────────
    # Ort/Umkreis-Filter Methoden
    # ─────────────────────────────────────────────────────────────

    def _on_location_input_change(self) -> None:
        """Wird aufgerufen wenn der Nutzer im Ort-Feld tippt.
        
        Ignoriert programmatische Wertaenderungen (Flag _location_setting_value).
        """
        if self._location_setting_value:
            return

        self._location_selected = {"text": None, "lat": None, "lon": None}
        self._location_query_version += 1
        query = self._location_field.value or ""

        # Entfernungs-Sortierung entfernen wenn kein Ort mehr gewaehlt
        self._hide_distance_sort_option()

        # Bei leerem Feld: Vorschlaege schliessen und Posts ohne Ort-Filter laden
        if not query or not query.strip():
            self._clear_location_suggestions()
            self.page.update()
            self.page.run_task(self.load_posts)
            return

        self.page.run_task(
            self._update_location_suggestions,
            query,
            self._location_query_version,
        )

    async def _update_location_suggestions(self, query: str, version: int) -> None:
        """Laedt Geocoding-Vorschlaege fuer den eingegebenen Ort (async mit Debounce)."""
        import asyncio
        await asyncio.sleep(0.3)
        if version != self._location_query_version:
            return
        if not query or len(query.strip()) < 3:
            self._clear_location_suggestions()
            return

        from services.geocoding import geocode_suggestions
        suggestions = geocode_suggestions(query)
        if not suggestions:
            self._clear_location_suggestions()
            return

        def build_item(item: Dict[str, Any]) -> ft.Control:
            return ft.TextButton(
                text=item.get("text", ""),
                on_click=lambda _, i=item: self._select_location_suggestion(i),
                style=ft.ButtonStyle(alignment=ft.alignment.center_left),
            )

        self._location_suggestions_list.controls = [build_item(s) for s in suggestions]
        self._location_suggestions_box.visible = True
        self.page.update()

    def _select_location_suggestion(self, item: Dict[str, Any]) -> None:
        """Nutzer hat einen Vorschlag ausgewaehlt."""
        self._location_selected = {
            "text": item.get("text"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
        }

        # Flag setzen damit on_change die Auswahl nicht zuruecksetzt
        self._location_setting_value = True
        self._location_field.value = item.get("text", "")
        self._location_setting_value = False

        self._clear_location_suggestions()

        # Sicherstellen, dass ein Umkreis gewaehlt ist
        if not self._radius_dropdown.value:
            self._radius_dropdown.value = "all"

        self.page.update()
        # Posts neu laden mit Umkreis
        self.page.run_task(self.load_posts)

    def _clear_location_suggestions(self) -> None:
        """Loescht die Vorschlagsliste."""
        self._location_suggestions_list.controls = []
        self._location_suggestions_box.visible = False
        self.page.update()

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

        # Umkreis-Daten sammeln
        orig_lat = self._location_selected.get("lat")
        orig_lon = self._location_selected.get("lon")
        location_text = self._location_selected.get("text")
        location_lat = orig_lat
        location_lon = orig_lon
        radius_km = None
        radius_val = self._radius_dropdown.value if self._radius_dropdown else "all"
        location_text_filter = None
        has_radius = False
        if radius_val == "all" and location_text:
            # "Ganzer Ort": per Stadtname filtern, kein Umkreis
            location_lat = orig_lat
            location_lon = orig_lon
            radius_km = None
            location_text_filter = location_text
        elif location_lat is not None and location_lon is not None:
            try:
                radius_km = float(radius_val)
                has_radius = True
            except (ValueError, TypeError):
                radius_km = 25.0
                has_radius = True

        # Entfernungs-Sortierung nur bei konkretem Umkreis anzeigen
        if has_radius and orig_lat is not None:
            self._show_distance_sort_option()
        else:
            self._hide_distance_sort_option()
        
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
            empty_state_card=self._empty_state_card,
            page=self.page,
            on_render=self._render_items,
            get_filter_value=handle_view_get_filter_value,
            location_lat=location_lat,
            location_lon=location_lon,
            radius_km=radius_km,
            location_text_filter=location_text_filter,
        )
        self._has_loaded_posts = True

    async def ensure_loaded(self) -> None:
        """Lädt Meldungen nur beim ersten Anzeigen der Discover-View."""
        if self._has_loaded_posts:
            return
        await self.load_posts()

    def reset_filters(self) -> None:
        """Setzt alle Filter zurueck und laedt Posts neu.

        Wird z.B. vom Reset-Button aufgerufen.
        """
        self._hide_distance_sort_option()
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
            on_reset=lambda: self.page.run_task(self.load_posts),
            update_breeds_callback=lambda: handle_view_update_rassen_dropdown(
                filter_art=self._filter_art,
                filter_rasse=self._filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
            ),
            location_field=self._location_field,
            radius_dropdown=self._radius_dropdown,
            location_selected=self._location_selected,
        )

    def reset_filters_silent(self) -> None:
        """Setzt alle Filter zurueck OHNE Posts neu zu laden.

        Wird aufgerufen wenn von einem anderen Tab zur Startseite
        zuruecknavigiert wird. Die Posts werden danach von
        ensure_loaded/load_posts separat geladen.
        """
        self._hide_distance_sort_option()
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
            on_reset=None,
            update_breeds_callback=lambda: handle_view_update_rassen_dropdown(
                filter_art=self._filter_art,
                filter_rasse=self._filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
            ),
            location_field=self._location_field,
            radius_dropdown=self._radius_dropdown,
            location_selected=self._location_selected,
        )
        # Posts muessen neu geladen werden
        self._has_loaded_posts = False
    
    def _render_items(self, items: list[dict]) -> None:
        """Rendert die geladenen Items in der Listen-Ansicht."""
        handle_view_render_items(
            items=items,
            current_items=self.current_items,
            list_view=self._list_view,
            empty_state_card=self._empty_state_card,
            page=self.page,
            on_favorite_click=self._toggle_favorite,
            on_card_click=self._show_detail_dialog,
            on_contact_click=self.on_contact_click,
            supabase=self.sb,
            profile_service=self.profile_service,
            on_comment_login_required=self.on_comment_login_required,
        )
    
    def _show_detail_dialog(self, item: Dict[str, Any]) -> None:
        """Zeigt den Detail-Dialog für eine Meldung inkl. Kommentare."""
        handle_view_show_detail_dialog(
            item=item,
            page=self.page,
            on_contact_click=self.on_contact_click,
            on_favorite_click=self._toggle_favorite,
            profile_service=self.profile_service,
            supabase=self.sb,
            on_comment_login_required=self.on_comment_login_required,
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
            location_field=self._location_field,
            radius_dropdown=self._radius_dropdown,
            location_selected=self._location_selected,
        )
        # Entfernungs-Sortierung nur bei konkretem Umkreis (nicht "Ganzer Ort")
        has_location = self._location_selected and self._location_selected.get("lat")
        has_radius = self._radius_dropdown and self._radius_dropdown.value and self._radius_dropdown.value != "all"
        if has_location and has_radius:
            self._show_distance_sort_option()
        else:
            self._hide_distance_sort_option()

    def build_start_section(
        self,
        is_logged_in: bool,
        on_login_click: Callable[[ft.ControlEvent], None],
    ) -> ft.Control:
        """Erstellt den Start-Tab mit Login-Banner, Filter-Toggle und Liste."""
        try:
            if not hasattr(self, "search_row"):
                return ft.Container(
                    content=ft.Text("Fehler: search_row nicht initialisiert"),
                    padding=20,
                )

            search_filters = ft.Container(
                content=self.search_row,
                visible=False,
                padding=ft.padding.only(top=0),
            )

            def toggle_search(_):
                search_filters.visible = not search_filters.visible
                toggle_btn.icon = (
                    ft.Icons.SEARCH_OFF if search_filters.visible
                    else ft.Icons.SEARCH
                )
                toggle_btn.tooltip = (
                    "Filter ausblenden" if search_filters.visible
                    else "Filter einblenden"
                )
                self.page.update()

            toggle_btn = ft.IconButton(
                icon=ft.Icons.SEARCH,
                icon_size=22,
                tooltip="Filter einblenden",
                on_click=toggle_search,
                style=ft.ButtonStyle(padding=4),
            )

            search_toggle_card = soft_card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                toggle_btn,
                                ft.Text("Filter & Suche", weight=ft.FontWeight.W_700, size=14),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=4,
                        ),
                        search_filters,
                    ],
                    spacing=0,
                ),
                pad=4,
                elev=2,
            )

            # Alle Inhalte in einer gemeinsamen scrollbaren Column
            scroll_children: list[ft.Control] = []

            if not is_logged_in:
                scroll_children.append(create_login_banner(on_login_click))

            scroll_children.append(search_toggle_card)
            scroll_children.append(self.build())

            return ft.Column(
                scroll_children,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        except Exception as e:
            logger.error(f"Fehler in build_start_section: {e}")
            return ft.Container(
                content=ft.Text(f"Fehler beim Laden: {str(e)}"),
                padding=20,
            )

    # ─────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────

    def build(self) -> ft.Column:
        """Erstellt und gibt die komplette Discover-UI zurück."""

        # Post-Liste (kein eigenes Scrollen)
        content_container = ft.Container(
            padding=ft.padding.only(left=4, right=4, top=0),
            content=self._list_view,
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

        # Tab-Inhalte: Index 0 = Meldungen, Index 1 = Karte
        tab_contents = [content_container, map_placeholder]
        tab_body = ft.Container(content=tab_contents[0])

        def switch_tab(index: int):
            tab_body.content = tab_contents[index]
            for i, btn in enumerate(tab_buttons):
                btn.style = ft.ButtonStyle(
                    color=ft.Colors.PRIMARY if i == index else ft.Colors.GREY_500,
                )
            self.page.update()

        tab_buttons = [
            ft.TextButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.PETS, size=24), ft.Text("Meldungen", size=14)],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                style=ft.ButtonStyle(
                    color=ft.Colors.PRIMARY,
                    padding=ft.padding.symmetric(horizontal=24, vertical=12),
                ),
                on_click=lambda _, i=0: switch_tab(i),
            ),
            ft.TextButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.MAP, size=24), ft.Text("Karte", size=14)],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                style=ft.ButtonStyle(
                    color=ft.Colors.GREY_500,
                    padding=ft.padding.symmetric(horizontal=24, vertical=12),
                ),
                on_click=lambda _, i=1: switch_tab(i),
            ),
        ]

        tab_bar = ft.Container(
            content=ft.Row(
                [
                    *tab_buttons,
                    ft.Container(expand=True),  # Spacer
                    ft.Container(
                        self._sort_dropdown,
                        width=200,
                    ),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

        self.page.run_task(self.load_posts)

        return ft.Column([tab_bar, ft.Divider(height=1), tab_body], spacing=0)
