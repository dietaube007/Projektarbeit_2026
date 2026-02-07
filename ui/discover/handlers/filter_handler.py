"""
Filter-Handler: UI-Handler für Filter-Management.
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
    update_breeds_callback: Optional[Callable[[], None]] = None,
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
        update_breeds_callback: Optional Callback zum Aktualisieren des Rassen-Dropdowns (Tierart „Alle“)
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

    # Rassen-Dropdown an Tierart „Alle“ anpassen (alle Rassen anzeigen)
    if update_breeds_callback:
        update_breeds_callback()

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


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler 
# ─────────────────────────────────────────────────────────────

def handle_view_reset_filters(
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
    update_breeds_callback: Optional[Callable[[], None]] = None,
) -> None:
    """Setzt alle Filter zurück (View-Wrapper für reset_filters).
    
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
        update_breeds_callback: Optional Callback zum Aktualisieren des Rassen-Dropdowns
    """
    reset_filters(
        search_field=search_field,
        filter_typ=filter_typ,
        filter_art=filter_art,
        filter_geschlecht=filter_geschlecht,
        filter_rasse=filter_rasse,
        sort_dropdown=sort_dropdown,
        selected_colors=selected_colors,
        color_checkboxes_container=color_checkboxes_container,
        page=page,
        on_reset=on_reset,
        update_breeds_callback=update_breeds_callback,
    )


def handle_view_apply_saved_search(
    search: Dict[str, Any],
    search_field: ft.TextField,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    selected_colors: list[int],
    color_checkboxes_container: ft.ResponsiveRow,
    update_breeds_callback: Optional[Callable[[], None]] = None,
    load_posts_callback: Optional[Callable[[], None]] = None,
    page: Optional[ft.Page] = None,
) -> None:
    """Wendet einen gespeicherten Suchauftrag auf die Filter an (View-Wrapper).
    
    Args:
        search: Dictionary mit gespeichertem Suchauftrag
        search_field: Suchfeld
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        selected_colors: Liste der ausgewählten Farb-IDs (wird aktualisiert)
        color_checkboxes_container: Container mit Farb-Checkboxen
        update_breeds_callback: Optional Callback zum Aktualisieren der Rassen-Dropdown
        load_posts_callback: Optional Callback zum Neuladen der Posts
        page: Optional Flet Page-Instanz für Updates
    """
    apply_saved_search_filters(
        search=search,
        search_field=search_field,
        filter_typ=filter_typ,
        filter_art=filter_art,
        filter_geschlecht=filter_geschlecht,
        filter_rasse=filter_rasse,
        selected_colors=selected_colors,
        color_checkboxes_container=color_checkboxes_container,
        update_breeds_callback=update_breeds_callback,
        page=page,
    )
    if load_posts_callback:
        if page:
            page.run_task(load_posts_callback)
        else:
            load_posts_callback()


def handle_view_show_save_search_dialog(
    page: ft.Page,
    saved_search_service,
    search_field: ft.TextField,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    selected_colors: list[int],
    current_user_id: Optional[str],
    on_save_search_login_required: Optional[Callable[[], None]] = None,
    on_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Zeigt Dialog zum Speichern der aktuellen Suche (View-Wrapper).
    
    Args:
        page: Flet Page-Instanz
        saved_search_service: SavedSearchService-Instanz
        search_field: Suchfeld
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        selected_colors: Liste der ausgewählten Farb-IDs
        current_user_id: Aktuelle User-ID (None wenn nicht eingeloggt)
        on_save_search_login_required: Optional Callback wenn Login für Save Search erforderlich
        on_login_required: Optional Callback wenn Login erforderlich
    """
    if not current_user_id:
        if on_save_search_login_required:
            on_save_search_login_required()
        elif on_login_required:
            on_login_required()
        else:
            return
        return

    current_filters = collect_current_filters(
        search_field=search_field,
        filter_typ=filter_typ,
        filter_art=filter_art,
        filter_geschlecht=filter_geschlecht,
        filter_rasse=filter_rasse,
        selected_colors=selected_colors,
    )

    from .saved_search_handler import show_save_search_dialog
    show_save_search_dialog(
        page=page,
        saved_search_service=saved_search_service,
        current_filters=current_filters,
    )


def handle_view_filter_change(
    page: ft.Page,
    load_posts_callback: Callable[[], None],
) -> None:
    """Wird aufgerufen wenn ein Filter geändert wird (View-Wrapper).
    
    Lädt die Posts neu mit aktualisierten Filterwerten.
    
    Args:
        page: Flet Page-Instanz
        load_posts_callback: Callback zum Neuladen der Posts
    """
    page.run_task(load_posts_callback)


def handle_view_get_filter_value(dropdown: ft.Dropdown, default: str = "alle") -> str:
    """Holt den Wert aus einem Dropdown mit Fallback (View-Hilfsfunktion).
    
    Args:
        dropdown: Dropdown-Widget
        default: Standard-Wert wenn None oder leer
    
    Returns:
        Dropdown-Wert oder default
    """
    return dropdown.value if dropdown.value else default


def handle_view_toggle_farben_panel(
    farben_panel: ft.Container,
    farben_toggle_icon: ft.Icon,
    farben_panel_visible: dict, 
    page: ft.Page,
) -> None:
    """Öffnet oder schließt das Farben-Panel (View-Wrapper).
    
    Args:
        farben_panel: Container des Farben-Panels
        farben_toggle_icon: Icon für Toggle-Button
        farben_panel_visible: Dictionary mit "visible" key (wird modifiziert)
        page: Flet Page-Instanz
    """
    farben_panel_visible["visible"] = not farben_panel_visible["visible"]
    farben_panel.visible = farben_panel_visible["visible"]
    farben_toggle_icon.name = (
        ft.Icons.KEYBOARD_ARROW_UP if farben_panel_visible["visible"] else ft.Icons.KEYBOARD_ARROW_DOWN
    )
    page.update()
