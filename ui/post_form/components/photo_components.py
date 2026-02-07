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
    loading_indicator: ft.Control,
    on_pick_photo: Callable[[ft.ControlEvent], None],
    on_remove_photo: Callable[[ft.ControlEvent], None],
    page: Optional[ft.Page] = None,
) -> ft.Container:
    """Erstellt den Foto-Upload Bereich.
    
    Args:
        photo_preview: Image-Widget für Vorschau
        loading_indicator: Ladeanzeige fuer Upload
        on_pick_photo: Callback für Foto-Auswahl
        on_remove_photo: Callback für Foto-Entfernung
        page: Optional Flet Page-Instanz für Theme-Erkennung
    
    Returns:
        Container mit Upload-Bereich und Vorschau
    """
    # Theme-aware Farben (lesbar in Hell- und Dunkelmodus)
    text_color = ft.Colors.ON_SURFACE_VARIANT
    icon_color = ft.Colors.ON_SURFACE_VARIANT
    border_color = getattr(ft.Colors, "OUTLINE_VARIANT", None) or ft.Colors.ON_SURFACE_VARIANT
    
    return ft.Container(
        content=ft.Column(
            [
                photo_preview,
                loading_indicator,
                ft.Row(
                    [
                        ft.FilledButton(
                            "Foto hochladen",
                            icon=ft.Icons.UPLOAD,
                            on_click=on_pick_photo,
                        ),
                        ft.TextButton(
                            "Foto entfernen",
                            icon=ft.Icons.DELETE,
                            on_click=on_remove_photo,
                        ),
                    ],
                    spacing=12,
                ),
            ],
            spacing=10,
        ),
    )
