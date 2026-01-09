"""
ui/profile/edit_post.py
Dialog zum Bearbeiten einer Meldung.
"""

from datetime import datetime, date
from typing import Callable, Dict, List, Optional, Any
import flet as ft

from services.posts.references import ReferenceService
from services.posts import PostService, PostRelationsService
from ui.constants import (
    PRIMARY_COLOR,
    DATE_FORMAT,
    NO_SELECTION_VALUE,
    NO_SELECTION_LABEL,
    ALLOWED_POST_STATUSES,
)
from utils.logging_config import get_logger
from ui.components import show_success_dialog

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

        # Referenzdaten
        self.post_statuses: List[dict] = []
        self.species_list: List[dict] = []
        self.breeds_by_species: Dict[int, List[dict]] = {}
        self.colors_list: List[dict] = []
        self.sex_list: List[dict] = []

        # Ausgewählte Farben
        self.selected_farben: List[int] = []

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
        )

        self.name_tf = ft.TextField(
            label="Name / Überschrift﹡",
            value=self.post.get("headline", ""),
            border_radius=8,
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

        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)

        self.info_tf = ft.TextField(
            label="Beschreibung﹡",
            value=self.post.get("description", ""),
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_radius=8,
        )

        self.location_tf = ft.TextField(
            label="Ort﹡",
            value=self.post.get("location_text", ""),
            border_radius=8,
        )

        self.date_tf = ft.TextField(
            label="Datum﹡ (TT.MM.JJJJ)",
            value=self._format_date(self.post.get("event_date", "")),
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

    # ══════════════════════════════════════════════════════════════════════
    # HILFSMETHODEN
    # ══════════════════════════════════════════════════════════════════════

    def _format_date(self, date_str: str) -> str:
        """Konvertiert DB-Datum (YYYY-MM-DD) ins Anzeigeformat (TT.MM.JJJJ)."""
        if not date_str:
            return ""
        try:
            return datetime.strptime(date_str[:10], EditPostDialog.DATE_FORMAT_DB).strftime(DATE_FORMAT)
        except ValueError:
            return ""

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parst ein Datum im Anzeigeformat. Gibt None bei Fehler zurück."""
        try:
            return datetime.strptime(date_str.strip(), DATE_FORMAT).date()
        except ValueError:
            return None

    def _get_nested_id(self, key: str) -> Optional[int]:
        """Extrahiert die ID aus einem verschachtelten Dict-Feld."""
        value = self.post.get(key)
        return value.get("id") if isinstance(value, dict) else None

    def _get_dropdown_id(self, dropdown: ft.Dropdown) -> Optional[int]:
        """Extrahiert die ID aus einem Dropdown, None bei 'Keine Angabe'."""
        val = dropdown.value
        return int(val) if val and val != NO_SELECTION_VALUE else None

    def _get_original_color_ids(self) -> List[int]:
        """Extrahiert die ursprünglichen Farb-IDs."""
        return sorted([
            pc["color"]["id"]
            for pc in (self.post.get("post_color") or [])
            if pc.get("color") and pc["color"].get("id")
        ])

    # ══════════════════════════════════════════════════════════════════════
    # EVENT HANDLER
    # ══════════════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════════════
    # DATEN LADEN
    # ══════════════════════════════════════════════════════════════════════

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

        current_id = self._get_nested_id("post_status")
        if current_id:
            self.meldungsart.selected = {str(current_id)}
        elif self.post_statuses:
            self.meldungsart.selected = {str(self.post_statuses[0]["id"])}

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
        current_species = self._get_nested_id("species")
        if current_species:
            self.species_dd.value = str(current_species)
        elif self.species_list:
            self.species_dd.value = str(self.species_list[0]["id"])

        # Rasse
        self._update_breeds()
        current_breed = self._get_nested_id("breed")
        if current_breed:
            self.breed_dd.value = str(current_breed)

        # Geschlecht
        self.sex_dd.options = [
            ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)
        ] + [
            ft.dropdown.Option(str(s["id"]), s["name"])
            for s in self.sex_list
        ]
        current_sex = self._get_nested_id("sex")
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

    # ══════════════════════════════════════════════════════════════════════
    # VALIDIERUNG & ÄNDERUNGSPRÜFUNG
    # ══════════════════════════════════════════════════════════════════════

    def _validate(self) -> List[str]:
        """Validiert die Eingaben und gibt fehlende Pflichtfelder zurück."""
        checks = [
            (self.name_tf.value, "Name/Überschrift"),
            (self.species_dd.value, "Tierart"),
            (self.selected_farben, "Mindestens eine Farbe"),
            (self.info_tf.value, "Beschreibung"),
            (self.location_tf.value, "Ort"),
            (self.date_tf.value, "Datum"),
        ]
        return [
            f"• {name}" for value, name in checks
            if not value or (isinstance(value, str) and not value.strip())
        ]

    def _has_changes(self) -> bool:
        """Prüft, ob Änderungen vorgenommen wurden."""
        try:
            # Status
            current_status = int(list(self.meldungsart.selected)[0]) if self.meldungsart.selected else None
            if current_status != self._get_nested_id("post_status"):
                return True

            # Textfelder
            text_checks = [
                (self.name_tf.value, "headline"),
                (self.info_tf.value, "description"),
                (self.location_tf.value, "location_text"),
            ]
            for field_value, post_key in text_checks:
                if field_value.strip() != self.post.get(post_key, ""):
                    return True

            # Datum
            if self.date_tf.value.strip() != self._format_date(self.post.get("event_date", "")):
                return True

            # Dropdowns
            if int(self.species_dd.value) != self._get_nested_id("species"):
                return True
            if self._get_dropdown_id(self.breed_dd) != self._get_nested_id("breed"):
                return True
            if self._get_dropdown_id(self.sex_dd) != self._get_nested_id("sex"):
                return True

            # Farben
            if sorted(self.selected_farben) != self._get_original_color_ids():
                return True

            return False

        except Exception as ex:
            logger.error(f"Fehler beim Prüfen auf Änderungen: {ex}", exc_info=True)
            return True

    # ══════════════════════════════════════════════════════════════════════
    # SPEICHERN
    # ══════════════════════════════════════════════════════════════════════

    def _save(self, _):
        """Speichert die Änderungen."""
        # Validierung
        errors = self._validate()
        if errors:
            self._show_error("Pflichtfelder fehlen:\n" + "\n".join(errors))
            return

        # Änderungsprüfung
        if not self._has_changes():
            self._show_info_dialog("Keine Änderungen", "Es wurden keine Änderungen vorgenommen.")
            return

        # Datum parsen
        event_date = self._parse_date(self.date_tf.value)
        if not event_date:
            self._show_error("Ungültiges Datumsformat.\nBitte verwende: TT.MM.YYYY")
            return

        # Speichern
        try:
            post_data = {
                "post_status_id": int(list(self.meldungsart.selected)[0]),
                "headline": self.name_tf.value.strip(),
                "description": self.info_tf.value.strip(),
                "species_id": int(self.species_dd.value),
                "breed_id": self._get_dropdown_id(self.breed_dd),
                "sex_id": self._get_dropdown_id(self.sex_dd),
                "event_date": event_date.isoformat(),
                "location_text": self.location_tf.value.strip(),
            }

            self.post_service.update(self.post["id"], post_data)
            self.post_relations_service.update_colors(self.post["id"], self.selected_farben)
            self.page.close(self.dialog)

            self._show_success_dialog("Erfolgreich gespeichert", "Die Meldung wurde erfolgreich aktualisiert.")

            if self.on_save_callback:
                self.on_save_callback()

        except Exception as ex:
            self._show_error(f"Fehler beim Speichern: {ex}")

    # ══════════════════════════════════════════════════════════════════════
    # DIALOGE & MELDUNGEN
    # ══════════════════════════════════════════════════════════════════════

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

    def _close(self, _):
        """Schließt den Dialog."""
        self.page.close(self.dialog)

    # ══════════════════════════════════════════════════════════════════════
    # DIALOG ANZEIGEN
    # ══════════════════════════════════════════════════════════════════════

    def show(self):
        """Zeigt den Bearbeitungsdialog an."""
        self._load_refs()
        self.error_banner.visible = False

        self.content_column = ft.Column(
            [
                self.error_banner,
                ft.Text("Meldungsart", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.meldungsart,
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                self.name_tf,
                ft.Row([self.species_dd, self.breed_dd, self.sex_dd], spacing=12, wrap=True),
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                ft.Text("Farben﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.farben_container,
                ft.Divider(height=16, color=ft.Colors.GREY_200),
                self.info_tf,
                ft.Row([ft.Container(self.location_tf, expand=True), self.date_tf], spacing=12),
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
            content=ft.Container(content=self.content_column, width=500, height=500),
            actions=[
                ft.TextButton("Abbrechen", on_click=self._close),
                ft.FilledButton("Speichern", on_click=self._save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(self.dialog)
