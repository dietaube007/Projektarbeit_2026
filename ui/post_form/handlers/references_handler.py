"""
References-Feature: UI und Logik zum Laden und Befüllen von Referenz-Dropdowns.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Callable
import asyncio

import flet as ft

from services.posts.references import ReferenceService
from utils.logging_config import get_logger
from ui.constants import ALLOWED_POST_STATUSES, NO_SELECTION_VALUE, NO_SELECTION_LABEL

logger = get_logger(__name__)


def populate_dropdown_options(
    dropdown: ft.Dropdown,
    items: List[Dict[str, Any]],
    with_none_option: bool = False
) -> None:
    """Füllt ein Dropdown mit Optionen.
    
    Args:
        dropdown: Dropdown-Widget das befüllt werden soll
        items: Liste von Dictionaries mit 'id' und 'name'
        with_none_option: Ob "Keine Angabe"-Option hinzugefügt werden soll
    """
    options = []
    
    if with_none_option:
        options.append(ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL))
    
    for item in items:
        options.append(ft.dropdown.Option(str(item["id"]), item["name"]))
    
    dropdown.options = options
    
    if with_none_option:
        dropdown.value = NO_SELECTION_VALUE


async def load_and_populate_references(
    ref_service: ReferenceService,
    meldungsart: ft.SegmentedButton,
    species_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
    farben_container: ft.ResponsiveRow,
    farben_checkboxes: Dict[int, ft.Checkbox],
    selected_farben: List[int],
    on_color_change_callback: Callable[[int, bool], None],
    page: ft.Page,
) -> Dict[str, Any]:
    """Lädt alle Referenzen und befüllt die Dropdowns.
    
    Args:
        ref_service: ReferenceService-Instanz
        meldungsart: SegmentedButton für Meldungsart
        species_dd: Tierart-Dropdown
        sex_dd: Geschlecht-Dropdown
        farben_container: Container für Farb-Checkboxen
        farben_checkboxes: Dictionary mit Checkbox-Referenzen (wird modifiziert)
        selected_farben: Liste der ausgewählten Farb-IDs
        on_color_change_callback: Callback wenn eine Farbe geändert wird
        page: Flet Page-Instanz
    
    Returns:
        Dictionary mit:
        - post_statuses: Liste der Meldungsarten
        - species_list: Liste der Tierarten
        - breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        - colors_list: Liste der Farben
        - sex_list: Liste der Geschlechter
    """
    try:
        # Meldungsarten laden
        all_statuses = ref_service.get_post_statuses()
        post_statuses = [
            s for s in all_statuses
            if s["name"].lower() in ALLOWED_POST_STATUSES
        ]
        meldungsart.segments = [
            ft.Segment(value=str(s["id"]), label=ft.Text(s["name"]))
            for s in post_statuses
        ]
        if post_statuses:
            meldungsart.selected = {str(post_statuses[0]["id"])}
        
        # Andere Referenzdaten laden
        species_list = ref_service.get_species()
        breeds_by_species = ref_service.get_breeds_by_species()
        colors_list = ref_service.get_colors()
        sex_list = ref_service.get_sex()
        
        # Species Dropdown füllen
        populate_dropdown_options(species_dd, species_list)
        
        # Geschlecht Dropdown mit "Keine Angabe"
        populate_dropdown_options(sex_dd, sex_list, with_none_option=True)
        
        # Farben-Checkboxes erstellen
        farben_container.controls = []
        farben_checkboxes.clear()
        for color in colors_list:
            def make_on_change(c_id: int):
                def handler(e):
                    on_color_change_callback(c_id, e.control.value)
                return handler
            
            cb = ft.Checkbox(label=color["name"], value=False, on_change=make_on_change(color["id"]))
            farben_checkboxes[color["id"]] = cb
            farben_container.controls.append(
                ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
            )
        
        if species_list:
            species_dd.value = str(species_list[0]["id"])
        
        page.update()
        
        return {
            "post_statuses": post_statuses,
            "species_list": species_list,
            "breeds_by_species": breeds_by_species,
            "colors_list": colors_list,
            "sex_list": sex_list,
        }
                
    except Exception as ex:
        logger.error(f"Fehler beim Laden der Referenzdaten: {ex}", exc_info=True)
        return {
            "post_statuses": [],
            "species_list": [],
            "breeds_by_species": {},
            "colors_list": [],
            "sex_list": [],
        }


def update_breeds_dropdown(
    breed_dd: ft.Dropdown,
    species_value: Optional[str],
    breeds_by_species: Dict[int, List[Dict[str, Any]]],
    page: Optional[ft.Page] = None,
) -> None:
    """Aktualisiert das Rassen-Dropdown basierend auf der ausgewählten Tierart.
    
    Args:
        breed_dd: Rasse-Dropdown
        species_value: Wert des Tierart-Dropdowns
        breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        page: Optional Flet Page-Instanz für Updates
    """
    try:
        sid = int(species_value) if species_value else None
        if sid and sid in breeds_by_species:
            breed_dd.options = [ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)]
            breed_dd.options += [
                ft.dropdown.Option(str(b["id"]), b["name"])
                for b in breeds_by_species[sid]
            ]
            breed_dd.value = NO_SELECTION_VALUE
        else:
            breed_dd.options = [ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL)]
            breed_dd.value = NO_SELECTION_VALUE
        if page:
            page.update()
    except Exception as ex:
        logger.error(f"Fehler beim Aktualisieren der Rassen: {ex}", exc_info=True)


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler 
# ─────────────────────────────────────────────────────────────

async def handle_view_load_references(
    ref_service: ReferenceService,
    meldungsart: ft.SegmentedButton,
    species_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
    farben_container: ft.ResponsiveRow,
    farben_checkboxes: Dict[int, ft.Checkbox],
    selected_farben: List[int],
    post_statuses: list,  # list für Mutability
    species_list: list,  # list für Mutability
    breeds_by_species: dict,  # dict für Mutability
    colors_list: list,  # list für Mutability
    sex_list: list,  # list für Mutability
    page: ft.Page,
    on_color_change_callback: Callable[[int, bool], None],
    update_breeds_callback: Callable[[], None],
    update_title_label_callback: Callable[[], None],
) -> None:
    """Lädt alle Referenzdaten aus der Datenbank (View-Wrapper).
    
    Args:
        ref_service: ReferenceService-Instanz
        meldungsart: SegmentedButton für Meldungsart
        species_dd: Tierart-Dropdown
        sex_dd: Geschlecht-Dropdown
        farben_container: Container für Farb-Checkboxen
        farben_checkboxes: Dictionary mit Checkbox-Referenzen (wird modifiziert)
        selected_farben: Liste der ausgewählten Farb-IDs
        post_statuses: Liste der Meldungsarten (wird aktualisiert)
        species_list: Liste der Tierarten (wird aktualisiert)
        breeds_by_species: Dictionary mit Rassen (wird aktualisiert)
        colors_list: Liste der Farben (wird aktualisiert)
        sex_list: Liste der Geschlechter (wird aktualisiert)
        page: Flet Page-Instanz
        on_color_change_callback: Callback wenn eine Farbe geändert wird
        update_breeds_callback: Callback zum Aktualisieren der Rassen-Dropdown
        update_title_label_callback: Callback zum Aktualisieren des Titel-Labels
    """
    try:
        result = await load_and_populate_references(
            ref_service=ref_service,
            meldungsart=meldungsart,
            species_dd=species_dd,
            sex_dd=sex_dd,
            farben_container=farben_container,
            farben_checkboxes=farben_checkboxes,
            selected_farben=selected_farben,
            on_color_change_callback=on_color_change_callback,
            page=page,
        )
        
        post_statuses.clear()
        post_statuses.extend(result["post_statuses"])
        
        species_list.clear()
        species_list.extend(result["species_list"])
        
        breeds_by_species.clear()
        breeds_by_species.update(result["breeds_by_species"])
        
        colors_list.clear()
        colors_list.extend(result["colors_list"])
        
        sex_list.clear()
        sex_list.extend(result["sex_list"])
        
        if species_list:
            # update_breeds_callback verwaltet Task-Verwaltung intern (ruft page.run_task auf)
            update_breeds_callback()
            page.update()
        
        update_title_label_callback()
            
    except Exception as ex:
        logger.error(f"Fehler beim Laden der Referenzdaten: {ex}", exc_info=True)


async def handle_view_update_breeds(
    breed_dd: ft.Dropdown,
    species_value: Optional[str],
    breeds_by_species: Dict[int, List[Dict[str, Any]]],
    page: Optional[ft.Page] = None,
) -> None:
    """Aktualisiert das Rassen-Dropdown basierend auf der Tierart (View-Wrapper).
    
    Args:
        breed_dd: Rasse-Dropdown
        species_value: Wert des Tierart-Dropdowns
        breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        page: Optional Flet Page-Instanz für Updates
    """
    update_breeds_dropdown(
        breed_dd=breed_dd,
        species_value=species_value,
        breeds_by_species=breeds_by_species,
        page=page,
    )
