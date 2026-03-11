"""
Map-Handler: Event-Handler für Karteninteraktionen.
"""

from __future__ import annotations

from typing import Callable, List, Dict, Any

from utils.logging_config import get_logger

logger = get_logger(__name__)


def handle_map_marker_click(
    post_id: str,
    posts: List[Dict[str, Any]],
    page=None,  # Optional für Kompatibilität
    show_detail_dialog: Callable[[Dict[str, Any]], None] = None,
    on_detail_click: Callable[[Dict[str, Any]], None] = None,  # Legacy-Parameter
) -> None:
    """Handler wenn User auf einen Marker klickt.

    Args:
        post_id: UUID des geklickten Posts
        posts: Liste aller Posts zum Suchen
        page: Optional Flet Page (für Kompatibilität)
        show_detail_dialog: Callback zur Detailansicht
        on_detail_click: Legacy-Callback (deprecated)
    """
    # Callback bestimmen (neue oder alte Variante)
    callback = show_detail_dialog or on_detail_click
    
    if not callback:
        logger.error("Kein Detail-Dialog-Callback übergeben")
        return
    
    # Post in der Liste finden
    for post in posts:
        if str(post.get("id")) == str(post_id):
            logger.info(f"Zeige Details für Post: {post.get('headline')}")
            callback(post)
            return

    logger.warning(f"Post mit ID {post_id} nicht gefunden")
