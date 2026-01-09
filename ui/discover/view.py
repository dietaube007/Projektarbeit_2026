"""
ui/discover/view.py
Discover-View mit Listen- und Kartendarstellung (refaktoriert).
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List
import flet as ft
from supabase import Client

from ui.constants import MAX_POSTS_LIMIT
from ui.theme import soft_card
from services.references import ReferenceService
from services.profile import SavedSearchService, FavoritesService
from services.discover import DiscoverService
from utils.logging_config import get_logger

logger = get_logger(__name__)

from .cards import show_detail_dialog, build_small_card, build_big_card
from .saved_search_dialog import show_save_search_dialog
from .filters import (
    reset_filters,
    apply_saved_search_filters,
    collect_current_filters,
    create_search_field,
    create_dropdown,
    create_farben_header,
    create_reset_button,
    create_view_toggle,
    create_sort_dropdown,
)
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

    def _init_ui_elements(self):
        # Suche
        self.search_q = create_search_field(
            on_change=lambda _: self.page.run_task(self.load_posts)
        )

        # Filter Dropdowns
        self.filter_typ = create_dropdown(
            label="Kategorie",
            on_change=lambda _: self.page.run_task(self.load_posts),
        )

        self.filter_art = create_dropdown(
            label="Tierart",
            on_change=self._on_tierart_change,
        )

        self.filter_geschlecht = create_dropdown(
            label="Geschlecht",
            on_change=lambda _: self.page.run_task(self.load_posts),
            initial_options=[
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ],
        )

        self.filter_rasse = create_dropdown(
            label="Rasse",
            on_change=lambda _: self.page.run_task(self.load_posts),
        )

        # Farben Panel - wird später in _load_references befüllt
        self.farben_filter_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
        self.farben_panel = ft.Container(
            content=self.farben_filter_container,
            padding=12,
            visible=False,
        )

        self.farben_header = create_farben_header(
            toggle_icon=self.farben_toggle_icon,
            on_click=self._toggle_farben_panel,
        )

        # Sortier-Dropdown
        self.sort_dropdown = create_sort_dropdown(
            on_change=lambda _: self.page.run_task(self.load_posts)
        )

        # Buttons
        self.reset_btn = create_reset_button(on_click=self._reset_filters)

        self.search_row = ft.ResponsiveRow(
            controls=[
                ft.Container(self.search_q, col={"xs": 12, "md": 5}),
                ft.Container(self.filter_typ, col={"xs": 6, "md": 2}),
                ft.Container(self.filter_art, col={"xs": 6, "md": 2}),
                ft.Container(self.filter_geschlecht, col={"xs": 6, "md": 2}),
                ft.Container(self.filter_rasse, col={"xs": 6, "md": 1}),
                ft.Container(self.reset_btn, col={"xs": 12, "md": 12}),
                ft.Container(self.farben_header, col={"xs": 12, "md": 12}),
                ft.Container(self.farben_panel, col={"xs": 12, "md": 12}),
            ],
            spacing=10,
            run_spacing=10,
        )

        # View toggle
        self.view_toggle = create_view_toggle(on_change=self._on_view_change)

        # Ergebnisbereiche
        self.list_view = ft.Column(spacing=14, expand=True)
        self.grid_view = ft.ResponsiveRow(spacing=12, run_spacing=12, visible=False)
        
        # Initial mit empty_state_card befüllen
        self.empty_state_card = soft_card(
            ft.Column(
                [
                    ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Noch keine Meldungen", weight=ft.FontWeight.W_600),
                    ft.Text("Passe deine Filter an oder melde ein Tier.", color=ft.Colors.GREY_700),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            elev=1,
            pad=24,
        )
        
        # Initial empty state anzeigen
        self.list_view.controls = [self.empty_state_card]
        self.list_view.visible = True

    def _on_view_change(self, e: ft.ControlEvent) -> None:
        val = next(iter(e.control.selected), "list")
        self.view_mode = val
        self._render_items(self.current_items)

    # ──────────────────────────────────────────────────────────────────
    # REFERENCES
    # ──────────────────────────────────────────────────────────────────

    async def _load_references(self):
        """Lädt alle Referenzen und befüllt die Dropdowns."""
        try:
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

            # Farben Checkboxen
            self.farben_filter_container.controls = []
            for c in self.ref_service.get_colors() or []:
                c_id = c["id"]

                def on_color_change(e, color_id=c_id):
                    if e.control.value:
                        if color_id not in self.selected_farben:
                            self.selected_farben.append(color_id)
                    else:
                        if color_id in self.selected_farben:
                            self.selected_farben.remove(color_id)
                    self.page.run_task(self.load_posts)

                cb = ft.Checkbox(label=c["name"], value=False, on_change=on_color_change)
                self.farben_filter_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
                )

            self.page.update()
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzen: {ex}")

    def _on_tierart_change(self, e: ft.ControlEvent):
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
                    ft.Text("Bitte melde dich an, um Meldungen zu favorisieren."),
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
                    ft.Text("Laden...", size=14, color=ft.Colors.GREY_600),
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

            # Filter-Werte sammeln (mit Fallback auf "alle" wenn None)
            filters = {
                "typ": self.filter_typ.value if self.filter_typ.value else "alle",
                "art": self.filter_art.value if self.filter_art.value else "alle",
                "geschlecht": self.filter_geschlecht.value if self.filter_geschlecht.value else "alle",
                "rasse": self.filter_rasse.value if self.filter_rasse.value else "alle",
            }

            # Favoriten-IDs laden (für Markierung)
            favorite_ids = get_favorite_ids(self.sb, self.current_user_id)

            # Posts über DiscoverService laden
            sort_option = self.sort_dropdown.value if self.sort_dropdown.value else "created_at_desc"
            items = self.discover_service.search_posts(
                filters=filters,
                search_query=self.search_q.value if self.search_q.value else None,
                selected_colors=set(self.selected_farben) if self.selected_farben else None,
                sort_option=sort_option,
                favorite_ids=favorite_ids,
            )

            self.current_items = items
            self._render_items(items)

        except Exception as ex:
            logger.error(f"Fehler beim Laden der Daten: {ex}", exc_info=True)
            import traceback
            traceback.print_exc()
            self.current_items = []
            self.list_view.controls = [self.empty_state_card]
            self.grid_view.controls = []
            self.list_view.visible = True
            self.grid_view.visible = False
            self.page.update()

    def _render_items(self, items: list[dict]):
        if not items:
            no_results = soft_card(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY_400),
                        ft.Text("Keine Meldungen gefunden", weight=ft.FontWeight.W_600),
                        ft.Text("Versuche andere Suchkriterien", color=ft.Colors.GREY_700),
                        ft.TextButton("Filter zurücksetzen", on_click=self._reset_filters),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                elev=1,
                pad=24,
            )
            self.list_view.controls = [no_results]
            self.grid_view.controls = []
            self.list_view.visible = True
            self.grid_view.visible = False
            self.page.update()
            return

        if self.view_mode == "grid":
            self.grid_view.controls = [
                build_small_card(
                    item=it,
                    page=self.page,
                    on_favorite_click=self._toggle_favorite,
                    on_card_click=self._show_detail_dialog,
                )
                for it in items
            ]
            self.list_view.controls = []
            self.list_view.visible = False
            self.grid_view.visible = True
        else:
            self.list_view.controls = [
                build_big_card(
                    item=it,
                    page=self.page,
                    on_favorite_click=self._toggle_favorite,
                    on_card_click=self._show_detail_dialog,
                    on_contact_click=self.on_contact_click,
                    supabase=self.sb,
                )
                for it in items
            ]
            self.grid_view.controls = []
            self.list_view.visible = True
            self.grid_view.visible = False

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
