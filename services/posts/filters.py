"""
Filter- und Sortier-Helper-Funktionen für Posts.

Diese Funktionen enthalten nur reine Python-Logik ohne Datenbank-Aufrufe.
"""

from __future__ import annotations

import math
import re
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from utils.logging_config import get_logger
from utils.constants import MAX_SEARCH_QUERY_LENGTH

logger = get_logger(__name__)


def _extract_city_name(location_text: str) -> str:
    """Extrahiert den Stadtnamen aus einem Mapbox-Ortstext.

    Mapbox liefert z.B. "Fuerth, Bayern, Deutschland" oder
    "90762 Fuerth, Deutschland". Der Stadtname wird extrahiert.

    Args:
        location_text: Vollstaendiger Ortstext von Mapbox

    Returns:
        Extrahierter Stadtname (lowercase), ohne PLZ / Land / Bundesland
    """
    if not location_text:
        return ""
    # Teile durch Komma trennen
    parts = [p.strip() for p in location_text.split(",")]
    # Ersten Teil nehmen (ist normalerweise Stadt oder PLZ+Stadt)
    first = parts[0]
    # PLZ entfernen (z.B. "90762 Fürth" -> "Fürth")
    words = [w for w in first.split() if not w.isdigit()]
    return " ".join(words).lower().strip()


def filter_by_location_text(
    items: List[Dict[str, Any]],
    location_text: str,
) -> List[Dict[str, Any]]:
    """Filtert Posts nach Stadtname im location_text.

    Extrahiert den Stadtnamen aus dem Mapbox-Ortstext und prueft,
    ob er im location_text der Posts vorkommt.

    Args:
        items: Liste von Post-Dictionaries
        location_text: Ausgewaehlter Ortstext (z.B. "Fuerth, Bayern, Deutschland")

    Returns:
        Posts deren location_text den Stadtnamen enthaelt
    """
    city = _extract_city_name(location_text)
    if not city:
        return items

    # Regex mit Wortgrenzen, damit "fürth" nicht "fürtherstraße" matcht
    pattern = re.compile(r"\b" + re.escape(city) + r"\b", re.IGNORECASE)

    def matches(it: dict) -> bool:
        loc = it.get("location_text") or ""
        return bool(pattern.search(loc))

    return [it for it in items if matches(it)]


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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet die Distanz in Kilometern zwischen zwei Koordinaten (Haversine).

    Args:
        lat1: Breitengrad Punkt 1
        lon1: Laengengrad Punkt 1
        lat2: Breitengrad Punkt 2
        lon2: Laengengrad Punkt 2

    Returns:
        Distanz in Kilometern
    """
    R = 6_371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def filter_by_location(
    items: List[Dict[str, Any]],
    center_lat: float,
    center_lon: float,
    radius_km: float,
) -> List[Dict[str, Any]]:
    """Filtert Posts nach Umkreis (Haversine-Formel).

    Posts innerhalb des Radius kommen zuerst (sortiert nach Entfernung).
    Posts ohne Koordinaten werden am Ende angehaengt (nicht ausgeschlossen),
    damit keine Meldungen verloren gehen.

    Args:
        items: Liste von Post-Dictionaries
        center_lat: Breitengrad des Suchzentrums
        center_lon: Laengengrad des Suchzentrums
        radius_km: Umkreis in Kilometern

    Returns:
        Posts innerhalb des Umkreises (sortiert nach Entfernung),
        gefolgt von Posts ohne Koordinaten.
    """
    in_radius: List[Dict[str, Any]] = []

    for item in items:
        lat = item.get("location_lat")
        lon = item.get("location_lon")
        if lat is None or lon is None:
            continue
        try:
            dist = _haversine_km(center_lat, center_lon, float(lat), float(lon))
        except (ValueError, TypeError):
            continue
        if dist <= radius_km:
            item["_distance_km"] = round(dist, 1)
            in_radius.append(item)

    return in_radius


def enrich_with_distance(
    items: List[Dict[str, Any]],
    center_lat: float,
    center_lon: float,
) -> List[Dict[str, Any]]:
    """Berechnet die Entfernung jedes Posts zum Suchzentrum und speichert sie als _distance_km.

    Posts ohne Koordinaten erhalten _distance_km = 9999 (werden hinten sortiert).

    Args:
        items: Liste von Post-Dictionaries
        center_lat: Breitengrad des Suchzentrums
        center_lon: Laengengrad des Suchzentrums

    Returns:
        Dieselbe Liste mit _distance_km angereichert
    """
    for item in items:
        lat = item.get("location_lat")
        lon = item.get("location_lon")
        if lat is None or lon is None:
            item["_distance_km"] = 9999
            continue
        try:
            dist = _haversine_km(center_lat, center_lon, float(lat), float(lon))
            item["_distance_km"] = round(dist, 1)
        except (ValueError, TypeError):
            item["_distance_km"] = 9999
    return items


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
