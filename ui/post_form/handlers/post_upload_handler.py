"""
Post Upload-Feature: UI und Logik für Post-Erstellung und Speicherung.
"""

from __future__ import annotations

from datetime import date
from typing import Callable, Optional, Dict, Any, List

import flet as ft

from services.posts import PostService, PostRelationsService, PostStorageService
from services.account import ProfileService
from .photo_upload_handler import cleanup_local_file
from utils.validators import sanitize_string
from utils.logging_config import get_logger
from ui.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    NO_SELECTION_VALUE,
    NO_SELECTION_LABEL,
)
from ui.shared_components import show_error_dialog, show_success_dialog, show_progress_dialog

logger = get_logger(__name__)


async def handle_save_post(
    page: ft.Page,
    sb,
    post_service: PostService,
    post_relations_service: PostRelationsService,
    post_storage_service: PostStorageService,
    meldungsart: ft.SegmentedButton,
    name_tf: ft.TextField,
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
    info_tf: ft.TextField,
    location_tf: ft.TextField,
    location_selected: Dict[str, Any],
    date_tf: ft.TextField,
    selected_farben: List[int],
    selected_photo: Dict[str, Any],
    show_status_callback: Callable[[str, bool, bool], None],
    show_validation_dialog_callback: Callable[[str, str, List[str]], None],
    parse_event_date: Callable[[str], Optional[date]],
    on_saved_callback: Optional[Callable[[int], None]] = None,
) -> None:
    """Speichert die Meldung in der Datenbank.
    
    Args:
        page: Flet Page-Instanz
        sb: Supabase Client
        post_service: PostService-Instanz
        post_relations_service: PostRelationsService-Instanz
        meldungsart: SegmentedButton für Meldungsart
        name_tf: TextField für Name/Überschrift
        species_dd: Dropdown für Tierart
        breed_dd: Dropdown für Rasse
        sex_dd: Dropdown für Geschlecht
        info_tf: TextField für Beschreibung
        location_tf: TextField für Ort
        location_selected: Ausgewaehlter Standort (text/lat/lon)
        date_tf: TextField für Datum
        selected_farben: Liste der ausgewählten Farb-IDs
        selected_photo: Dictionary mit Foto-Informationen
        show_status_callback: Callback für Status-Nachrichten
        show_validation_dialog_callback: Callback für Validierungsfehler
        parse_event_date: Funktion zum Parsen des Datums
        on_saved_callback: Optionaler Callback nach erfolgreichem Speichern
    """
    # Datum parsen
    event_date = parse_event_date(date_tf.value)
    if not event_date:
        show_validation_dialog_callback(
            "Ungültiges Format",
            "Das Datum hat ein falsches Format.",
            ["• Bitte verwende: TT.MM.YYYY", "• Beispiel: 04.01.2026"]
        )
        return
    
    # Eingeloggten Benutzer holen
    try:
        profile_service = ProfileService(sb)
        user_id = profile_service.get_user_id()
        if not user_id:
            show_error_dialog(page, "Nicht eingeloggt", "Bitte melden Sie sich an, um eine Meldung zu erstellen.")
            return
    except Exception as e:
        show_error_dialog(page, "Fehler", f"Fehler beim Abrufen des Benutzers: {e}")
        return
    
    progress_dlg = None
    try:
        progress_dlg = show_progress_dialog(page, "Meldung wird gespeichert...")
        
        # Input sanitizen vor dem Speichern
        headline = sanitize_string(name_tf.value, max_length=MAX_HEADLINE_LENGTH)
        description = sanitize_string(info_tf.value, max_length=MAX_DESCRIPTION_LENGTH)
        location = sanitize_string(location_tf.value, max_length=MAX_LOCATION_LENGTH)
        
        if location_selected.get("lat") is None or location_selected.get("lon") is None:
            show_validation_dialog_callback(
                "Standort unklar",
                "Bitte waehlen Sie einen Standort aus der Vorschlagsliste.",
                ["• Geben Sie einen konkreten Ort oder eine Adresse ein."],
            )
            if progress_dlg:
                page.close(progress_dlg)
            return

        post_data = {
            "user_id": user_id,
            "post_status_id": int(list(meldungsart.selected)[0]),
            "headline": headline,
            "description": description,
            "species_id": int(species_dd.value),
            "breed_id": int(breed_dd.value) if breed_dd.value and breed_dd.value != NO_SELECTION_VALUE else None,
            "sex_id": int(sex_dd.value) if sex_dd.value and sex_dd.value != NO_SELECTION_VALUE else None,
            "event_date": event_date.isoformat(),
            "location_text": location_selected.get("text") or location,
            "location_lat": location_selected.get("lat"),
            "location_lon": location_selected.get("lon"),
        }
        
        new_post = post_service.create(post_data)
        post_id = new_post["id"]
        
        # Farben verknüpfen
        for color_id in selected_farben:
            post_relations_service.add_color(post_id, color_id)
        
        # Bild: wenn nur lokal vorhanden, jetzt in Storage hochladen und verknüpfen
        photo_url = selected_photo.get("url")
        local_path = selected_photo.get("local_path")
        if local_path:
            upload_result = post_storage_service.upload_post_image(
                file_path=local_path,
                original_filename=selected_photo.get("name") or "image.jpg",
            )
            if upload_result.get("url"):
                post_relations_service.add_photo(post_id, upload_result["url"])
            cleanup_local_file(local_path)
        elif photo_url:
            post_relations_service.add_photo(post_id, photo_url)
        
        if progress_dlg:
            page.close(progress_dlg)
        show_success_dialog(page, "Meldung erstellt", "Ihre Meldung wurde erfolgreich veröffentlicht!")
        
        if on_saved_callback:
            on_saved_callback(post_id)
                
    except Exception as ex:
        if progress_dlg:
            page.close(progress_dlg)
        show_error_dialog(page, "Speichern fehlgeschlagen", f"Fehler beim Erstellen der Meldung: {ex}")
        logger.error(f"Fehler beim Speichern des Posts: {ex}", exc_info=True)


