"""
Favoriten-Feature: UI und Logik für Favoriten-Verwaltung.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft

from utils.logging_config import get_logger
from services.posts import FavoritesService
from ui.components import show_success_dialog, show_error_dialog, show_login_required_snackbar

logger = get_logger(__name__)


def handle_toggle_favorite(
    favorites_service: FavoritesService,
    item: Dict[str, Any],
    icon_button: ft.IconButton,
    page: ft.Page,
    current_user_id: Optional[str],
    on_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie.
    
    Args:
        favorites_service: FavoritesService-Instanz
        item: Post-Dictionary
        icon_button: IconButton-Widget das aktualisiert werden soll
        page: Flet Page-Instanz
        current_user_id: Aktuelle User-ID (None wenn nicht eingeloggt)
        on_login_required: Optionaler Callback wenn Login erforderlich ist
    """
    if not current_user_id:
        if on_login_required:
            on_login_required()
        else:
            show_login_required_snackbar(
                page,
                "Bitte melden Sie sich an, um Meldungen zu favorisieren."
            )
        return

    post_id = item.get("id")
    if not post_id:
        return

    try:
        is_favorite = item.get("is_favorite", False)
        if is_favorite:
            success = favorites_service.remove_favorite(post_id)
            if success:
                item["is_favorite"] = False
                icon_button.icon = ft.Icons.FAVORITE_BORDER
                icon_button.icon_color = ft.Colors.GREY_600
                show_success_dialog(
                    page,
                    "Aus Favoriten entfernt",
                    "Die Meldung wurde aus Ihren Favoriten entfernt."
                )
        else:
            success = favorites_service.add_favorite(post_id)
            if success:
                item["is_favorite"] = True
                icon_button.icon = ft.Icons.FAVORITE
                icon_button.icon_color = ft.Colors.RED
                show_success_dialog(
                    page,
                    "Zu Favoriten hinzugefügt",
                    "Die Meldung wurde zu Ihren Favoriten hinzugefügt."
                )

        if success:
            page.update()

    except Exception as ex:
        logger.error(f"Fehler beim Aktualisieren der Favoriten (Post {post_id}): {ex}", exc_info=True)
        show_error_dialog(
            page,
            "Fehler",
            "Die Favoriten-Aktion konnte nicht durchgeführt werden."
        )
