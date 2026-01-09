"""
Filter- und Sortier-Helper-Funktionen für Posts.

Diese Funktionen enthalten nur reine Python-Logik ohne Datenbank-Aufrufe.
"""

from __future__ import annotations

from typing import List, Dict, Any, Set
from datetime import datetime
from utils.logging_config import get_logger
from utils.constants import MAX_SEARCH_QUERY_LENGTH

logger = get_logger(__name__)


def filter_by_search(items: List[Dict[str, Any]], search_query: str) -> List[Dict[str, Any]]:
    """Filtert Einträge nach Suchbegriff (headline, description, location_text).

    Args:
        items: Liste von Post-Dictionaries
        search_query: Suchbegriff

    Returns:
        Gefilterte Liste von Posts
    """
    # Input validieren und sanitizen
    if search_query is None:
        return items
    
    if not isinstance(search_query, str):
        logger.warning(f"Ungültiger Suchbegriff-Typ: {type(search_query)}")
        return items
    
    # Sanitize: Whitespace normalisieren, max. MAX_SEARCH_QUERY_LENGTH Zeichen
    q = " ".join(search_query.split())[:MAX_SEARCH_QUERY_LENGTH].lower()
    
    if not q:
        return items
    
    def matches(it: dict) -> bool:
        h = (it.get("headline") or "").lower()
        d = (it.get("description") or "").lower()
        loc = (it.get("location_text") or "").lower()
        return q in h or q in d or q in loc
    
    return [it for it in items if matches(it)]


def sort_by_event_date(items: List[Dict[str, Any]], desc: bool = True) -> List[Dict[str, Any]]:
    """Sortiert Posts nach Event-Datum.
    
    Posts ohne event_date werden am Ende platziert.
    
    Args:
        items: Liste von Post-Dictionaries
        desc: True für absteigend (neueste zuerst), False für aufsteigend
    
    Returns:
        Sortierte Liste von Posts
    """
    def get_sort_key(item: Dict[str, Any]) -> tuple:
        """Gibt einen Sortier-Schlüssel zurück.
        
        Returns:
            Tuple (has_date, date_value) - Posts mit Datum kommen zuerst
        """
        event_date = item.get("event_date")
        if event_date:
            try:
                # Parse ISO-Format Datum
                if isinstance(event_date, str):
                    date_obj = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                else:
                    date_obj = event_date
                # has_date=True bedeutet, dass es vor Posts ohne Datum kommt
                return (True, date_obj)
            except (ValueError, AttributeError):
                pass
        # Posts ohne Datum bekommen (False, None) - kommen ans Ende
        return (False, None)
    
    # Sortiere: Posts mit event_date zuerst, dann nach Datum, dann Posts ohne Datum
    sorted_items = sorted(items, key=get_sort_key, reverse=desc)
    return sorted_items


def filter_by_colors(items: List[Dict[str, Any]], selected_color_ids: Set[int]) -> List[Dict[str, Any]]:
    """Filtert Einträge nach ausgewählten Farben.

    Args:
        items: Liste von Post-Dictionaries
        selected_color_ids: Set mit IDs der ausgewählten Farben

    Returns:
        Gefilterte Liste von Posts die ALLE ausgewählten Farben haben
    """
    if not selected_color_ids:
        return items

    def has_all_colors(it: dict) -> bool:
        pcs = it.get("post_color") or []
        ids = set()
        for pc in pcs:
            c = pc.get("color") if isinstance(pc, dict) else None
            if isinstance(c, dict) and c.get("id") is not None:
                ids.add(c["id"])
        # Prüfen ob ALLE ausgewählten Farben im Post vorhanden sind
        return selected_color_ids.issubset(ids)

    return [it for it in items if has_all_colors(it)]


def mark_favorites(items: List[Dict[str, Any]], favorite_ids: Set[int]) -> List[Dict[str, Any]]:
    """Markiert Einträge mit is_favorite Flag.

    Args:
        items: Liste von Post-Dictionaries
        favorite_ids: Set mit Post-IDs der Favoriten

    Returns:
        Liste mit Posts, jeweils mit is_favorite Flag
    """
    for it in items:
        it["is_favorite"] = it.get("id") in favorite_ids
    return items
