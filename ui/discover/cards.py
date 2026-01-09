"""
Card-Komponenten für die Discover View.

Enthält Funktionen zum Erstellen von kleinen und großen Meldungskarten
sowie den Detail-Dialog.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft

from ui.theme import soft_card
from ui.constants import (
    CARD_IMAGE_HEIGHT, LIST_IMAGE_HEIGHT, DIALOG_IMAGE_HEIGHT,
    DEFAULT_PLACEHOLDER
)
from ui.helpers import extract_item_data
from ui.comment_section import CommentSection
from ui.components import (
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

    visual_content = (
        ft.Image(src=data["img_src"], height=CARD_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(CARD_IMAGE_HEIGHT, expand=True)
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
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
) -> ft.Control:
    """Erstellt eine große Listen-Karte für die Listen-Ansicht.
    
    Args:
        item: Post-Dictionary mit allen Daten
        page: Flet Page-Instanz
        on_favorite_click: Callback (item, control) für Favoriten-Toggle
        on_card_click: Callback (item) für Karten-Klick
        on_contact_click: Optionaler Callback (item) für Kontakt-Button
        supabase: Supabase-Client für Kommentare
    
    Returns:
        Container mit großer Karten-Komponente
    """
    data = extract_item_data(item)

    visual_content = (
        ft.Image(src=data["img_src"], height=LIST_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(LIST_IMAGE_HEIGHT, icon_size=64, expand=True)
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
            meta_row(ft.Icons.PERSON, data["username"]),
            meta_row(ft.Icons.CALENDAR_TODAY, f"Erstellt am: {data['created_at']}"),
        ],
        spacing=16,
        wrap=True,
    )

    # -----------------------------
    # Kommentare - erst bei Bedarf laden
    # -----------------------------
    post_id = str(item.get("id") or "")
    comment_section = None  # Wird erst beim Öffnen erstellt
    
    # Kommentar-Anzahl ermitteln
    comment_count = 0
    if supabase and post_id:
        try:
            response = supabase.table('comment') \
                .select('id', count='exact') \
                .eq('post_id', post_id) \
                .eq('is_deleted', False) \
                .execute()
            comment_count = response.count or 0
        except Exception as e:
            print(f"Fehler beim Laden der Kommentar-Anzahl: {e}")

    # Button-Text mit Anzahl
    comment_button_text = f"Kommentare ({comment_count})" if comment_count > 0 else "Kommentare"
    
    # Container für Kommentare (anfangs leer - kein Ladebalken!)
    comments_container = ft.Container(
        content=ft.Container(),  # Leerer Container statt ProgressRing
        height=400,
        visible=False,
        padding=ft.padding.only(top=8),
    )

    def toggle_comments(e):
        """Öffnet/Schließt die Kommentar-Sektion"""
        nonlocal comment_section
        
        comments_container.visible = not comments_container.visible
        
        # CommentSection erst beim ersten Öffnen erstellen
        if comments_container.visible:
            if comment_section is None and supabase and post_id:
                # Zeige kurz Ladeindikator
                comments_container.content = ft.Container(
                    content=ft.Column([
                        ft.ProgressRing(),
                        ft.Text("Lade Kommentare...", size=12, color=ft.Colors.GREY_600)
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10),
                    alignment=ft.alignment.center,
                    padding=20
                )
                page.update()
                
                # CommentSection erstellen
                comment_section = CommentSection(page, post_id, supabase)
                comments_container.content = comment_section
                comment_section.load_comments()
            elif comment_section:
                # Bereits existierende Section neu laden
                comment_section.load_comments()
        
        page.update()

    # -----------------------------
    # Aktionen (Kontakt + Kommentar-Button)
    # -----------------------------
    actions = ft.Row(
        [
            ft.FilledButton(
                "Kontakt",
                icon=ft.Icons.EMAIL,
                on_click=lambda e, it=item: on_contact_click(it) if on_contact_click else None,
            ),
            ft.OutlinedButton(
                comment_button_text,
                icon=ft.Icons.COMMENT,
                on_click=toggle_comments,
                disabled=(not supabase or not post_id),
            ),
        ],
        spacing=10,
    )

    card_inner = ft.Column([visual, header, line1, metas, actions, comments_container], spacing=10)
    card = soft_card(card_inner, pad=12, elev=3)

    wrapper = ft.Container(
        content=card,
        animate_scale=300,
        scale=ft.Scale(1.0),
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
    on_favorite_click: Optional[Callable[[Dict[str, Any], ft.Control], None]] = None
) -> None:
    """Zeigt den Detail-Dialog für eine Meldung.
    
    Args:
        page: Flet Page-Instanz
        item: Post-Dictionary mit allen Daten
        on_contact_click: Optionaler Callback (item) für Kontakt-Button
        on_favorite_click: Optionaler Callback (item, control) für Favoriten-Toggle
    """
    data = extract_item_data(item)

    visual = (
        ft.Image(src=data["img_src"], height=DIALOG_IMAGE_HEIGHT, fit=ft.ImageFit.COVER)
        if data["img_src"]
        else image_placeholder(DIALOG_IMAGE_HEIGHT, icon_size=72)
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

    # Titel mit Favoriten-Button
    title_row = ft.Row(
        [
            ft.Text(data["title"], expand=True),
            favorite_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    ) if favorite_btn else ft.Text(data["title"])

    dlg = ft.AlertDialog(
        title=title_row,
        content=ft.Column(
            [
                ft.Container(visual, border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
                ft.Container(height=8),
                ft.Text(item.get("description") or "Keine Beschreibung.", color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(height=8),
                meta_row(ft.Icons.LOCATION_ON, data["ort"] or DEFAULT_PLACEHOLDER),
                meta_row(ft.Icons.SCHEDULE, data["when"] or DEFAULT_PLACEHOLDER),
                meta_row(ft.Icons.PERSON, data["username"]),
                meta_row(ft.Icons.CALENDAR_TODAY, f"Erstellt am: {data['created_at']}"),
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
