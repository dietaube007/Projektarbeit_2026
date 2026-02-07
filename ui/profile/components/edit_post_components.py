"""
Edit Post Components: UI-Komponenten zum Bearbeiten von Meldungen.

Enthält:
- EditPostDialog: Dialog-Klasse zum Bearbeiten einer Meldung
"""

from __future__ import annotations

import asyncio
from datetime import datetime, date
from typing import Callable, Dict, List, Optional, Any
import flet as ft

from services.posts.references import ReferenceService
from services.posts import PostService, PostRelationsService, PostStorageService
from services.geocoding import geocode_suggestions
from ui.constants import (
    PRIMARY_COLOR,
    BORDER_COLOR,
    DATE_FORMAT,
    NO_SELECTION_VALUE,
    NO_SELECTION_LABEL,
    ALLOWED_POST_STATUSES,
    PLACEHOLDER_IMAGE,
)
from ui.helpers import format_date, get_nested_id
from utils.logging_config import get_logger
from utils.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
)
from ui.shared_components import show_success_dialog
from ui.post_form.handlers.photo_upload_handler import (
    handle_pick_photo,
    cleanup_local_file,
)
from ui.profile.handlers.edit_post_handler import (
    validate_edit_form,
    has_edit_changes,
    save_edit_post,
)

logger = get_logger(__name__)


