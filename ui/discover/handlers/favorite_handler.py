"""
Favorite-Handler: UI-Handler für Favoriten-Verwaltung.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft

from utils.logging_config import get_logger
from services.posts import FavoritesService
from ui.shared_components import show_error_dialog

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
            return
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
        else:
            success = favorites_service.add_favorite(post_id)
            if success:
                item["is_favorite"] = True
                icon_button.icon = ft.Icons.FAVORITE
                icon_button.icon_color = ft.Colors.RED

        if success:
            page.update()

    except Exception as ex:
        logger.error(f"Fehler beim Aktualisieren der Favoriten (Post {post_id}): {ex}", exc_info=True)
        show_error_dialog(
            page,
            "Fehler",
            "Die Favoriten-Aktion konnte nicht durchgeführt werden."
        )


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler 
# ─────────────────────────────────────────────────────────────

def handle_view_toggle_favorite(
    favorites_service: FavoritesService,
    item: Dict[str, Any],
    icon_button: ft.IconButton,
    page: ft.Page,
    current_user_id: Optional[str],
    on_login_required: Optional[Callable[[], None]] = None,
    refresh_user_callback: Optional[Callable[[], str]] = None,
) -> None:
    """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie (View-Wrapper).
    
    Args:
        favorites_service: FavoritesService-Instanz
        item: Post-Dictionary
        icon_button: IconButton-Widget das aktualisiert werden soll
        page: Flet Page-Instanz
        current_user_id: Aktuelle User-ID (None wenn nicht eingeloggt)
        on_login_required: Optionaler Callback wenn Login erforderlich ist
        refresh_user_callback: Optionaler Callback zum Aktualisieren der User-ID (gibt neue ID zurück)
    """
    # User-ID aktualisieren falls Callback vorhanden
    updated_user_id = current_user_id
    if refresh_user_callback:
        updated_user_id = refresh_user_callback()
    
    handle_toggle_favorite(
        favorites_service=favorites_service,
        item=item,
        icon_button=icon_button,
        page=page,
        current_user_id=updated_user_id,
        on_login_required=on_login_required,
    )
