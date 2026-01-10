"""
My Favorites Components: UI-Komponenten für Favoriten-Anzeige.
"""

from __future__ import annotations

from typing import Callable, Dict, Any

import flet as ft

from ui.theme import soft_card
from ui.constants import STATUS_COLORS, SPECIES_COLORS
from ui.helpers import extract_item_data
from .menu_components import create_back_button, create_section_title

# Konstanten
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


def build_favorite_card(
    post: Dict[str, Any],
    on_remove: Callable[[int], None],
) -> ft.Control:
    """Erstellt eine Karte für eine favorisierte Meldung.
    
    Args:
        post: Post-Dictionary
        on_remove: Callback-Funktion die beim Entfernen aufgerufen wird
    
    Returns:
        Container mit Favoriten-Karte
    """
    # Daten extrahieren (zentrale Funktion)
    post_id = post.get("id")
    data = extract_item_data(post)

    title = data["title"]
    typ = data["typ"] or "Unbekannt"
    typ_lower = typ.lower()
    art = data["art"] or "Unbekannt"
    art_lower = art.lower()
    rasse = data["rasse"]
    farbe = data["farbe"]
    ort = data["ort"]
    when = data["when"]
    status = data["status"]
    img_src = data["img_src"]
    
    if img_src:
        visual_content = ft.Image(
            src=img_src,
            height=220,
            fit=ft.ImageFit.COVER,
            gapless_playback=True,
        )
    else:
        visual_content = ft.Container(
            height=220,
            bgcolor=ft.Colors.GREY_100,
            alignment=ft.alignment.center,
            content=ft.Icon(
                ft.Icons.PETS,
                size=64,
                color=ft.Colors.GREY_500,
            ),
        )
    
    visual = ft.Container(
        content=visual_content,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=ft.Colors.GREY_200,
    )
    
    # Badges
    def badge(label: str, color: str) -> ft.Control:
        return ft.Container(
            content=ft.Text(label, size=12),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            bgcolor=color,
        )
    
    status_color = STATUS_COLORS.get(typ_lower, ft.Colors.GREY_300)
    species_color = SPECIES_COLORS.get(art_lower, ft.Colors.GREY_300)

    badges = ft.Row(
        [
            badge(typ, status_color),
            badge(art, species_color),
        ],
        spacing=8,
        wrap=True,
    )
    
    # Entfernen-Button
    remove_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE,
        icon_color=ft.Colors.RED,
        tooltip="Aus Favoriten entfernen",
        on_click=lambda e, pid=post_id: on_remove(pid),
    )
    
    header = ft.Row(
        [
            ft.Text(title, size=18, weight=ft.FontWeight.W_600),
            ft.Container(expand=True),
            badges,
            remove_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    
    meta_row = ft.Row(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(ort if ort else "—", color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=6,
            ),
            ft.Row(
                [
                    ft.Icon(ft.Icons.SCHEDULE, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(when if when else "—", color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=6,
            ),
            ft.Row(
                [
                    ft.Icon(ft.Icons.LABEL, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(status, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=6,
            ),
        ],
        spacing=16,
        wrap=True,
    )
    
    line1 = ft.Text(
        f"{rasse} • {farbe}".strip(" • "),
        color=ft.Colors.ON_SURFACE_VARIANT,
    )
    
    card_inner = ft.Column(
        [visual, header, line1, meta_row],
        spacing=10,
    )
    
    return soft_card(card_inner, pad=12, elev=3)


def create_favorites_view(
    favorites_list: ft.Column,
    on_back: Callable,
) -> list[ft.Control]:
    """Erstellt die Favoriten-Ansicht.
    
    Args:
        favorites_list: Column-Container für die Favoriten-Liste
        on_back: Callback für Zurück-Button
    
    Returns:
        Liste von Controls für Favoriten-View
    """
    back_btn = create_back_button(on_back)

    favorites_card = soft_card(
        ft.Column([
            create_section_title("Favorisierte Meldungen"),
            ft.Container(height=8),
            favorites_list,
        ], spacing=12),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )

    return [back_btn, favorites_card]
