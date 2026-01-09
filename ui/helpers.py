"""
Hilfsfunktionen für Datenverarbeitung und Formatierung.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, Dict, Any, List

from ui.constants import DATE_FORMAT


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
    when_raw = (item.get("event_date") or item.get("created_at") or "")[:10]
    when = format_date(when_raw)
    status = "Aktiv" if item.get("is_active") else "Inaktiv"

    # Benutzer-Informationen (aus separater Abfrage)
    username = item.get("user_display_name") or ""
    if not username:
        username = "Nutzer"

    # Erstellungsdatum (wann gepostet)
    created_at_raw = (item.get("created_at") or "")[:10]
    created_at = format_date(created_at_raw)

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
        "username": username,
        "created_at": created_at,
    }


def format_date(date_str: Optional[str], return_format: Optional[str] = None) -> str:
    """Formatiert ein Datum aus ISO-Format ins Anzeigeformat TT.MM.JJJJ.

    Args:
        date_str: Datumsstring im ISO-Format (YYYY-MM-DD)
        return_format: Optionales Datumsformat (Standard: DATE_FORMAT aus constants)

    Returns:
        Formatiertes Datum (TT.MM.JJJJ) oder "—" wenn leer
    """
    if not date_str or not date_str.strip():
        return "—"
    
    output_format = return_format or DATE_FORMAT
    
    try:
        # ISO-Format parsen (YYYY-MM-DD)
        date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
        # Formatieren als TT.MM.JJJJ
        return date_obj.strftime(output_format)
    except (ValueError, TypeError):
        # Fallback: Original zurückgeben wenn Parsing fehlschlägt
        return date_str[:10] if date_str else "—"


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


# ══════════════════════════════════════════════════════════════════════
# ZEIT- UND DATUMSFORMATIERUNG
# ══════════════════════════════════════════════════════════════════════

def format_time(timestamp: Optional[str]) -> str:
    """Formatiert Zeitstempel zu relativem, lesbarem Format.
    
    Args:
        timestamp: ISO-Format Zeitstempel (z.B. "2024-01-15T10:30:00Z")
    
    Returns:
        Formatierter Zeitstring (z.B. "vor 5 Min.", "Gestern", "15.01.2024")
        oder leerer String bei Fehler
    """
    if not timestamp:
        return ""
    
    try:
        # Supabase timestamps sind ISO format
        created = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
        diff = now - created
        
        # Zeitdifferenz berechnen
        if diff.days == 0:
            if diff.seconds < 60:
                return "Gerade eben"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"vor {minutes} Min."
            else:
                hours = diff.seconds // 3600
                return f"vor {hours} Std."
        elif diff.days == 1:
            return "Gestern"
        elif diff.days < 7:
            return f"vor {diff.days} Tagen"
        else:
            return created.strftime(DATE_FORMAT)
            
    except Exception:
        return ""


def parse_date(date_str: str) -> Optional[date]:
    """Parst ein Datum im Anzeigeformat (TT.MM.JJJJ).
    
    Args:
        date_str: Datumsstring im Anzeigeformat (TT.MM.JJJJ)
    
    Returns:
        date-Objekt oder None bei Fehler
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str.strip(), DATE_FORMAT).date()
    except ValueError:
        return None


# ══════════════════════════════════════════════════════════════════════
# DICTIONARY-ZUGRIFF
# ══════════════════════════════════════════════════════════════════════

def get_nested_id(data: Dict[str, Any], key: str) -> Optional[int]:
    """Extrahiert die ID aus einem verschachtelten Dict-Feld.
    
    Args:
        data: Quell-Dictionary
        key: Schlüssel für das verschachtelte Dictionary
    
    Returns:
        ID als Integer oder None wenn nicht gefunden
    """
    value = data.get(key)
    if isinstance(value, dict):
        id_value = value.get("id")
        if isinstance(id_value, int):
            return id_value
        elif isinstance(id_value, str):
            try:
                return int(id_value)
            except ValueError:
                return None
    return None
