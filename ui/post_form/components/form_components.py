"""
Form Components: UI-Komponenten für Formular-Eingabefelder und Layout.

Enthält:
- Einzelne Formular-Felder (TextFields, Dropdowns, etc.)
- Layout-Sektionen für das Formular
- Komplette Formular-Layout-Komponenten
"""

from __future__ import annotations

from typing import List, Dict, Callable, Tuple, Any

import flet as ft

from ui.constants import (
    FIELD_WIDTH_SMALL,
    FIELD_WIDTH_MEDIUM,
    FIELD_WIDTH_LARGE,
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
        segments=[ft.Segment(value="1", label=ft.Text("Vermisst"))],
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
        width=FIELD_WIDTH_MEDIUM,
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
        color=ft.Colors.GREY_700
    )


def create_species_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für die Tierart.
    
    Returns:
        Dropdown-Widget für Tierart-Auswahl
    """
    return ft.Dropdown(
        label="Tierart﹡",
        text_size=14,
        width=FIELD_WIDTH_SMALL
    )


def create_breed_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für die Rasse.
    
    Returns:
        Dropdown-Widget für Rassen-Auswahl (optional)
    """
    return ft.Dropdown(
        label="Rasse (optional)",
        width=FIELD_WIDTH_SMALL
    )


def create_sex_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für das Geschlecht.
    
    Returns:
        Dropdown-Widget für Geschlechts-Auswahl (optional)
    """
    return ft.Dropdown(
        label="Geschlecht (optional)",
        width=FIELD_WIDTH_SMALL
    )


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
    return ft.Text("", color=ft.Colors.BLUE, size=12)


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
                ft.Icon(ft.Icons.PALETTE, size=18),
                ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                farben_toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
    )
    
    return farben_container, farben_panel, farben_header, farben_toggle_icon, farben_checkboxes


def create_farben_header_and_panel(
    farben_container: ft.ResponsiveRow,
    farben_toggle_icon: ft.Icon,
    farben_panel_visible: dict,
    on_toggle: Callable,
    theme_colors: dict,
) -> Tuple[ft.Container, ft.Container]:
    """Erstellt Farben-Header und -Panel-Container (ohne Checkboxes).
    
    Args:
        farben_container: ResponsiveRow Container für Checkboxes
        farben_toggle_icon: Icon für Toggle-Button
        farben_panel_visible: Dictionary mit "visible" key
        on_toggle: Callback-Funktion für Toggle
        theme_colors: Dictionary mit Theme-Farben (surface, outline)
    
    Returns:
        Tuple mit (farben_header, farben_panel)
    """
    farben_panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=farben_panel_visible["visible"],
        bgcolor=theme_colors.get("surface"),
        border_radius=8,
        border=ft.border.all(1, theme_colors["outline"]) if theme_colors.get("outline") else None,
    )
    
    farben_header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18),
                ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                farben_toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=on_toggle,
        border_radius=8,
        bgcolor=theme_colors.get("surface"),
        border=ft.border.all(1, theme_colors["outline"]) if theme_colors.get("outline") else None,
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
        ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(height=20),
    ]


def create_form_photo_section(photo_area: ft.Control, text_color: str) -> List[ft.Control]:
    """Erstellt die Foto-Upload-Sektion.
    
    Args:
        photo_area: Container mit Photo-Upload-Bereich
        text_color: Textfarbe für Labels
    
    Returns:
        Liste von Controls für die Foto-Sektion
    """
    return [
        ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=text_color),
        photo_area,
        ft.Divider(height=20),
    ]


def create_form_basic_info_section(
    title_label: ft.Text,
    name_tf: ft.TextField,
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    sex_dd: ft.Dropdown,
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
    ai_button: ft.Control,
    ai_result_container: ft.Container,
    location_tf: ft.TextField,
    date_tf: ft.TextField,
    text_color: str,
) -> List[ft.Control]:
    """Erstellt die Details-Sektion (Beschreibung, Standort, Datum).
    
    Args:
        info_tf: TextField für Beschreibung
        ai_button: Button für KI-Erkennung
        ai_result_container: Container für AI-Ergebnisse
        location_tf: TextField für Standort
        date_tf: TextField für Datum
        text_color: Textfarbe für Labels
    
    Returns:
        Liste von Controls für die Details-Sektion
    """
    return [
        ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=text_color),
        info_tf,
        ai_button,
        ai_result_container,
        ft.Divider(height=20),
        ft.Text("Standort & Datum﹡", size=12, weight=ft.FontWeight.W_600, color=text_color),
        location_tf,
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
    location_tf: ft.TextField,
    date_tf: ft.TextField,
    save_button: ft.FilledButton,
    status_text: ft.Text,
    photo_area: ft.Control,
    text_color: str,
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
        location_tf: TextField für Standort
        date_tf: TextField für Datum
        save_button: Button zum Speichern
        status_text: Text-Widget für Status-Nachrichten
        photo_area: Container mit Photo-Upload-Bereich
        text_color: Textfarbe für Labels
    
    Returns:
        Column mit komplettem Formular-Layout
    """
    # Alle Sektionen zusammenfügen
    controls = []
    
    # Header
    controls.extend(create_form_header())
    
    # Foto-Sektion
    controls.extend(create_form_photo_section(photo_area, text_color))
    
    # Basis-Info-Sektion
    controls.extend(create_form_basic_info_section(
        title_label, name_tf, species_dd, breed_dd, sex_dd
    ))
    
    # Farben-Sektion
    controls.extend(create_form_colors_section(farben_header, farben_panel))
    
    # Details-Sektion
    controls.extend(create_form_details_section(
        info_tf, ai_button, ai_result_container, location_tf, date_tf, text_color
    ))
    
    # Action-Sektion
    controls.extend(create_form_action_section(save_button, status_text))
    
    return ft.Column(controls, spacing=10)
