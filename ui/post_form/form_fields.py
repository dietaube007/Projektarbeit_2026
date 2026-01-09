"""
Form Fields - UI-Komponenten für das Meldungsformular.

Enthält Funktionen zum Erstellen von:
- Meldungsart SegmentedButton
- Eingabefelder (Name, Beschreibung, Ort, Datum)
- Dropdowns (Tierart, Rasse, Geschlecht)
- Farben-Panel mit Checkboxes
- Foto-Upload Bereich
"""

from typing import List, Dict, Callable, Optional

import flet as ft

from ui.post_form.constants import (
    FIELD_WIDTH_SMALL,
    FIELD_WIDTH_MEDIUM,
    FIELD_WIDTH_LARGE,
    PLACEHOLDER_IMAGE,
    NO_SELECTION_VALUE,
    NO_SELECTION_LABEL,
)


def create_meldungsart_button(on_change: Callable) -> ft.SegmentedButton:
    """Erstellt den SegmentedButton für die Meldungsart."""
    return ft.SegmentedButton(
        selected={"1"},
        segments=[ft.Segment(value="1", label=ft.Text("Vermisst"))],
        allow_empty_selection=False,
        allow_multiple_selection=False,
        on_change=on_change,
    )


def create_photo_preview() -> ft.Image:
    """Erstellt das Image-Element für die Foto-Vorschau."""
    return ft.Image(
        width=FIELD_WIDTH_MEDIUM,
        height=250,
        fit=ft.ImageFit.COVER,
        visible=False,
        src_base64=PLACEHOLDER_IMAGE
    )


def create_name_field() -> ft.TextField:
    """Erstellt das Eingabefeld für Name/Überschrift."""
    return ft.TextField(width=FIELD_WIDTH_MEDIUM)


def create_title_label() -> ft.Text:
    """Erstellt das Label für Name/Überschrift."""
    return ft.Text(
        "Name﹡",
        size=14,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.GREY_700
    )


def create_species_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für die Tierart."""
    return ft.Dropdown(
        label="Tierart﹡",
        text_size=14,
        width=FIELD_WIDTH_SMALL
    )


def create_breed_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für die Rasse."""
    return ft.Dropdown(
        label="Rasse (optional)",
        width=FIELD_WIDTH_SMALL
    )


def create_sex_dropdown() -> ft.Dropdown:
    """Erstellt das Dropdown für das Geschlecht."""
    return ft.Dropdown(
        label="Geschlecht (optional)",
        width=FIELD_WIDTH_SMALL
    )


def create_description_field() -> ft.TextField:
    """Erstellt das mehrzeilige Beschreibungsfeld."""
    return ft.TextField(
        multiline=True,
        max_lines=4,
        width=FIELD_WIDTH_LARGE,
        min_lines=2,
    )


def create_location_field() -> ft.TextField:
    """Erstellt das Eingabefeld für den Ort."""
    return ft.TextField(
        label="Ort﹡",
        width=FIELD_WIDTH_LARGE
    )


def create_date_field() -> ft.TextField:
    """Erstellt das Eingabefeld für das Datum."""
    return ft.TextField(
        label="Datum﹡ (TT.MM.YYYY)",
        width=FIELD_WIDTH_SMALL,
        hint_text="z.B. 15.11.2025"
    )


def create_status_text() -> ft.Text:
    """Erstellt das Status-Text Element für Meldungen."""
    return ft.Text("", color=ft.Colors.BLUE, size=12)


def create_farben_panel(
    colors_list: List[Dict],
    on_color_change: Callable[[int, bool], None]
) -> tuple[ft.ResponsiveRow, ft.Container, ft.Container, ft.Icon, Dict[int, ft.Checkbox]]:
    """Erstellt das Farben-Panel mit Checkboxes."""
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


def create_photo_upload_area(
    photo_preview: ft.Image,
    on_pick_photo: Callable,
    on_remove_photo: Callable
) -> ft.Container:
    """Erstellt den Foto-Upload Bereich."""
    return ft.Container(
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
                on_click=on_pick_photo,
            ),
            photo_preview,
            ft.TextButton(
                "Foto entfernen",
                icon=ft.Icons.DELETE,
                on_click=on_remove_photo
            ),
        ], spacing=10),
    )


def create_save_button(on_click: Callable) -> ft.FilledButton:
    """Erstellt den Speichern-Button."""
    return ft.FilledButton(
        "Meldung erstellen",
        width=200,
        on_click=on_click
    )


def create_ai_recognition_button(on_click: Callable) -> ft.ElevatedButton:
    """Erstellt den Button für die KI-Rassenerkennung."""
    return ft.ElevatedButton(
        "🤖 KI-Rassenerkennung starten",
        icon=ft.Icons.AUTO_AWESOME,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.PURPLE_600,
        )
    )


def create_ai_result_container() -> ft.Container:
    """Erstellt den Container für KI-Erkennungsergebnisse."""
    return ft.Container(
        visible=False,
        padding=15,
        border=ft.border.all(2, ft.Colors.PURPLE_200),
        border_radius=8,
        bgcolor=ft.Colors.PURPLE_50,
    )


def populate_dropdown_options(
    dropdown: ft.Dropdown,
    items: List[Dict],
    with_none_option: bool = False
) -> None:
    """Füllt ein Dropdown mit Optionen."""
    options = []
    
    if with_none_option:
        options.append(ft.dropdown.Option(NO_SELECTION_VALUE, NO_SELECTION_LABEL))
    
    for item in items:
        options.append(ft.dropdown.Option(str(item["id"]), item["name"]))
    
    dropdown.options = options
    
    if with_none_option:
        dropdown.value = NO_SELECTION_VALUE
