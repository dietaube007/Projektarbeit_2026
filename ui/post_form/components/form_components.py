"""
Form Components: UI-Komponenten für Formular-Eingabefelder und Layout.

Enthält:
- Einzelne Formular-Felder (TextFields, Dropdowns, etc.)
- Layout-Sektionen für das Formular
- Komplette Formular-Layout-Komponenten
"""

from __future__ import annotations

from typing import List, Dict, Callable, Tuple, Any, Optional

import flet as ft

from ui.constants import (
    FIELD_WIDTH_SMALL,
    FIELD_WIDTH_MEDIUM,
    FIELD_WIDTH_LARGE,
    DROPDOWN_MENU_HEIGHT,
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    BORDER_COLOR,
    PRIMARY_COLOR,
)


def create_meldungsart_button(on_change: Callable[[ft.ControlEvent], None]) -> ft.SegmentedButton:
    """Erstellt den SegmentedButton für die Meldungsart.
    
    Args:
        on_change: Callback-Funktion die bei Änderung aufgerufen wird
    
    Returns:
        Konfigurierter SegmentedButton für Meldungsart
    """
    return ft.SegmentedButton(
        selected={"1"},
        segments=[ft.Segment(value="1", label=ft.Text("Vermisst", color=ft.Colors.ON_SURFACE))],
        allow_empty_selection=False,
        allow_multiple_selection=False,
        on_change=on_change,
    )


