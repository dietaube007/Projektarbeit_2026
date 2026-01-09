"""
Filter-Feature: UI und Logik für Filter-Management.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List
import flet as ft

from utils.logging_config import get_logger

logger = get_logger(__name__)


def reset_filters(
    search_field: ft.TextField,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    sort_dropdown: ft.Dropdown,
    selected_colors: list[int],
    color_checkboxes_container: ft.ResponsiveRow,
    page: ft.Page,
    on_reset: Optional[Callable[[], None]] = None,
) -> None:
    """Setzt alle Filter zurück.

    Args:
        search_field: Suchfeld
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        sort_dropdown: Sortier-Dropdown
        selected_colors: Liste der ausgewählten Farb-IDs (wird geleert)
        color_checkboxes_container: Container mit Farb-Checkboxen
        page: Flet Page-Instanz
        on_reset: Optional Callback nach Reset
    """
    search_field.value = ""
    filter_typ.value = "alle"
    filter_art.value = "alle"
    filter_geschlecht.value = "alle"
    filter_rasse.value = "alle"
    sort_dropdown.value = "created_at_desc"
    selected_colors.clear()

    # Farben-Checkboxen zurücksetzen
    for container in color_checkboxes_container.controls:
        if hasattr(container, "content") and isinstance(container.content, ft.Checkbox):
            container.content.value = False

    page.update()
    if on_reset:
        on_reset()


def apply_saved_search_filters(
    search: Dict[str, Any],
    search_field: ft.TextField,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    selected_colors: list[int],
    color_checkboxes_container: ft.ResponsiveRow,
    update_breeds_callback: Optional[Callable[[], None]] = None,
    page: Optional[ft.Page] = None,
) -> None:
    """Wendet einen gespeicherten Suchauftrag auf die Filter an.

    Args:
        search: Dictionary mit gespeichertem Suchauftrag (enthält "filters")
        search_field: Suchfeld
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        selected_colors: Liste der ausgewählten Farb-IDs (wird aktualisiert)
        color_checkboxes_container: Container mit Farb-Checkboxen
        update_breeds_callback: Optional Callback zum Aktualisieren der Rassen-Dropdown
        page: Optional Flet Page-Instanz für Updates
    """
    # Saved Search speichert Filter als JSON in search["filters"]
    filters = search.get("filters") or {}

    # Suchbegriff
    search_field.value = filters.get("search_query", "") or ""

    # Status/Kategorie
    status_id = filters.get("status_id")
    filter_typ.value = str(status_id) if status_id else "alle"

    # Tierart
    species_id = filters.get("species_id")
    filter_art.value = str(species_id) if species_id else "alle"

    # Geschlecht
    sex_id = filters.get("sex_id")
    geschlecht_value = filters.get("geschlecht")
    # Prüfen, ob "keine_angabe" gespeichert ist
    if geschlecht_value == "keine_angabe":
        filter_geschlecht.value = "keine_angabe"
    elif sex_id:
        filter_geschlecht.value = str(sex_id)
    else:
        filter_geschlecht.value = "alle"

    # Farben
    colors = filters.get("colors", [])
    selected_colors.clear()
    selected_colors.extend(colors if colors else [])

    # Farben-Checkboxen aktualisieren
    for container in color_checkboxes_container.controls:
        if hasattr(container, "content") and isinstance(container.content, ft.Checkbox):
            cb = container.content
            if hasattr(cb, "data") and cb.data:
                cb.value = cb.data in selected_colors

    # Rassen für die gewählte Tierart laden
    breed_id = filters.get("breed_id")
    rasse_value = filters.get("rasse")
    
    # Rassen-Dropdown aktualisieren
    if species_id and update_breeds_callback:
        update_breeds_callback()
    
    # Wert zuweisen
    if rasse_value == "keine_angabe":
        filter_rasse.value = "keine_angabe"
    elif breed_id:
        filter_rasse.value = str(breed_id)
    else:
        filter_rasse.value = "alle"

    if page:
        page.update()


def collect_current_filters(
    search_field: ft.TextField,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    selected_colors: list[int],
) -> Dict[str, Any]:
    """Sammelt die aktuellen Filterwerte in einem Dictionary.

    Args:
        search_field: Suchfeld
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        selected_colors: Liste der ausgewählten Farb-IDs

    Returns:
        Dictionary mit Filterwerten für SavedSearchService
    """
    filters = {
        "typ": filter_typ.value,
        "art": filter_art.value,
        "geschlecht": filter_geschlecht.value,
        "rasse": filter_rasse.value,
    }

    # Für SavedSearchService: IDs extrahieren
    search_query = search_field.value.strip() if search_field.value else None
    status_id = None
    species_id = None
    breed_id = None
    sex_id = None

    try:
        if filter_typ.value and filter_typ.value != "alle":
            status_id = int(filter_typ.value)
    except (ValueError, TypeError):
        pass

    try:
        if filter_art.value and filter_art.value != "alle":
            species_id = int(filter_art.value)
    except (ValueError, TypeError):
        pass

    try:
        if filter_rasse.value and filter_rasse.value not in ["alle", "keine_angabe"]:
            breed_id = int(filter_rasse.value)
    except (ValueError, TypeError):
        pass

    try:
        if filter_geschlecht.value and filter_geschlecht.value not in ["alle", "keine_angabe"]:
            sex_id = int(filter_geschlecht.value)
    except (ValueError, TypeError):
        pass

    return {
        "filters": filters,  # Für SearchService
        "search_query": search_query,
        "status_id": status_id,
        "species_id": species_id,
        "breed_id": breed_id,
        "sex_id": sex_id,
        "colors": selected_colors if selected_colors else None,
    }
