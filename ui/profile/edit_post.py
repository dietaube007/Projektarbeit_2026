"""
ui/profile/edit_post.py
Dialog zum Bearbeiten einer Meldung.
"""

from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
import flet as ft

from services.references import ReferenceService
from services.posts import PostService
from ui.constants import PRIMARY_COLOR


class EditPostDialog:
    """Dialog zum Bearbeiten einer bestehenden Meldung."""
    
    DATE_FORMAT = "%d.%m.%Y"
    NO_SELECTION_VALUE = "-1"
    NO_SELECTION_LABEL = "Keine Angabe"
    ALLOWED_POST_STATUSES = ["vermisst", "gefunden"]
    
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
        
        # Referenzdaten
        self.post_statuses = []
        self.species_list = []
        self.breeds_by_species = {}
        self.colors_list = []
        self.sex_list = []
        
        # Ausgewählte Farben
        self.selected_farben = []
        self.farben_checkboxes = {}
        
        # UI-Elemente
        self._init_ui_elements()
        
        # Dialog
        self.dialog = None
        self.content_column = None

        # Fehler-Banner
        self.error_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.WHITE, size=20),
                    ft.Text("", color=ft.Colors.WHITE, size=13, expand=True),
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
        # Meldungsart
        self.meldungsart = ft.SegmentedButton(
            segments=[],
            selected=set(),
            allow_empty_selection=False,
            allow_multiple_selection=False,
            expand=True,
        )
        
        # Name/Überschrift
        self.name_tf = ft.TextField(
            label="Name / Überschrift﹡",
            value=self.post.get("headline", ""),
            border_radius=8,
        )
        
        # Dropdowns
        self.species_dd = ft.Dropdown(
            label="Tierart﹡",
            width=180,
            border_radius=8,
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
        
        # Species-Dropdown Event
        self.species_dd.on_change = self._on_species_change
        
        # Farben-Container
        self.farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        
        # Beschreibung
        self.info_tf = ft.TextField(
            label="Beschreibung﹡",
            value=self.post.get("description", ""),
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_radius=8,
        )
        
        # Standort
        self.location_tf = ft.TextField(
            label="Ort﹡",
            value=self.post.get("location_text", ""),
            border_radius=8,
        )
        
        # Datum
        event_date = self.post.get("event_date", "")
        if event_date:
            try:
                parsed_date = datetime.strptime(event_date[:10], "%Y-%m-%d")
                event_date = parsed_date.strftime(self.DATE_FORMAT)
            except ValueError:
                pass
        
        self.date_tf = ft.TextField(
            label="Datum﹡ (TT.MM.JJJJ)",
            value=event_date,
            width=180,
            border_radius=8,
        )
    
    def _on_species_change(self, e):
        """Handler für Tierart-Änderung."""
        self._update_breeds()
        self.page.update()
    
    def _update_breeds(self):
        """Aktualisiert das Rassen-Dropdown."""
        try:
            self.breed_dd.options = [
                ft.dropdown.Option(self.NO_SELECTION_VALUE, self.NO_SELECTION_LABEL)
            ]
            sid = int(self.species_dd.value) if self.species_dd.value else None
            if sid and sid in self.breeds_by_species:
                self.breed_dd.options += [
                    ft.dropdown.Option(str(b["id"]), b["name"])
                    for b in self.breeds_by_species[sid]
                ]
            self.breed_dd.value = self.NO_SELECTION_VALUE
        except Exception as ex:
            print(f"Fehler beim Aktualisieren der Rassen: {ex}")
    
    def _on_color_change(self, color_id: int, is_selected: bool):
        """Handler für Farbänderungen."""
        if is_selected:
            if color_id not in self.selected_farben:
                self.selected_farben.append(color_id)
        else:
            if color_id in self.selected_farben:
                self.selected_farben.remove(color_id)
    
    def _load_refs(self):
        """Lädt alle Referenzdaten."""
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
            
            # Aktuellen Status setzen
            current_status_id = None
            post_status = self.post.get("post_status")
            if isinstance(post_status, dict):
                current_status_id = post_status.get("id")
            
            if current_status_id:
                self.meldungsart.selected = {str(current_status_id)}
            elif self.post_statuses:
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
            
            # Aktuelle Tierart setzen
            current_species = self.post.get("species")
            if isinstance(current_species, dict) and current_species.get("id"):
                self.species_dd.value = str(current_species["id"])
            elif self.species_list:
                self.species_dd.value = str(self.species_list[0]["id"])
            
            # Rassen laden und setzen
            self._update_breeds()
            current_breed = self.post.get("breed")
            if isinstance(current_breed, dict) and current_breed.get("id"):
                self.breed_dd.value = str(current_breed["id"])
            
            # Geschlecht Dropdown füllen
            self.sex_dd.options = [
                ft.dropdown.Option(self.NO_SELECTION_VALUE, self.NO_SELECTION_LABEL)
            ]
            self.sex_dd.options += [
                ft.dropdown.Option(str(s["id"]), s["name"])
                for s in self.sex_list
            ]
            current_sex = self.post.get("sex")
            if isinstance(current_sex, dict) and current_sex.get("id"):
                self.sex_dd.value = str(current_sex["id"])
            else:
                self.sex_dd.value = self.NO_SELECTION_VALUE
            
            # Aktuelle Farben laden
            post_colors = self.post.get("post_color") or []
            self.selected_farben = [
                pc.get("color", {}).get("id")
                for pc in post_colors
                if pc.get("color") and pc.get("color").get("id")
            ]
            
            # Farben-Checkboxes erstellen
            self.farben_container.controls = []
            for color in self.colors_list:
                is_selected = color["id"] in self.selected_farben
                
                def on_color_change(e, c_id=color["id"]):
                    self._on_color_change(c_id, e.control.value)
                
                cb = ft.Checkbox(
                    label=color["name"],
                    value=is_selected,
                    on_change=on_color_change,
                )
                self.farben_checkboxes[color["id"]] = cb
                self.farben_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4})
                )
            
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzdaten: {ex}")
    
    def _validate(self) -> List[str]:
        """Validiert die Eingaben und gibt Fehlermeldungen zurück."""
        errors = []
        
        if not self.name_tf.value or not self.name_tf.value.strip():
            errors.append("• Name/Überschrift")
        if not self.species_dd.value:
            errors.append("• Tierart")
        if not self.selected_farben:
            errors.append("• Mindestens eine Farbe")
        if not self.info_tf.value or not self.info_tf.value.strip():
            errors.append("• Beschreibung")
        if not self.location_tf.value or not self.location_tf.value.strip():
            errors.append("• Ort")
        if not self.date_tf.value or not self.date_tf.value.strip():
            errors.append("• Datum")
        
        return errors
    
    def _get_nested_id(self, key: str) -> Optional[int]:
        """Extrahiert die ID aus einem verschachtelten Dict-Feld."""
        value = self.post.get(key)
        return value.get("id") if isinstance(value, dict) else None

    def _get_dropdown_id(self, dropdown: ft.Dropdown) -> Optional[int]:
        """Extrahiert die ID aus einem Dropdown, None bei 'Keine Angabe'."""
        val = dropdown.value
        if val and val != self.NO_SELECTION_VALUE:
            return int(val)
        return None

    def _get_original_date_str(self) -> str:
        """Konvertiert das ursprüngliche Datum ins Anzeigeformat."""
        event_date = self.post.get("event_date", "")
        if event_date:
            try:
                return datetime.strptime(event_date[:10], "%Y-%m-%d").strftime(self.DATE_FORMAT)
            except ValueError:
                pass
        return ""

    def _get_original_color_ids(self) -> List[int]:
        """Extrahiert die ursprünglichen Farb-IDs."""
        post_colors = self.post.get("post_color") or []
        return sorted([
            pc["color"]["id"]
            for pc in post_colors
            if pc.get("color") and pc["color"].get("id")
        ])

    def _has_changes(self) -> bool:
        """Prüft, ob Änderungen vorgenommen wurden."""
        try:
            # Status
            current_status = int(list(self.meldungsart.selected)[0]) if self.meldungsart.selected else None
            if current_status != self._get_nested_id("post_status"):
                return True

            # Textfelder
            if self.name_tf.value.strip() != self.post.get("headline", ""):
                return True
            if self.info_tf.value.strip() != self.post.get("description", ""):
                return True
            if self.location_tf.value.strip() != self.post.get("location_text", ""):
                return True
            if self.date_tf.value.strip() != self._get_original_date_str():
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
            print(f"Fehler beim Prüfen auf Änderungen: {ex}")
            return True

    def _save(self, _):
        """Speichert die Änderungen."""
        errors = self._validate()
        if errors:
            self._show_error("Pflichtfelder fehlen:\n" + "\n".join(errors))
            return

        if not self._has_changes():
            self._show_info_dialog("Keine Änderungen", "Es wurden keine Änderungen vorgenommen.")
            return

        try:
            event_date = datetime.strptime(self.date_tf.value.strip(), self.DATE_FORMAT).date()
        except ValueError:
            self._show_error("Ungültiges Datumsformat.\nBitte verwende: TT.MM.YYYY")
            return

        try:
            post_id = self.post.get("id")
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

            self.post_service.update(post_id, post_data)
            self.post_service.update_colors(post_id, self.selected_farben)
            self.page.close(self.dialog)

            self._show_success_dialog("Erfolgreich gespeichert", "Die Meldung wurde erfolgreich aktualisiert.")

            if self.on_save_callback:
                self.on_save_callback()

        except Exception as ex:
            self._show_error(f"Fehler beim Speichern: {ex}")
    
    def _show_error(self, message: str):
        """Zeigt einen Fehler-Banner im Dialog an und scrollt nach oben."""
        self.error_banner.content.controls[1].value = message
        self.error_banner.visible = True
        if self.content_column:
            self.content_column.scroll_to(offset=0, duration=300)
        self.page.update()

    def _hide_error(self):
        """Versteckt das Fehler-Banner."""
        self.error_banner.visible = False

    def _show_info_dialog(self, title: str, message: str):
        """Zeigt einen Info-Dialog an."""
        self._show_dialog(title, message, ft.Icons.INFO_OUTLINE, PRIMARY_COLOR)

    def _show_success_dialog(self, title: str, message: str):
        """Zeigt einen Erfolgs-Dialog an."""
        self._show_dialog(title, message, ft.Icons.CHECK_CIRCLE_OUTLINE, ft.Colors.GREEN_600)

    def _show_dialog(self, title: str, message: str, icon: str, icon_color: str):
        """Zeigt einen Dialog mit Icon an."""
        def close_dlg(_):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(icon, color=icon_color, size=24),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Text(message, size=13, color=ft.Colors.GREY_700),
            actions=[ft.TextButton("OK", on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _close(self, _):
        """Schließt den Dialog."""
        self.page.close(self.dialog)
    
    def show(self):
        """Zeigt den Bearbeitungsdialog an."""
        # Referenzdaten laden
        self._load_refs()
        
        # Fehler-Banner zurücksetzen
        self.error_banner.visible = False

        # Dialog-Inhalt
        self.content_column = ft.Column(
            [
                # Fehler-Banner (oben)
                self.error_banner,

                # Meldungsart
                ft.Text("Meldungsart", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.meldungsart,

                ft.Divider(height=16, color=ft.Colors.GREY_200),

                # Name/Überschrift
                self.name_tf,

                # Tierart, Rasse, Geschlecht
                ft.Row(
                    [self.species_dd, self.breed_dd, self.sex_dd],
                    spacing=12,
                    wrap=True,
                ),

                ft.Divider(height=16, color=ft.Colors.GREY_200),

                # Farben
                ft.Text("Farben﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.farben_container,

                ft.Divider(height=16, color=ft.Colors.GREY_200),

                # Beschreibung
                self.info_tf,

                # Ort und Datum
                ft.Row(
                    [
                        ft.Container(self.location_tf, expand=True),
                        self.date_tf,
                    ],
                    spacing=12,
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        content = ft.Container(
            content=self.content_column,
            width=500,
            height=500,
        )
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT, color=PRIMARY_COLOR, size=24),
                    ft.Text("Meldung bearbeiten", size=18, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=content,
            actions=[
                ft.TextButton("Abbrechen", on_click=self._close),
                ft.FilledButton(
                    "Speichern",
                    on_click=self._save,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(self.dialog)
