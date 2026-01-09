"""
Post Form View - Hauptformular zum Erstellen von Tier-Meldungen.

Dieses Modul enthält die PostForm-Klasse, die das UI für
Vermisst-/Gefunden-Meldungen bereitstellt.
"""

import os
from datetime import datetime
import re
import asyncio
from typing import Callable, Optional

import flet as ft

from services.references import ReferenceService
from services.posts import PostService
from services.pet_recognition import get_recognition_service

from ui.post_form.constants import (
    VALID_IMAGE_TYPES,
    DATE_FORMAT,
    ALLOWED_POST_STATUSES,
    NO_SELECTION_VALUE,
    NO_SELECTION_LABEL,
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
    create_ai_recognition_button,
    create_ai_result_container,
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
        self.recognition_service = get_recognition_service()
        
        # KI-Erkennungs-State
        self.ai_result = None
        self.ai_consent_given = False
        self.ai_recognition_cancelled = False
        
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
        
        # Beschreibung & Standort
        self.info_tf = create_description_field()
        # KI-Hinweis-Badge über der Beschreibung
        def on_remove_hint(_=None):
            self._remove_ai_hint()
        self.ai_hint_badge = ft.Container(
            visible=False,
            padding=6,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=16,
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.BLUE_700),
                    ft.Text("KI‑Hinweis eingefügt", size=12, color=ft.Colors.BLUE_800, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.TextButton("Hinweis entfernen", icon=ft.Icons.CLOSE, on_click=on_remove_hint),
                ],
                spacing=8,
            ),
        )
        self.location_tf = create_location_field()
        self.date_tf = create_date_field()
        
        # KI-Rassenerkennung
        self.ai_button = create_ai_recognition_button(
            lambda _: self.page.run_task(self._start_ai_recognition)
        )
        self.ai_result_container = create_ai_result_container()
        
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
        def close_dialog(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_600, size=24),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    ft.Text(message, size=13, color=ft.Colors.GREY_700),
                    ft.Column(
                        [ft.Text(item, size=12, color=ft.Colors.GREY_800) for item in items],
                        spacing=2,
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(dlg)
    
    def _show_success_dialog(self, title: str, message: str):
        """Zeigt einen Erfolgs-Dialog an."""
        def close_dialog(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN_600, size=28),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Text(message, size=13, color=ft.Colors.GREY_700),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(dlg)
    
    def _show_progress_dialog(self, message: str):
        """Zeigt einen modalen Fortschrittsdialog mit Lade-Indikator an."""
        try:
            def on_cancel(e):
                # Setze Abbruch-Flag und schließe Dialog
                self.ai_recognition_cancelled = True
                self.page.close(dlg)
                self._show_status("❌ KI-Erkennung abgebrochen", is_error=True)
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.HOURGLASS_TOP, color=ft.Colors.BLUE_600, size=22),
                    ft.Text("Bitte kurz warten", size=16, weight=ft.FontWeight.W_600),
                ], spacing=8),
                content=ft.Row([
                    ft.ProgressRing(width=20, height=20),
                    ft.Text(message, size=13, color=ft.Colors.GREY_700),
                ], spacing=10),
                actions=[ft.TextButton("Abbrechen", on_click=on_cancel)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            # Speichere Referenz, um später schließen zu können
            self._progress_dlg = dlg
            self.page.open(dlg)
            self.page.update()
        except Exception as _:
            # Fallback: Statusleiste verwenden
            self._show_status(message, is_loading=True)

    def _show_error_dialog(self, title: str, message: str):
        """Zeigt einen Fehler-Dialog an."""
        def close_dialog(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_600, size=24),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Text(message, size=13, color=ft.Colors.GREY_700),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(dlg)

    def _show_ai_suggestion_dialog(self, error_text: str, suggested_breed: str, suggested_species: str | None, confidence: float):
        """Zeigt einen Dialog an, der bei unsicheren Ergebnissen nur einen Hinweis in die Beschreibung einfügt."""
        def accept_to_description(e):
            self.page.close(dlg)
            # Hinweis-Text in Beschreibung einfügen
            self._insert_or_update_ai_hint(suggested_species, suggested_breed, confidence)
        
        def close_dialog(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_600, size=24),
                    ft.Text("Erkennung fehlgeschlagen", size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Column(
                [
                    ft.Text(error_text, size=13, color=ft.Colors.GREY_700),
                    ft.Container(height=8),
                    ft.Text(
                        "Option: Hinweis in die Beschreibung einfügen (Felder bleiben unverändert).",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                tight=True,
                spacing=6,
            ),
            actions=[
                ft.TextButton("Abbrechen", on_click=close_dialog),
                ft.FilledButton("Nur Hinweis einfügen", icon=ft.Icons.NOTE_ADD, on_click=accept_to_description),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(dlg)

    # ───────────────────────────────────────────────────────────────────
    # KI-Hinweis Helpers
    # ───────────────────────────────────────────────────────────────────
    def _build_ai_hint_text(self, species: Optional[str], breed: str, confidence: float) -> str:
        conf_percent = int((confidence or 0) * 100)
        if species:
            return f"[KI-Vorschlag (unsicher): {species}, Rasse: {breed} ({conf_percent}% Konfidenz)]"
        return f"[KI-Vorschlag (unsicher): {breed} ({conf_percent}% Konfidenz)]"

    def _insert_or_update_ai_hint(self, species: Optional[str], breed: str, confidence: float):
        """Fügt den KI-Hinweis am Anfang der Beschreibung ein oder aktualisiert ihn (Duplikat-Schutz)."""
        hint = self._build_ai_hint_text(species, breed, confidence)
        current = self.info_tf.value or ""
        # Suche nach existierendem Hint am Anfang
        pattern = r"^\[KI-Vorschlag \(unsicher\):.*?\]\n\n"
        if re.match(pattern, current):
            # Ersetze bestehenden Hinweis
            new_value = re.sub(pattern, hint + "\n\n", current, count=1)
            self.info_tf.value = new_value
        else:
            # Präfix hinzufügen
            self.info_tf.value = f"{hint}\n\n{current}" if current else hint
        # Badge zeigen
        self.ai_hint_badge.visible = True
        self._show_status("Hinweis aus KI übernommen.", is_error=False)
        self.page.update()

    def _remove_ai_hint(self):
        """Entfernt den KI-Hinweis am Anfang der Beschreibung, falls vorhanden."""
        current = self.info_tf.value or ""
        pattern = r"^\[KI-Vorschlag \(unsicher\):.*?\]\n\n?"
        new_value = re.sub(pattern, "", current, count=1)
        self.info_tf.value = new_value
        self.ai_hint_badge.visible = False
        self.page.update()
    
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
    
    def _on_color_change(self, color_id: int, is_selected: bool):
        """Handler für Farbänderungen."""
        if is_selected:
            if color_id not in self.selected_farben:
                self.selected_farben.append(color_id)
        else:
            if color_id in self.selected_farben:
                self.selected_farben.remove(color_id)
    
    # ════════════════════════════════════════════════════════════════════
    # KI-RASSENERKENNUNG
    # ════════════════════════════════════════════════════════════════════
    
    async def _start_ai_recognition(self):
        """Startet die KI-Rassenerkennung mit Einverständnisabfrage."""
        # Prüfe ob Foto vorhanden
        if not self.selected_photo.get("path"):
            self._show_error_dialog(
                "Kein Foto",
                "Bitte lade zuerst ein Foto hoch, bevor du die KI-Erkennung startest."
            )
            return
        
        # Prüfe ob "Fundtier" ausgewählt ist
        selected_id = list(self.meldungsart.selected)[0] if self.meldungsart.selected else None
        selected_status = None
        for status in self.post_statuses:
            if str(status["id"]) == selected_id:
                selected_status = status["name"].lower()
                break
        
        if selected_status != "fundtier":
            self._show_error_dialog(
                "Nur für Fundtiere",
                "Die KI-Rassenerkennung ist nur für gefundene Tiere verfügbar. "
                "Besitzer vermisster Tiere kennen in der Regel die Rasse ihres Tieres bereits."
            )
            return
        
        # Einverständnisdialog anzeigen
        await self._show_consent_dialog()
    
    async def _show_consent_dialog(self):
        """Zeigt den Einverständnisdialog für die KI-Erkennung."""
        def on_accept(e):
            self.ai_consent_given = True
            self.page.close(dlg)
            self.page.run_task(self._perform_ai_recognition)
        
        def on_decline(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PURPLE_600, size=24),
                    ft.Text("KI-Rassenerkennung", size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Einverständniserklärung:",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "Das hochgeladene Bild wird durch eine KI analysiert, um die Tierart und Rasse zu erkennen. "
                            "Die Analyse erfolgt lokal und das Bild wird nicht an externe Dienste gesendet.",
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Divider(),
                        ft.Text(
                            "Wichtige Hinweise:",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "• Die KI-Erkennung dient nur als Vorschlag\n"
                            "• Es gibt keine Garantie für die Richtigkeit\n"
                            "• Du kannst den Vorschlag ablehnen und selbst eintragen\n"
                            "• Bei Unsicherheit kontaktiere ein Tierheim",
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Abbrechen", on_click=on_decline),
                ft.FilledButton("Akzeptieren & Starten", on_click=on_accept),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.open(dlg)
    
    async def _perform_ai_recognition(self):
        """Führt die KI-Erkennung durch."""
        try:
            # Reset Cancel-Flag
            self.ai_recognition_cancelled = False
            
            # Zeige Fortschrittsdialog, damit Nutzer den Status erkennt
            self._show_progress_dialog("KI analysiert das Bild...")
            self._show_status("🔄 KI analysiert das Bild...", is_loading=True)
            # Kurz yield, damit der Dialog sichtbar wird, bevor die Analyse startet
            await asyncio.sleep(0.05)
            
            # Prüfe auf Abbruch
            if self.ai_recognition_cancelled:
                return
            
            # Hole Bilddaten vom Storage
            if not self.selected_photo.get("path"):
                self._show_status("❌ Kein Bild vorhanden", is_error=True)
                try:
                    if hasattr(self, "_progress_dlg") and self._progress_dlg:
                        self.page.close(self._progress_dlg)
                        self._progress_dlg = None
                except Exception:
                    pass
                return
            
            # Lade Bild von Supabase
            try:
                response = self.sb.storage.from_(self.post_service.STORAGE_BUCKET).download(
                    self.selected_photo["path"]
                )
                image_data = response
            except Exception as ex:
                self._show_status(f"❌ Fehler beim Laden des Bildes: {ex}", is_error=True)
                try:
                    if hasattr(self, "_progress_dlg") and self._progress_dlg:
                        self.page.close(self._progress_dlg)
                        self._progress_dlg = None
                except Exception:
                    pass
                return
            
            # Prüfe erneut auf Abbruch vor der Analyse
            if self.ai_recognition_cancelled:
                try:
                    if hasattr(self, "_progress_dlg") and self._progress_dlg:
                        self.page.close(self._progress_dlg)
                        self._progress_dlg = None
                except Exception:
                    pass
                return
            
            # Führe Erkennung in einem Executor aus, damit wir währenddessen auf Abbruch prüfen können
            import concurrent.futures
            
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self.recognition_service.recognize_pet, image_data)
            
            # Warte auf das Ergebnis und prüfe periodisch auf Abbruch
            result = None
            while not future.done():
                await asyncio.sleep(0.1)
                if self.ai_recognition_cancelled:
                    # Abbruch wurde angefordert
                    executor.shutdown(wait=False, cancel_futures=True)
                    try:
                        if hasattr(self, "_progress_dlg") and self._progress_dlg:
                            self.page.close(self._progress_dlg)
                            self._progress_dlg = None
                    except Exception:
                        pass
                    return
            
            # Hole das Ergebnis
            result = future.result()
            executor.shutdown(wait=False)
            
            # Finale Abbruch-Prüfung nach der Erkennung
            if self.ai_recognition_cancelled:
                try:
                    if hasattr(self, "_progress_dlg") and self._progress_dlg:
                        self.page.close(self._progress_dlg)
                        self._progress_dlg = None
                except Exception:
                    pass
                return
            
            if result["success"]:
                self.ai_result = result
                self._show_ai_result(result)
                self._show_status("✅ Erkennung abgeschlossen!", is_error=False)
            else:
                # Wenn es einen Vorschlag gibt, biete Übernahme in die Beschreibung an
                suggested_breed = result.get("suggested_breed")
                suggested_species = result.get("suggested_species")
                if suggested_breed:
                    self._show_ai_suggestion_dialog(
                        result.get("error") or "Die KI konnte das Tier nicht sicher erkennen.",
                        suggested_breed,
                        suggested_species,
                        result.get("confidence", 0.0),
                    )
                else:
                    self._show_error_dialog(
                        "Erkennung fehlgeschlagen",
                        result.get("error") or "Die KI konnte das Tier nicht sicher erkennen. "
                        "Bitte versuche ein anderes Bild oder trage die Rasse manuell ein. "
                        "Du kannst auch das Tierheim kontaktieren und das Tier beschreiben."
                    )
                self._show_status("", is_error=False)
            # Fortschrittsdialog schließen
            try:
                if hasattr(self, "_progress_dlg") and self._progress_dlg:
                    self.page.close(self._progress_dlg)
                    self._progress_dlg = None
            except Exception:
                pass
                
        except Exception as ex:
            self._show_status(f"❌ Fehler: {ex}", is_error=True)
            try:
                if hasattr(self, "_progress_dlg") and self._progress_dlg:
                    self.page.close(self._progress_dlg)
                    self._progress_dlg = None
            except Exception:
                pass
    
    def _show_ai_result(self, result: dict):
        """Zeigt das KI-Erkennungsergebnis an."""
        confidence_percent = int(result["confidence"] * 100)
        
        # Erstelle Ergebnis-UI
        result_content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.PURPLE_600, size=20),
                        ft.Text(
                            "KI-Erkennungsergebnis",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PURPLE_900,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=10, color=ft.Colors.PURPLE_200),
                ft.Text(
                    f"Tierart: {result['species']}",
                    size=13,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    f"Rasse: {result['breed']}",
                    size=13,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    f"Konfidenz: {confidence_percent}%",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
                ft.Container(
                    content=ft.Text(
                        "⚠️ Hinweis: Dies ist nur ein KI-Vorschlag ohne Garantie auf Richtigkeit.",
                        size=11,
                        color=ft.Colors.ORANGE_800,
                        italic=True,
                    ),
                    padding=8,
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=4,
                ),
                ft.Divider(height=10, color=ft.Colors.PURPLE_200),
                ft.Row(
                    [
                        ft.TextButton(
                            "Ablehnen",
                            icon=ft.Icons.CLOSE,
                            on_click=lambda _: self._reject_ai_result(),
                        ),
                        ft.FilledButton(
                            "Übernehmen",
                            icon=ft.Icons.CHECK,
                            on_click=lambda _: self._accept_ai_result(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=10,
                ),
            ],
            spacing=8,
        )
        
        self.ai_result_container.content = result_content
        self.ai_result_container.visible = True
        self.page.update()
    
    def _accept_ai_result(self):
        """Übernimmt das KI-Erkennungsergebnis in die Formularfelder."""
        if not self.ai_result:
            return
        
        # Finde Tierart-ID
        species_name = self.ai_result["species"]
        species_id = None
        for species in self.species_list:
            if species["name"].lower() == species_name.lower():
                species_id = species["id"]
                break
        
        # Setze Tierart
        if species_id:
            self.species_dd.value = str(species_id)
            self.page.run_task(self._update_breeds)
        
        # Finde Rasse-ID (nach einem kurzen Delay, damit Breeds geladen sind)
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
            
            # Füge Erkennungsinfo zur Beschreibung hinzu
            confidence_percent = int(self.ai_result["confidence"] * 100)
            ai_info = f"[KI-Erkennung: {species_name}, Rasse: {breed_name} ({confidence_percent}% Konfidenz)]"
            
            current_description = self.info_tf.value or ""
            if current_description:
                self.info_tf.value = f"{ai_info}\n\n{current_description}"
            else:
                self.info_tf.value = ai_info
            
            self.ai_result_container.visible = False
            self._show_status("✅ KI-Vorschlag übernommen!", is_error=False)
            self.page.update()
        
        self.page.run_task(set_breed)
    
    def _reject_ai_result(self):
        """Lehnt das KI-Erkennungsergebnis ab."""
        self.ai_result = None
        self.ai_result_container.visible = False
        self._show_status("KI-Vorschlag abgelehnt. Bitte trage die Daten manuell ein.", is_error=False)
        self.page.update()
    
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
                    # Versuche beide mögliche Pfade (mit und ohne Session-ID)
                    upload_path_with_session = get_upload_path(ev.file_name, self.page.session_id)
                    upload_path_direct = get_upload_path(ev.file_name, None)
                    
                    print(f"[DEBUG] Prüfe Pfad mit Session: {upload_path_with_session}")
                    print(f"[DEBUG] Existiert: {os.path.exists(upload_path_with_session)}")
                    print(f"[DEBUG] Prüfe Pfad ohne Session: {upload_path_direct}")
                    print(f"[DEBUG] Existiert: {os.path.exists(upload_path_direct)}")
                    
                    # Wähle den Pfad der existiert
                    if os.path.exists(upload_path_with_session):
                        upload_path = upload_path_with_session
                    elif os.path.exists(upload_path_direct):
                        upload_path = upload_path_direct
                    else:
                        # Liste alle Dateien im Upload-Verzeichnis
                        import glob
                        all_files = glob.glob(os.path.join(get_upload_path("", None), "**", "*.*"), recursive=True)
                        print(f"[DEBUG] Alle Dateien im Upload-Verzeichnis: {all_files}")
                        self._show_status(f"❌ Datei nicht gefunden: {ev.file_name}", is_error=True)
                        return
                    
                    print(f"[DEBUG] Verwende Pfad: {upload_path}")
                    
                    # Bild hochladen und komprimieren
                    print(f"[DEBUG] Starte Upload zu Supabase...")
                    result = upload_to_storage(self.sb, upload_path, ev.file_name)
                    print(f"[DEBUG] Upload-Ergebnis: url={result.get('url') is not None}")
                    
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
                    print(f"[DEBUG] Exception im on_upload: {type(ex).__name__}: {ex}")
                    import traceback
                    traceback.print_exc()
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
        
        # Validierung
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
        if not self.selected_photo.get("url"):
            errors.append("• Foto")
        
        if errors:
            self._show_validation_dialog(
                "Pflichtfelder fehlen",
                "Bitte fülle folgende Felder aus:",
                errors
            )
            return
        
        # Datum parsen
        try:
            event_date = datetime.strptime(self.date_tf.value.strip(), DATE_FORMAT).date()
        except ValueError:
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
                self._show_error_dialog("Nicht eingeloggt", "Bitte melde dich an, um eine Meldung zu erstellen.")
                return
            user_id = user_response.user.id
        except Exception as e:
            self._show_error_dialog("Fehler", f"Fehler beim Abrufen des Benutzers: {e}")
            return
        
        try:
            self._show_status("⏳ Erstelle Meldung...", is_loading=True)
            
            post_data = {
                "user_id": user_id,
                "post_status_id": int(list(self.meldungsart.selected)[0]),
                "headline": self.name_tf.value.strip(),
                "description": self.info_tf.value.strip(),
                "species_id": int(self.species_dd.value),
                "breed_id": int(self.breed_dd.value) if self.breed_dd.value and self.breed_dd.value != NO_SELECTION_VALUE else None,
                "sex_id": int(self.sex_dd.value) if self.sex_dd.value and self.sex_dd.value != NO_SELECTION_VALUE else None,
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
            
            self._show_status("")
            self._show_success_dialog("Meldung erstellt", "Deine Meldung wurde erfolgreich veröffentlicht!")
            
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
        # KI-Hinweis-Badge zurücksetzen
        self.ai_hint_badge.visible = False
    
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
            
            # Initiale KI-Button-Sichtbarkeit basierend auf der Meldungsart setzen
            self._update_title_label()
                
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzdaten: {ex}")
    
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
            print(f"Fehler beim Aktualisieren der Rassen: {ex}")
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD - Erstellt das UI
    # ════════════════════════════════════════════════════════════════════
    
    def build(self) -> ft.Column:
        """Baut und gibt das Formular-Layout zurück."""
        
        # Foto-Upload Bereich
        photo_area = ft.Container(
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
        )
        
        form_column = ft.Column(
            [
                ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                
                self.meldungsart,
                ft.Divider(height=20),
                
                ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                photo_area,
                
                # KI-Rassenerkennung Button (nur für Fundtiere)
                self.ai_button,
                self.ai_result_container,
                
                ft.Divider(height=20),
                
                self.title_label,
                self.name_tf,
                ft.Row([self.species_dd, self.breed_dd, self.sex_dd], spacing=15, wrap=True),
                
                self.farben_header,
                self.farben_panel,
                ft.Divider(height=20),
                
                ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                self.ai_hint_badge,
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
