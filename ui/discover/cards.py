"""
Card-Komponenten für die Discover View.

Enthält Funktionen zum Erstellen von kleinen und großen Meldungskarten
sowie den Detail-Dialog.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft

from ui.theme import soft_card, chip
from ui.constants import (
    STATUS_COLORS, SPECIES_COLORS,
    CARD_IMAGE_HEIGHT, LIST_IMAGE_HEIGHT, DIALOG_IMAGE_HEIGHT,
    DEFAULT_PLACEHOLDER
)
from ui.helpers import extract_item_data


def badge_for_typ(typ: str) -> ft.Control:
    """Erstellt ein Badge für den Meldungstyp (Vermisst/Fundtier).
    
    Args:
        typ: Meldungstyp (z.B. "Vermisst", "Fundtier")
    
    Returns:
        Control-Widget mit Badge für den Typ
    """
    typ_lower = (typ or "").lower().strip()
    color = STATUS_COLORS.get(typ_lower, ft.Colors.GREY_700)
    label = typ.capitalize() if typ else "Unbekannt"
    return chip(label, color)


def badge_for_species(species: str) -> ft.Control:
    """Erstellt ein Badge für die Tierart.
    
    Args:
        species: Tierart (z.B. "Hund", "Katze")
    
    Returns:
        Control-Widget mit Badge für die Tierart
    """
    species_lower = (species or "").lower().strip()
    color = SPECIES_COLORS.get(species_lower, ft.Colors.GREY_500)
    label = species.capitalize() if species else "Unbekannt"
    return chip(label, color)


def meta_row(icon: str, text: str) -> ft.Control:
    """Erstellt eine Zeile mit Icon und Text für Metadaten.
    
    Args:
        icon: Icon-Name (z.B. ft.Icons.LOCATION_ON)
        text: Anzuzeigender Text
    
    Returns:
        Row-Widget mit Icon und Text
    """
    return ft.Row(
        [
            ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(text, color=ft.Colors.ON_SURFACE_VARIANT)
        ],
        spacing=6,
    )


def image_placeholder(height: int, icon_size: int = 50) -> ft.Container:
    """Erstellt einen Platzhalter für fehlende Bilder.
    
    Args:
        height: Höhe des Platzhalters
        icon_size: Größe des Platzhalter-Icons (Standard: 50)
    
    Returns:
        Container mit Platzhalter-Icon
    """
    return ft.Container(
        height=height,
        bgcolor=ft.Colors.GREY_200,
        alignment=ft.alignment.center,
        content=ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.GREY_400),
        expand=True,
    )


def build_small_card(
    item: Dict[str, Any],
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.Control], None],
    on_card_click: Callable[[Dict[str, Any]], None]
) -> ft.Control:
    """Erstellt eine kleine Kachel-Karte für die Grid-Ansicht.
    
    Args:
        item: Post-Dictionary mit allen Daten
        page: Flet Page-Instanz
        on_favorite_click: Callback (item, control) für Favoriten-Toggle
        on_card_click: Callback (item) für Karten-Klick
    
    Returns:
        Container mit kleiner Karten-Komponente
    """
    data = extract_item_data(item)

    visual_content = (
        ft.Image(src=data["img_src"], height=CARD_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(CARD_IMAGE_HEIGHT)
    )

    visual = ft.Container(
        content=visual_content,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=ft.Colors.GREY_200,
    )

    badges = ft.Row(
        [badge_for_typ(data["typ"]), badge_for_species(data["art"])],
        spacing=8,
        wrap=True,
    )

    is_fav = item.get("is_favorite", False)
    favorite_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
        icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
        tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
        on_click=lambda e, it=item: on_favorite_click(it, e.control),
    )

    header = ft.Row(
        [
            ft.Text(data["title"], size=14, weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Container(expand=True),
            favorite_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    card_inner = ft.Column([visual, badges, header], spacing=8)
    card = soft_card(card_inner, pad=12, elev=2)

    wrapper = ft.Container(
        content=card,
        animate_scale=200,
        scale=ft.Scale(1.0),
        on_click=lambda _, it=item: on_card_click(it),
    )

    def on_hover(e: ft.HoverEvent):
        wrapper.scale = ft.Scale(1.02) if e.data == "true" else ft.Scale(1.0)
        page.update()

    wrapper.on_hover = on_hover

    return ft.Container(content=wrapper, col={"xs": 6, "sm": 4, "md": 3, "lg": 2.4})


def build_big_card(
    item: Dict[str, Any],
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.Control], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None
) -> ft.Control:
    """Erstellt eine große Listen-Karte für die Listen-Ansicht.
    
    Args:
        item: Post-Dictionary mit allen Daten
        page: Flet Page-Instanz
        on_favorite_click: Callback (item, control) für Favoriten-Toggle
        on_card_click: Callback (item) für Karten-Klick
        on_contact_click: Optionaler Callback (item) für Kontakt-Button
    
    Returns:
        Container mit großer Karten-Komponente
    """
    data = extract_item_data(item)

    visual_content = (
        ft.Image(src=data["img_src"], height=LIST_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(LIST_IMAGE_HEIGHT, icon_size=64)
    )

    visual = ft.Container(
        content=visual_content,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=ft.Colors.GREY_200,
    )

    badges = ft.Row(
        [badge_for_typ(data["typ"]), badge_for_species(data["art"])],
        spacing=8,
        wrap=True,
    )

    is_fav = item.get("is_favorite", False)
    favorite_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
        icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
        tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
        on_click=lambda e, it=item: on_favorite_click(it, e.control),
    )

    header = ft.Row(
        [
            ft.Text(data["title"], size=18, weight=ft.FontWeight.W_600),
            ft.Container(expand=True),
            badges,
            favorite_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    line1 = ft.Text(f"{data['rasse']} • {data['farbe']}".strip(" • "), color=ft.Colors.ON_SURFACE_VARIANT)

    metas = ft.Row(
        [
            meta_row(ft.Icons.LOCATION_ON, data["ort"] or DEFAULT_PLACEHOLDER),
            meta_row(ft.Icons.SCHEDULE, data["when"] or DEFAULT_PLACEHOLDER),
            meta_row(ft.Icons.LABEL, data["status"]),
        ],
        spacing=16,
        wrap=True,
    )

    actions = ft.Row(
        [
            ft.FilledButton(
                "Kontakt",
                icon=ft.Icons.EMAIL,
                on_click=lambda e, it=item: on_contact_click(it) if on_contact_click else None,
            ),
        ],
        spacing=10,
    )

    card_inner = ft.Column([visual, header, line1, metas, actions], spacing=10)
    card = soft_card(card_inner, pad=12, elev=3)

    wrapper = ft.Container(
        content=card,
        animate_scale=300,
        scale=ft.Scale(1.0),
        on_click=lambda _, it=item: on_card_click(it),
    )

    def on_hover(e: ft.HoverEvent):
        wrapper.scale = ft.Scale(1.01) if e.data == "true" else ft.Scale(1.0)
        page.update()

    wrapper.on_hover = on_hover
    return wrapper


def show_detail_dialog(
    page: ft.Page,
    item: Dict[str, Any],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None
) -> None:
    """Zeigt den Detail-Dialog für eine Meldung.
    
    Args:
        page: Flet Page-Instanz
        item: Post-Dictionary mit allen Daten
        on_contact_click: Optionaler Callback (item) für Kontakt-Button
    """
    data = extract_item_data(item)

    visual = (
        ft.Image(src=data["img_src"], height=DIALOG_IMAGE_HEIGHT, fit=ft.ImageFit.COVER)
        if data["img_src"]
        else image_placeholder(DIALOG_IMAGE_HEIGHT, icon_size=72)
    )

    dlg = ft.AlertDialog(
        title=ft.Text(data["title"]),
        content=ft.Column(
            [
                ft.Container(visual, border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
                ft.Container(height=8),
                ft.Text(item.get("description") or "Keine Beschreibung.", color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(height=8),
                meta_row(ft.Icons.LOCATION_ON, data["ort"] or DEFAULT_PLACEHOLDER),
                meta_row(ft.Icons.SCHEDULE, data["when"] or DEFAULT_PLACEHOLDER),
                meta_row(ft.Icons.LABEL, data["status"]),
            ],
            tight=True,
            spacing=8,
        ),
        actions=[
            ft.TextButton("Schließen", on_click=lambda _: page.close(dlg)),
            ft.FilledButton(
                "Kontakt",
                icon=ft.Icons.EMAIL,
                on_click=lambda e, it=item: on_contact_click(it) if on_contact_click else None,
            ),
        ],
    )
    page.open(dlg)
