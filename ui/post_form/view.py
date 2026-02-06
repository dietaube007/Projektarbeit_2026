"""
Post Form-View mit Meldungsformular.

Enthält UI-Komposition und koordiniert Post Form-Features.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List
import asyncio

import flet as ft

from services.posts.references import ReferenceService
from services.geocoding import geocode_suggestions
from services.posts import PostService, PostRelationsService, PostStorageService
from services.ai.pet_recognition import get_recognition_service
from utils.logging_config import get_logger
from ui.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    DATE_FORMAT,
    NO_SELECTION_VALUE,
)
from ui.shared_components import show_validation_dialog, show_success_dialog, show_error_dialog
from ui.constants import MAX_HEADLINE_LENGTH, MAX_DESCRIPTION_LENGTH
from ui.theme import get_theme_color

from .components import (
    create_meldungsart_button,
    create_photo_preview,
    create_photo_upload_area,
    create_name_field,
    create_title_label,
    create_species_dropdown,
    create_breed_dropdown,
    create_sex_dropdown,
    create_description_field,
    create_location_field,
    create_date_field,
    create_status_text,
    create_farben_header_and_panel,
    create_ai_recognition_button,
    create_ai_result_container,
    create_save_button,
    create_form_layout,
)
from .handlers import (
    handle_view_pick_photo,
    handle_view_remove_photo,
    validate_form_fields,
    handle_view_save_post,
    handle_view_load_references,
    handle_view_update_breeds,
    handle_ai_recognition_flow,
)
from ui.helpers import parse_date

logger = get_logger(__name__)


class PostForm:
    """Formular zum Erstellen von Tier-Meldungen (vermisst/gefunden)."""
    
    def __init__(
        self,
        page: ft.Page,
        sb,
        on_saved_callback: Optional[Callable] = None
    ):
        """Initialisiert das Meldungsformular."""
        self.page = page
        self.sb = sb
        self.on_saved_callback = on_saved_callback
        
        # Services
        self.ref_service = ReferenceService(self.sb)
        self.post_service = PostService(self.sb)
        self.post_relations_service = PostRelationsService(self.sb)
        self.post_storage_service = PostStorageService(self.sb)
        self.recognition_service = get_recognition_service()
        
        # KI-Erkennungs-State (als dict für Mutability in Handlern)
        self.ai_result = {"result": None}
        self.ai_recognition_cancelled = {"cancelled": False}
        
        # Referenzdaten (als list/dict für Mutability in Handlern)
        self.post_statuses: List[Dict[str, Any]] = []
        self.species_list: List[Dict[str, Any]] = []
        self.breeds_by_species: Dict[int, List[Dict[str, Any]]] = {}
        self.colors_list: List[Dict[str, Any]] = []
        self.sex_list: List[Dict[str, Any]] = []
        
        # Ausgewählte Werte
        self.selected_farben: List[int] = []
        self.farben_checkboxes: Dict[int, ft.Checkbox] = {}
        self.selected_photo: Dict[str, Any] = {"path": None, "name": None, "url": None, "base64": None, "local_path": None}
        self.farben_panel_visible = {"visible": True}
        self.location_selected: Dict[str, Any] = {"text": None, "lat": None, "lon": None}
        self._location_query_version = 0
        
        # UI-Elemente initialisieren
        self._init_ui_elements()
        
        # Daten laden
        self.page.run_task(self._load_refs)
    
    # ─────────────────────────────────────────────────────────────
    # UI-Initialisierung
    # ─────────────────────────────────────────────────────────────
    
    def _init_ui_elements(self):
        """Initialisiert alle UI-Elemente."""
        # Callbacks für Event-Handler
        def on_update_title_label(_=None) -> None:
            self._update_title_label()
        
        def on_update_name_counter(_=None) -> None:
            self._update_name_counter()
        
        def on_update_description_counter(_=None) -> None:
            self._update_description_counter()
        
        def on_update_breeds(_=None) -> None:
            self.page.run_task(self._update_breeds)
        
        def on_toggle_farben_panel(_=None) -> None:
            self._toggle_farben_panel()
        
        def on_color_change(color_id: int, is_selected: bool) -> None:
            self._on_color_change(color_id, is_selected)
        
        def on_start_ai_recognition(_=None) -> None:
            self.page.run_task(self._start_ai_recognition_flow)
        
        # Meldungsart
        self.meldungsart = create_meldungsart_button(on_update_title_label)
        
        # Foto-Vorschau
        self.photo_preview = create_photo_preview()
        
        # Name/Überschrift
        self.title_label = create_title_label()
        self.name_tf = create_name_field()
        self.name_tf.on_change = on_update_name_counter
        
        # Dropdowns
        self.species_dd = create_species_dropdown()
        self.breed_dd = create_breed_dropdown()
        self.sex_dd = create_sex_dropdown()
        self.species_dd.on_change = lambda _: self.page.run_task(self._update_breeds)
        
        # Farben-Container
        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)
        
        # Farben-Header und -Panel erstellen
        self.farben_header, self.farben_panel = create_farben_header_and_panel(
            farben_container=self.farben_container,
            farben_toggle_icon=self.farben_toggle_icon,
            farben_panel_visible=self.farben_panel_visible,
            on_toggle=on_toggle_farben_panel,
            page=self.page,
        )
        
        # Beschreibung & Standort
        self.info_tf = create_description_field()
        self.info_tf.on_change = on_update_description_counter
        self.location_tf = create_location_field()
        self.location_tf.on_change = lambda _: self._on_location_change()
        self.date_tf = create_date_field()

        self.location_suggestions_list = ft.Column(spacing=2)
        self.location_suggestions_box = ft.Container(
            content=self.location_suggestions_list,
            visible=False,
            padding=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
        )
        
        # Status-Nachricht
        self.status_text = create_status_text()
        
        # KI-Button und Container
        self.ai_button = create_ai_recognition_button(on_start_ai_recognition)
        self.ai_result_container = create_ai_result_container()
        self.ai_hint_badge: Optional[ft.Control] = None
        
        # Save-Button erstellen
        self.save_button = create_save_button(
            on_click=lambda e: self.page.run_task(self._save_post, e)
        )
    
    # ─────────────────────────────────────────────────────────────
    # Private Methoden für Handler-Callbacks
    # ─────────────────────────────────────────────────────────────
    
    def _show_status(self, message: str, is_error: bool = False, is_loading: bool = False):
        """Zeigt eine Statusnachricht an."""
        if is_error:
            self.status_text.color = ft.Colors.RED
        elif is_loading:
            self.status_text.color = ft.Colors.BLUE
        else:
            self.status_text.color = ft.Colors.GREEN
        self.status_text.value = message
        self.page.update()
    
    def _show_validation_dialog(self, title: str, message: str, items: List[str]):
        """Zeigt einen Validierungs-Dialog mit Fehlermeldungen."""
        show_validation_dialog(self.page, title, message, items)
    
    def _update_title_label(self):
        """Aktualisiert das Label basierend auf der gewählten Meldungsart."""
        selected_id = list(self.meldungsart.selected)[0] if self.meldungsart.selected else None
        
        selected_status = None
        for status in self.post_statuses:
            if str(status["id"]) == selected_id:
                selected_status = status["name"].lower()
                break
        
        if selected_status == "vermisst":
            self.title_label.value = "Name﹡"
            self.ai_button.visible = False
        else:
            self.title_label.value = "Überschrift﹡"
            self.ai_button.visible = True
        
        self.page.update()
    
    def _update_name_counter(self):
        """Aktualisiert den Zeichenzähler für das Name/Überschrift-Feld."""
        text = self.name_tf.value or ""
        length = len(text)
        self.name_tf.counter_text = f"{length} / {MAX_HEADLINE_LENGTH}"
        self.page.update()
    
    def _update_description_counter(self):
        """Aktualisiert den Zeichenzähler für das Beschreibungsfeld."""
        text = self.info_tf.value or ""
        length = len(text)
        self.info_tf.counter_text = f"{length} / {MAX_DESCRIPTION_LENGTH}"
        self.page.update()
    
    def _toggle_farben_panel(self):
        """Toggle für das Farben-Panel."""
        self.farben_panel_visible["visible"] = not self.farben_panel_visible["visible"]
        self.farben_panel.visible = self.farben_panel_visible["visible"]
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible["visible"]
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()
    
    def _on_color_change(self, color_id: int, is_selected: bool):
        """Handler für Farbänderungen."""
        if is_selected:
            if color_id not in self.selected_farben:
                self.selected_farben.append(color_id)
        else:
            if color_id in self.selected_farben:
                self.selected_farben.remove(color_id)

    def _on_location_change(self) -> None:
        """Lädt Vorschlaege fuer den Standort basierend auf dem Freitext."""
        self.location_selected = {"text": None, "lat": None, "lon": None}
        self._location_query_version += 1
        query = self.location_tf.value or ""
        self.page.run_task(
            self._update_location_suggestions,
            query,
            self._location_query_version,
        )

    async def _update_location_suggestions(self, query: str, version: int) -> None:
        await asyncio.sleep(0.3)
        if version != self._location_query_version:
            return
        if not query or len(query.strip()) < 3:
            self._clear_location_suggestions()
            return
        suggestions = geocode_suggestions(query)
        if not suggestions:
            self._clear_location_suggestions()
            return

        def build_item(item: Dict[str, Any]) -> ft.Control:
            return ft.TextButton(
                item.get("text", ""),
                on_click=lambda e, it=item: self._select_location_suggestion(it),
                style=ft.ButtonStyle(alignment=ft.alignment.center_left),
            )

        self.location_suggestions_list.controls = [build_item(s) for s in suggestions]
        self.location_suggestions_box.visible = True
        self.page.update()

    def _select_location_suggestion(self, item: Dict[str, Any]) -> None:
        self.location_selected = {
            "text": item.get("text"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
        }
        self.location_tf.value = item.get("text", "")
        self._clear_location_suggestions()
        self.page.update()

    def _clear_location_suggestions(self) -> None:
        self.location_suggestions_list.controls = []
        self.location_suggestions_box.visible = False
        self.page.update()
    
    async def _start_ai_recognition_flow(self):
        """Startet den kompletten KI-Rassenerkennungs-Flow."""
        scroll_column = getattr(self, "_form_scroll_column", None)
        await handle_ai_recognition_flow(
            page=self.page,
            recognition_service=self.recognition_service,
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            post_statuses=self.post_statuses,
            meldungsart=self.meldungsart,
            ai_result=self.ai_result,
            ai_recognition_cancelled_ref=self.ai_recognition_cancelled,
            species_list=self.species_list,
            breeds_by_species=self.breeds_by_species,
            species_dd=self.species_dd,
            breed_dd=self.breed_dd,
            info_tf=self.info_tf,
            ai_result_container=self.ai_result_container,
            show_status_callback=self._show_status,
            update_breeds_callback=lambda: self.page.run_task(self._update_breeds),
            form_scroll_column=scroll_column,
        )
    
    async def _pick_photo(self):
        """Öffnet Dateiauswahl und lädt Bild hoch."""
        await handle_view_pick_photo(
            page=self.page,
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            photo_preview=self.photo_preview,
            show_status_callback=self._show_status,
        )
    
    def _remove_photo(self):
        """Entfernt das Foto."""
        handle_view_remove_photo(
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            photo_preview=self.photo_preview,
            status_text=self.status_text,
            page=self.page,
        )
    
    async def _save_post(self, _=None):
        """Speichert die Meldung in der Datenbank."""
        await handle_view_save_post(
            page=self.page,
            sb=self.sb,
            post_service=self.post_service,
            post_relations_service=self.post_relations_service,
            post_storage_service=self.post_storage_service,
            meldungsart=self.meldungsart,
            name_tf=self.name_tf,
            species_dd=self.species_dd,
            breed_dd=self.breed_dd,
            sex_dd=self.sex_dd,
            info_tf=self.info_tf,
            location_tf=self.location_tf,
            location_selected=self.location_selected,
            date_tf=self.date_tf,
            selected_farben=self.selected_farben,
            selected_photo=self.selected_photo,
            post_statuses=self.post_statuses,
            species_list=self.species_list,
            breeds_by_species=self.breeds_by_species,
            title_label=self.title_label,
            farben_checkboxes=self.farben_checkboxes,
            photo_preview=self.photo_preview,
            status_text=self.status_text,
            ai_hint_badge=self.ai_hint_badge,
            show_status_callback=self._show_status,
            show_validation_dialog_callback=self._show_validation_dialog,
            parse_event_date=parse_date,
            on_saved_callback=self.on_saved_callback,
        )
        self.location_selected = {"text": None, "lat": None, "lon": None}
        self._clear_location_suggestions()
    
    async def _load_refs(self, _=None):
        """Lädt alle Referenzdaten aus der Datenbank."""
        def on_color_change_callback(color_id: int, is_selected: bool) -> None:
            self._on_color_change(color_id, is_selected)
        
        def update_breeds_callback() -> None:
            self.page.run_task(self._update_breeds)
        
        def update_title_label_callback() -> None:
            self._update_title_label()
        
        await handle_view_load_references(
            ref_service=self.ref_service,
            meldungsart=self.meldungsart,
            species_dd=self.species_dd,
            sex_dd=self.sex_dd,
            farben_container=self.farben_container,
            farben_checkboxes=self.farben_checkboxes,
            selected_farben=self.selected_farben,
            post_statuses=self.post_statuses,
            species_list=self.species_list,
            breeds_by_species=self.breeds_by_species,
            colors_list=self.colors_list,
            sex_list=self.sex_list,
            page=self.page,
            on_color_change_callback=on_color_change_callback,
            update_breeds_callback=update_breeds_callback,
            update_title_label_callback=update_title_label_callback,
        )
    
    async def _update_breeds(self, _=None):
        """Aktualisiert das Rassen-Dropdown basierend auf der Tierart."""
        await handle_view_update_breeds(
            breed_dd=self.breed_dd,
            species_value=self.species_dd.value,
            breeds_by_species=self.breeds_by_species,
            page=self.page,
        )
    
    # ─────────────────────────────────────────────────────────────
    # Build - Erstellt das UI
    # ─────────────────────────────────────────────────────────────
    
    def build(self) -> ft.Column:
        """Baut und gibt das Formular-Layout zurück."""
        # Photo-Upload-Bereich erstellen
        photo_area = create_photo_upload_area(
            photo_preview=self.photo_preview,
            on_pick_photo=lambda _: self.page.run_task(self._pick_photo),
            on_remove_photo=lambda _: self._remove_photo(),
            page=self.page,
        )
        
        # Formular-Layout aus Components erstellen
        form_column = create_form_layout(
            title_label=self.title_label,
            name_tf=self.name_tf,
            species_dd=self.species_dd,
            breed_dd=self.breed_dd,
            sex_dd=self.sex_dd,
            farben_header=self.farben_header,
            farben_panel=self.farben_panel,
            info_tf=self.info_tf,
            ai_button=self.ai_button,
            ai_result_container=self.ai_result_container,
            location_tf=self.location_tf,
            location_suggestions=self.location_suggestions_box,
            date_tf=self.date_tf,
            save_button=self.save_button,
            status_text=self.status_text,
            photo_area=photo_area,
            page=self.page,
            meldungsart=self.meldungsart,
        )
        
        self._form_scroll_column = ft.Column(
            [form_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        return self._form_scroll_column
