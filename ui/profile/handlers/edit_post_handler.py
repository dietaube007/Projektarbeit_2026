"""
Edit Post Handler: Validierung, Änderungsprüfung und Speicherlogik
für das Bearbeiten von Meldungen.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

from services.posts import PostService, PostRelationsService, PostStorageService
from ui.constants import NO_SELECTION_VALUE
from ui.helpers import format_date, parse_date, get_nested_id
from utils.logging_config import get_logger
from utils.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
)
from ui.post_form.handlers.photo_upload_handler import cleanup_local_file

logger = get_logger(__name__)


def validate_edit_form(
    name_value: Optional[str],
    species_value: Optional[str],
    selected_farben: List[int],
    description_value: Optional[str],
    location_value: Optional[str],
    date_value: Optional[str],
    selected_photo: Dict[str, Any],
) -> List[str]:
    """Validiert alle Formularfelder des Edit-Dialogs.

    Args:
        name_value: Wert des Name/Überschrift-Feldes
        species_value: Wert des Tierart-Dropdowns
        selected_farben: Liste der ausgewählten Farb-IDs
        description_value: Wert des Beschreibungsfeldes
        location_value: Wert des Orts-Feldes
        date_value: Wert des Datums-Feldes
        selected_photo: Dictionary mit Foto-Informationen

    Returns:
        Liste von Fehlermeldungen (leer wenn alles valide)
    """
    errors: List[str] = []

    # Pflichtfeld-Prüfung
    checks = [
        (name_value, "Name/Überschrift"),
        (species_value, "Tierart"),
        (selected_farben, "Mindestens eine Farbe"),
        (description_value, "Beschreibung"),
        (location_value, "Ort"),
        (date_value, "Datum"),
    ]
    for value, name in checks:
        if not value or (isinstance(value, str) and not value.strip()):
            errors.append(f"• {name}")

    # Foto erforderlich
    has_photo = (
        selected_photo.get("url")
        or selected_photo.get("base64")
        or selected_photo.get("local_path")
    )
    if not has_photo:
        errors.append("• Foto ist erforderlich")

    # Zeichenlängen-Prüfung Name/Überschrift
    name_val = (name_value or "").strip()
    if name_val and len(name_val) > MAX_HEADLINE_LENGTH:
        errors.append(f"• Name/Überschrift darf max. {MAX_HEADLINE_LENGTH} Zeichen haben")

    # Zeichenlängen-Prüfung Beschreibung
    desc_val = (description_value or "").strip()
    if desc_val and len(desc_val) < MIN_DESCRIPTION_LENGTH:
        errors.append(f"• Beschreibung muss mind. {MIN_DESCRIPTION_LENGTH} Zeichen haben")
    if desc_val and len(desc_val) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"• Beschreibung darf max. {MAX_DESCRIPTION_LENGTH} Zeichen haben")

    return errors


def has_edit_changes(
    post: Dict[str, Any],
    meldungsart_selected: set,
    name_value: str,
    description_value: str,
    location_value: str,
    date_value: str,
    species_value: Optional[str],
    breed_value: Optional[str],
    sex_value: Optional[str],
    selected_farben: List[int],
    image_changed: bool,
) -> bool:
    """Prüft, ob im Edit-Dialog Änderungen vorgenommen wurden.

    Args:
        post: Original-Post-Daten
        meldungsart_selected: Ausgewählte Meldungsart (Set mit ID-String)
        name_value: Aktueller Name/Überschrift-Wert
        description_value: Aktueller Beschreibungs-Wert
        location_value: Aktueller Ort-Wert
        date_value: Aktueller Datums-Wert (formatiert)
        species_value: Aktuelle Tierart-ID (String oder None)
        breed_value: Aktuelle Rassen-ID (String oder None)
        sex_value: Aktuelles Geschlecht-ID (String oder None)
        selected_farben: Ausgewählte Farb-IDs
        image_changed: Ob das Bild geändert wurde

    Returns:
        True wenn Änderungen vorhanden
    """
    try:
        if image_changed:
            return True

        # Status
        current_status = int(list(meldungsart_selected)[0]) if meldungsart_selected else None
        if current_status != get_nested_id(post, "post_status"):
            return True

        # Textfelder
        text_checks = [
            (name_value, "headline"),
            (description_value, "description"),
            (location_value, "location_text"),
        ]
        for field_value, post_key in text_checks:
            if field_value.strip() != post.get(post_key, ""):
                return True

        # Datum
        if date_value.strip() != format_date(post.get("event_date", "")):
            return True

        # Dropdowns
        if species_value and int(species_value) != get_nested_id(post, "species"):
            return True

        breed_id = int(breed_value) if breed_value and breed_value != NO_SELECTION_VALUE else None
        if breed_id != get_nested_id(post, "breed"):
            return True

        sex_id = int(sex_value) if sex_value and sex_value != NO_SELECTION_VALUE else None
        if sex_id != get_nested_id(post, "sex"):
            return True

        # Farben
        original_colors = sorted([
            pc["color"]["id"]
            for pc in (post.get("post_color") or [])
            if pc.get("color") and pc["color"].get("id")
        ])
        if sorted(selected_farben) != original_colors:
            return True

        return False

    except Exception as ex:
        logger.error(f"Fehler beim Prüfen auf Änderungen: {ex}", exc_info=True)
        return True


def save_edit_post(
    sb,
    post: Dict[str, Any],
    post_service: PostService,
    post_relations_service: PostRelationsService,
    post_storage_service: PostStorageService,
    meldungsart_selected: set,
    name_value: str,
    description_value: str,
    species_value: str,
    breed_value: Optional[str],
    sex_value: Optional[str],
    event_date_str: str,
    location_value: str,
    selected_farben: List[int],
    selected_photo: Dict[str, Any],
    image_changed: bool,
    original_image_url: Optional[str],
) -> None:
    """Speichert die Änderungen einer bearbeiteten Meldung.

    Args:
        sb: Supabase-Client
        post: Original-Post-Daten
        post_service: PostService-Instanz
        post_relations_service: PostRelationsService-Instanz
        post_storage_service: PostStorageService-Instanz
        meldungsart_selected: Ausgewählte Meldungsart (Set mit ID-String)
        name_value: Name/Überschrift
        description_value: Beschreibung
        species_value: Tierart-ID (String)
        breed_value: Rassen-ID (String oder None)
        sex_value: Geschlecht-ID (String oder None)
        event_date_str: Datum als formatierter String (TT.MM.YYYY)
        location_value: Ort-Text
        selected_farben: Ausgewählte Farb-IDs
        selected_photo: Dictionary mit Foto-Informationen
        image_changed: Ob das Bild geändert wurde
        original_image_url: Ursprüngliche Bild-URL

    Raises:
        ValueError: Bei ungültigem Datumsformat
        Exception: Bei Fehlern beim Speichern
    """
    # Datum parsen
    event_date = parse_date(event_date_str)
    if not event_date:
        raise ValueError("Ungültiges Datumsformat.\nBitte verwende: TT.MM.YYYY")

    breed_id = int(breed_value) if breed_value and breed_value != NO_SELECTION_VALUE else None
    sex_id = int(sex_value) if sex_value and sex_value != NO_SELECTION_VALUE else None

    post_data = {
        "post_status_id": int(list(meldungsart_selected)[0]),
        "headline": name_value.strip(),
        "description": description_value.strip(),
        "species_id": int(species_value),
        "breed_id": breed_id,
        "sex_id": sex_id,
        "event_date": event_date.isoformat(),
        "location_text": location_value.strip(),
    }

    post_id = post["id"]
    post_service.update(post_id, post_data)
    post_relations_service.update_colors(post_id, selected_farben)

    # Bild aktualisieren (wenn geändert)
    if image_changed:
        _save_image(
            sb=sb,
            post_id=post_id,
            post_storage_service=post_storage_service,
            post_relations_service=post_relations_service,
            selected_photo=selected_photo,
            original_image_url=original_image_url,
        )


def _save_image(
    sb,
    post_id: str,
    post_storage_service: PostStorageService,
    post_relations_service: PostRelationsService,
    selected_photo: Dict[str, Any],
    original_image_url: Optional[str],
) -> None:
    """Speichert das neue Bild und entfernt das alte.

    Args:
        sb: Supabase-Client
        post_id: ID des Posts
        post_storage_service: PostStorageService-Instanz
        post_relations_service: PostRelationsService-Instanz
        selected_photo: Dictionary mit Foto-Informationen
        original_image_url: Ursprüngliche Bild-URL
    """
    # 1. Altes Bild aus Storage löschen (wenn vorhanden)
    if original_image_url:
        old_storage_path = post_storage_service.extract_storage_path_from_url(
            original_image_url
        )
        if old_storage_path:
            post_storage_service.remove_post_image(old_storage_path)

    # 2. Alte post_image-Einträge löschen
    try:
        sb.table("post_image").delete().eq("post_id", post_id).execute()
    except Exception as ex:
        logger.warning(f"Fehler beim Löschen alter post_image-Einträge: {ex}")

    # 3. Neues Bild hochladen (wenn vorhanden)
    local_path = selected_photo.get("local_path")
    existing_url = selected_photo.get("url")

    if local_path:
        # Neues lokales Bild → zu Storage hochladen
        result = post_storage_service.upload_post_image(
            local_path, selected_photo.get("name", "image.jpg")
        )
        new_url = result.get("url")
        if new_url:
            post_relations_service.add_photo(post_id, new_url)
        cleanup_local_file(local_path)
    elif existing_url:
        # Vorhandenes Bild beibehalten (URL unverändert)
        post_relations_service.add_photo(post_id, existing_url)
