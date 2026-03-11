"""
Map-Service: Daten-Vorbereitung für Kartenvisualisierung.

Konvertiert Post-Daten in GeoJSON-Format und bereitet sie für Folium-Maps auf.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class MapDataService:
    """Service zur Vorbereitung von Post-Daten für Kartendarstellung."""

    @staticmethod
    def posts_to_geojson(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Konvertiert Posts mit Geokoordinaten zu GeoJSON-Features.

        Args:
            posts: Liste von Post-Dictionaries mit location_lat/location_lon

        Returns:
            Liste von GeoJSON-Feature-Dictionaries (nur Posts mit Koordinaten)
        """
        features = []
        for post in posts:
            lat = post.get("location_lat")
            lon = post.get("location_lon")

            # Posts ohne Koordinaten überspringen
            if lat is None or lon is None:
                logger.debug(f"Post {post.get('id')} hat keine Koordinaten, wird übersprungen")
                continue

            try:
                lat = float(lat)
                lon = float(lon)
            except (ValueError, TypeError):
                logger.warning(f"Ungültige Koordinaten für Post {post.get('id')}")
                continue

            # Erstes Bild extrahieren (wie in extract_item_data)
            post_images = post.get("post_image") or []
            first_image_url = post_images[0].get("url") if post_images else None
            
            # Status extrahieren
            post_status = post.get("post_status") or {}
            status_name = post_status.get("name", "") if isinstance(post_status, dict) else ""
            
            # Species extrahieren
            species = post.get("species") or {}
            species_name = species.get("name", "") if isinstance(species, dict) else ""
            species_id = species.get("id") if isinstance(species, dict) else post.get("species_id")

            # GeoJSON-Feature erstellen
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],  # GeoJSON: [lon, lat]!
                },
                "properties": {
                    "id": post.get("id"),
                    "headline": post.get("headline", ""),
                    "description": post.get("description", ""),
                    "location_text": post.get("location_text", ""),
                    "post_status_id": post_status.get("id") if isinstance(post_status, dict) else None,
                    "species_id": species_id,
                    "first_image_url": first_image_url,
                    "created_at": post.get("created_at"),
                    "user_id": post.get("user_id"),
                    "username": post.get("username", "Anonym"),
                    "user_profile_image": post.get("user_profile_image"),
                    "typ": "fund" if status_name == "Fundtier" else "vermisst",
                    "is_favorite": post.get("is_favorite", False),
                    "species_name": species_name,
                    "breed_id": post.get("breed_id"),
                    "sex_id": post.get("sex_id"),
                    "color_ids": post.get("color_ids", []),
                },
            }
            features.append(feature)

        logger.info(f"{len(features)} von {len(posts)} Posts haben Koordinaten")
        return features

    @staticmethod
    def get_map_bounds(posts: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """Berechnet die Bounding Box für alle Posts mit Koordinaten.

        Args:
            posts: Liste von Post-Dictionaries

        Returns:
            Dict mit min_lat, max_lat, min_lon, max_lon oder None
        """
        lats = []
        lons = []

        for post in posts:
            lat = post.get("location_lat")
            lon = post.get("location_lon")
            if lat is not None and lon is not None:
                try:
                    lats.append(float(lat))
                    lons.append(float(lon))
                except (ValueError, TypeError):
                    continue

        if not lats or not lons:
            return None

        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
        }

    @staticmethod
    def get_center_point(posts: List[Dict[str, Any]]) -> tuple[float, float]:
        """Berechnet den Mittelpunkt aller Posts.

        Args:
            posts: Liste von Post-Dictionaries

        Returns:
            Tuple (latitude, longitude), Standard: Deutschland-Mitte
        """
        bounds = MapDataService.get_map_bounds(posts)
        if bounds is None:
            # Deutschland Mittelpunkt als Fallback
            return (51.1657, 10.4515)

        center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
        center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2
        return (center_lat, center_lon)

    @staticmethod
    def get_post_by_id(posts: List[Dict[str, Any]], post_id: str) -> Optional[Dict[str, Any]]:
        """Findet einen Post anhand seiner ID.

        Args:
            posts: Liste von Post-Dictionaries
            post_id: Post-UUID

        Returns:
            Post-Dictionary oder None
        """
        for post in posts:
            if post.get("id") == post_id:
                return post
        return None

    @staticmethod
    def get_species_emoji(species_id: Optional[int]) -> str:
        """Gibt das passende Emoji für eine Tierart zurück.

        Args:
            species_id: ID der Tierart (1=Hund, 2=Katze, 3=Kleintier, etc.)

        Returns:
            Emoji-String
        """
        # Mapping basierend auf den üblichen IDs
        species_emojis = {
            1: "🐕",  # Hund
            2: "🐈",  # Katze
            3: "🐇",  # Kleintier (Kaninchen)
            4: "🦎",  # Reptil
            5: "🐦",  # Vogel
            6: "🐠",  # Fisch
        }
        return species_emojis.get(species_id, "🐾")  # Fallback: Pfote
