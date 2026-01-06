"""
Post Form View - Hauptformular zum Erstellen von Tier-Meldungen.

Dieses Modul enthält die PostForm-Klasse, die das UI für
Vermisst-/Gefunden-Meldungen bereitstellt.
"""

import os
from datetime import datetime
from typing import Callable, Optional

import flet as ft

from services.references import ReferenceService
from services.posts import PostService
from utils.logging_config import get_logger
from utils.validators import (
    validate_not_empty,
    validate_length,
    validate_date_format,
    validate_list_not_empty,
    sanitize_string,
)
from ui.components import (
    show_success_dialog,
    show_error_dialog,
    show_validation_dialog,
)
from ui.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
)

logger = get_logger(__name__)

from ui.post_form.constants import (
    VALID_IMAGE_TYPES,
    DATE_FORMAT,
    ALLOWED_POST_STATUSES,
    NO_SELECTION_VALUE,
    NO_SELECTION_LABEL,
    UPLOAD_DIR,
)
from ui.post_form.photo_manager import (
    upload_to_storage,
    remove_from_storage,
    cleanup_local_file,
    get_upload_path,
)
from ui.post_form.form_fields import (
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
    populate_dropdown_options,
)


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
        
        # Referenzdaten
        self.post_statuses = []
        self.species_list = []
        self.breeds_by_species = {}
        self.colors_list = []
        self.sex_list = []
        
        # Ausgewählte Werte
        self.selected_farben = []
        self.farben_checkboxes = {}
        self.selected_photo = {"path": None, "name": None, "url": None, "base64": None}
        self.farben_panel_visible = True
        
        # UI-Elemente initialisieren
        self._init_ui_elements()
        
        # Daten laden
        self.page.run_task(self._load_refs)
    
    # ════════════════════════════════════════════════════════════════════
    # UI-INITIALISIERUNG
    # ════════════════════════════════════════════════════════════════════
    
    def _init_ui_elements(self):
        """Initialisiert alle UI-Elemente."""
        # Meldungsart
        self.meldungsart = create_meldungsart_button(self._update_title_label)
        
        # Foto-Vorschau
        self.photo_preview = create_photo_preview()
        
        # Name/Überschrift
        self.title_label = create_title_label()
        self.name_tf = create_name_field()
        
        # Dropdowns
        self.species_dd = create_species_dropdown()
        self.breed_dd = create_breed_dropdown()
        self.sex_dd = create_sex_dropdown()
        
        # Species-Dropdown Event
        self.species_dd.on_change = lambda _: self.page.run_task(self._update_breeds)
        
        # Farben-Container (werden in _load_refs gefüllt)
        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)
        
        # Theme-Farben für Light/Dark Mode (sicherer Zugriff mit Fallback)
        panel_surface_color = getattr(ft.Colors, "SURFACE_VARIANT", None)
        panel_outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
        
        self.farben_panel = ft.Container(
            content=self.farben_container,
            padding=12,
            visible=True,
            bgcolor=panel_surface_color,
            border_radius=8,
            border=ft.border.all(1, panel_outline_color) if panel_outline_color else None,
        )
        
        # Theme-Farben für Light/Dark Mode (sicherer Zugriff mit Fallback)
        surface_color = getattr(ft.Colors, "SURFACE_VARIANT", None)
        outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
        
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
            bgcolor=surface_color,
            border=ft.border.all(1, outline_color) if outline_color else None,
        )
        
        # Beschreibung & Standort
        self.info_tf = create_description_field()
        self.location_tf = create_location_field()
        self.date_tf = create_date_field()
        
        # Status-Nachricht
        self.status_text = create_status_text()
    
    # ════════════════════════════════════════════════════════════════════
    # EVENT HANDLER
    # ════════════════════════════════════════════════════════════════════
    
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
    
    def _show_validation_dialog(self, title: str, message: str, items: list):
        """Zeigt einen Validierungs-Dialog mit Fehlermeldungen."""
        show_validation_dialog(self.page, title, message, items)
    
    def _show_success_dialog(self, title: str, message: str):
        """Zeigt einen Erfolgs-Dialog an."""
        show_success_dialog(self.page, title, message)
    
    def _show_error_dialog(self, title: str, message: str):
        """Zeigt einen Fehler-Dialog an."""
        show_error_dialog(self.page, title, message)
    
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
        else:
            self.title_label.value = "Überschrift﹡"
        self.page.update()
    
    def _on_color_change(self, color_id: int, is_selected: bool):
        """Handler für Farbänderungen."""
        if is_selected:
            if color_id not in self.selected_farben:
                self.selected_farben.append(color_id)
        else:
            if color_id in self.selected_farben:
                self.selected_farben.remove(color_id)
    
    # ════════════════════════════════════════════════════════════════════
    # FOTO-MANAGEMENT
    # ════════════════════════════════════════════════════════════════════
    
    async def _pick_photo(self):
        """Öffnet Dateiauswahl und lädt Bild zu Supabase Storage hoch."""
        
        def on_result(ev: ft.FilePickerResultEvent):
            if ev.files:
                f = ev.files[0]
                self.selected_photo["name"] = f.name
                
                fp.upload([ft.FilePickerUploadFile(
                    f.name,
                    upload_url=self.page.get_upload_url(f.name, 60)
                )])
        
        def on_upload(ev: ft.FilePickerUploadEvent):
            if ev.progress == 1.0:
                try:
                    upload_path = get_upload_path(ev.file_name)
                    
                    # Bild hochladen und komprimieren
                    result = upload_to_storage(self.sb, upload_path, ev.file_name)
                    
                    if result["url"]:
                        self.selected_photo["path"] = result["path"]
                        self.selected_photo["base64"] = result["base64"]
                        self.selected_photo["url"] = result["url"]
                        
                        self.photo_preview.src_base64 = result["base64"]
                        self.photo_preview.visible = True
                        self._show_status(f"✓ Hochgeladen: {ev.file_name}")
                    else:
                        self._show_status("❌ Fehler beim Hochladen", is_error=True)
                    
                    # Lokale Datei aufräumen
                    cleanup_local_file(upload_path)
                    
                except Exception as ex:
                    self._show_status(f"❌ Fehler: {ex}", is_error=True)
        
        fp = ft.FilePicker(on_result=on_result, on_upload=on_upload)
        self.page.overlay.append(fp)
        self.page.update()
        fp.pick_files(allow_multiple=False, allowed_extensions=VALID_IMAGE_TYPES)
    
    def _remove_photo(self):
        """Entfernt das Foto aus der Vorschau und aus Supabase Storage."""
        remove_from_storage(self.sb, self.selected_photo.get("path"))
        
        self.selected_photo = {"path": None, "name": None, "url": None, "base64": None}
        self.photo_preview.visible = False
        self.status_text.value = ""
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # SPEICHERN
    # ════════════════════════════════════════════════════════════════════
    
    async def _save_post(self, _=None):
        """Speichert die Meldung in der Datenbank."""
        
        # Validierung mit zentralen Validatoren
        errors = []
        
        # Name/Überschrift validieren
        name_valid, name_error = validate_not_empty(self.name_tf.value, "Name/Überschrift")
        if not name_valid:
            errors.append(f"• {name_error}")
        else:
            # Länge prüfen (max. MAX_HEADLINE_LENGTH Zeichen)
            name_length_valid, name_length_error = validate_length(
                self.name_tf.value, max_length=MAX_HEADLINE_LENGTH, field_name="Name/Überschrift"
            )
            if not name_length_valid:
                errors.append(f"• {name_length_error}")
        
        # Tierart validieren
        if not self.species_dd.value:
            errors.append("• Tierart ist erforderlich")
        
        # Farben validieren
        colors_valid, colors_error = validate_list_not_empty(
            self.selected_farben, "Farben", min_items=1
        )
        if not colors_valid:
            errors.append(f"• {colors_error}")
        
        # Beschreibung validieren
        desc_valid, desc_error = validate_not_empty(self.info_tf.value, "Beschreibung")
        if not desc_valid:
            errors.append(f"• {desc_error}")
        else:
            # Beschreibung sollte mindestens MIN_DESCRIPTION_LENGTH Zeichen haben
            desc_length_valid, desc_length_error = validate_length(
                self.info_tf.value, min_length=MIN_DESCRIPTION_LENGTH, max_length=MAX_DESCRIPTION_LENGTH, field_name="Beschreibung"
            )
            if not desc_length_valid:
                errors.append(f"• {desc_length_error}")
        
        # Ort validieren
        location_valid, location_error = validate_not_empty(self.location_tf.value, "Ort")
        if not location_valid:
            errors.append(f"• {location_error}")
        else:
            # Ort sollte max. MAX_LOCATION_LENGTH Zeichen haben
            location_length_valid, location_length_error = validate_length(
                self.location_tf.value, max_length=MAX_LOCATION_LENGTH, field_name="Ort"
            )
            if not location_length_valid:
                errors.append(f"• {location_length_error}")
        
        # Datum validieren
        date_valid, date_error = validate_date_format(self.date_tf.value, DATE_FORMAT)
        if not date_valid:
            errors.append(f"• {date_error}")
        
        # Foto validieren
        if not self.selected_photo.get("url"):
            errors.append("• Foto ist erforderlich")
        
        if errors:
            self._show_validation_dialog(
                "Pflichtfelder fehlen",
                "Bitte korrigiere folgende Fehler:",
                errors
            )
            return
        
        # Datum parsen (nach Validierung)
        try:
            event_date = datetime.strptime(self.date_tf.value.strip(), DATE_FORMAT).date()
        except ValueError:
            # Sollte nicht passieren nach Validierung, aber als Fallback
            self._show_validation_dialog(
                "Ungültiges Format",
                "Das Datum hat ein falsches Format.",
                ["• Bitte verwende: TT.MM.YYYY", "• Beispiel: 04.01.2026"]
            )
            return
        
        # Eingeloggten Benutzer holen
        try:
            user_response = self.sb.auth.get_user()
            if not user_response or not user_response.user:
                self._show_error_dialog("Nicht eingeloggt", "Bitte melden Sie sich an, um eine Meldung zu erstellen.")
                return
            user_id = user_response.user.id
        except Exception as e:
            self._show_error_dialog("Fehler", f"Fehler beim Abrufen des Benutzers: {e}")
            return
        
        try:
            self._show_status("⏳ Erstelle Meldung...", is_loading=True)
            
            # Input sanitizen vor dem Speichern
            headline = sanitize_string(self.name_tf.value, max_length=MAX_HEADLINE_LENGTH)
            description = sanitize_string(self.info_tf.value, max_length=MAX_DESCRIPTION_LENGTH)
            location = sanitize_string(self.location_tf.value, max_length=MAX_LOCATION_LENGTH)
            
            post_data = {
                "user_id": user_id,
                "post_status_id": int(list(self.meldungsart.selected)[0]),
                "headline": headline,
                "description": description,
                "species_id": int(self.species_dd.value),
                "breed_id": int(self.breed_dd.value) if self.breed_dd.value and self.breed_dd.value != NO_SELECTION_VALUE else None,
                "sex_id": int(self.sex_dd.value) if self.sex_dd.value and self.sex_dd.value != NO_SELECTION_VALUE else None,
                "event_date": event_date.isoformat(),
                "location_text": location,
            }
            
            new_post = self.post_service.create(post_data)
            post_id = new_post["id"]
            
            # Farben verknüpfen
            for color_id in self.selected_farben:
                self.post_service.add_color(post_id, color_id)
            
            # Bild verknüpfen
            if self.selected_photo.get("url"):
                self.post_service.add_photo(post_id, self.selected_photo["url"])
            
            self._show_status("")
            self._show_success_dialog("Meldung erstellt", "Ihre Meldung wurde erfolgreich veröffentlicht!")
            
            self._reset_form()
            
            if self.on_saved_callback:
                self.on_saved_callback(post_id)
                
        except Exception as ex:
            self._show_status("")
            self._show_error_dialog("Speichern fehlgeschlagen", f"Fehler beim Erstellen der Meldung: {ex}")
    
    def _reset_form(self):
        """Setzt das Formular auf Standardwerte zurück."""
        if self.post_statuses:
            self.meldungsart.selected = {str(self.post_statuses[0]["id"])}
        self.name_tf.value = ""
        if self.species_list:
            self.species_dd.value = str(self.species_list[0]["id"])
            # Rassen für die ausgewählte Tierart laden
            species_id = self.species_list[0]["id"]
            breeds = self.breeds_by_species.get(species_id, [])
            self.breed_dd.options = [ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)] + [
                ft.dropdown.Option(str(b["id"]), b["name"]) for b in breeds
            ]
        self.breed_dd.value = NO_SELECTION_VALUE
        self.sex_dd.value = NO_SELECTION_VALUE
        self.info_tf.value = ""
        self.location_tf.value = ""
        self.date_tf.value = ""
        
        self.selected_farben.clear()
        for cb in self.farben_checkboxes.values():
            cb.value = False
        
        self.selected_photo = {"path": None, "name": None, "url": None, "base64": None}
        self.photo_preview.visible = False
        self.title_label.value = "Name﹡"
        self.status_text.value = ""
        
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # DATEN LADEN
    # ════════════════════════════════════════════════════════════════════
    
    async def _load_refs(self, _=None):
        """Lädt alle Referenzdaten aus der Datenbank."""
        try:
            # Meldungsarten laden
            all_statuses = self.ref_service.get_post_statuses()
            self.post_statuses = [
                s for s in all_statuses
                if s["name"].lower() in ALLOWED_POST_STATUSES
            ]
            self.meldungsart.segments = [
                ft.Segment(value=str(s["id"]), label=ft.Text(s["name"]))
                for s in self.post_statuses
            ]
            if self.post_statuses:
                self.meldungsart.selected = {str(self.post_statuses[0]["id"])}
            
            # Andere Referenzdaten laden
            self.species_list = self.ref_service.get_species()
            self.breeds_by_species = self.ref_service.get_breeds_by_species()
            self.colors_list = self.ref_service.get_colors()
            self.sex_list = self.ref_service.get_sex()
            
            # Species Dropdown füllen
            populate_dropdown_options(self.species_dd, self.species_list)
            
            # Geschlecht Dropdown mit "Keine Angabe"
            populate_dropdown_options(self.sex_dd, self.sex_list, with_none_option=True)
            
            # Farben-Checkboxes erstellen
            self.farben_container.controls = []
            for color in self.colors_list:
                def on_color_change(e, c_id=color["id"]):
                    self._on_color_change(c_id, e.control.value)
                
                cb = ft.Checkbox(label=color["name"], value=False, on_change=on_color_change)
                self.farben_checkboxes[color["id"]] = cb
                self.farben_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
                )
            
            if self.species_list:
                self.species_dd.value = str(self.species_list[0]["id"])
            
            self.page.update()
            
            if self.species_list:
                await self._update_breeds()
                self.page.update()
                
        except Exception as ex:
            logger.error(f"Fehler beim Laden der Referenzdaten: {ex}", exc_info=True)
    
    async def _update_breeds(self, _=None):
        """Aktualisiert das Rassen-Dropdown basierend auf der Tierart."""
        try:
            sid = int(self.species_dd.value) if self.species_dd.value else None
            if sid and sid in self.breeds_by_species:
                self.breed_dd.options = [ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)]
                self.breed_dd.options += [
                    ft.dropdown.Option(str(b["id"]), b["name"])
                    for b in self.breeds_by_species[sid]
                ]
                self.breed_dd.value = NO_SELECTION_VALUE
            else:
                self.breed_dd.options = [ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)]
                self.breed_dd.value = NO_SELECTION_VALUE
            self.page.update()
        except Exception as ex:
            logger.error(f"Fehler beim Aktualisieren der Rassen: {ex}", exc_info=True)
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD - Erstellt das UI
    # ════════════════════════════════════════════════════════════════════
    
    def build(self) -> ft.Column:
        """Baut und gibt das Formular-Layout zurück."""
        
        # Theme-Farben für Light/Dark Mode
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        surface_color = getattr(ft.Colors, "SURFACE_VARIANT", None)
        outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
        on_surface_variant = getattr(ft.Colors, "ON_SURFACE_VARIANT", None)
        
        # Text-Farben basierend auf Theme
        text_color = on_surface_variant if on_surface_variant else (ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_700)
        icon_color = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_500
        border_color = outline_color if outline_color else (ft.Colors.GREY_600 if is_dark else ft.Colors.GREY_300)
        
        # Foto-Upload Bereich
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
                
                self.meldungsart,
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
