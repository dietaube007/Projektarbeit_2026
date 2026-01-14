"""
Reference-Handler: UI-Handler zum Laden und Befüllen von Referenz-Dropdowns.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Callable
import flet as ft

from services.posts.references import ReferenceService
from utils.logging_config import get_logger
from ui.shared_components import show_error_dialog
from ..components.search_filter_components import populate_dropdown

logger = get_logger(__name__)


def load_and_populate_references(
    ref_service: ReferenceService,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    farben_filter_container: ft.ResponsiveRow,
    selected_colors: list[int],
    on_color_change_callback: Callable[[], None],
    page: ft.Page,
) -> Dict[int, List[Dict[str, Any]]]:
    """Lädt alle Referenzen und befüllt die Dropdowns.

    Args:
        ref_service: ReferenceService-Instanz
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        farben_filter_container: Container für Farb-Checkboxen
        selected_colors: Liste der ausgewählten Farb-IDs (wird modifiziert)
        on_color_change_callback: Callback wenn eine Farbe geändert wird
        page: Flet Page-Instanz

    Returns:
        Dictionary mit Rassen gruppiert nach Tierart-ID
    """
    try:
        # Status/Kategorie
        populate_dropdown(filter_typ, ref_service.get_post_statuses())
        
        # Tierart
        populate_dropdown(filter_art, ref_service.get_species())

        # Geschlecht
        sex_options = ref_service.get_sex() or []
        filter_geschlecht.options = [
            ft.dropdown.Option("alle", "Alle"),
        ]
        for it in sex_options:
            filter_geschlecht.options.append(
                ft.dropdown.Option(str(it.get("id")), it.get("name", ""))
            )

        # Rassen (abhängig von Art)
        all_breeds = ref_service.get_breeds_by_species() or {}

        # Farben Checkboxen
        farben_filter_container.controls = []
        for c in ref_service.get_colors() or []:
            c_id = c["id"]

            def on_color_change(e, color_id=c_id):
                if e.control.value:
                    if color_id not in selected_colors:
                        selected_colors.append(color_id)
                else:
                    if color_id in selected_colors:
                        selected_colors.remove(color_id)
                on_color_change_callback()

            cb = ft.Checkbox(label=c["name"], value=False, on_change=on_color_change)
            farben_filter_container.controls.append(
                ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
            )

        page.update()
        return all_breeds

    except Exception as ex:
        logger.error(f"Fehler beim Laden der Referenzen: {ex}", exc_info=True)
        return {}


def update_breeds_dropdown(
    filter_art: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    all_breeds: Dict[int, List[Dict[str, Any]]],
    page: Optional[ft.Page] = None,
) -> None:
    """Aktualisiert das Rassen-Dropdown basierend auf der ausgewählten Tierart.

    Args:
        filter_art: Tierart-Dropdown
        filter_rasse: Rasse-Dropdown
        all_breeds: Dictionary mit Rassen gruppiert nach Tierart-ID
        page: Optional Flet Page-Instanz für Updates
    """
    filter_rasse.options = [
        ft.dropdown.Option("alle", "Alle"),
    ]
    try:
        if filter_art.value and filter_art.value != "alle":
            species_id = int(filter_art.value)
            breeds = all_breeds.get(species_id, [])
        else:
            breeds = []
            for arr in all_breeds.values():
                breeds.extend(arr)

        for b in breeds:
            filter_rasse.options.append(
                ft.dropdown.Option(str(b.get("id")), b.get("name", ""))
            )
    except Exception as e:
        logger.warning(f"Fehler beim Aktualisieren des Rassen-Dropdowns: {e}", exc_info=True)

    if filter_rasse.value not in [o.key for o in filter_rasse.options]:
        filter_rasse.value = "alle"

    if page:
        page.update()


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler
# ─────────────────────────────────────────────────────────────

async def handle_view_load_references(
    ref_service: ReferenceService,
    filter_typ: ft.Dropdown,
    filter_art: ft.Dropdown,
    filter_geschlecht: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    farben_filter_container: ft.ResponsiveRow,
    selected_colors: list[int],
    all_breeds: dict, 
    page: ft.Page,
    on_color_change_callback: Callable[[], None],
    update_breeds_callback: Callable[[], None],
) -> None:
    """Lädt alle Referenzen und befüllt die Dropdowns (View-Wrapper).
    
    Args:
        ref_service: ReferenceService-Instanz
        filter_typ: Kategorie-Dropdown
        filter_art: Tierart-Dropdown
        filter_geschlecht: Geschlecht-Dropdown
        filter_rasse: Rasse-Dropdown
        farben_filter_container: Container für Farb-Checkboxen
        selected_colors: Liste der ausgewählten Farb-IDs (wird modifiziert)
        all_breeds: Dictionary mit "breeds" key (wird aktualisiert)
        page: Flet Page-Instanz
        on_color_change_callback: Callback wenn eine Farbe geändert wird
        update_breeds_callback: Callback zum Aktualisieren des Rassen-Dropdowns
    """
    try:
        all_breeds["breeds"] = load_and_populate_references(
            ref_service=ref_service,
            filter_typ=filter_typ,
            filter_art=filter_art,
            filter_geschlecht=filter_geschlecht,
            filter_rasse=filter_rasse,
            farben_filter_container=farben_filter_container,
            selected_colors=selected_colors,
            on_color_change_callback=on_color_change_callback,
            page=page,
        )
        update_breeds_callback()
        page.update()
    except Exception as ex:
        logger.error(f"Fehler beim Laden der Referenzen: {ex}", exc_info=True)
        show_error_dialog(
            page,
            "Fehler beim Laden",
            "Die Filteroptionen konnten nicht geladen werden. Bitte versuchen Sie es später erneut."
        )


def handle_view_tierart_change(
    filter_art: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    all_breeds: dict,  # dict mit "breeds" key
    page: ft.Page,
    update_breeds_callback: Callable[[], None],
) -> None:
    """Wird aufgerufen wenn die Tierart geändert wird (View-Wrapper).
    
    Args:
        filter_art: Tierart-Dropdown
        filter_rasse: Rasse-Dropdown
        all_breeds: Dictionary mit "breeds" key
        page: Flet Page-Instanz
        update_breeds_callback: Callback zum Aktualisieren des Rassen-Dropdowns
    """
    update_breeds_callback()


def handle_view_update_rassen_dropdown(
    filter_art: ft.Dropdown,
    filter_rasse: ft.Dropdown,
    all_breeds: dict,  # dict mit "breeds" key
    page: Optional[ft.Page] = None,
) -> None:
    """Aktualisiert das Rassen-Dropdown basierend auf der ausgewählten Tierart (View-Wrapper).
    
    Args:
        filter_art: Tierart-Dropdown
        filter_rasse: Rasse-Dropdown
        all_breeds: Dictionary mit "breeds" key
        page: Optional Flet Page-Instanz für Updates
    """
    breeds_data = all_breeds.get("breeds", {})
    if breeds_data:
        update_breeds_dropdown(
            filter_art=filter_art,
            filter_rasse=filter_rasse,
            all_breeds=breeds_data,
            page=page,
        )
