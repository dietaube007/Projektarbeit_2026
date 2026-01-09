"""
Filter-Komponenten für die Discover View.

Enthält Funktionen zum Erstellen und Verwalten der Filter-UI.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, List, Dict, Any, Tuple, Optional


def create_search_field(on_change: Callable[[ft.ControlEvent], None]) -> ft.TextField:
    """Erstellt das Suchfeld.
    
    Args:
        on_change: Callback-Funktion die bei Eingabe aufgerufen wird
    
    Returns:
        TextField für Suchbegriff-Eingabe
    """
    return ft.TextField(
        label="Suche",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=on_change,
    )


def create_dropdown(
    label: str,
    on_change: Callable[[ft.ControlEvent], None],
    initial_options: Optional[List[ft.dropdown.Option]] = None
) -> ft.Dropdown:
    """Erstellt ein Dropdown-Menü.
    
    Args:
        label: Label-Text für das Dropdown
        on_change: Callback-Funktion die bei Auswahl aufgerufen wird
        initial_options: Optionale initiale Optionen (Standard: ["Alle"])
    
    Returns:
        Konfiguriertes Dropdown-Widget
    """
    if initial_options is None:
        initial_options = [ft.dropdown.Option("alle", "Alle")]
    
    return ft.Dropdown(
        label=label,
        options=initial_options,
        value="alle",
        expand=True,
        on_change=on_change,
    )


def populate_dropdown(
    dropdown: ft.Dropdown,
    items: List[Dict[str, Any]],
    id_key: str = "id",
    name_key: str = "name",
    include_all: bool = True
) -> None:
    """Befüllt ein Dropdown mit Optionen.
    
    Args:
        dropdown: Dropdown-Widget das befüllt werden soll
        items: Liste von Dictionaries mit den Daten
        id_key: Schlüssel für die ID im Dictionary (Standard: "id")
        name_key: Schlüssel für den Namen im Dictionary (Standard: "name")
        include_all: Ob "Alle"-Option hinzugefügt werden soll
    """
    if include_all:
        dropdown.options = [ft.dropdown.Option("alle", "Alle")]
    else:
        dropdown.options = []
    
    for it in items or []:
        dropdown.options.append(
            ft.dropdown.Option(str(it.get(id_key)), it.get(name_key, ""))
        )


def create_farben_panel(
    colors: List[Dict[str, Any]],
    selected_farben: List[int],
    on_color_change: Callable[[], None]
) -> Tuple[ft.ResponsiveRow, ft.Icon, ft.Container]:
    """Erstellt das Farben-Filter-Panel.
    
    Args:
        colors: Liste von Farb-Dictionaries mit 'id' und 'name'
        selected_farben: Liste mit IDs der bereits ausgewählten Farben
        on_color_change: Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        Tuple mit:
        - ResponsiveRow mit Checkboxes
        - Toggle-Icon
        - Container für Panel
    """
    farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
    
    for c in colors or []:
        c_id = c["id"]
        
        def make_on_change(color_id):
            def handler(e):
                if e.control.value:
                    if color_id not in selected_farben:
                        selected_farben.append(color_id)
                else:
                    if color_id in selected_farben:
                        selected_farben.remove(color_id)
                on_color_change()
            return handler
        
        cb = ft.Checkbox(
            label=c["name"],
            value=c_id in selected_farben,
            on_change=make_on_change(c_id)
        )
        farben_container.controls.append(
            ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
        )
    
    # Theme-Farben für Light/Dark Mode (sicherer Zugriff mit Fallback)
    surface_color = getattr(ft.Colors, "SURFACE_VARIANT", None)
    outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
    
    panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=False,
        bgcolor=surface_color,
        border_radius=8,
        border=ft.border.all(1, outline_color) if outline_color else None,
    )
    
    return farben_container, toggle_icon, panel


def create_farben_header(toggle_icon: ft.Icon, on_click: Callable) -> ft.Container:
    """Erstellt den Header für das Farben-Panel."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18, color=ft.Colors.GREY_700),
                ft.Text("Farben wählen", size=14, color=ft.Colors.GREY_900),
                ft.Container(expand=True),
                toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=on_click,
        border_radius=8,
        bgcolor=ft.Colors.GREY_50,
        border=ft.border.all(1, ft.Colors.GREY_200),
    )


def create_view_toggle(on_change: Callable[[ft.ControlEvent], None]) -> ft.SegmentedButton:
    """Erstellt den View-Toggle (Liste/Kacheln).
    
    Args:
        on_change: Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        SegmentedButton für View-Auswahl (Liste/Grid)
    """
    return ft.SegmentedButton(
        selected={"list"},
        segments=[
            ft.Segment(value="list", label=ft.Text("Liste"), icon=ft.Icon(ft.Icons.VIEW_AGENDA)),
            ft.Segment(value="grid", label=ft.Text("Kacheln"), icon=ft.Icon(ft.Icons.GRID_VIEW)),
        ],
        on_change=on_change,
    )


def create_sort_dropdown(
    on_change: Callable[[ft.ControlEvent], None]
) -> ft.Dropdown:
    """Erstellt das Sortier-Dropdown.
    
    Args:
        on_change: Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        Dropdown für Sortier-Optionen
    """
    return ft.Dropdown(
        label="Sortieren",
        options=[
            ft.dropdown.Option("created_at_desc", "Erstellungsdatum (neueste)"),
            ft.dropdown.Option("created_at_asc", "Erstellungsdatum (älteste)"),
            ft.dropdown.Option("event_date_desc", "Event-Datum (neueste)"),
            ft.dropdown.Option("event_date_asc", "Event-Datum (älteste)"),
        ],
        value="created_at_desc",
        expand=True,
        on_change=on_change,
    )


def create_reset_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.TextButton:
    """Erstellt den Filter-Reset-Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        TextButton zum Zurücksetzen der Filter
    """
    return ft.TextButton(
        "Filter zurücksetzen",
        icon=ft.Icons.RESTART_ALT,
        on_click=on_click,
    )


# ════════════════════════════════════════════════════════════════════
# FILTER MANAGEMENT
# ════════════════════════════════════════════════════════════════════


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
    # Prüfen, ob "keine_angabe" gespeichert ist
    if rasse_value == "keine_angabe":
        if species_id and update_breeds_callback:
            update_breeds_callback()
        filter_rasse.value = "keine_angabe"
    elif breed_id:
        if species_id and update_breeds_callback:
            update_breeds_callback()
        filter_rasse.value = str(breed_id)
    else:
        if species_id and update_breeds_callback:
            update_breeds_callback()
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
        "filters": filters,  # Für DiscoverService
        "search_query": search_query,
        "status_id": status_id,
        "species_id": species_id,
        "breed_id": breed_id,
        "sex_id": sex_id,
        "colors": selected_colors if selected_colors else None,
    }