class EditPostDialog:
    """Dialog zum Bearbeiten einer bestehenden Meldung."""

    DATE_FORMAT_DB = "%Y-%m-%d"

    def __init__(
        self,
        page: ft.Page,
        sb,
        post: Dict[str, Any],
        on_save_callback: Optional[Callable] = None,
    ):
        """Initialisiert den Dialog."""
        self.page = page
        self.sb = sb
        self.post = post
        self.on_save_callback = on_save_callback

        # Services
        self.ref_service = ReferenceService(self.sb)
        self.post_service = PostService(self.sb)
        self.post_relations_service = PostRelationsService(self.sb)
        self.post_storage_service = PostStorageService(self.sb)

        # Referenzdaten
        self.post_statuses: List[dict] = []
        self.species_list: List[dict] = []
        self.breeds_by_species: Dict[int, List[dict]] = {}
        self.colors_list: List[dict] = []
        self.sex_list: List[dict] = []

        # Ausgewählte Farben
        self.selected_farben: List[int] = []

        # Foto-State
        self.selected_photo: Dict[str, Any] = {
            "path": None, "name": None, "url": None, "base64": None, "local_path": None
        }
        self._original_image_url: Optional[str] = None
        self._image_changed: bool = False

        # Location-State
        self.location_selected: Dict[str, Any] = {"text": None, "lat": None, "lon": None}
        self._location_query_version: int = 0

        # UI-Elemente
        self._init_ui_elements()

        # Dialog-Referenzen
        self.dialog: Optional[ft.AlertDialog] = None
        self.content_column: Optional[ft.Column] = None

        # Fehler-Banner
        self._error_text = ft.Text("", color=ft.Colors.WHITE, size=13, expand=True)
        self.error_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.WHITE, size=20),
                    self._error_text,
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.RED_600,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=8,
            visible=False,
        )

    def _init_ui_elements(self):
        """Initialisiert alle UI-Elemente mit den Daten des Posts."""
        self.meldungsart = ft.SegmentedButton(
            segments=[],
            selected=set(),
            allow_empty_selection=False,
            allow_multiple_selection=False,
            expand=True,
            on_change=lambda _: self._on_meldungsart_change(),
        )

        # Dynamisches Label für Name/Überschrift
        self.title_label = ft.Text(
            "Name﹡",
            size=12,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.GREY_700,
        )

        headline_value = self.post.get("headline", "")
        self.name_tf = ft.TextField(
            label="Name﹡",
            value=headline_value,
            border_radius=8,
            max_length=MAX_HEADLINE_LENGTH,
            counter_text=f"{len(headline_value)} / {MAX_HEADLINE_LENGTH}",
            helper_text=f"Max. {MAX_HEADLINE_LENGTH} Zeichen",
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY_COLOR,
            on_change=lambda _: self._update_name_counter(),
        )

        self.species_dd = ft.Dropdown(
            label="Tierart﹡",
            width=180,
            border_radius=8,
            on_change=lambda _: self._on_species_change(),
        )

        self.breed_dd = ft.Dropdown(
            label="Rasse",
            width=180,
            border_radius=8,
        )

        self.sex_dd = ft.Dropdown(
            label="Geschlecht",
            width=180,
            border_radius=8,
        )

        # Farben-Container mit auf-/zuklappbarem Panel
        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_panel_visible = True
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)

        outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", ft.Colors.GREY_400)

        self.farben_panel = ft.Container(
            content=self.farben_container,
            padding=12,
            visible=self.farben_panel_visible,
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=8,
            border=ft.border.all(1, outline_color),
        )

        self.farben_header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PALETTE, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                    ft.Container(expand=True),
                    self.farben_toggle_icon,
                ],
                spacing=12,
            ),
            padding=8,
            on_click=lambda _: self._toggle_farben_panel(),
            border_radius=8,
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.border.all(1, outline_color),
        )

        description_value = self.post.get("description", "")
        self.info_tf = ft.TextField(
            label="Beschreibung﹡",
            value=description_value,
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_radius=8,
            max_length=MAX_DESCRIPTION_LENGTH,
            counter_text=f"{len(description_value)} / {MAX_DESCRIPTION_LENGTH}",
            helper_text=f"Min. {MIN_DESCRIPTION_LENGTH}, max. {MAX_DESCRIPTION_LENGTH} Zeichen",
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY_COLOR,
            on_change=lambda _: self._update_description_counter(),
        )

        self.location_tf = ft.TextField(
            label="Ort﹡",
            value=self.post.get("location_text", ""),
            border_radius=8,
            on_change=lambda _: self._on_location_change(),
        )

        # Location-Vorschläge
        self.location_suggestions_list = ft.Column(spacing=2)
        self.location_suggestions_box = ft.Container(
            content=self.location_suggestions_list,
            visible=False,
            padding=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
        )

        self.date_tf = ft.TextField(
            label="Datum﹡ (TT.MM.JJJJ)",
            value=format_date(self.post.get("event_date", "")),
            width=180,
            border_radius=8,
            read_only=True,
        )

        # DatePicker einbinden (kein zukünftiges Datum erlaubt, nur Kalender)
        self.date_picker = ft.DatePicker(
            first_date=date(2000, 1, 1),
            last_date=date.today(),
            on_change=self._on_date_picked,
            help_text="Datum auswählen",
            error_invalid_text="Datum außerhalb des gültigen Bereichs",
            error_format_text="Ungültiges Datum",
            cancel_text="Abbrechen",
            confirm_text="OK",
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
        )
        # DatePicker als Overlay zur Seite hinzufügen (nur einmal)
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)

        # Textfeld nur über Kalender änderbar (keine direkte Eingabe)
        self.date_tf.suffix = ft.IconButton(
            ft.Icons.CALENDAR_MONTH,
            on_click=lambda _: self._open_date_picker(),
        )
        self.date_tf.on_tap = lambda _: self._open_date_picker()

        # Initiales Datum setzen (falls vorhanden)
        event_date_str = self.post.get("event_date", "")
        if event_date_str:
            try:
                parsed_date = datetime.strptime(event_date_str[:10], EditPostDialog.DATE_FORMAT_DB).date()
                self.date_picker.value = parsed_date
            except (ValueError, TypeError):
                pass

        # ── Foto-Vorschau und -Buttons ──
        self.photo_preview = ft.Image(
            width=400,
            height=200,
            fit=ft.ImageFit.COVER,
            visible=False,
            border_radius=8,
            src_base64=PLACEHOLDER_IMAGE,
        )
        self.photo_loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Bild wird geladen...", size=12)],
                spacing=8,
            ),
            visible=False,
        )
        self.photo_status_text = ft.Text("", color=PRIMARY_COLOR, size=12, visible=False)

        # Aktuelles Bild des Posts laden
        self._init_current_photo()

    def _init_current_photo(self):
        """Lädt das aktuelle Bild des Posts in die Vorschau."""
        post_images = self.post.get("post_image") or []
        if post_images:
            url = post_images[0].get("url", "")
            if url:
                self._original_image_url = url
                self.selected_photo["url"] = url
                self.photo_preview.src = url
                self.photo_preview.src_base64 = None
                self.photo_preview.visible = True

    # ─────────────────────────────────────────────────────────────
    # Foto-Verwaltung
    # ─────────────────────────────────────────────────────────────

    def _pick_photo(self):
        """Öffnet Dateiauswahl für ein neues Foto."""
        self.page.run_task(self._async_pick_photo)

    async def _async_pick_photo(self):
        """Async-Handler für Foto-Auswahl."""
        def show_status(msg: str, is_error: bool = False, is_loading: bool = False):
            if is_error:
                self.photo_status_text.color = ft.Colors.RED
            elif is_loading:
                self.photo_status_text.color = PRIMARY_COLOR
            else:
                self.photo_status_text.color = ft.Colors.GREEN
            self.photo_status_text.value = msg
            self.photo_status_text.visible = bool(msg)
            self.page.update()

        def set_loading(loading: bool):
            self.photo_loading.visible = loading
            self.page.update()

        await handle_pick_photo(
            page=self.page,
            post_storage_service=self.post_storage_service,
            selected_photo=self.selected_photo,
            photo_preview=self.photo_preview,
            show_status_callback=show_status,
            set_loading_callback=set_loading,
        )
        self._image_changed = True

    def _remove_photo(self):
        """Entfernt das aktuelle Foto aus der Vorschau."""
        # Nur lokale Datei löschen (nicht Storage - dort erst beim Speichern)
        local_path = self.selected_photo.get("local_path")
        if local_path:
            cleanup_local_file(local_path)

        self.selected_photo.update({
            "path": None, "name": None, "url": None, "base64": None, "local_path": None
        })
        self.photo_preview.visible = False
        self.photo_preview.src = None
        self.photo_preview.src_base64 = PLACEHOLDER_IMAGE
        self.photo_status_text.value = ""
        self.photo_status_text.visible = False
        self._image_changed = True
        self.page.update()

    # ─────────────────────────────────────────────────────────────
    # Location-Vorschläge (Geocoding)
    # ─────────────────────────────────────────────────────────────

    def _on_location_change(self):
        """Lädt Vorschläge für den Standort basierend auf dem Freitext."""
        self.location_selected = {"text": None, "lat": None, "lon": None}
        self._location_query_version += 1
        query = self.location_tf.value or ""
        self.page.run_task(
            self._update_location_suggestions,
            query,
            self._location_query_version,
        )

    async def _update_location_suggestions(self, query: str, version: int):
        """Aktualisiert die Location-Vorschläge asynchron mit Debounce."""
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
        # Nach unten scrollen damit Vorschlaege sichtbar sind
        if self.content_column:
            self.content_column.scroll_to(offset=99999, duration=300)

    def _select_location_suggestion(self, item: Dict[str, Any]):
        """Wählt einen Location-Vorschlag aus."""
        self.location_selected = {
            "text": item.get("text"),
            "lat": item.get("lat"),
            "lon": item.get("lon"),
        }
        self.location_tf.value = item.get("text", "")
        self._clear_location_suggestions()
        self.page.update()

    def _clear_location_suggestions(self):
        """Leert die Location-Vorschlagsliste."""
        self.location_suggestions_list.controls = []
        self.location_suggestions_box.visible = False
        self.page.update()

    # ─────────────────────────────────────────────────────────────
    # Sonstige Handler
    # ─────────────────────────────────────────────────────────────

    def _on_meldungsart_change(self):
        """Aktualisiert das Label basierend auf der gewählten Meldungsart."""
        selected_id = list(self.meldungsart.selected)[0] if self.meldungsart.selected else None
        selected_status = None
        for status in self.post_statuses:
            if str(status["id"]) == selected_id:
                selected_status = status["name"].lower()
                break

        if selected_status == "vermisst":
            self.title_label.value = "Name﹡"
            self.name_tf.label = "Name﹡"
        else:
            self.title_label.value = "Überschrift﹡"
            self.name_tf.label = "Überschrift﹡"
        self.page.update()

    def _update_name_counter(self):
        """Aktualisiert den Zeichenzähler für das Name/Überschrift-Feld."""
        text = self.name_tf.value or ""
        self.name_tf.counter_text = f"{len(text)} / {MAX_HEADLINE_LENGTH}"
        self.page.update()

    def _update_description_counter(self):
        """Aktualisiert den Zeichenzähler für das Beschreibungsfeld."""
        text = self.info_tf.value or ""
        self.info_tf.counter_text = f"{len(text)} / {MAX_DESCRIPTION_LENGTH}"
        self.page.update()

    def _toggle_farben_panel(self):
        """Toggle für das Farben-Panel (auf- und zuklappen)."""
        self.farben_panel_visible = not self.farben_panel_visible
        self.farben_panel.visible = self.farben_panel_visible
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()

    def _on_species_change(self):
        """Handler für Tierart-Änderung."""
        self._update_breeds()
        self.page.update()

    def _on_color_change(self, color_id: int, is_selected: bool):
        """Handler für Farbänderungen."""
        if is_selected and color_id not in self.selected_farben:
            self.selected_farben.append(color_id)
        elif not is_selected and color_id in self.selected_farben:
            self.selected_farben.remove(color_id)

    def _open_date_picker(self):
        """Öffnet den DatePicker (kompatibel mit verschiedenen Flet-Versionen)."""
        try:
            self.date_picker.open = True
            self.page.update()
        except Exception:
            pass

    def _on_date_picked(self, e):
        """Wird aufgerufen, wenn im DatePicker ein Datum gewählt wird."""
        if getattr(e, "control", None) and getattr(e.control, "value", None):
            try:
                # value ist vom Typ date
                selected_date = e.control.value
                if isinstance(selected_date, date):
                    # Formatieren im Anzeigeformat (TT.MM.JJJJ)
                    self.date_tf.value = selected_date.strftime(DATE_FORMAT)
                    self.page.update()
            except Exception as ex:
                logger.warning(f"Fehler beim Verarbeiten des ausgewählten Datums: {ex}")

    def _update_breeds(self):
        """Aktualisiert das Rassen-Dropdown basierend auf der Tierart."""
        self.breed_dd.options = [
            ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)
        ]
        try:
            species_id = int(self.species_dd.value) if self.species_dd.value else None
            if species_id and species_id in self.breeds_by_species:
                self.breed_dd.options += [
                    ft.dropdown.Option(str(b["id"]), b["name"])
                    for b in self.breeds_by_species[species_id]
                ]
        except (ValueError, TypeError):
            pass
        self.breed_dd.value = NO_SELECTION_VALUE

    # ─────────────────────────────────────────────────────────────
    # Referenzdaten laden
    # ─────────────────────────────────────────────────────────────

    def _load_refs(self):
        """Lädt alle Referenzdaten und initialisiert die Formularfelder."""
        try:
            self._load_post_statuses()
            self._load_dropdowns()
            self._load_colors()
        except Exception as ex:
            logger.error(f"Fehler beim Laden der Referenzdaten: {ex}", exc_info=True)

    def _load_post_statuses(self):
        """Lädt und setzt die Meldungsarten."""
        all_statuses = self.ref_service.get_post_statuses()
        self.post_statuses = [
            s for s in all_statuses
            if s["name"].lower() in ALLOWED_POST_STATUSES
        ]
        self.meldungsart.segments = [
            ft.Segment(value=str(s["id"]), label=ft.Text(s["name"]))
            for s in self.post_statuses
        ]

        current_id = get_nested_id(self.post, "post_status")
        if current_id:
            self.meldungsart.selected = {str(current_id)}
        elif self.post_statuses:
            self.meldungsart.selected = {str(self.post_statuses[0]["id"])}

        # Label basierend auf aktueller Meldungsart setzen
        self._on_meldungsart_change()

    def _load_dropdowns(self):
        """Lädt Tierart, Rasse und Geschlecht."""
        self.species_list = self.ref_service.get_species()
        self.breeds_by_species = self.ref_service.get_breeds_by_species()
        self.sex_list = self.ref_service.get_sex()

        # Tierart
        self.species_dd.options = [
            ft.dropdown.Option(str(s["id"]), s["name"])
            for s in self.species_list
        ]
        current_species = get_nested_id(self.post, "species")
        if current_species:
            self.species_dd.value = str(current_species)
        elif self.species_list:
            self.species_dd.value = str(self.species_list[0]["id"])

        # Rasse
        self._update_breeds()
        current_breed = get_nested_id(self.post, "breed")
        if current_breed:
            self.breed_dd.value = str(current_breed)

        # Geschlecht
        self.sex_dd.options = [
            ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)
        ] + [
            ft.dropdown.Option(str(s["id"]), s["name"])
            for s in self.sex_list
        ]
        current_sex = get_nested_id(self.post, "sex")
        self.sex_dd.value = str(current_sex) if current_sex else NO_SELECTION_VALUE

    def _load_colors(self):
        """Lädt die Farben und erstellt Checkboxen."""
        self.colors_list = self.ref_service.get_colors()

        # Aktuelle Farben aus Post
        self.selected_farben = [
            pc["color"]["id"]
            for pc in (self.post.get("post_color") or [])
            if pc.get("color") and pc["color"].get("id")
        ]

        # Checkboxen erstellen
        self.farben_container.controls = [
            ft.Container(
                ft.Checkbox(
                    label=color["name"],
                    value=color["id"] in self.selected_farben,
                    on_change=lambda e, cid=color["id"]: self._on_color_change(cid, e.control.value),
                ),
                col={"xs": 6, "sm": 4},
            )
            for color in self.colors_list
        ]

    # ─────────────────────────────────────────────────────────────
    # Validierung & Speichern (delegiert an edit_post_handler)
    # ─────────────────────────────────────────────────────────────

    def _save(self, _):
        """Speichert die Änderungen."""
        # Pruefen ob der Ort geaendert wurde (Freitext statt Vorschlag)
        original_location = self.post.get("location_text", "")
        current_location = (self.location_tf.value or "").strip()
        location_changed = current_location != original_location

        # Validierung
        errors = validate_edit_form(
            name_value=self.name_tf.value,
            species_value=self.species_dd.value,
            selected_farben=self.selected_farben,
            description_value=self.info_tf.value,
            location_value=self.location_tf.value,
            date_value=self.date_tf.value,
            selected_photo=self.selected_photo,
            location_selected=self.location_selected,
            location_changed=location_changed,
        )
        if errors:
            self._show_error("Pflichtfelder fehlen:\n" + "\n".join(errors))
            return

        # Änderungsprüfung
        if not has_edit_changes(
            post=self.post,
            meldungsart_selected=self.meldungsart.selected,
            name_value=self.name_tf.value,
            description_value=self.info_tf.value,
            location_value=self.location_tf.value,
            date_value=self.date_tf.value,
            species_value=self.species_dd.value,
            breed_value=self.breed_dd.value,
            sex_value=self.sex_dd.value,
            selected_farben=self.selected_farben,
            image_changed=self._image_changed,
        ):
            self._show_info_dialog("Keine Änderungen", "Es wurden keine Änderungen vorgenommen.")
            return

        # Speichern
        try:
            save_edit_post(
                sb=self.sb,
                post=self.post,
                post_service=self.post_service,
                post_relations_service=self.post_relations_service,
                post_storage_service=self.post_storage_service,
                meldungsart_selected=self.meldungsart.selected,
                name_value=self.name_tf.value,
                description_value=self.info_tf.value,
                species_value=self.species_dd.value,
                breed_value=self.breed_dd.value,
                sex_value=self.sex_dd.value,
                event_date_str=self.date_tf.value,
                location_value=self.location_tf.value,
                selected_farben=self.selected_farben,
                selected_photo=self.selected_photo,
                image_changed=self._image_changed,
                original_image_url=self._original_image_url,
                location_selected=self.location_selected,
            )

            self.page.close(self.dialog)
            self._show_success_dialog("Erfolgreich gespeichert", "Die Meldung wurde erfolgreich aktualisiert.")

            if self.on_save_callback:
                self.on_save_callback()

        except ValueError as ve:
            self._show_error(str(ve))
        except Exception as ex:
            self._show_error(f"Fehler beim Speichern: {ex}")

    # ─────────────────────────────────────────────────────────────
    # Dialoge & Feedback
    # ─────────────────────────────────────────────────────────────

    def _show_error(self, message: str):
        """Zeigt einen Fehler-Banner im Dialog an und scrollt nach oben."""
        self._error_text.value = message
        self.error_banner.visible = True
        if self.content_column:
            self.content_column.scroll_to(offset=0, duration=300)
        self.page.update()

    def _show_info_dialog(self, title: str, message: str):
        """Zeigt einen Info-Dialog an."""
        self._show_dialog(title, message, ft.Icons.INFO_OUTLINE, PRIMARY_COLOR)

    def _show_success_dialog(self, title: str, message: str):
        """Zeigt einen Erfolgs-Dialog an."""
        show_success_dialog(self.page, title, message)

    def _show_dialog(self, title: str, message: str, icon, color):
        """Zeigt einen Dialog an."""
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(icon, color=color, size=24), ft.Text(title, size=18, weight=ft.FontWeight.W_600)], spacing=8),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=lambda _: self.page.close(dlg))],
        )
        self.page.open(dlg)

    def _close(self, _):
        """Schließt den Dialog."""
        # Lokale Dateien aufräumen (falls nicht gespeichert)
        local_path = self.selected_photo.get("local_path")
        if local_path and self._image_changed:
            cleanup_local_file(local_path)
        self.page.close(self.dialog)

    # ─────────────────────────────────────────────────────────────
    # Dialog anzeigen
    # ─────────────────────────────────────────────────────────────

    def show(self):
        """Zeigt den Bearbeitungsdialog an."""
        self._load_refs()
        self.error_banner.visible = False

        # Foto-Bereich
        photo_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                    self.photo_preview,
                    self.photo_loading,
                    ft.Row(
                        [
                            ft.FilledButton(
                                "Neues Foto",
                                icon=ft.Icons.UPLOAD,
                                on_click=lambda _: self._pick_photo(),
                            ),
                            ft.TextButton(
                                "Foto entfernen",
                                icon=ft.Icons.DELETE,
                                on_click=lambda _: self._remove_photo(),
                            ),
                        ],
                        spacing=12,
                    ),
                    self.photo_status_text,
                ],
                spacing=8,
            ),
        )

        self.content_column = ft.Column(
            [
                self.error_banner,
                photo_section,
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                ft.Text("Meldungsart", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.meldungsart,
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                self.title_label,
                self.name_tf,
                ft.Row([self.species_dd, self.breed_dd, self.sex_dd], spacing=12, wrap=True),
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                self.farben_header,
                self.farben_panel,
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                self.info_tf,
                ft.Row([ft.Container(self.location_tf, expand=True), self.date_tf], spacing=12),
                self.location_suggestions_box,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [ft.Icon(ft.Icons.EDIT, color=PRIMARY_COLOR, size=24), ft.Text("Meldung bearbeiten", size=18, weight=ft.FontWeight.W_600)],
                spacing=8,
            ),
            content=ft.Container(content=self.content_column, width=600, height=700),
            actions=[
                ft.TextButton("Abbrechen", on_click=self._close),
                ft.FilledButton("Speichern", on_click=self._save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(self.dialog)
