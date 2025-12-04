"""
Post Form - Meldungsformular für Haustiere.

Dieses Modul implementiert das Formular zum Erstellen neuer Tiermeldungen
(Vermisste oder gefundene Haustiere) in der PetBuddy-Anwendung.

"""

import os
import io
import base64
from datetime import datetime
from typing import Callable, Optional

import flet as ft
from PIL import Image
from services.references import ReferenceService
from services.posts import PostService


class PostForm:
    """Formular zum Erstellen von Tier-Meldungen (vermisst/gefunden)."""
    
    # ════════════════════════════════════════════════════════════════════
    # KONSTANTEN
    # ════════════════════════════════════════════════════════════════════
    
    VALID_IMAGE_TYPES: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    PLACEHOLDER_IMAGE: str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    STORAGE_BUCKET: str = "pet-images"
    UPLOAD_DIR: str = "image_uploads"
    DATE_FORMAT: str = "%d.%m.%Y"
    ALLOWED_POST_STATUSES: list[str] = ["vermisst", "fundtier"]
    MAX_IMAGE_SIZE: tuple[int, int] = (800, 800)
    IMAGE_QUALITY: int = 85
    
    # UI-Konstanten
    FIELD_WIDTH_SMALL: int = 250
    FIELD_WIDTH_MEDIUM: int = 400
    FIELD_WIDTH_LARGE: int = 500
    NO_SELECTION_VALUE: str = "none"
    NO_SELECTION_LABEL: str = "— Keine Angabe —"
    
    def __init__(
        self,
        page: ft.Page,
        sb,
        on_saved_callback: Optional[Callable] = None
    ):
        """Initialisiert das Meldungsformular.
        
        Args:
            page: Flet Page-Instanz
            sb: Supabase Client
            on_saved_callback: Callback nach erfolgreichem Speichern
        """
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
    
    def _init_ui_elements(self):
        # Initialisiert alle UI-Elemente.
        # Meldungsart SegmentedButton 
        self.meldungsart = ft.SegmentedButton(
            selected={"1"},
            segments=[ft.Segment(value="1", label=ft.Text("Vermisst"))],
            allow_empty_selection=False,
            allow_multiple_selection=False,
            on_change=self._update_title_label,
        )
        
        # Foto-Vorschau
        self.photo_preview = ft.Image(
            width=self.FIELD_WIDTH_MEDIUM, height=250,
            fit=ft.ImageFit.COVER,
            visible=False,
            src_base64=self.PLACEHOLDER_IMAGE
        )
        
        # Name/Überschrift
        self.title_label = ft.Text(
            "Name﹡", size=14,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.GREY_700
        )
        self.name_tf = ft.TextField(width=self.FIELD_WIDTH_MEDIUM)
        
        # Dropdowns
        self.species_dd = ft.Dropdown(label="Tierart﹡", text_size=14, width=self.FIELD_WIDTH_SMALL)
        self.breed_dd = ft.Dropdown(label="Rasse (optional)", width=self.FIELD_WIDTH_SMALL)
        self.sex_dd = ft.Dropdown(label="Geschlecht (optional)", width=self.FIELD_WIDTH_SMALL)
        
        # Species-Dropdown Event
        self.species_dd.on_change = lambda _: self.page.run_task(self._update_breeds)
        
        # Farben-Container
        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)
        
        self.farben_panel = ft.Container(
            content=self.farben_container,
            padding=12,
            visible=True,
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
            bgcolor=ft.Colors.GREY_100,
        )
        
        # Beschreibung
        self.info_tf = ft.TextField(
            multiline=True,
            max_lines=4,
            width=self.FIELD_WIDTH_LARGE,
            min_lines=2,
        )
        
        # Standort & Datum
        self.location_tf = ft.TextField(label="Ort﹡", width=self.FIELD_WIDTH_LARGE)
        self.date_tf = ft.TextField(
            label="Datum﹡ (TT.MM.YYYY)",
            width=self.FIELD_WIDTH_SMALL,
            hint_text="z.B. 15.11.2025"
        )
        
        # Status-Nachricht
        self.status_text = ft.Text("", color=ft.Colors.BLUE, size=12)
    
    # ════════════════════════════════════════════════════════════════════
    # EVENT HANDLER
    # ════════════════════════════════════════════════════════════════════
    
    def _show_status(self, message: str, is_error: bool = False, is_loading: bool = False):
        """Zeigt eine Statusnachricht an.
        
        Args:
            message: Die anzuzeigende Nachricht
            is_error: True für Fehlermeldung (rot)
            is_loading: True für Ladevorgang (blau)w
        """
        if is_error:
            self.status_text.color = ft.Colors.RED
        elif is_loading:
            self.status_text.color = ft.Colors.BLUE
        else:
            self.status_text.color = ft.Colors.GREEN
        self.status_text.value = message
        self.page.update()
    
    def _toggle_farben_panel(self, _):
        # Toggle für das Farben-Panel.
        self.farben_panel_visible = not self.farben_panel_visible
        self.farben_panel.visible = self.farben_panel_visible
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()
    
    def _update_title_label(self, _=None):
        # Aktualisiert das Label basierend auf der gewählten Meldungsart.
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
    
    # ════════════════════════════════════════════════════════════════════
    # FOTO-MANAGEMENT
    # ════════════════════════════════════════════════════════════════════
    
    def _compress_image(self, file_path: str) -> tuple[bytes, str]:
        # Komprimiert ein Bild für schnelleres Laden.
        with Image.open(file_path) as img:
            # EXIF-Orientierung beibehalten
            img = img.convert("RGB")
            
            # Größe anpassen wenn nötig
            img.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Als JPEG komprimieren
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.IMAGE_QUALITY, optimize=True)
            buffer.seek(0)
            
            return buffer.read(), "jpeg"
    
    async def _pick_photo(self):
        # Öffnet Dateiauswahl und lädt Bild zu Supabase Storage hoch.
        
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
                    upload_path = f"{self.UPLOAD_DIR}/{ev.file_name}"
                    
                    # Bild komprimieren für schnelleres Laden
                    compressed_bytes, file_ext = self._compress_image(upload_path)
                    image_data = base64.b64encode(compressed_bytes).decode()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Immer .jpg als Extension da wir zu JPEG konvertieren
                    original_name = ev.file_name.rsplit(".", 1)[0]
                    storage_filename = f"{timestamp}_{original_name}.jpg"
                    
                    self.sb.storage.from_(self.STORAGE_BUCKET).upload(
                        path=storage_filename,
                        file=compressed_bytes,
                        file_options={"content-type": "image/jpeg"}
                    )
                    
                    public_url = self.sb.storage.from_(self.STORAGE_BUCKET).get_public_url(storage_filename)
                    
                    self.selected_photo["path"] = storage_filename
                    self.selected_photo["base64"] = image_data
                    self.selected_photo["url"] = public_url
                    
                    self.photo_preview.src_base64 = image_data
                    self.photo_preview.visible = True
                    self._show_status(f"✓ Hochgeladen: {ev.file_name}")
                    
                    os.remove(upload_path)
                    
                except Exception as ex:
                    self._show_status(f"❌ Fehler: {ex}", is_error=True)
        
        fp = ft.FilePicker(on_result=on_result, on_upload=on_upload)
        self.page.overlay.append(fp)
        self.page.update()
        fp.pick_files(allow_multiple=False, allowed_extensions=self.VALID_IMAGE_TYPES)
    
    def _remove_photo(self):
        # Entfernt das Foto aus der Vorschau und aus Supabase Storage.
        try:
            if self.selected_photo.get("path"):
                self.sb.storage.from_(self.STORAGE_BUCKET).remove([self.selected_photo["path"]])
        except Exception as ex:
            print(f"Fehler beim Löschen aus Storage: {ex}")
        
        self.selected_photo = {"path": None, "name": None, "url": None, "base64": None}
        self.photo_preview.visible = False
        self.status_text.value = ""
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # SPEICHERN
    # ════════════════════════════════════════════════════════════════════
    
    async def _save_post(self, _=None):
        # Speichert die Meldung in der Datenbank.
        
        # Validierung
        errors = []
        if not self.name_tf.value or not self.name_tf.value.strip():
            errors.append("Name/Überschrift")
        if not self.species_dd.value:
            errors.append("Tierart")
        if not self.selected_farben:
            errors.append("Mindestens eine Farbe")
        if not self.info_tf.value or not self.info_tf.value.strip():
            errors.append("Beschreibung")
        if not self.location_tf.value or not self.location_tf.value.strip():
            errors.append("Ort")
        if not self.date_tf.value or not self.date_tf.value.strip():
            errors.append("Datum")
        if not self.selected_photo.get("url"):
            errors.append("Foto")
        
        if errors:
            self._show_status(f"❌ Bitte ausfüllen: {', '.join(errors)}", is_error=True)
            return
        
        # Datum parsen
        try:
            event_date = datetime.strptime(self.date_tf.value.strip(), self.DATE_FORMAT).date()
        except ValueError:
            self._show_status("❌ Ungültiges Datum. Format: TT.MM.YYYY", is_error=True)
            return
        
        # Eingeloggten Benutzer holen
        try:
            user_response = self.sb.auth.get_user()
            if not user_response or not user_response.user:
                self._show_status("❌ Nicht eingeloggt. Bitte neu anmelden.", is_error=True)
                return
            user_id = user_response.user.id
        except Exception as e:
            self._show_status(f"❌ Fehler beim Abrufen des Benutzers: {e}", is_error=True)
            return
        
        try:
            self._show_status("⏳ Erstelle Meldung...", is_loading=True)
            
            post_data = {
                "user_id": user_id,
                "post_status_id": int(list(self.meldungsart.selected)[0]),
                "headline": self.name_tf.value.strip(),
                "description": self.info_tf.value.strip(),
                "species_id": int(self.species_dd.value),
                "breed_id": int(self.breed_dd.value) if self.breed_dd.value and self.breed_dd.value != self.NO_SELECTION_VALUE else None,
                "sex_id": int(self.sex_dd.value) if self.sex_dd.value and self.sex_dd.value != self.NO_SELECTION_VALUE else None,
                "event_date": event_date.isoformat(),
                "location_text": self.location_tf.value.strip(),
            }
            
            new_post = self.post_service.create(post_data)
            post_id = new_post["id"]
            
            # Farben verknüpfen
            for color_id in self.selected_farben:
                self.post_service.add_color(post_id, color_id)
            
            # Bild verknüpfen
            if self.selected_photo.get("url"):
                self.post_service.add_photo(post_id, self.selected_photo["url"])
            
            self._show_status("✓ Meldung erfolgreich erstellt!")
            
            self._reset_form()
            
            if self.on_saved_callback:
                self.on_saved_callback(post_id)
                
        except Exception as ex:
            self._show_status(f"❌ Fehler beim Speichern: {ex}", is_error=True)
    
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
            self.breed_dd.options = [ft.dropdown.Option(self.NO_SELECTION_VALUE, "- Keine Angabe -")] + [
                ft.dropdown.Option(str(b["id"]), b["name"]) for b in breeds
            ]
        self.breed_dd.value = self.NO_SELECTION_VALUE
        self.sex_dd.value = self.NO_SELECTION_VALUE
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
        # Lädt alle Referenzdaten aus der Datenbank.
        try:
            # Meldungsarten laden
            all_statuses = self.ref_service.get_post_statuses()
            self.post_statuses = [
                s for s in all_statuses
                if s["name"].lower() in self.ALLOWED_POST_STATUSES
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
            self.species_dd.options = [
                ft.dropdown.Option(str(s["id"]), s["name"])
                for s in self.species_list
            ]
            
            # Geschlecht Dropdown mit "Keine Angabe"
            self.sex_dd.options = [ft.dropdown.Option(self.NO_SELECTION_VALUE, self.NO_SELECTION_LABEL)]
            self.sex_dd.options += [
                ft.dropdown.Option(str(s["id"]), s["name"])
                for s in self.sex_list
            ]
            self.sex_dd.value = self.NO_SELECTION_VALUE
            
            # Farben-Checkboxes erstellen
            self.farben_container.controls = []
            for color in self.colors_list:
                def on_color_change(e, c_id=color["id"]):
                    if e.control.value:
                        if c_id not in self.selected_farben:
                            self.selected_farben.append(c_id)
                    else:
                        if c_id in self.selected_farben:
                            self.selected_farben.remove(c_id)
                
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
            print(f"Fehler beim Laden der Referenzdaten: {ex}")
    
    async def _update_breeds(self, _=None):
        """Aktualisiert das Rassen-Dropdown basierend auf der Tierart."""
        try:
            sid = int(self.species_dd.value) if self.species_dd.value else None
            if sid and sid in self.breeds_by_species:
                self.breed_dd.options = [ft.dropdown.Option(self.NO_SELECTION_VALUE, self.NO_SELECTION_LABEL)]
                self.breed_dd.options += [
                    ft.dropdown.Option(str(b["id"]), b["name"])
                    for b in self.breeds_by_species[sid]
                ]
                self.breed_dd.value = self.NO_SELECTION_VALUE
            else:
                self.breed_dd.options = [ft.dropdown.Option(self.NO_SELECTION_VALUE, self.NO_SELECTION_LABEL)]
                self.breed_dd.value = self.NO_SELECTION_VALUE
            self.page.update()
        except Exception as ex:
            print(f"Fehler beim Aktualisieren der Rassen: {ex}")
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD - Erstellt das UI
    # ════════════════════════════════════════════════════════════════════
    
    def build(self) -> ft.Column:
        # Baut und gibt das Formular-Layout zurück.
        form_column = ft.Column(
            [
                ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                
                self.meldungsart,
                ft.Divider(height=20),
                
                ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=ft.Colors.GREY_500),
                                ft.Text("Foto hochladen (Tippen)", color=ft.Colors.GREY_700, size=12),
                            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=400,
                            height=150,
                            border=ft.border.all(2, ft.Colors.GREY_300),
                            border_radius=8,
                            on_click=lambda _: self.page.run_task(self._pick_photo),
                        ),
                        self.photo_preview,
                        ft.TextButton("Foto entfernen", icon=ft.Icons.DELETE, on_click=lambda _: self._remove_photo()),
                    ], spacing=10),
                ),
                ft.Divider(height=20),
                
                self.title_label,
                self.name_tf,
                ft.Row([self.species_dd, self.breed_dd, self.sex_dd], spacing=15, wrap=True),
                
                self.farben_header,
                self.farben_panel,
                ft.Divider(height=20),
                
                ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.info_tf,
                ft.Divider(height=20),
                
                ft.Text("Standort & Datum﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
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