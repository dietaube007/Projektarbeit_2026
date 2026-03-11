"""
Discover-View mit Listen- und Kartendarstellung.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List
import flet as ft
from supabase import Client

from services.posts.references import ReferenceService
from services.posts import SavedSearchService, FavoritesService, SearchService
from services.posts.map_service import MapDataService
from services.account import ProfileService
from ui.theme import get_theme_color, soft_card
from ui.constants import PRIMARY_COLOR
from ui.shared_components import (
    create_empty_state_card,
    create_loading_indicator,
)
from ui.discover.map import (
    build_map_container,
    build_map_loading_indicator,
    build_map_empty_state,
    build_map_error,
    handle_map_marker_click,
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

        # Karten-State
        self._map_container: Optional[ft.Container] = None
        self._map_data_service = MapDataService()
        self._all_loaded_posts: List[Dict[str, Any]] = []  # Alle Posts für die Karte
        self._map_loaded = False  # Flag ob Karte bereits gerendert wurde
        self._current_tab_index = 0  # 0 = Liste, 1 = Karte

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
        # Speichere Posts für Karten-Rendering
        self._all_loaded_posts = items
        # Markiere Karte als nicht geladen damit sie neu gerendert wird bei Filter-Änderung
        self._map_loaded = False
        
        handle_view_render_items(
            items=items,
            current_items=self.current_items,
            list_view=self._list_view,
            empty_state_card=self._empty_state_card,
            page=self.page,
            on_favorite_click=self._toggle_favorite,
            on_card_click=self._show_detail_dialog,
            on_contact_click=self._handle_contact_click,
            supabase=self.sb,
            profile_service=self.profile_service,
            on_comment_login_required=self.on_comment_login_required,
        )
    
    def _show_detail_dialog(self, item: Dict[str, Any]) -> None:
        """Zeigt den Detail-Dialog für eine Meldung inkl. Kommentare."""
        handle_view_show_detail_dialog(
            item=item,
            page=self.page,
            on_contact_click=self._handle_contact_click,
            on_favorite_click=self._toggle_favorite,
            profile_service=self.profile_service,
            supabase=self.sb,
            on_comment_login_required=self.on_comment_login_required,
        )

    def _handle_contact_click(self, item: Dict[str, Any]) -> None:
        """Verarbeitet Kontakt-Klick: Login prüfen und Kontaktformular anzeigen."""
        self.refresh_user()
        if not self.current_user_id:
            if self.on_login_required:
                self.on_login_required()
            return

        self._show_contact_form_dialog(item)

    def _show_contact_form_dialog(self, item: Dict[str, Any]) -> None:
        """Zeigt ein an das App-Design angepasstes Kontaktformular als Popup."""
        current_user = self.profile_service.get_current_user()
        email_value = (self.profile_service.get_email() or "").strip()

        user_meta = getattr(current_user, "user_metadata", {}) or {}
        first_name_value = (
            user_meta.get("first_name")
            or user_meta.get("firstname")
            or ""
        )
        last_name_value = (
            user_meta.get("last_name")
            or user_meta.get("lastname")
            or ""
        )

        email_field = ft.TextField(
            label="E-Mail",
            value=email_value,
            read_only=True,
            border_radius=10,
            expand=True,
        )
        phone_field = ft.TextField(
            label="Telefon (optional)",
            hint_text="z. B. 0911/123456",
            border_radius=10,
            expand=True,
        )
        first_name_field = ft.TextField(
            label="Vorname",
            value=str(first_name_value or ""),
            border_radius=10,
            expand=True,
        )
        last_name_field = ft.TextField(
            label="Nachname",
            value=str(last_name_value or ""),
            border_radius=10,
            expand=True,
        )
        subject_field = ft.TextField(
            label="Betreff",
            border_radius=10,
            max_length=120,
            counter_text="",
            expand=True,
        )
        message_field = ft.TextField(
            label="Mitteilung",
            multiline=True,
            min_lines=6,
            max_lines=8,
            border_radius=10,
            max_length=2000,
            hint_text="Textlänge (maximal 2000)",
            expand=True,
        )

        post_title = str(item.get("headline") or item.get("title") or "Meldung")

        def close_dialog(_e: Optional[ft.ControlEvent] = None) -> None:
            self.page.close(contact_dialog)

        def submit_contact(_e: ft.ControlEvent) -> None:
            subject = (subject_field.value or "").strip()
            message = (message_field.value or "").strip()

            if not subject:
                subject_field.error_text = "Bitte Betreff eingeben."
                self.page.update()
                return
            subject_field.error_text = None

            if not message:
                message_field.error_text = "Bitte Mitteilung eingeben."
                self.page.update()
                return
            message_field.error_text = None

            contact_payload = {
                "post_id": item.get("id"),
                "post_title": post_title,
                "email": email_field.value,
                "phone": (phone_field.value or "").strip() or None,
                "first_name": (first_name_field.value or "").strip() or None,
                "last_name": (last_name_field.value or "").strip() or None,
                "subject": subject,
                "message": message,
            }

            logger.info("Kontaktanfrage erstellt für Post %s", contact_payload.get("post_id"))

            if self.on_contact_click:
                try:
                    callback_payload = dict(item)
                    callback_payload["contact_request"] = contact_payload
                    self.on_contact_click(callback_payload)
                except Exception as ex:
                    logger.warning(f"Externer Kontakt-Callback fehlgeschlagen: {ex}")

            self.page.close(contact_dialog)
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Kontaktanfrage vorbereitet."),
                bgcolor=PRIMARY_COLOR,
            )
            self.page.snack_bar.open = True
            self.page.update()

        contact_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Kontaktformular", weight=ft.FontWeight.W_600),
            content=ft.Container(
                width=760,
                content=ft.Column(
                    [
                        ft.Text(
                            f"Ihre Nachricht zu: {post_title}",
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.ResponsiveRow(
                            [
                                ft.Container(first_name_field, col={"xs": 12, "md": 6}),
                                ft.Container(last_name_field, col={"xs": 12, "md": 6}),
                            ],
                            spacing=12,
                            run_spacing=8,
                        ),
                        ft.ResponsiveRow(
                            [
                                ft.Container(email_field, col={"xs": 12, "md": 6}),
                                ft.Container(phone_field, col={"xs": 12, "md": 6}),
                            ],
                            spacing=12,
                            run_spacing=8,
                        ),
                        subject_field,
                        message_field,
                    ],
                    tight=True,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=ft.padding.only(top=4),
            ),
            actions=[
                ft.TextButton("Abbrechen", on_click=close_dialog),
                ft.ElevatedButton(
                    "Senden",
                    on_click=submit_contact,
                    style=ft.ButtonStyle(
                        bgcolor=PRIMARY_COLOR,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(contact_dialog)
    
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

    def _toggle_favorite_from_map(self, post_id: str) -> None:
        """Toggelt Favoritenstatus für einen Post aus der Kartenansicht."""
        # Auth prüfen
        self.refresh_user()
        if not self.current_user_id:
            if self.on_login_required:
                self.on_login_required()
            return

        try:
            post_id = str(post_id)
            is_favorite = self.favorites_service.is_favorite(post_id)

            success = (
                self.favorites_service.remove_favorite(post_id)
                if is_favorite
                else self.favorites_service.add_favorite(post_id)
            )

            if not success:
                self.page.snack_bar = ft.SnackBar(ft.Text("Favorit konnte nicht aktualisiert werden."))
                self.page.snack_bar.open = True
                self.page.update()
                return

            message = "Aus Favoriten entfernt" if is_favorite else "Zu Favoriten hinzugefügt"
            self.page.snack_bar = ft.SnackBar(ft.Text(message))
            self.page.snack_bar.open = True
            self.page.update()

            # Daten neu laden, damit Status in Listen-/Kartensicht konsistent bleibt
            self.page.run_task(self.load_posts)

        except Exception as ex:
            logger.error(f"Fehler beim Favorisieren aus Karte: {ex}", exc_info=True)
            self.page.snack_bar = ft.SnackBar(ft.Text("Fehler beim Favorisieren."))
            self.page.snack_bar.open = True
            self.page.update()
    
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

            toggle_row = ft.Container(
                content=ft.Row(
                    [
                        toggle_btn,
                        ft.Text("Filter & Suche", weight=ft.FontWeight.W_700, size=14),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=4,
                ),
                on_click=toggle_search,
                ink=True,
                border_radius=8,
                padding=ft.padding.symmetric(vertical=4),
            )

            search_toggle_card = soft_card(
                ft.Column(
                    [
                        toggle_row,
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
    # Map Rendering
    # ─────────────────────────────────────────────────────────────

    async def _load_and_render_map(self) -> None:
        """Lädt und rendert die Karte mit aktuellen gefilterten Posts."""
        if not self._map_container:
            return

        # Loading-Indikator anzeigen
        self._map_container.content = build_map_loading_indicator()
        self.page.update()

        try:
            # Posts holen (gefiltert)
            posts = self._all_loaded_posts if self._all_loaded_posts else []

            if not posts:
                # Keine Posts vorhanden
                self._map_container.content = build_map_empty_state()
                self.page.update()
                return

            # Posts mit Koordinaten filtern
            posts_with_coords = [
                p for p in posts 
                if p.get("location_lat") is not None and p.get("location_lon") is not None
            ]

            if not posts_with_coords:
                # Keine Posts mit Koordinaten
                self._map_container.content = build_map_empty_state()
                self.page.update()
                return

            # Mittelpunkt berechnen
            center = self._map_data_service.get_center_point(posts_with_coords)

            # Verfügbare Resthöhe für Karte berechnen
            page_height = self.page.height if self.page and self.page.height else 900
            map_height = max(float(page_height) - 255.0, 360.0)

            # Marker-Click-Handler
            def on_marker_click(post_id: str):
                handle_map_marker_click(
                    post_id=post_id,
                    posts=posts,  # ALLE Posts übergeben (nicht nur mit Koordinaten)
                    page=self.page,
                    show_detail_dialog=self._show_detail_dialog,
                )

            # Karte rendern (mit Clustering bei >10 Posts)
            map_widget = build_map_container(
                posts=posts_with_coords,
                page=self.page,
                on_marker_click=on_marker_click,
                on_favorite_click=self._toggle_favorite_from_map,
                center_lat=center[0],
                center_lon=center[1],
                zoom_level=5,
                use_clustering=len(posts_with_coords) > 10,
                map_height=map_height,
            )

            self._map_container.content = map_widget
            self._map_container.height = map_height
            self._map_loaded = True
            logger.info(f"Karte gerendert mit {len(posts_with_coords)} Meldungen")
            self.page.update()

        except Exception as e:
            logger.error(f"Fehler beim Rendern der Karte: {e}", exc_info=True)
            self._map_container.content = build_map_error(str(e))
            self.page.update()

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

        # Map-Container (wird lazy geladen)
        self._map_container = ft.Container(
            content=build_map_loading_indicator(),
            expand=True,
            bgcolor=ft.Colors.SURFACE,
        )

        # Tab-Inhalte: Index 0 = Meldungen, Index 1 = Karte
        tab_contents = [content_container, self._map_container]
        tab_body = ft.Container(content=tab_contents[0], expand=True)

        def switch_tab(index: int):
            """Wechselt zwischen List- und Map-Tab."""
            self._current_tab_index = index
            tab_body.content = tab_contents[index]
            
            # Button-Styling aktualisieren
            for i, btn in enumerate(tab_buttons):
                btn.style = ft.ButtonStyle(
                    color=ft.Colors.PRIMARY if i == index else ft.Colors.GREY_500,
                )
            
            # Bei Wechsel zur Karte: Lazy-Loading
            if index == 1:
                # Karte neu rendern wenn Filter geändert oder noch nicht geladen
                if not self._map_loaded:
                    self.page.run_task(self._load_and_render_map)
            
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

        return ft.Column([tab_bar, ft.Divider(height=1), tab_body], spacing=0, expand=True)