def reset_form_fields(
    post_statuses: List[Dict[str, Any]],
    meldungsart: ft.SegmentedButton,
    name_tf: ft.TextField,
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
    info_tf: ft.TextField,
    location_tf: ft.TextField,
    date_tf: ft.TextField,
    title_label: ft.Text,
    selected_farben: List[int],
    farben_checkboxes: Dict[int, ft.Checkbox],
    selected_photo: Dict[str, Any],
    photo_preview: ft.Image,
    status_text: ft.Text,
    species_list: List[Dict[str, Any]],
    breeds_by_species: Dict[int, List[Dict[str, Any]]],
    ai_hint_badge: Optional[ft.Control],
    page: ft.Page,
) -> None:
    """Setzt das Formular auf Standardwerte zurück.
    
    Args:
        post_statuses: Liste der Meldungsarten
        meldungsart: SegmentedButton für Meldungsart
        name_tf: TextField für Name/Überschrift
        species_dd: Dropdown für Tierart
        breed_dd: Dropdown für Rasse
        sex_dd: Dropdown für Geschlecht
        info_tf: TextField für Beschreibung
        location_tf: TextField für Ort
        date_tf: TextField für Datum
        title_label: Label für Name/Überschrift
        selected_farben: Liste der ausgewählten Farb-IDs (wird zurückgesetzt)
        farben_checkboxes: Dictionary mit Checkbox-Referenzen
        selected_photo: Dictionary mit Foto-Informationen (wird zurückgesetzt)
        photo_preview: Image-Widget für Vorschau
        status_text: Text-Widget für Status-Nachrichten
        species_list: Liste der Tierarten
        breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        ai_hint_badge: Optionales Badge für KI-Hinweis
        page: Flet Page-Instanz
    """
    if post_statuses:
        meldungsart.selected = {str(post_statuses[0]["id"])}
    name_tf.value = ""
    if species_list:
        species_dd.value = str(species_list[0]["id"])
        # Rassen für die ausgewählte Tierart laden
        species_id = species_list[0]["id"]
        breeds = breeds_by_species.get(species_id, [])
        breed_dd.options = [ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)] + [
            ft.dropdown.Option(str(b["id"]), b["name"]) for b in breeds
        ]
    breed_dd.value = NO_SELECTION_VALUE
    sex_dd.value = NO_SELECTION_VALUE
    info_tf.value = ""
    location_tf.value = ""
    date_tf.value = ""
    
    selected_farben.clear()
    for cb in farben_checkboxes.values():
        cb.value = False
    local_path = selected_photo.get("local_path")
    if local_path:
        cleanup_local_file(local_path)
    selected_photo.update({"path": None, "name": None, "url": None, "base64": None, "local_path": None})
    photo_preview.visible = False
    title_label.value = "Name﹡"
    status_text.value = ""
    
    if ai_hint_badge:
        ai_hint_badge.visible = False
    
    page.update()


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler 
# ─────────────────────────────────────────────────────────────

