"""
ui/profile/favorites.py
Favoriten-Tab Logik und Karten für die Profil-Ansicht.
"""

from typing import Callable, List, Optional
import flet as ft

from ui.theme import soft_card
from ui.constants import STATUS_COLORS, SPECIES_COLORS
from ui.components import loading_indicator
from ui.helpers import extract_item_data
from utils.logging_config import get_logger

logger = get_logger(__name__)


def build_favorite_card(
    post: dict,
    on_remove: Callable[[int], None],
) -> ft.Control:
    """Erstellt eine Karte für eine favorisierte Meldung."""
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
        logger.error(f"Fehler beim Laden der Favoriten (User {user_id}): {e}", exc_info=True)
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
        logger.error(f"Fehler beim Entfernen aus Favoriten (User {user_id}, Post {post_id}): {e}", exc_info=True)
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
                    ft.Text("Sie haben noch keine Meldungen favorisiert.", color=ft.Colors.GREY_600),
                    ft.Text("Klicken Sie auf ❤️ bei einer Meldung, um sie hier zu speichern.",
                           size=12, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        )
    else:
        for post in favorites_items:
            favorites_list.controls.append(build_favorite_card(post, on_remove))


class ProfileFavoritesMixin:
    """Mixin-Klasse für Favoriten-Funktionalität in ProfileView.
    
    Enthält Methoden für:
    - Favoriten laden
    - Favorit entfernen
    """
    
    async def _load_favorites(self):
        """Lädt alle favorisierten Meldungen des aktuellen Benutzers."""
        try:
            self.favorites_list.controls = [loading_indicator("Favoriten werden geladen...")]
            self.page.update()

            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                self.favorites_items = []
                render_favorites_list(
                    self.favorites_list,
                    self.favorites_items,
                    self._remove_favorite,
                    not_logged_in=True,
                )
                self.page.update()
                return

            user_id = user_resp.user.id
            self.favorites_items = await load_favorites(self.sb, user_id)
            render_favorites_list(
                self.favorites_list,
                self.favorites_items,
                self._remove_favorite,
            )
            self.page.update()

        except Exception as e:
            logger.error(f"Fehler beim Laden der Favoriten: {e}", exc_info=True)
            self.favorites_items = []
            render_favorites_list(
                self.favorites_list,
                self.favorites_items,
                self._remove_favorite,
            )
            self.page.update()

    def _remove_favorite(self, post_id: int):
        """Entfernt einen Post aus den Favoriten."""
        try:
            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                return

            user_id = user_resp.user.id

            # Aus Datenbank löschen
            if remove_favorite(self.sb, user_id, post_id):
                # Lokal entfernen
                self.favorites_items = [
                    p for p in self.favorites_items if p.get("id") != post_id
                ]
                render_favorites_list(
                    self.favorites_list,
                    self.favorites_items,
                    self._remove_favorite,
                )
                self.page.update()

                # Startseite informieren
                if self.on_favorites_changed:
                    self.on_favorites_changed()

        except Exception as e:
            logger.error(f"Fehler beim Entfernen aus Favoriten (Post {post_id}): {e}", exc_info=True)
