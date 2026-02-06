"""
Meldung-Komponenten für die Discover-View.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft

from ui.theme import soft_card, get_theme_color
from ui.constants import (
    CARD_IMAGE_HEIGHT, LIST_IMAGE_HEIGHT, DIALOG_IMAGE_HEIGHT,
    DEFAULT_PLACEHOLDER
)
from ui.helpers import extract_item_data
from .comment_components import CommentSection
from ui.shared_components import (
    badge_for_typ,
    badge_for_species,
    meta_row,
    image_placeholder,
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
    is_dark = page.theme_mode == ft.ThemeMode.DARK

    visual_content = (
        ft.Image(src=data["img_src"], height=CARD_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(CARD_IMAGE_HEIGHT, expand=True, page=page)
    )

    visual = ft.Container(
        content=visual_content,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=get_theme_color("card", is_dark),
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

    # Ersteller mit Profilbild
    profile_img_sm = data.get("user_profile_image")
    user_row = ft.Row(
        [
            ft.CircleAvatar(
                foreground_image_src=profile_img_sm if profile_img_sm else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=8) if not profile_img_sm else None,
                bgcolor=ft.Colors.BLUE_GREY_400,
                radius=8,
            ),
            ft.Text(data["username"], size=11, color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        ],
        spacing=4,
    )

    card_inner = ft.Column([visual, badges, header, user_row], spacing=8)
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
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> ft.Control:
    """Erstellt eine große Listen-Karte für die Listen-Ansicht.
    
    Kommentare werden nur im Detail-Dialog angezeigt.
    
    Args:
        item: Post-Dictionary mit allen Daten
        page: Flet Page-Instanz
        on_favorite_click: Callback (item, control) für Favoriten-Toggle
        on_card_click: Callback (item) für Karten-Klick
        on_contact_click: Optionaler Callback (item) für Kontakt-Button
        supabase: Optional Supabase-Client (für Detail-Dialog)
        profile_service: Optional ProfileService (für Detail-Dialog)
        on_comment_login_required: Optional Callback wenn Login zum Kommentieren erforderlich
    
    Returns:
        Container mit großer Karten-Komponente
    """
    data = extract_item_data(item)
    is_dark = page.theme_mode == ft.ThemeMode.DARK

    # --- Bild ---
    visual_content = (
        ft.Image(src=data["img_src"], height=LIST_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(LIST_IMAGE_HEIGHT, icon_size=64, expand=True, page=page)
    )

    image_col = ft.Container(
        content=visual_content,
        height=LIST_IMAGE_HEIGHT,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=get_theme_color("card", is_dark),
        col={"xs": 12, "md": 5},  # Volle Breite mobil, ~40% Desktop
    )

    # --- Infos ---
    title_text = ft.Text(data["title"], size=18, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

    badges = ft.Row(
        [badge_for_typ(data["typ"]), badge_for_species(data["art"])],
        spacing=8,
        wrap=True,
    )

    line1 = ft.Text(f"{data['rasse']} • {data['farbe']}".strip(" • "), color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

    # Ersteller mit Profilbild
    profile_img = data.get("user_profile_image")
    user_chip = ft.Row(
        [
            ft.CircleAvatar(
                foreground_image_src=profile_img if profile_img else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=10) if not profile_img else None,
                bgcolor=ft.Colors.BLUE_GREY_400,
                radius=10,
            ),
            ft.Text(data["username"], color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        ],
        spacing=6,
    )

    metas = ft.Column(
        [
            meta_row(ft.Icons.LOCATION_ON, data["ort"] or DEFAULT_PLACEHOLDER),
            user_chip,
            meta_row(ft.Icons.SCHEDULE, f"Erstellt am: {data['created_at']}"),
        ],
        spacing=4,
    )

    # Herz rechts neben Kontakt
    is_fav = item.get("is_favorite", False)
    favorite_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
        icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
        tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
        on_click=lambda e, it=item: on_favorite_click(it, e.control),
    )

    actions = ft.Row(
        [
            ft.FilledButton(
                "Kontakt",
                icon=ft.Icons.EMAIL,
                on_click=lambda e, it=item: on_contact_click(it) if on_contact_click else None,
            ),
            favorite_btn,
        ],
        spacing=4,
    )

    info_col = ft.Container(
        content=ft.Column(
            [title_text, badges, line1, metas, actions],
            spacing=8,
        ),
        col={"xs": 12, "md": 7},  # Volle Breite mobil, ~60% Desktop
    )

    # Responsives Layout: Mobil vertikal, Desktop horizontal
    card_inner = ft.ResponsiveRow(
        [image_col, info_col],
        spacing=12,
        run_spacing=10,
    )
    card = soft_card(card_inner, pad=12, elev=3)

    wrapper = ft.Container(
        content=card,
        animate_scale=300,
        scale=ft.Scale(1.0),
        on_click=lambda e, it=item: on_card_click(it) if on_card_click else None,
        col={"xs": 12, "md": 6},  # 2 Karten pro Zeile ab mittlerer Breite
    )

    def on_hover(e: ft.HoverEvent):
        wrapper.scale = ft.Scale(1.01) if e.data == "true" else ft.Scale(1.0)
        page.update()

    wrapper.on_hover = on_hover
    return wrapper


def show_detail_dialog(
    page: ft.Page,
    item: Dict[str, Any],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_favorite_click: Optional[Callable[[Dict[str, Any], ft.Control], None]] = None,
    profile_service=None,
    supabase=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Zeigt den Detail-Dialog für eine Meldung inkl. Kommentarbereich."""
    data = extract_item_data(item)

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    
    visual = (
        ft.Image(src=data["img_src"], height=DIALOG_IMAGE_HEIGHT, fit=ft.ImageFit.COVER)
        if data["img_src"]
        else image_placeholder(DIALOG_IMAGE_HEIGHT, icon_size=72, page=page)
    )

    # Favoriten-Button
    is_fav = item.get("is_favorite", False)
    favorite_btn = None
    if on_favorite_click:
        favorite_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
            tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
            on_click=lambda e, it=item: on_favorite_click(it, e.control),
        )

    title_row = ft.Container(height=0)

    # Eventdatum-Label je nach Meldungstyp
    typ_lower = (data["typ"] or "").lower().strip()
    if "fundtier" in typ_lower or "gefunden" in typ_lower or "zugelaufen" in typ_lower:
        event_label = "Gefunden am"
    elif "vermisst" in typ_lower or "entlaufen" in typ_lower:
        event_label = "Vermisst seit"
    elif "wiedervereint" in typ_lower:
        event_label = "Wiedervereint am"
    else:
        event_label = "Ereignis am"

    # Aktions-Zeile: Kontakt links, Herz daneben
    action_controls = []
    action_controls.append(
        ft.FilledButton(
            "Kontakt",
            icon=ft.Icons.EMAIL,
            on_click=lambda e, it=item: on_contact_click(it) if on_contact_click else None,
        )
    )
    if favorite_btn:
        action_controls.append(favorite_btn)

    actions_row = ft.Row(action_controls, spacing=4)

    # Links: Infos (Bild, Beschreibung, Metadaten) | Rechts: Kommentare
    post_id = str(item.get("id") or "")
    details_column = ft.Column(
        [
            ft.Column(
                [
                    ft.Container(visual, border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
                    ft.Container(height=2),
                    ft.Row(
                        [
                            ft.CircleAvatar(
                                foreground_image_src=data.get("user_profile_image") or None,
                                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=18)
                                if not data.get("user_profile_image")
                                else None,
                                bgcolor=ft.Colors.BLUE_GREY_400,
                                radius=18,
                            ),
                            ft.Text(data["username"], color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        data["title"],
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Text(
                        item.get("description") or "Keine Beschreibung.",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        width=480,
                        text_align=ft.TextAlign.JUSTIFY,
                    ),
                ],
                tight=True,
                spacing=2,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            ft.Divider(height=16, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
            ft.Column(
                [
                    meta_row(ft.Icons.LOCATION_ON, data["ort"] or DEFAULT_PLACEHOLDER),
                    meta_row(
                        ft.Icons.SCHEDULE,
                        f"{event_label}: {data['when']}" if data["when"] and data["when"] != "—" else DEFAULT_PLACEHOLDER,
                    ),
                    meta_row(ft.Icons.CALENDAR_TODAY, f"Erstellt am: {data['created_at']}"),
                ],
                tight=True,
                spacing=8,
            ),
        ],
        tight=True,
        spacing=8,
        width=480,
        expand=True,
    )

    if supabase and post_id and profile_service is not None:
        comment_section = CommentSection(
            page, post_id, supabase,
            profile_service=profile_service,
            on_login_required=on_comment_login_required,
        )
        # CommentSection transparent - Dialog-Hintergrund scheint durch
        right_column = ft.Container(
            content=comment_section,
            width=480,
            expand=True,
            padding=ft.padding.only(left=8),
        )
        dialog_content = ft.Row(
            [details_column, right_column],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    else:
        dialog_content = details_column

    actions_bar = ft.Row(
        [
            *action_controls,
            ft.Container(expand=True),
            ft.TextButton("Schließen", on_click=lambda _: page.close(dlg)),
        ],
        spacing=4,
    )

    dlg = ft.AlertDialog(
        title=title_row,
        title_padding=ft.padding.only(left=30, right=30, top=30, bottom=8),
        content=ft.Container(
            content=dialog_content,
            width=1080,
            height=600,
        ),
        content_padding=ft.padding.symmetric(horizontal=30),
        actions=[actions_bar],
        actions_padding=ft.padding.only(left=30, right=30, top=8, bottom=30),
    )
    page.open(dlg)
    # Kommentare nach Öffnen laden (Dialog muss bereits in der Page sein)
    if supabase and post_id and profile_service is not None:
        comment_section.load_comments()
        page.update()
