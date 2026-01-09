"""
Post Form-View mit Meldungsformular.

Enthält UI-Komposition und koordiniert Post Form-Features.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List

import flet as ft

from services.posts.references import ReferenceService
from services.posts import PostService, PostRelationsService, PostStorageService
from services.ai.pet_recognition import get_recognition_service
from utils.logging_config import get_logger
from ui.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    DATE_FORMAT,
    NO_SELECTION_VALUE,
)
from ui.components import show_validation_dialog, show_success_dialog, show_error_dialog
from ui.helpers import get_theme_colors

from .components import (
    create_meldungsart_button,
    create_photo_preview,
    create_name_field,
    create_title_label,
    create_species_dropdown,
    create_breed_dropdown,
    create_sex_dropdown,
    create_description_field,
    create_location_field,
    create_date_field,
    create_status_text,
    create_ai_recognition_button,
    create_ai_result_container,
)
from .features.photo_upload import handle_pick_photo, handle_remove_photo
from .features.form_validation import validate_form_fields
from .features.post_upload import handle_save_post, reset_form_fields
from ui.helpers import parse_date
from .features.references import load_and_populate_references, update_breeds_dropdown
from .features.ai_recognition import (
    handle_start_ai_recognition,
    show_consent_dialog,
    perform_ai_recognition,
    show_ai_result,
    show_ai_suggestion_dialog,
)

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
        
        # KI-Erkennungs-State
        self.ai_result: Optional[Dict[str, Any]] = None
        self.ai_recognition_cancelled = {"cancelled": False}
        
        # Referenzdaten
        self.post_statuses: List[Dict[str, Any]] = []
        self.species_list: List[Dict[str, Any]] = []
        self.breeds_by_species: Dict[int, List[Dict[str, Any]]] = {}
        self.colors_list: List[Dict[str, Any]] = []
        self.sex_list: List[Dict[str, Any]] = []
        
        # Ausgewählte Werte
        self.selected_farben: List[int] = []
        self.farben_checkboxes: Dict[int, ft.Checkbox] = {}
        self.selected_photo: Dict[str, Any] = {"path": None, "name": None, "url": None, "base64": None}
        self.farben_panel_visible = True
        
        # UI-Elemente initialisieren
        self._init_ui_elements()
        
        # Daten laden
        self.page.run_task(self._load_refs)
    
    # ─────────────────────────────────────────────────────────────
    # UI-Initialisierung
    # ─────────────────────────────────────────────────────────────
    
    def _init_ui_elements(self):
        """Initialisiert alle UI-Elemente."""
        # Meldungsart
        self.meldungsart = create_meldungsart_button(self._update_title_label)
        
        # Foto-Vorschau
        self.photo_preview = create_photo_preview()
        
        # Name/Überschrift
        self.title_label = create_title_label()
        self.name_tf = create_name_field()
        self.name_tf.on_change = self._update_name_counter
        
        # Dropdowns
        self.species_dd = create_species_dropdown()
        self.breed_dd = create_breed_dropdown()
        self.sex_dd = create_sex_dropdown()
        self.species_dd.on_change = lambda _: self.page.run_task(self._update_breeds)
        
        # Farben-Container
        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)
        
        # Theme-Farben holen
        theme_colors = get_theme_colors(self.page)
        
        self.farben_panel = ft.Container(
            content=self.farben_container,
            padding=12,
            visible=True,
            bgcolor=theme_colors["surface"],
            border_radius=8,
            border=ft.border.all(1, theme_colors["outline"]) if theme_colors["outline"] else None,
        )
        
        self.farben_header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PALETTE, size=18),
                    ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    self.farben_toggle_icon,
                ],
                spacing=12,
            ),
            padding=8,
            on_click=self._toggle_farben_panel,
            border_radius=8,
            bgcolor=theme_colors["surface"],
            border=ft.border.all(1, theme_colors["outline"]) if theme_colors["outline"] else None,
        )
        
        # Beschreibung & Standort
        self.info_tf = create_description_field()
        self.location_tf = create_location_field()
        self.date_tf = create_date_field()
        
        # Status-Nachricht
        self.status_text = create_status_text()
        
        # KI-Button und Container
        self.ai_button = create_ai_recognition_button(
            lambda _: self.page.run_task(self._start_ai_recognition)
        )
        self.ai_result_container = create_ai_result_container()
        self.ai_hint_badge: Optional[ft.Control] = None
    
    # ─────────────────────────────────────────────────────────────
    # Event Handler
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
    
    def _toggle_farben_panel(self, _):
        """Toggle für das Farben-Panel."""
        self.farben_panel_visible = not self.farben_panel_visible
        self.farben_panel.visible = self.farben_panel_visible
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()
    
    def _update_title_label(self, _=None):
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

    def _update_name_counter(self, _=None):
        """Aktualisiert den Zeichenzähler für das Name/Überschrift-Feld."""
        text = self.name_tf.value or ""
        length = len(text)
        self.name_tf.counter_text = f"{length} / {MAX_HEADLINE_LENGTH}"
        self.page.update()

    def _update_description_counter(self, _=None):
        """Aktualisiert den Zeichenzähler für das Beschreibungsfeld."""
        text = self.info_tf.value or ""
        length = len(text)
        self.info_tf.counter_text = f"{length} / {MAX_DESCRIPTION_LENGTH}"
        self.page.update()

    def _on_color_change(self, color_id: int, is_selected: bool):
        """Handler für Farbänderungen."""
        if is_selected:
            if color_id not in self.selected_farben:
                self.selected_farben.append(color_id)
        else:
            if color_id in self.selected_farben:
                self.selected_farben.remove(color_id)
    
    # ─────────────────────────────────────────────────────────────
    # KI-Rassenerkennung
    # ─────────────────────────────────────────────────────────────
    
    async def _start_ai_recognition(self):
        """Startet die KI-Rassenerkennung."""
        await handle_start_ai_recognition(
            page=self.page,
            selected_photo=self.selected_photo,
            post_statuses=self.post_statuses,
            meldungsart=self.meldungsart,
            show_consent_dialog_callback=lambda: self.page.run_task(self._show_consent_dialog_wrapper),
        )
    
    async def _show_consent_dialog_wrapper(self):
        """Wrapper für Consent-Dialog."""
        await show_consent_dialog(
            page=self.page,
            on_accept=lambda: self.page.run_task(self._perform_ai_recognition),
        )
    
    async def _perform_ai_recognition(self):
        """Führt die KI-Erkennung durch."""
        await perform_ai_recognition(
            page=self.page,
            recognition_service=self.recognition_service,
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            ai_recognition_cancelled_ref=self.ai_recognition_cancelled,
            show_status_callback=self._show_status,
            show_ai_result_callback=self._show_ai_result_wrapper,
            show_ai_suggestion_callback=self._show_ai_suggestion_wrapper,
        )
    
    def _show_ai_result_wrapper(self, result: Dict[str, Any]):
        """Wrapper für AI-Ergebnis anzeigen."""
        self.ai_result = result
        show_ai_result(
            ai_result_container=self.ai_result_container,
            result=result,
            on_accept=self._accept_ai_result,
            on_reject=self._reject_ai_result,
            page=self.page,
        )
    
    def _accept_ai_result(self):
        """Übernimmt das KI-Erkennungsergebnis in die Formularfelder."""
        if not self.ai_result:
            return
        
        species_name = self.ai_result["species"]
        species_id = None
        for species in self.species_list:
            if species["name"].lower() == species_name.lower():
                species_id = species["id"]
                break
        
        if species_id:
            self.species_dd.value = str(species_id)
            self.page.run_task(self._update_breeds)
        
        async def set_breed():
            await self._update_breeds()
            
            breed_name = self.ai_result["breed"]
            breed_id = None
            
            if species_id and species_id in self.breeds_by_species:
                for breed in self.breeds_by_species[species_id]:
                    if breed["name"].lower() == breed_name.lower():
                        breed_id = breed["id"]
                        break
            
            if breed_id:
                self.breed_dd.value = str(breed_id)
            
            confidence_percent = int(self.ai_result["confidence"] * 100)
            ai_info = f"[KI-Erkennung: {species_name}, Rasse: {breed_name} ({confidence_percent}% Konfidenz)]"
            
            current_description = self.info_tf.value or ""
            if current_description:
                self.info_tf.value = f"{ai_info}\n\n{current_description}"
            else:
                self.info_tf.value = ai_info
            
            self.ai_result_container.visible = False
            self._show_status("KI-Vorschlag übernommen!", is_error=False)
            self.page.update()
        
        self.page.run_task(set_breed)
    
    def _reject_ai_result(self):
        """Lehnt das KI-Erkennungsergebnis ab."""
        self.ai_result = None
        self.ai_result_container.visible = False
        self._show_status("KI-Vorschlag abgelehnt. Bitte tragen Sie die Daten manuell ein.", is_error=False)
        self.page.update()
    
    def _show_ai_suggestion_wrapper(self, error_message: str, suggested_breed: Optional[str], suggested_species: Optional[str], confidence: float):
        """Wrapper für AI-Vorschlag anzeigen."""
        def on_accept(breed: str, species: Optional[str]):
            # Ähnlich wie _accept_ai_result, aber mit niedrigerer Konfidenz
            pass
        
        show_ai_suggestion_dialog(
            page=self.page,
            error_message=error_message,
            suggested_breed=suggested_breed or "",
            suggested_species=suggested_species,
            confidence=confidence,
            on_accept=on_accept,
        )
    
    # ─────────────────────────────────────────────────────────────
    # Foto-Management
    # ─────────────────────────────────────────────────────────────
    
    async def _pick_photo(self):
        """Öffnet Dateiauswahl und lädt Bild hoch."""
        await handle_pick_photo(
            page=self.page,
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            photo_preview=self.photo_preview,
            show_status_callback=self._show_status,
        )
    
    def _remove_photo(self):
        """Entfernt das Foto."""
        handle_remove_photo(
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            photo_preview=self.photo_preview,
            status_text=self.status_text,
            page=self.page,
        )
    
    # ─────────────────────────────────────────────────────────────
    # Speichern
    # ─────────────────────────────────────────────────────────────
    
    async def _save_post(self, _=None):
        """Speichert die Meldung in der Datenbank."""
        is_valid, errors = validate_form_fields(
            name_value=self.name_tf.value,
            species_value=self.species_dd.value,
            selected_farben=self.selected_farben,
            description_value=self.info_tf.value,
            location_value=self.location_tf.value,
            date_value=self.date_tf.value,
            photo_url=self.selected_photo.get("url"),
        )
        
        if not is_valid:
            self._show_validation_dialog(
                "Pflichtfelder fehlen",
                "Bitte korrigiere folgende Fehler:",
                errors
            )
            return
        
        await handle_save_post(
            page=self.page,
            sb=self.sb,
            post_service=self.post_service,
            post_relations_service=self.post_relations_service,
            meldungsart=self.meldungsart,
            name_tf=self.name_tf,
            species_dd=self.species_dd,
            breed_dd=self.breed_dd,
            sex_dd=self.sex_dd,
            info_tf=self.info_tf,
            location_tf=self.location_tf,
            date_tf=self.date_tf,
            selected_farben=self.selected_farben,
            selected_photo=self.selected_photo,
            show_status_callback=self._show_status,
            show_validation_dialog_callback=self._show_validation_dialog,
            parse_event_date=parse_date,
            on_saved_callback=self.on_saved_callback,
        )
        
        # Formular zurücksetzen
        reset_form_fields(
            post_statuses=self.post_statuses,
            meldungsart=self.meldungsart,
            name_tf=self.name_tf,
            species_dd=self.species_dd,
            breed_dd=self.breed_dd,
            sex_dd=self.sex_dd,
            info_tf=self.info_tf,
            location_tf=self.location_tf,
            date_tf=self.date_tf,
            title_label=self.title_label,
            selected_farben=self.selected_farben,
            farben_checkboxes=self.farben_checkboxes,
            selected_photo=self.selected_photo,
            photo_preview=self.photo_preview,
            status_text=self.status_text,
            species_list=self.species_list,
            breeds_by_species=self.breeds_by_species,
            ai_hint_badge=self.ai_hint_badge,
            page=self.page,
        )
    
    # ─────────────────────────────────────────────────────────────
    # Daten laden
    # ─────────────────────────────────────────────────────────────
    
    async def _load_refs(self, _=None):
        """Lädt alle Referenzdaten aus der Datenbank."""
        try:
            result = await load_and_populate_references(
                ref_service=self.ref_service,
                meldungsart=self.meldungsart,
                species_dd=self.species_dd,
                sex_dd=self.sex_dd,
                farben_container=self.farben_container,
                farben_checkboxes=self.farben_checkboxes,
                selected_farben=self.selected_farben,
                on_color_change_callback=self._on_color_change,
                page=self.page,
            )
            
            self.post_statuses = result["post_statuses"]
            self.species_list = result["species_list"]
            self.breeds_by_species = result["breeds_by_species"]
            self.colors_list = result["colors_list"]
            self.sex_list = result["sex_list"]
            
            if self.species_list:
                await self._update_breeds()
                self.page.update()
            
            self._update_title_label()
                
        except Exception as ex:
            logger.error(f"Fehler beim Laden der Referenzdaten: {ex}", exc_info=True)
    
    async def _update_breeds(self, _=None):
        """Aktualisiert das Rassen-Dropdown basierend auf der Tierart."""
        update_breeds_dropdown(
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
        # Theme-Farben holen
        theme_colors = get_theme_colors(self.page)
        text_color = theme_colors["text"]
        icon_color = theme_colors["icon"]
        border_color = theme_colors["border"]
        
        photo_area = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=icon_color),
                        ft.Text("Foto hochladen (Tippen)", color=text_color, size=12),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    width=400,
                    height=150,
                    border=ft.border.all(2, border_color),
                    border_radius=8,
                    on_click=lambda _: self.page.run_task(self._pick_photo),
                ),
                self.photo_preview,
                ft.TextButton("Foto entfernen", icon=ft.Icons.DELETE, on_click=lambda _: self._remove_photo()),
            ], spacing=10),
        )
        
        form_column = ft.Column(
            [
                ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                
                ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=text_color),
                photo_area,
                ft.Divider(height=20),
                
                self.title_label,
                self.name_tf,
                ft.Row([self.species_dd, self.breed_dd, self.sex_dd], spacing=15, wrap=True),
                
                self.farben_header,
                self.farben_panel,
                ft.Divider(height=20),
                
                ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=text_color),
                self.info_tf,
                self.ai_button,
                self.ai_result_container,
                ft.Divider(height=20),
                
                ft.Text("Standort & Datum﹡", size=12, weight=ft.FontWeight.W_600, color=text_color),
                self.location_tf,
                self.date_tf,
                ft.Divider(height=20),
                
                ft.Row([
                    ft.FilledButton(
                        "Meldung erstellen",
                        width=200,
                        on_click=lambda e: self.page.run_task(self._save_post, e)
                    ),
                ]),
                self.status_text,
            ],
            spacing=10,
        )
        
        return ft.Column(
            [form_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
