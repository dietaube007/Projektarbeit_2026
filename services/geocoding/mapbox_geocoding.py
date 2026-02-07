"""Mapbox-Geocoding Hilfsfunktionen."""

from __future__ import annotations

import json
import os
import ssl
from typing import List, Dict, Any
from urllib.parse import quote
from urllib.request import urlopen

import certifi

from utils.logging_config import get_logger

logger = get_logger(__name__)


MAPBOX_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"


def geocode_suggestions(
    query: str,
    limit: int = 5,
    language: str = "de",
    country: str = "de",
) -> List[Dict[str, Any]]:
    """Liefert Ortsvorschlaege inkl. Koordinaten fuer einen Suchtext.

    Ergebnisse werden standardmaessig auf Deutschland begrenzt.

    Args:
        query: Suchtext (Ort, PLZ, Adresse)
        limit: Maximale Anzahl Vorschlaege (Standard: 5)
        language: Sprache der Ergebnisse (Standard: "de")
        country: ISO-3166-1 Laendercode zur Begrenzung (Standard: "de")

    Rueckgabe: Liste mit Schluesseln "text", "lat", "lon".
    """
    token = os.getenv("MAPBOX_TOKEN")
    if not token:
        logger.warning("MAPBOX_TOKEN fehlt. Geocoding wird uebersprungen.")
        return []

    q = (query or "").strip()
    if not q:
        return []

    try:
        url = (
            f"{MAPBOX_BASE_URL}/{quote(q)}.json"
            f"?access_token={token}"
            f"&autocomplete=true"
            f"&limit={limit}"
            f"&language={language}"
            f"&country={country}"
            f"&types=address,place,locality,postcode"
        )
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(url, timeout=10, context=ssl_context) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        features = payload.get("features", []) if isinstance(payload, dict) else []
        results: List[Dict[str, Any]] = []
        for feature in features:
            center = feature.get("center") or []
            if len(center) != 2:
                continue
            results.append({
                "text": feature.get("place_name") or feature.get("text") or "",
                "lon": center[0],
                "lat": center[1],
            })
        return results
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Fehler bei Mapbox-Geocoding: {exc}", exc_info=True)
        return []
