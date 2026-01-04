"""
Hilfsfunktionen für Datenverarbeitung und Formatierung.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List


def extract_item_data(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extrahiert und formatiert Daten aus einem Post-Item.

    Args:
        item: Post-Dictionary mit Rohdaten aus der Datenbank

    Returns:
        Dictionary mit formatierten Anzeigewerten
    """
    post_images = item.get("post_image") or []
    img_src = post_images[0].get("url") if post_images else None

    title = item.get("headline") or "Ohne Namen"

    post_status = item.get("post_status") or {}
    typ = post_status.get("name", "") if isinstance(post_status, dict) else ""

    species = item.get("species") or {}
    art = species.get("name", "") if isinstance(species, dict) else ""

    breed = item.get("breed") or {}
    rasse = breed.get("name", "Mischling") if isinstance(breed, dict) else "Unbekannt"

    post_colors = item.get("post_color") or []
    farben_namen = [
        pc.get("color", {}).get("name", "")
        for pc in post_colors
        if isinstance(pc, dict) and pc.get("color")
    ]
    farbe = ", ".join([x for x in farben_namen if x]) if farben_namen else ""

    ort = item.get("location_text") or ""
    when = (item.get("event_date") or item.get("created_at") or "")[:10]
    status = "Aktiv" if item.get("is_active") else "Inaktiv"

    return {
        "img_src": img_src,
        "title": title,
        "typ": typ,
        "art": art,
        "rasse": rasse,
        "farbe": farbe,
        "ort": ort,
        "when": when,
        "status": status,
    }


def format_date(date_str: Optional[str]) -> str:
    """Formatiert ein Datum aus ISO-Format.

    Args:
        date_str: Datumsstring im ISO-Format (YYYY-MM-DD)

    Returns:
        Formatiertes Datum (YYYY-MM-DD) oder "—" wenn leer
    """
    if not date_str:
        return "—"
    return date_str[:10]


def truncate_text(text: str, max_length: int = 100) -> str:
    """Kürzt Text auf maximale Länge.

    Args:
        text: Zu kürzender Text
        max_length: Maximale Länge (Standard: 100)

    Returns:
        Gekürzter Text mit "..." oder Original wenn kürzer
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_color_names(post_colors: List[Dict[str, Any]]) -> str:
    """Extrahiert Farbnamen aus post_color Liste.

    Args:
        post_colors: Liste von post_color Dictionaries

    Returns:
        Komma-separierte Farbnamen oder leerer String
    """
    if not post_colors:
        return ""

    farben_namen = [
        pc.get("color", {}).get("name", "")
        for pc in post_colors
        if isinstance(pc, dict) and pc.get("color")
    ]
    return ", ".join([x for x in farben_namen if x])


def get_nested_value(data: Dict[str, Any], *keys, default: str = "") -> str:
    """Holt verschachtelte Werte sicher aus einem Dictionary.

    Args:
        data: Quell-Dictionary
        *keys: Verschachtelte Schlüssel (z.B. "species", "name")
        default: Standardwert bei Fehler

    Returns:
        Gefundener Wert oder default
    """
    current: Any = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return str(current) if current else default
