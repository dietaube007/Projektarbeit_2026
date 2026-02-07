"""
Favoriten-Feature: UI und Logik für Favoriten-Verwaltung im Profilbereich.
"""

from __future__ import annotations

from typing import Callable, List, Optional
import flet as ft

from ui.shared_components import loading_indicator, show_confirm_dialog
from ..components.my_favorites_components import build_favorite_card
from utils.logging_config import get_logger

logger = get_logger(__name__)


# build_favorite_card wird aus components.my_favorites_components importiert


def render_favorites_list(
    favorites_list: ft.Column,
    favorites_items: List[dict],
    on_remove: Callable[[int], None],
    not_logged_in: bool = False,
):
    """Rendert die Favoriten-Liste in den Container.
    
    Args:
        favorites_list: Column-Container für die Liste
        favorites_items: Liste der Favoriten-Posts
        on_remove: Callback beim Entfernen
        not_logged_in: Ob der Benutzer nicht eingeloggt ist
    """
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
                    ft.Text("Klicken Sie auf das Herz-Symbol bei einer Meldung, um sie hier zu speichern.",
                           size=12, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        )
    else:
        for post in favorites_items:
            favorites_list.controls.append(build_favorite_card(post, on_remove))


async def load_favorites(
    favorites_list: ft.Column,
    favorites_items: List[dict],
    page: ft.Page,
    sb,
    on_favorites_changed: Optional[Callable] = None,
) -> List[dict]:
    """Lädt alle favorisierten Meldungen des aktuellen Benutzers.
    
    Args:
        favorites_list: Column-Container für die Liste
        favorites_items: Liste der Favoriten-Posts (wird aktualisiert)
        page: Flet Page-Instanz
        sb: Supabase Client
        on_favorites_changed: Optionaler Callback wenn Favoriten geändert wurden
    
    Returns:
        Liste der geladenen Favoriten
    """
    try:
        favorites_list.controls = [loading_indicator("Favoriten werden geladen...")]
        page.update()

        from services.account import ProfileService
        profile_service = ProfileService(sb)
        user_id = profile_service.get_user_id()
        
        if not user_id:
            favorites_items.clear()
            render_favorites_list(
                favorites_list,
                favorites_items,
                lambda pid: remove_favorite(
                    post_id=pid,
                    favorites_items=favorites_items,
                    favorites_list=favorites_list,
                    page=page,
                    sb=sb,
                    on_favorites_changed=on_favorites_changed,
                ),
                not_logged_in=True,
            )
            page.update()
            return favorites_items

        # FavoritesService nutzen
        from services.posts import FavoritesService
        favorites_service = FavoritesService(sb)
        favorites_items.clear()
        favorites_items.extend(favorites_service.get_favorites())
        render_favorites_list(
            favorites_list,
            favorites_items,
            lambda pid: remove_favorite(
                post_id=pid,
                favorites_items=favorites_items,
                favorites_list=favorites_list,
                page=page,
                sb=sb,
                on_favorites_changed=on_favorites_changed,
            ),
        )
        page.update()
        return favorites_items

    except Exception as e:
        logger.error(f"Fehler beim Laden der Favoriten: {e}", exc_info=True)
        favorites_items.clear()
        render_favorites_list(
            favorites_list,
            favorites_items,
            lambda pid: remove_favorite(
                post_id=pid,
                favorites_items=favorites_items,
                favorites_list=favorites_list,
                page=page,
                sb=sb,
                on_favorites_changed=on_favorites_changed,
            ),
        )
        page.update()
        return favorites_items


def remove_favorite(
    post_id: str,
    favorites_items: List[dict],
    favorites_list: ft.Column,
    page: ft.Page,
    sb,
    on_favorites_changed: Optional[Callable] = None,
) -> None:
    """Entfernt einen Post aus den Favoriten.
    
    Args:
        post_id: ID des Posts (UUID als String)
        favorites_items: Liste der Favoriten-Posts (wird aktualisiert)
        favorites_list: Column-Container für die Liste
        page: Flet Page-Instanz
        sb: Supabase Client
        on_favorites_changed: Optionaler Callback wenn Favoriten geändert wurden
    """
    def on_confirm() -> None:
        try:
            from services.posts import FavoritesService
            favorites_service = FavoritesService(sb)

            # Aus Datenbank löschen
            if favorites_service.remove_favorite(str(post_id)):
                # Lokal entfernen
                favorites_items[:] = [
                    p for p in favorites_items if p.get("id") != post_id
                ]
                render_favorites_list(
                    favorites_list,
                    favorites_items,
                    lambda pid: remove_favorite(
                        post_id=pid,
                        favorites_items=favorites_items,
                        favorites_list=favorites_list,
                        page=page,
                        sb=sb,
                        on_favorites_changed=on_favorites_changed,
                    ),
                )
                page.update()

                # Startseite informieren
                if on_favorites_changed:
                    on_favorites_changed()

        except Exception as e:
            logger.error(
                f"Fehler beim Entfernen aus Favoriten (Post {post_id}): {e}",
                exc_info=True,
            )

    show_confirm_dialog(
        page=page,
        title="Aus Favoriten entfernen?",
        message="Moechten Sie diese Meldung wirklich aus Ihren Favoriten entfernen?",
        confirm_text="Entfernen",
        on_confirm=on_confirm,
    )
