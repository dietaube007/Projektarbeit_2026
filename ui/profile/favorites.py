"""
ui/profile/favorites.py
Favoriten-Tab Logik und Karten für die Profil-Ansicht.
"""

from typing import Callable, List, Optional
import flet as ft

from ui.theme import soft_card


def build_favorite_card(
    post: dict,
    on_remove: Callable[[int], None],
) -> ft.Control:
    """Erstellt eine Karte für eine favorisierte Meldung."""
    # Daten extrahieren
    post_id = post.get("id")
    title = post.get("headline") or "Ohne Namen"
    
    post_status = post.get("post_status") or {}
    typ = post_status.get("name", "Unbekannt") if isinstance(post_status, dict) else "Unbekannt"
    
    species = post.get("species") or {}
    art = species.get("name", "Unbekannt") if isinstance(species, dict) else "Unbekannt"
    
    breed = post.get("breed") or {}
    rasse = breed.get("name", "Mischling") if isinstance(breed, dict) else "Unbekannt"
    
    post_colors = post.get("post_color") or []
    farben_namen = [
        pc.get("color", {}).get("name", "")
        for pc in post_colors
        if pc.get("color")
    ]
    farbe = ", ".join(farben_namen) if farben_namen else ""
    
    ort = post.get("location_text") or ""
    when = (post.get("event_date") or post.get("created_at") or "")[:10]
    status = "Aktiv" if post.get("is_active") else "Inaktiv"
    
    # Bild
    post_images = post.get("post_image") or []
    img_src = post_images[0].get("url") if post_images else None
    
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
    
    badges = ft.Row(
        [
            badge(typ, "#C5CAE9"),
            badge(art, "#B2DFDB"),
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


async def load_favorites(sb, user_id: str) -> List[dict]:
    """Lädt alle favorisierten Meldungen eines Benutzers."""
    try:
        # 1) Favoriten-Einträge lesen
        fav_res = (
            sb.table("favorite")
            .select("post_id")
            .eq("user_id", user_id)
            .execute()
        )
        fav_rows = fav_res.data or []
        
        post_ids = [row["post_id"] for row in fav_rows if row.get("post_id")]
        
        if not post_ids:
            return []
        
        # 2) Dazu passende Posts laden
        posts_res = (
            sb.table("post")
            .select(
                """
                id,
                headline,
                location_text,
                event_date,
                created_at,
                is_active,
                post_status(id, name),
                species(id, name),
                breed(id, name),
                post_image(url),
                post_color(color(id, name))
                """
            )
            .in_("id", post_ids)
            .order("created_at", desc=True)
            .execute()
        )
        
        return posts_res.data or []
        
    except Exception as e:
        print(f"Fehler beim Laden der Favoriten: {e}")
        return []


def remove_favorite(sb, user_id: str, post_id: int) -> bool:
    """Entfernt einen Post aus den Favoriten."""
    try:
        (
            sb.table("favorite")
            .delete()
            .eq("user_id", user_id)
            .eq("post_id", post_id)
            .execute()
        )
        return True
    except Exception as e:
        print(f"Fehler beim Entfernen aus Favoriten: {e}")
        return False


def render_favorites_list(
    favorites_list: ft.Column,
    favorites_items: List[dict],
    on_remove: Callable[[int], None],
    not_logged_in: bool = False,
):
    """Rendert die Favoriten-Liste in den Container."""
    favorites_list.controls.clear()
    
    if not_logged_in:
        favorites_list.controls.append(
            ft.Text("Bitte einloggen um Favoriten zu sehen.", color=ft.Colors.GREY_600)
        )
    elif not favorites_items:
        favorites_list.controls.append(
            ft.Column(
                [
                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Du hast noch keine Meldungen favorisiert.", color=ft.Colors.GREY_600),
                    ft.Text("Klicke auf ❤️ bei einer Meldung, um sie hier zu speichern.", 
                           size=12, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        )
    else:
        for post in favorites_items:
            favorites_list.controls.append(build_favorite_card(post, on_remove))