def create_name_field() -> ft.TextField:
    """Erstellt das Eingabefeld für Name/Überschrift.
    
    Returns:
        TextField für Name/Überschrift-Eingabe
    """
    return ft.TextField(
        max_length=MAX_HEADLINE_LENGTH,
        counter_text=f"0 / {MAX_HEADLINE_LENGTH}",
        helper_text=f"Max. {MAX_HEADLINE_LENGTH} Zeichen",
        border_radius=12,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_title_label() -> ft.Text:
    """Erstellt das Label für Name/Überschrift.
    
    Returns:
        Text-Widget als Label (zeigt "Name﹡" oder "Überschrift﹡")
    """
    return ft.Text(
        "Name﹡",
        size=14,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.ON_SURFACE,
    )


def create_species_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für die Tierart.
    
    Returns:
        Dropdown-Widget für Tierart-Auswahl
    """
    dropdown = ft.Dropdown(
        label="Tierart﹡",
        text_size=14,
        width=FIELD_WIDTH_SMALL,
    )
    if hasattr(dropdown, "max_menu_height"):
        dropdown.max_menu_height = DROPDOWN_MENU_HEIGHT
    return dropdown


def create_breed_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für die Rasse.
    
    Returns:
        Dropdown-Widget für Rassen-Auswahl (optional)
    """
    dropdown = ft.Dropdown(
        label="Rasse (optional)",
        width=FIELD_WIDTH_SMALL,
    )
    if hasattr(dropdown, "max_menu_height"):
        dropdown.max_menu_height = DROPDOWN_MENU_HEIGHT
    return dropdown


def create_sex_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für das Geschlecht.
    
    Returns:
        Dropdown-Widget für Geschlechts-Auswahl (optional)
    """
    dropdown = ft.Dropdown(
        label="Geschlecht (optional)",
        width=FIELD_WIDTH_SMALL,
    )
    if hasattr(dropdown, "max_menu_height"):
        dropdown.max_menu_height = DROPDOWN_MENU_HEIGHT
    return dropdown


def create_description_field() -> ft.TextField:
    """Erstellt das mehrzeilige Beschreibungsfeld.
    
    Returns:
        Mehrzeiliges TextField für Beschreibung (2-4 Zeilen)
    """
    return ft.TextField(
        multiline=True,
        max_lines=4,
        width=FIELD_WIDTH_LARGE,
        min_lines=2,
        max_length=MAX_DESCRIPTION_LENGTH,
        counter_text=f"0 / {MAX_DESCRIPTION_LENGTH}",
        helper_text=f"Min. {MIN_DESCRIPTION_LENGTH}, max. {MAX_DESCRIPTION_LENGTH} Zeichen",
        border_radius=12,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_location_field() -> ft.TextField:
    """Erstellt das Eingabefeld für den Ort.
    
    Returns:
        TextField für Orts-Eingabe
    """
    return ft.TextField(
        label="Ort﹡",
        width=FIELD_WIDTH_LARGE,
        border_radius=12,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_date_field() -> ft.TextField:
    """Erstellt das Eingabefeld für das Datum.
    
    Returns:
        TextField für Datums-Eingabe (Format: TT.MM.YYYY)
    """
    return ft.TextField(
        label="Datum﹡ (TT.MM.YYYY)",
        width=FIELD_WIDTH_SMALL,
        hint_text="z.B. 15.11.2025",
        border_radius=12,
        border_color=BORDER_COLOR,
        focused_border_color=PRIMARY_COLOR,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def create_status_text() -> ft.Text:
    """Erstellt das Status-Text Element für Meldungen.
    
    Returns:
        Text-Widget für Status-Nachrichten (Fehler, Erfolg, etc.)
    """
    return ft.Text("", color=PRIMARY_COLOR, size=12)


def create_farben_panel(
    colors_list: List[Dict[str, Any]],
    on_color_change: Callable[[int, bool], None]
) -> Tuple[ft.ResponsiveRow, ft.Container, ft.Container, ft.Icon, Dict[int, ft.Checkbox]]:
    """Erstellt das Farben-Panel mit Checkboxes.
    
    Args:
        colors_list: Liste von Farb-Dictionaries mit 'id' und 'name'
        on_color_change: Callback-Funktion (color_id, is_selected)
    
    Returns:
        Tuple mit:
        - ResponsiveRow mit Checkboxes
        - Container für Panel
        - Container für Header
        - Icon für Toggle
        - Dictionary mit Checkbox-Referenzen
    """
    farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    farben_checkboxes: Dict[int, ft.Checkbox] = {}
    
    # Checkboxes für jede Farbe erstellen
    for color in colors_list:
        def make_on_change(c_id: int):
            def handler(e):
                on_color_change(c_id, e.control.value)
            return handler
        
        cb = ft.Checkbox(
            label=color["name"],
            value=False,
            on_change=make_on_change(color["id"])
        )
        farben_checkboxes[color["id"]] = cb
        farben_container.controls.append(
            ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
        )
    
    farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)
    
    farben_panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=True,
    )
    
    farben_header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                ft.Container(expand=True),
                farben_toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        border_radius=8,
        bgcolor=ft.Colors.TRANSPARENT,
    )
    
    return farben_container, farben_panel, farben_header, farben_toggle_icon, farben_checkboxes


def create_farben_header_and_panel(
    farben_container: ft.ResponsiveRow,
    farben_toggle_icon: ft.Icon,
    farben_panel_visible: dict,
    on_toggle: Callable,
    page: ft.Page,
) -> Tuple[ft.Container, ft.Container]:
    """Erstellt Farben-Header und -Panel-Container (ohne Checkboxes).
    
    Args:
        farben_container: ResponsiveRow Container für Checkboxes
        farben_toggle_icon: Icon für Toggle-Button
        farben_panel_visible: Dictionary mit "visible" key
        on_toggle: Callback-Funktion für Toggle
        page: Flet Page-Instanz für Theme-Erkennung
    
    Returns:
        Tuple mit (farben_header, farben_panel)
    """
    from ui.theme import get_theme_color
    
    # Material-3 outline als Fallback, sonst text_secondary
    outline_color = getattr(ft.Colors, "OUTLINE_VARIANT", None)
    if not outline_color:
        outline_color = get_theme_color("text_secondary", page=page)
    
    farben_panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=farben_panel_visible["visible"],
        bgcolor=ft.Colors.TRANSPARENT,
        border_radius=8,
        border=ft.border.all(1, outline_color) if outline_color else None,
    )
    
    farben_header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                ft.Container(expand=True),
                farben_toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=on_toggle,
        border_radius=8,
        bgcolor=ft.Colors.TRANSPARENT,
        border=ft.border.all(1, outline_color) if outline_color else None,
    )
    
    return farben_header, farben_panel


def create_save_button(on_click: Callable[[ft.ControlEvent], None]) -> ft.FilledButton:
    """Erstellt den Speichern-Button.
    
    Args:
        on_click: Callback-Funktion für Button-Klick
    
    Returns:
        FilledButton zum Speichern der Meldung
    """
    return ft.FilledButton(
        "Meldung erstellen",
        width=200,
        on_click=on_click
    )


# ════════════════════════════════════════════════════════════════════
# FORMULAR-LAYOUT-SEKTIONEN
# ════════════════════════════════════════════════════════════════════

def create_form_header() -> List[ft.Control]:
    """Erstellt den Formular-Header mit Titel.
    
    Returns:
        Liste von Controls für den Header (Titel + Divider)
    """
    return [
        ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
        ft.Divider(height=8),
    ]


def create_form_meldungsart_section(meldungsart: ft.SegmentedButton) -> List[ft.Control]:
    """Erstellt die Meldungsart-Sektion (Vermisst/Fundtier).
    
    Args:
        meldungsart: SegmentedButton für Meldungsart
    
    Returns:
        Liste von Controls für die Meldungsart-Sektion
    """
    return [
        ft.Divider(height=8),
        ft.Text("Meldungsart﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
        meldungsart,
    ]


def create_form_photo_section(
    photo_area: ft.Control,
    photo_status_text: ft.Text,
    page: ft.Page,
) -> List[ft.Control]:
    """Erstellt die Foto-Upload-Sektion.
    
    Args:
        photo_area: Container mit Photo-Upload-Bereich
        photo_status_text: Statusanzeige fuer Fotoaktionen
        page: Flet Page-Instanz für Theme-Erkennung
    
    Returns:
        Liste von Controls für die Foto-Sektion
    """
    return [
        ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
        photo_area,
        photo_status_text,
    ]


def create_form_basic_info_section(
    title_label: ft.Text,
    name_tf: ft.TextField,
    species_dd: ft.Control,
    breed_dd: ft.Control,
    sex_dd: ft.Control,
) -> List[ft.Control]:
    """Erstellt die Basis-Informationen-Sektion.
    
    Args:
        title_label: Label für Name/Überschrift
        name_tf: TextField für Name
        species_dd: Dropdown für Tierart
        breed_dd: Dropdown für Rasse
        sex_dd: Dropdown für Geschlecht
    
    Returns:
        Liste von Controls für die Basis-Info-Sektion
    """
    return [
        title_label,
        name_tf,
        ft.Row([species_dd, breed_dd, sex_dd], spacing=15, wrap=True),
    ]


def create_form_ai_section(
    ai_button: ft.Control,
    ai_result_container: ft.Container,
    ai_status_text: ft.Text,
    divider: ft.Divider,
) -> List[ft.Control]:
    """Erstellt die KI-Rassenerkennungs-Sektion (unterhalb des Bildes).
    
    Args:
        ai_button: Button für KI-Erkennung
        ai_result_container: Container für KI-Ergebnisse
        ai_status_text: Statusanzeige fuer KI-Aktionen
        divider: Trennlinie unter dem KI-Bereich
    
    Returns:
        Liste von Controls für die KI-Sektion
    """
    return [
        ai_button,
        ai_result_container,
        ai_status_text,
        divider,
    ]


def create_form_colors_section(
    farben_header: ft.Container,
    farben_panel: ft.Container,
) -> List[ft.Control]:
    """Erstellt die Farben-Sektion.
    
    Args:
        farben_header: Container mit Farben-Header
        farben_panel: Container mit Farben-Panel
    
    Returns:
        Liste von Controls für die Farben-Sektion (inkl. Divider nachher)
    """
    return [
        farben_header,
        farben_panel,
        ft.Divider(height=20),
    ]


def create_form_details_section(
    info_tf: ft.TextField,
    location_tf: ft.TextField,
    location_suggestions: ft.Control,
    date_tf: ft.TextField,
    page: ft.Page,
) -> List[ft.Control]:
    """Erstellt die Details-Sektion (Beschreibung, Standort, Datum).
    
    Args:
        info_tf: TextField für Beschreibung
        location_tf: TextField für Standort
        location_suggestions: Vorschlagsliste für Standort
        date_tf: TextField für Datum
        page: Flet Page-Instanz für Theme-Erkennung
    
    Returns:
        Liste von Controls für die Details-Sektion
    """
    return [
        ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
        info_tf,
        ft.Divider(height=20),
        ft.Text("Standort & Datum﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
        location_tf,
        location_suggestions,
        date_tf,
        ft.Divider(height=20),
    ]


def create_form_action_section(
    save_button: ft.FilledButton,
    status_text: ft.Text,
) -> List[ft.Control]:
    """Erstellt die Action-Sektion (Save-Button, Status).
    
    Args:
        save_button: Button zum Speichern
        status_text: Text-Widget für Status-Nachrichten
    
    Returns:
        Liste von Controls für die Action-Sektion
    """
    return [
        ft.Row([save_button]),
        status_text,
    ]


def create_form_layout(
    title_label: ft.Text,
    name_tf: ft.TextField,
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
    farben_header: ft.Container,
    farben_panel: ft.Container,
    info_tf: ft.TextField,
    ai_button: ft.Control,
    ai_result_container: ft.Container,
    ai_status_text: ft.Text,
    ai_divider: ft.Divider,
    location_tf: ft.TextField,
    location_suggestions: ft.Control,
    date_tf: ft.TextField,
    save_button: ft.FilledButton,
    status_text: ft.Text,
    photo_area: ft.Control,
    photo_status_text: ft.Text,
    page: ft.Page,
    meldungsart: ft.SegmentedButton,
) -> ft.Column:
    """Erstellt das komplette Formular-Layout.
    
    Args:
        title_label: Label für Name/Überschrift
        name_tf: TextField für Name
        species_dd: Dropdown für Tierart
        breed_dd: Dropdown für Rasse
        sex_dd: Dropdown für Geschlecht
        farben_header: Container mit Farben-Header
        farben_panel: Container mit Farben-Panel
        info_tf: TextField für Beschreibung
        ai_button: Button für KI-Erkennung
        ai_result_container: Container für AI-Ergebnisse
        ai_status_text: Statusanzeige fuer KI-Aktionen
        ai_divider: Trennlinie unter dem KI-Bereich
        location_tf: TextField für Standort
        location_suggestions: Vorschlagsliste für Standort
        date_tf: TextField für Datum
        save_button: Button zum Speichern
        status_text: Text-Widget für Status-Nachrichten
        photo_area: Container mit Photo-Upload-Bereich
        photo_status_text: Statusanzeige fuer Fotoaktionen
        page: Flet Page-Instanz für Theme-Erkennung
        meldungsart: SegmentedButton für Meldungsart (Vermisst/Fundtier)
    
    Returns:
        Column mit komplettem Formular-Layout
    """
    # Alle Sektionen zusammenfügen
    controls = []
    
    # Header
    controls.extend(create_form_header())
    
    # Foto-Sektion
    controls.extend(create_form_photo_section(photo_area, photo_status_text, page))
    
    # Meldungsart-Sektion (zwischen Bild und Name/Überschrift)
    controls.extend(create_form_meldungsart_section(meldungsart))

    # KI-Rassenerkennung (nur bei Fundtier)
    controls.extend(create_form_ai_section(ai_button, ai_result_container, ai_status_text, ai_divider))
    
    # Basis-Info-Sektion
    controls.extend(create_form_basic_info_section(
        title_label, name_tf, species_dd, breed_dd, sex_dd
    ))
    
    # Farben-Sektion
    controls.extend(create_form_colors_section(farben_header, farben_panel))
    
    # Details-Sektion
    controls.extend(create_form_details_section(info_tf, location_tf, location_suggestions, date_tf, page))
    
    # Action-Sektion
    controls.extend(create_form_action_section(save_button, status_text))
    
    return ft.Column(controls, spacing=10)
