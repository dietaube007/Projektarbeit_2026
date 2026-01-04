"""
ui/profile/my_posts.py
Meine Meldungen - Anzeige und Verwaltung eigener Tier-Meldungen.
"""

from typing import Callable, List, Optional
import flet as ft

from ui.theme import soft_card
from ui.constants import STATUS_COLORS, SPECIES_COLORS, PRIMARY_COLOR
from services.posts import PostService
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _show_post_details(page: ft.Page, post: dict) -> None:
    """Zeigt die Details einer Meldung in einem Dialog an."""
    title = post.get("headline") or "Ohne Namen"
    description = post.get("description") or "Keine Beschreibung vorhanden."
    
    post_status = post.get("post_status") or {}
    typ = post_status.get("name", "Unbekannt") if isinstance(post_status, dict) else "Unbekannt"
    
    species = post.get("species") or {}
    art = species.get("name", "Unbekannt") if isinstance(species, dict) else "Unbekannt"
    
    breed = post.get("breed") or {}
    rasse = breed.get("name", "—") if isinstance(breed, dict) else "—"
    
    sex = post.get("sex") or {}
    geschlecht = sex.get("name", "—") if isinstance(sex, dict) else "—"
    
    post_colors = post.get("post_color") or []
    farben_namen = [
        pc.get("color", {}).get("name", "")
        for pc in post_colors
        if pc.get("color")
    ]
    farbe = ", ".join(farben_namen) if farben_namen else "—"
    
    ort = post.get("location_text") or "—"
    event_date = (post.get("event_date") or "")[:10]
    created_at = (post.get("created_at") or "")[:10]
    is_active = post.get("is_active", True)
    
    # Bild
    post_images = post.get("post_image") or []
    img_src = post_images[0].get("url") if post_images else None
    
    if img_src:
        visual = ft.Container(
            content=ft.Image(
                src=img_src,
                height=200,
                fit=ft.ImageFit.COVER,
                gapless_playback=True,
            ),
            border_radius=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
    else:
        visual = ft.Container(
            height=200,
            bgcolor=ft.Colors.GREY_100,
            alignment=ft.alignment.center,
            border_radius=12,
            content=ft.Icon(ft.Icons.PETS, size=64, color=ft.Colors.GREY_400),
        )
    
    def detail_row(icon: str, label: str, value: str) -> ft.Control:
        return ft.Row(
            [
                ft.Icon(icon, size=18, color=ft.Colors.GREY_600),
                ft.Text(label, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                ft.Text(value, size=13, color=ft.Colors.GREY_800, expand=True),
            ],
            spacing=8,
        )
    
    def close_dialog(e):
        page.close(dlg)
    
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, size=18, weight=ft.FontWeight.W_600),
        content=ft.Container(
            content=ft.Column(
                [
                    visual,
                    ft.Container(height=8),
                    ft.Text(
                        "Beschreibung",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.GREY_800,
                    ),
                    ft.Text(
                        description,
                        size=13,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(height=16, color=ft.Colors.GREY_200),
                    detail_row(ft.Icons.CATEGORY, "Typ:", typ),
                    detail_row(ft.Icons.PETS, "Tierart:", art),
                    detail_row(ft.Icons.LABEL, "Rasse:", rasse),
                    detail_row(
                        ft.Icons.MALE if geschlecht.lower() == "männlich" 
                        else ft.Icons.FEMALE if geschlecht.lower() == "weiblich"
                        else ft.Icons.QUESTION_MARK,
                        "Geschlecht:", 
                        geschlecht,
                    ),
                    detail_row(ft.Icons.PALETTE, "Farbe:", farbe),
                    detail_row(ft.Icons.LOCATION_ON, "Ort:", ort),
                    detail_row(ft.Icons.EVENT, "Datum:", event_date if event_date else "—"),
                    ft.Divider(height=8, color=ft.Colors.GREY_200),
                    ft.Row(
                        [
                            ft.Text(
                                f"Erstellt am {created_at}" if created_at else "",
                                size=11,
                                color=ft.Colors.GREY_500,
                                italic=True,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "Aktiv" if is_active else "Inaktiv",
                                    size=10,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.WHITE,
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                border_radius=10,
                                bgcolor=ft.Colors.GREEN_600 if is_active else ft.Colors.GREY_500,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=350,
            height=500,
        ),
        actions=[
            ft.TextButton("Schließen", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.open(dlg)


def build_my_post_card(
    post: dict,
    page: ft.Page,
    on_edit: Optional[Callable[[dict], None]] = None,
    on_delete: Optional[Callable[[int], None]] = None,
) -> ft.Control:
    """Erstellt eine kompakte Karte für eine eigene Meldung."""
    # Daten extrahieren
    post_id = post.get("id")
    title = post.get("headline") or "Ohne Namen"
    
    post_status = post.get("post_status") or {}
    typ = post_status.get("name", "Unbekannt") if isinstance(post_status, dict) else "Unbekannt"
    typ_lower = typ.lower()
    
    species = post.get("species") or {}
    art = species.get("name", "Unbekannt") if isinstance(species, dict) else "Unbekannt"
    art_lower = art.lower()
    
    ort = post.get("location_text") or "—"
    event_date = (post.get("event_date") or "")[:10]
    is_active = post.get("is_active", True)
    
    # Bild (kleines Thumbnail)
    post_images = post.get("post_image") or []
    img_src = post_images[0].get("url") if post_images else None
    
    if img_src:
        thumbnail = ft.Container(
            content=ft.Image(
                src=img_src,
                width=70,
                height=70,
                fit=ft.ImageFit.COVER,
                gapless_playback=True,
            ),
            border_radius=10,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_200,
        )
    else:
        thumbnail = ft.Container(
            width=70,
            height=70,
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.PETS, size=32, color=ft.Colors.GREY_400),
        )
    
    # Badges
    status_color = STATUS_COLORS.get(typ_lower, ft.Colors.GREY_300)
    species_color = SPECIES_COLORS.get(art_lower, ft.Colors.GREY_300)
    
    def badge(label: str, color: str) -> ft.Control:
        return ft.Container(
            content=ft.Text(label, size=10, weight=ft.FontWeight.W_600),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=12,
            bgcolor=color,
        )
    
    active_badge = ft.Container(
        content=ft.Text(
            "Aktiv" if is_active else "Inaktiv",
            size=9,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.WHITE,
        ),
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
        border_radius=10,
        bgcolor=ft.Colors.GREEN_600 if is_active else ft.Colors.GREY_500,
    )
    
    # Info-Spalte
    info_col = ft.Column(
        [
            ft.Text(
                title,
                size=15,
                weight=ft.FontWeight.W_600,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Row(
                [badge(typ, status_color), badge(art, species_color), active_badge],
                spacing=4,
            ),
            ft.Row(
                [
                    ft.Icon(ft.Icons.LOCATION_ON, size=12, color=ft.Colors.GREY_500),
                    ft.Text(ort, size=11, color=ft.Colors.GREY_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text("•", size=11, color=ft.Colors.GREY_400),
                    ft.Icon(ft.Icons.EVENT, size=12, color=ft.Colors.GREY_500),
                    ft.Text(event_date if event_date else "—", size=11, color=ft.Colors.GREY_600),
                ],
                spacing=4,
            ),
        ],
        spacing=4,
        expand=True,
    )
    
    # Aktionen
    actions = ft.Column(
        [
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=20,
                icon_color=PRIMARY_COLOR,
                tooltip="Bearbeiten",
                on_click=lambda e, p=post: on_edit(p) if on_edit else None,
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=20,
                icon_color=ft.Colors.RED_600,
                tooltip="Löschen",
                on_click=lambda e, pid=post_id: on_delete(pid) if on_delete else None,
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Karten-Inhalt
    card_content = ft.Row(
        [thumbnail, info_col, actions],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # Klickbare Karte für Details
    def show_details(e):
        _show_post_details(page, post)
    
    clickable_card = ft.Container(
        content=card_content,
        padding=12,
        border_radius=14,
        bgcolor=ft.Colors.WHITE,
        ink=True,
        on_click=show_details,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
    )
    
    return clickable_card


async def load_my_posts(sb, user_id: str) -> List[dict]:
    """Lädt alle Meldungen eines Benutzers."""
    try:
        res = (
            sb.table("post")
            .select(
                """
                id,
                headline,
                description,
                location_text,
                event_date,
                created_at,
                is_active,
                post_status(id, name),
                species(id, name),
                breed(id, name),
                sex(id, name),
                post_image(url),
                post_color(color(id, name))
                """
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Fehler beim Laden der eigenen Meldungen (User {user_id}): {e}", exc_info=True)
        return []


def delete_post(sb, post_id: int) -> bool:
    """Löscht einen Post und alle verknüpften Daten inkl. Storage-Bilder.
    
    Diese Funktion verwendet PostService.delete() für konsistente Löschlogik.
    
    Args:
        sb: Supabase Client-Instanz
        post_id: ID des zu löschenden Posts (int wird zu str konvertiert)
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # PostService verwendet str für post_id, daher konvertieren
        post_service = PostService(sb)
        return post_service.delete(str(post_id))
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Posts {post_id}: {e}", exc_info=True)
        return False


def render_my_posts_list(
    posts_list: ft.Column,
    posts_items: List[dict],
    page: ft.Page,
    on_edit: Optional[Callable[[dict], None]] = None,
    on_delete: Optional[Callable[[int], None]] = None,
    not_logged_in: bool = False,
):
    """Rendert die Liste der eigenen Meldungen."""
    posts_list.controls.clear()
    
    if not_logged_in:
        posts_list.controls.append(
            ft.Text("Bitte einloggen um deine Meldungen zu sehen.", color=ft.Colors.GREY_600)
        )
    elif not posts_items:
        posts_list.controls.append(
            ft.Column(
                [
                    ft.Icon(ft.Icons.ARTICLE_OUTLINED, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Du hast noch keine Meldungen erstellt.", color=ft.Colors.GREY_600),
                    ft.Text(
                        "Erstelle eine Meldung über den 'Melden'-Tab.",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        )
    else:
        for post in posts_items:
            posts_list.controls.append(
                build_my_post_card(post, page=page, on_edit=on_edit, on_delete=on_delete)
            )
