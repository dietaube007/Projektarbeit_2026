"""
ui/discover/view.py
Discover-View mit Listen- und Kartendarstellung (refaktoriert).
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List
import flet as ft
from supabase import Client

from ui.constants import MAX_POSTS_LIMIT
from services.references import ReferenceService
from services.profile import SavedSearchService, FavoritesService
from services.discover import DiscoverService
from utils.logging_config import get_logger

logger = get_logger(__name__)

from .cards import show_detail_dialog
from .saved_search_dialog import show_save_search_dialog
from .filters import reset_filters, apply_saved_search_filters, collect_current_filters
from .references_loader import load_and_populate_references, update_breeds_dropdown
from .item_renderer import render_items, create_empty_state_card
from .ui_builder import build_discover_ui
from .data import get_favorite_ids


class DiscoverView:
    """Klasse für die Startseite mit Meldungsübersicht."""

    def __init__(
        self,
        page: ft.Page,
        sb: Client,
        on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_melden_click: Optional[Callable[[], None]] = None,
        on_login_required: Optional[Callable[[], None]] = None,
        on_save_search_login_required: Optional[Callable[[], None]] = None,
    ) -> None:
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
        self.discover_service = DiscoverService(self.sb)

        # Filter-Status
        self.selected_farben: list[int] = []
        self.farben_panel_visible = False
        self.view_mode = "list"  # "list" oder "grid"
        self.current_items: list[dict] = []

        # User
        self.current_user_id: Optional[str] = None
        self.refresh_user()

        # UI init
        self._init_ui_elements()

        # Referenzen laden
        self.page.run_task(self._load_references)

    # ──────────────────────────────────────────────────────────────────
    # USER / AUTH
    # ──────────────────────────────────────────────────────────────────

    def _get_current_user_id(self) -> Optional[str]:
        """Zieht die aktuelle User-ID aus Supabase."""
        try:
            user_resp = self.sb.auth.get_user()
            if user_resp and getattr(user_resp, "user", None):
                return user_resp.user.id
        except Exception:
            pass
        return None

    def refresh_user(self) -> None:
        """Kann von außen (z.B. nach Login) aufgerufen werden."""
        self.current_user_id = self._get_current_user_id()

    # ──────────────────────────────────────────────────────────────────
    # INIT UI
    # ──────────────────────────────────────────────────────────────────

    def _init_ui_elements(self) -> None:
        """Initialisiert alle UI-Elemente über den UI-Builder."""
        ui_elements = build_discover_ui(
            on_search_click=lambda _: self.page.run_task(self.load_posts),
            on_tierart_change=self._on_tierart_change,
            on_reset_click=self._reset_filters,
            on_save_search_click=self._show_save_search_dialog,
            on_view_change=self._on_view_change,
            on_toggle_farben=self._toggle_farben_panel,
        )

        # Alle UI-Elemente als Attribute setzen
        self.search_q = ui_elements["search_q"]
        self.filter_typ = ui_elements["filter_typ"]
        self.filter_art = ui_elements["filter_art"]
        self.filter_geschlecht = ui_elements["filter_geschlecht"]
        self.filter_rasse = ui_elements["filter_rasse"]
        self.farben_filter_container = ui_elements["farben_filter_container"]
        self.farben_toggle_icon = ui_elements["farben_toggle_icon"]
        self.farben_panel = ui_elements["farben_panel"]
        self.farben_header = ui_elements["farben_header"]
        self.sort_dropdown = ui_elements["sort_dropdown"]
        self.search_btn = ui_elements["search_btn"]
        self.reset_btn = ui_elements["reset_btn"]
        self.save_search_btn = ui_elements["save_search_btn"]
        self.search_row = ui_elements["search_row"]
        self.view_toggle = ui_elements["view_toggle"]
        self.list_view = ui_elements["list_view"]
        self.grid_view = ui_elements["grid_view"]
        self.empty_state_card = ui_elements["empty_state_card"]

    def _on_view_change(self, e: ft.ControlEvent) -> None:
        val = next(iter(e.control.selected), "list")
        self.view_mode = val
        self._render_items(self.current_items)

    # ──────────────────────────────────────────────────────────────────
    # REFERENCES
    # ──────────────────────────────────────────────────────────────────

    async def _load_references(self):
        """Lädt alle Referenzen und befüllt die Dropdowns."""
        self._all_breeds = load_and_populate_references(
            ref_service=self.ref_service,
            filter_typ=self.filter_typ,
            filter_art=self.filter_art,
            filter_geschlecht=self.filter_geschlecht,
            filter_rasse=self.filter_rasse,
            farben_filter_container=self.farben_filter_container,
            selected_colors=self.selected_farben,
            on_color_change_callback=lambda: None,  # Keine automatische Suche
            page=self.page,
        )
        self._update_rassen_dropdown()

    def _on_tierart_change(self, e: ft.ControlEvent) -> None:
        """Aktualisiert das Rassen-Dropdown bei Tierart-Änderung (ohne automatische Suche)."""
        self._update_rassen_dropdown()

    def _update_rassen_dropdown(self) -> None:
        """Aktualisiert das Rassen-Dropdown basierend auf der ausgewählten Tierart."""
        if hasattr(self, "_all_breeds"):
            update_breeds_dropdown(
                filter_art=self.filter_art,
                filter_rasse=self.filter_rasse,
                all_breeds=self._all_breeds,
                page=self.page,
            )

    def _toggle_farben_panel(self, _: Optional[ft.ControlEvent] = None) -> None:
        self.farben_panel_visible = not self.farben_panel_visible
        self.farben_panel.visible = self.farben_panel_visible
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # FAVORITEN
    # ──────────────────────────────────────────────────────────────────

    def _toggle_favorite(self, item: Dict[str, Any], icon_button: ft.IconButton) -> None:
        """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie."""
        self.refresh_user()

        if not self.current_user_id:
            if self.on_login_required:
                self.on_login_required()
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Bitte melden Sie sich an, um Meldungen zu favorisieren."),
                    open=True,
                )
                self.page.update()
            return

        post_id = item.get("id")
        if not post_id:
            return

        try:
            is_favorite = item.get("is_favorite", False)
            if is_favorite:
                success = self.favorites_service.remove_favorite(post_id)
                if success:
                    item["is_favorite"] = False
                    icon_button.icon = ft.Icons.FAVORITE_BORDER
                    icon_button.icon_color = ft.Colors.GREY_600
                    # Dialog anzeigen
                    from ui.components import show_success_dialog
                    show_success_dialog(
                        self.page,
                        "Aus Favoriten entfernt",
                        "Die Meldung wurde aus Ihren Favoriten entfernt."
                    )
            else:
                success = self.favorites_service.add_favorite(post_id)
                if success:
                    item["is_favorite"] = True
                    icon_button.icon = ft.Icons.FAVORITE
                    icon_button.icon_color = ft.Colors.RED
                    # Dialog anzeigen
                    from ui.components import show_success_dialog
                    show_success_dialog(
                        self.page,
                        "Zu Favoriten hinzugefügt",
                        "Die Meldung wurde zu Ihren Favoriten hinzugefügt."
                    )

            if success:
                self.page.update()

        except Exception as ex:
            logger.error(f"Fehler beim Aktualisieren der Favoriten (Post {post_id}): {ex}", exc_info=True)
            from ui.components import show_error_dialog
            show_error_dialog(
                self.page,
                "Fehler",
                "Die Favoriten-Aktion konnte nicht durchgeführt werden."
            )

    # ──────────────────────────────────────────────────────────────────
    # DATEN LADEN
    # ──────────────────────────────────────────────────────────────────

    async def load_posts(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen + Favoritenstatus."""
        loading_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=40, height=40),
                    ft.Text("Meldungen werden geladen…", size=14, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )
        self.list_view.controls = [loading_indicator]
        self.grid_view.controls = []
        self.list_view.visible = True
        self.grid_view.visible = False
        self.page.update()

        try:
            self.refresh_user()

            # Filter-Werte sammeln
            filters = {
                "typ": self.filter_typ.value,
                "art": self.filter_art.value,
                "geschlecht": self.filter_geschlecht.value,
                "rasse": self.filter_rasse.value,
            }

            # Favoriten-IDs laden (für Markierung)
            favorite_ids = get_favorite_ids(self.sb, self.current_user_id)

            # Posts über DiscoverService laden
            sort_option = self.sort_dropdown.value or "created_at_desc"
            items = self.discover_service.search_posts(
                filters=filters,
                search_query=self.search_q.value,
                selected_colors=set(self.selected_farben) if self.selected_farben else None,
                sort_option=sort_option,
                favorite_ids=favorite_ids,
            )

            self.current_items = items
            self._render_items(items)

        except Exception as ex:
            logger.error(f"Fehler beim Laden der Daten: {ex}", exc_info=True)
            self.current_items = []
            self.list_view.controls = [self.empty_state_card]
            self.grid_view.controls = []
            self.list_view.visible = True
            self.grid_view.visible = False
            self.page.update()

    def _render_items(self, items: List[Dict[str, Any]]) -> None:
        """Rendert Post-Items in List- oder Grid-Ansicht."""
        render_items(
            items=items,
            view_mode=self.view_mode,
            list_view=self.list_view,
            grid_view=self.grid_view,
            page=self.page,
            on_favorite_click=self._toggle_favorite,
            on_card_click=self._show_detail_dialog,
            on_contact_click=self.on_contact_click,
            on_reset=self._reset_filters,
        )

    def _show_detail_dialog(self, item: Dict[str, Any]) -> None:
        """Wrapper-Methode für den Detail-Dialog."""
        show_detail_dialog(
            item=item,
            page=self.page,
            on_contact_click=self.on_contact_click,
            on_favorite_click=self._toggle_favorite,
        )

    # ──────────────────────────────────────────────────────────────────
    # FILTER RESET
    # ──────────────────────────────────────────────────────────────────

    def _reset_filters(self, _: Optional[ft.ControlEvent] = None) -> None:
        reset_filters(
            search_field=self.search_q,
            filter_typ=self.filter_typ,
            filter_art=self.filter_art,
            filter_geschlecht=self.filter_geschlecht,
            filter_rasse=self.filter_rasse,
            sort_dropdown=self.sort_dropdown,
            selected_colors=self.selected_farben,
            color_checkboxes_container=self.farben_filter_container,
            page=self.page,
            on_reset=lambda: self.page.run_task(self.load_posts),
        )

    def _show_save_search_dialog(self, e: Optional[ft.ControlEvent] = None) -> None:
        """Zeigt Dialog zum Speichern der aktuellen Suche."""
        # Prüfen ob eingeloggt
        if not self.current_user_id:
            if self.on_save_search_login_required:
                self.on_save_search_login_required()
            elif self.on_login_required:
                # Fallback auf generischen Login-Callback
                self.on_login_required()
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Bitte melden Sie sich an, um Suchaufträge zu speichern."),
                    open=True,
                )
                self.page.update()
            return

        # Aktuelle Filter sammeln
        current_filters = collect_current_filters(
            search_field=self.search_q,
            filter_typ=self.filter_typ,
            filter_art=self.filter_art,
            filter_geschlecht=self.filter_geschlecht,
            filter_rasse=self.filter_rasse,
            selected_colors=self.selected_farben,
        )

        show_save_search_dialog(
            page=self.page,
            saved_search_service=self.saved_search_service,
            current_filters=current_filters,
            ref_service=self.ref_service,
        )

    def apply_saved_search(self, search: Dict[str, Any]) -> None:
        """Wendet einen gespeicherten Suchauftrag auf die Filter an."""
        apply_saved_search_filters(
            search=search,
            search_field=self.search_q,
            filter_typ=self.filter_typ,
            filter_art=self.filter_art,
            filter_geschlecht=self.filter_geschlecht,
            filter_rasse=self.filter_rasse,
            selected_colors=self.selected_farben,
            color_checkboxes_container=self.farben_filter_container,
            update_breeds_callback=self._update_rassen_dropdown,
            page=self.page,
        )
        self.page.run_task(self.load_posts)

    # ──────────────────────────────────────────────────────────────────
    # BUILD
    # ──────────────────────────────────────────────────────────────────

    def build(self) -> ft.Column:
        view_toggle_row = ft.Container(
            content=ft.Row([self.view_toggle], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.only(left=4, top=12, bottom=8),
        )

        content_container = ft.Container(
            padding=4,
            content=ft.Column([view_toggle_row, self.list_view, self.grid_view], spacing=8),
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

        # Beim ersten Build direkt laden
        self.page.run_task(self.load_posts)

        return ft.Column([tabs], spacing=14, expand=True)
