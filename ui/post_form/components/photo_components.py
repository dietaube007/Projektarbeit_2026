"""
Photo-Komponenten: UI-Komponenten für Foto-Upload und -Vorschau.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from ui.constants import (
    FIELD_WIDTH_MEDIUM,
    PLACEHOLDER_IMAGE,
)


def create_photo_preview() -> ft.Image:
    """Erstellt das Image-Element für die Foto-Vorschau.
    
    Returns:
        Image-Widget für Foto-Vorschau (initial unsichtbar)
    """
    return ft.Image(
        width=FIELD_WIDTH_MEDIUM,
        height=250,
        fit=ft.ImageFit.COVER,
        visible=False,
        src_base64=PLACEHOLDER_IMAGE
    )


def create_photo_upload_area(
    photo_preview: ft.Image,
    on_pick_photo: Callable[[ft.ControlEvent], None],
    on_remove_photo: Callable[[ft.ControlEvent], None],
    page: Optional[ft.Page] = None,
) -> ft.Container:
    """Erstellt den Foto-Upload Bereich.
    
    Args:
        photo_preview: Image-Widget für Vorschau
        on_pick_photo: Callback für Foto-Auswahl
        on_remove_photo: Callback für Foto-Entfernung
        page: Optional Flet Page-Instanz für Theme-Erkennung
    
    Returns:
        Container mit Upload-Bereich und Vorschau
    """
    from ui.theme import get_theme_color
    
    if page:
        text_color = get_theme_color("text_secondary", page=page)
        icon_color = get_theme_color("text_secondary", page=page)
        border_color = get_theme_color("text_secondary", page=page)
    else:
        text_color = ft.Colors.GREY_700
        icon_color = ft.Colors.GREY_500
        border_color = ft.Colors.GREY_300
    
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=icon_color),
                    ft.Text("Foto hochladen (Tippen)", color=text_color, size=12),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=400,
                height=150,
                border=ft.border.all(2, border_color),
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
