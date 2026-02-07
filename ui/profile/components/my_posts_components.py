"""
My Posts Components: UI-Komponenten für Post-Karten und View.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any, List

import flet as ft

from ui.theme import soft_card, get_theme_color
from ui.constants import STATUS_COLORS, SPECIES_COLORS, PRIMARY_COLOR
from ui.helpers import extract_item_data
from ui.discover.components.post_card_components import show_detail_dialog

# Konstanten
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


def build_my_post_card(
    post: dict,
    page: ft.Page,
    on_edit: Optional[Callable[[dict], None]] = None,
    on_delete: Optional[Callable[[int], None]] = None,
    on_mark_reunited: Optional[Callable[[dict], None]] = None,
    supabase=None,
    profile_service=None,
) -> ft.Control:
    """Erstellt eine responsive Grid-Karte für eine eigene Meldung.

    Args:
        post: Post-Dictionary
        page: Flet Page-Instanz
        on_edit: Optionaler Callback zum Bearbeiten
        on_delete: Optionaler Callback zum Löschen
        on_mark_reunited: Optionaler Callback zum Als-wiedervereint-markieren
        supabase: Supabase-Client (für Kommentare im Detail-Dialog)
        profile_service: ProfileService (für Kommentare im Detail-Dialog)

    Returns:
        Container mit Post-Karte (responsive col-Breakpoints)
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    card_bg = get_theme_color("card", is_dark=is_dark)
    c_secondary = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_600
    c_hint = ft.Colors.GREY_500

    # Daten extrahieren (zentrale Funktion)
    post_id = post.get("id")
    data = extract_item_data(post)

    title = data["title"]
    typ = data["typ"] or "Unbekannt"
    typ_lower = typ.lower()
    art = data["art"] or "Unbekannt"
    art_lower = art.lower()
    event_date = data["when"]
    img_src = data["img_src"]

    # ── Bild (volle Breite oben) ──
    if img_src:
        visual = ft.Container(
            content=ft.Image(
                src=img_src,
                width=float("inf"),
                height=300,
                fit=ft.ImageFit.COVER,
                gapless_playback=True,
            ),
            border_radius=ft.border_radius.only(top_left=14, top_right=14),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_200,
            expand=True,
        )
    else:
        visual = ft.Container(
            height=300,
            bgcolor=ft.Colors.GREY_800 if is_dark else ft.Colors.GREY_100,
            border_radius=ft.border_radius.only(top_left=14, top_right=14),
            alignment=ft.alignment.center,
            expand=True,
            content=ft.Icon(
                ft.Icons.PETS,
                size=48,
                color=ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_400,
            ),
        )

    # ── Badges ──
    status_color = STATUS_COLORS.get(typ_lower, ft.Colors.GREY_300)
    species_color = SPECIES_COLORS.get(art_lower, ft.Colors.GREY_300)

    def badge(label: str, color: str) -> ft.Control:
        return ft.Container(
            content=ft.Text(label, size=10, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=12,
            bgcolor=color,
        )

    badges_row = ft.Row(
        [badge(typ, status_color), badge(art, species_color)],
        spacing=4,
        wrap=True,
    )

    # ── Titel ──
    title_text = ft.Text(
        title,
        size=14,
        weight=ft.FontWeight.W_600,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    # ── Datum ──
    date_row = ft.Row(
        [
            ft.Icon(ft.Icons.EVENT, size=12, color=c_hint),
            ft.Text(event_date if event_date else "—", size=11, color=c_secondary),
        ],
        spacing=4,
    )

    # ── Aktionen ──
    action_controls = []
    if typ_lower != "wiedervereint":
        action_controls.append(
            ft.IconButton(
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                icon_size=18,
                icon_color=ft.Colors.GREEN_600,
                tooltip="Als wiedervereint markieren",
                on_click=lambda e, p=post: on_mark_reunited(p) if on_mark_reunited else None,
                style=ft.ButtonStyle(padding=4),
            )
        )
    action_controls.extend([
        ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_size=18,
            icon_color=PRIMARY_COLOR,
            tooltip="Bearbeiten",
            on_click=lambda e, p=post: on_edit(p) if on_edit else None,
            style=ft.ButtonStyle(padding=4),
        ),
        ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=18,
            icon_color=ft.Colors.RED_600,
            tooltip="Löschen",
            on_click=lambda e, pid=post_id: on_delete(pid) if on_delete else None,
            style=ft.ButtonStyle(padding=4),
        ),
    ])

    actions_row = ft.Row(
        action_controls,
        spacing=0,
    )

    # Badges links, Buttons rechts in einer Zeile
    top_row = ft.Row(
        [
            badges_row,
            ft.Container(expand=True),
            actions_row,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
    )

    # ── Karten-Inhalt (vertikal) ──
    card_body = ft.Container(
        content=ft.Column(
            [
                top_row,
                title_text,
                date_row,
            ],
            spacing=6,
        ),
        padding=ft.padding.only(left=12, right=8, bottom=16, top=8),
    )

    card_content = ft.Column(
        [visual, card_body],
        spacing=0,
    )

    # Klickbare Karte für Details (Discover-Dialog wiederverwenden)
    def show_details(e):
        show_detail_dialog(
            page=page,
            item=post,
            supabase=supabase,
            profile_service=profile_service,
        )

    clickable_card = ft.Container(
        content=card_content,
        border_radius=14,
        bgcolor=card_bg,
        ink=True,
        on_click=show_details,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        animate_scale=200,
        scale=ft.Scale(1.0),
    )

    def on_hover(e: ft.HoverEvent):
        clickable_card.scale = ft.Scale(1.02) if e.data == "true" else ft.Scale(1.0)
        page.update()

    clickable_card.on_hover = on_hover

    # Responsive Grid-Breakpoints: 1 mobil, 2 Tablet, 4 Desktop
    return ft.Container(
        content=clickable_card,
        col={"xs": 12, "sm": 6, "md": 3},
    )


def create_my_posts_view(
    my_posts_list: ft.ResponsiveRow,
    my_posts_items: List[dict],
    page: Optional[ft.Page] = None,
) -> list[ft.Control]:
    """Erstellt die Meine Posts-Ansicht.

    Args:
        my_posts_list: ResponsiveRow-Container für die Posts-Grid
        my_posts_items: Liste der Post-Dictionaries
        page: Flet Page-Instanz (für Dark-Mode)
    Returns:
        Liste von Controls für My Posts-View
    """
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    c_secondary = ft.Colors.GREY_400 if is_dark else ft.Colors.GREY_600
    count_text = f"{len(my_posts_items)} Meldung(en)" if my_posts_items else ""

    header = ft.Container(
        content=ft.Row([
            ft.Text("Meine Meldungen", size=18, weight=ft.FontWeight.W_600),
            ft.Container(expand=True),
            ft.Text(count_text, size=12, color=c_secondary),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    return [header, my_posts_list]