async def handle_view_save_post(
    page: ft.Page,
    sb,
    post_service: PostService,
    post_relations_service: PostRelationsService,
    post_storage_service: PostStorageService,
    meldungsart: ft.SegmentedButton,
    name_tf: ft.TextField,
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
    info_tf: ft.TextField,
    location_tf: ft.TextField,
    location_selected: Dict[str, Any],
    date_tf: ft.TextField,
    selected_farben: List[int],
    selected_photo: Dict[str, Any],
    post_statuses: List[Dict[str, Any]],
    species_list: List[Dict[str, Any]],
    breeds_by_species: Dict[int, List[Dict[str, Any]]],
    title_label: ft.Text,
    farben_checkboxes: Dict[int, ft.Checkbox],
    photo_preview: ft.Image,
    status_text: ft.Text,
    ai_hint_badge: Optional[ft.Control],
    show_status_callback: Callable[[str, bool, bool], None],
    show_validation_dialog_callback: Callable[[str, str, List[str]], None],
    parse_event_date: Callable[[str], Optional[date]],
    on_saved_callback: Optional[Callable[[int], None]] = None,
) -> None:
    """Speichert die Meldung in der Datenbank (View-Wrapper).
    
    Args:
        page: Flet Page-Instanz
        sb: Supabase Client
        post_service: PostService-Instanz
        post_relations_service: PostRelationsService-Instanz
        meldungsart: SegmentedButton für Meldungsart
        name_tf: TextField für Name/Überschrift
        species_dd: Dropdown für Tierart
        breed_dd: Dropdown für Rasse
        sex_dd: Dropdown für Geschlecht
        info_tf: TextField für Beschreibung
        location_tf: TextField für Ort
        date_tf: TextField für Datum
        selected_farben: Liste der ausgewählten Farb-IDs
        selected_photo: Dictionary mit Foto-Informationen
        post_statuses: Liste der Meldungsarten
        species_list: Liste der Tierarten
        breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        title_label: Label für Name/Überschrift
        farben_checkboxes: Dictionary mit Checkbox-Referenzen
        photo_preview: Image-Widget für Vorschau
        status_text: Text-Widget für Status-Nachrichten
        ai_hint_badge: Optionales Badge für KI-Hinweis
        show_status_callback: Callback für Status-Nachrichten
        show_validation_dialog_callback: Callback für Validierungsfehler
        parse_event_date: Funktion zum Parsen des Datums
        on_saved_callback: Optionaler Callback nach erfolgreichem Speichern
    """
    from .form_validation_handler import validate_form_fields
    
    is_valid, errors = validate_form_fields(
        name_value=name_tf.value,
        species_value=species_dd.value,
        selected_farben=selected_farben,
        description_value=info_tf.value,
        location_value=location_tf.value,
        date_value=date_tf.value,
        photo_url=selected_photo.get("url") or ("local" if selected_photo.get("local_path") else None),
    )
    
    if not is_valid:
        show_validation_dialog_callback(
            "Pflichtfelder fehlen",
            "Bitte korrigiere folgende Fehler:",
            errors
        )
        return
    
    await handle_save_post(
        page=page,
        sb=sb,
        post_service=post_service,
        post_relations_service=post_relations_service,
        post_storage_service=post_storage_service,
        meldungsart=meldungsart,
        name_tf=name_tf,
        species_dd=species_dd,
        breed_dd=breed_dd,
        sex_dd=sex_dd,
        info_tf=info_tf,
        location_tf=location_tf,
        location_selected=location_selected,
        date_tf=date_tf,
        selected_farben=selected_farben,
        selected_photo=selected_photo,
        show_status_callback=show_status_callback,
        show_validation_dialog_callback=show_validation_dialog_callback,
        parse_event_date=parse_event_date,
        on_saved_callback=on_saved_callback,
    )
    
    # Formular zurücksetzen
    reset_form_fields(
        post_statuses=post_statuses,
        meldungsart=meldungsart,
        name_tf=name_tf,
        species_dd=species_dd,
        breed_dd=breed_dd,
        sex_dd=sex_dd,
        info_tf=info_tf,
        location_tf=location_tf,
        date_tf=date_tf,
        title_label=title_label,
        selected_farben=selected_farben,
        farben_checkboxes=farben_checkboxes,
        selected_photo=selected_photo,
        photo_preview=photo_preview,
        status_text=status_text,
        species_list=species_list,
        breeds_by_species=breeds_by_species,
        ai_hint_badge=ai_hint_badge,
        page=page,
    )
