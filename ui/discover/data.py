"""
ui/discover/data.py
Datenladen und Filterlogik für die Discover-View.
"""

from __future__ import annotations

from typing import Optional, Dict, List, Set, Any
from utils.logging_config import get_logger
from ui.constants import MAX_SEARCH_QUERY_LENGTH

logger = get_logger(__name__)


def build_query(sb, filters: Dict[str, Any]):
    """Baut die Supabase-Abfrage mit den aktiven Filtern.

    Args:
        sb: Supabase Client-Instanz
        filters: Dictionary mit Filterwerten (typ, art, geschlecht, rasse)

    Returns:
        Supabase Query-Objekt mit angewendeten Filtern
    """
    query = (
        sb.table("post")
        .select(
            """
            id, headline, description, location_text, event_date, created_at, is_active,
            post_status(id, name),
            species(id, name),
            breed(id, name),
            sex(id, name),
            post_image(url),
            post_color(color(id, name))
            """
        )
        .order("created_at", desc=True)
    )
    
    # Filter: Kategorie (post_status) - mit Validierung
    filter_typ = filters.get("typ")
    if filter_typ and filter_typ != "alle":
        try:
            # Validiere dass es eine gültige Zahl ist
            typ_id = int(filter_typ)
            if typ_id > 0:  # Positive ID
                query = query.eq("post_status_id", typ_id)
        except (ValueError, TypeError):
            logger.warning(f"Ungültiger Filter-Typ: {filter_typ}")
    
    # Filter: Tierart (species) - mit Validierung
    filter_art = filters.get("art")
    if filter_art and filter_art != "alle":
        try:
            art_id = int(filter_art)
            if art_id > 0:
                query = query.eq("species_id", art_id)
        except (ValueError, TypeError):
            logger.warning(f"Ungültiger Filter-Art: {filter_art}")
    
    # Filter: Geschlecht - mit Validierung
    filter_geschlecht = filters.get("geschlecht")
    if filter_geschlecht and filter_geschlecht != "alle":
        if filter_geschlecht == "keine_angabe":
            query = query.is_("sex_id", "null")
        else:
            try:
                geschlecht_id = int(filter_geschlecht)
                if geschlecht_id > 0:
                    query = query.eq("sex_id", geschlecht_id)
            except (ValueError, TypeError):
                logger.warning(f"Ungültiger Filter-Geschlecht: {filter_geschlecht}")
    
    # Filter: Rasse - mit Validierung
    filter_rasse = filters.get("rasse")
    if filter_rasse and filter_rasse != "alle":
        try:
            rasse_id = int(filter_rasse)
            if rasse_id > 0:
                query = query.eq("breed_id", rasse_id)
        except (ValueError, TypeError):
            logger.warning(f"Ungültiger Filter-Rasse: {filter_rasse}")
    
    return query


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


def filter_by_colors(items: List[Dict[str, Any]], selected_color_ids: Set[int]) -> List[Dict[str, Any]]:
    """Filtert Einträge nach ausgewählten Farben.

    Args:
        items: Liste von Post-Dictionaries
        selected_color_ids: Set mit IDs der ausgewählten Farben

    Returns:
        Gefilterte Liste von Posts mit mindestens einer der Farben
    """
    if not selected_color_ids:
        return items
    
    def has_color(it: dict) -> bool:
        pcs = it.get("post_color") or []
        ids = set()
        for pc in pcs:
            c = pc.get("color") if isinstance(pc, dict) else None
            if isinstance(c, dict) and c.get("id") is not None:
                ids.add(c["id"])
        return bool(ids.intersection(selected_color_ids))
    
    return [it for it in items if has_color(it)]


def get_favorite_ids(sb, user_id: Optional[str]) -> Set[int]:
    """Holt die Favoriten-IDs eines Benutzers.

    Args:
        sb: Supabase Client-Instanz
        user_id: ID des Benutzers oder None

    Returns:
        Set mit Post-IDs der Favoriten, leeres Set wenn user_id None
    """
    if not user_id:
        return set()
    
    try:
        fav_res = (
            sb.table("favorite")
            .select("post_id")
            .eq("user_id", user_id)
            .execute()
        )
        return {row["post_id"] for row in (fav_res.data or []) if "post_id" in row}
    except Exception:
        return set()


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


async def load_filter_options(sb) -> Dict[str, List[Dict[str, Any]]]:
    """Lädt alle Filteroptionen aus der Datenbank.

    Args:
        sb: Supabase Client-Instanz

    Returns:
        Dictionary mit Filteroptionen (species, breeds, colors, post_status, sex)
    """
    options = {
        "species": [],
        "breeds": [],
        "colors": [],
        "post_status": [],
        "sex": [],
    }
    
    try:
        # Parallel laden wäre effizienter, aber für Demo reicht sequentiell
        species_res = sb.table("species").select("id, name").execute()
        options["species"] = species_res.data or []
        
        breed_res = sb.table("breed").select("id, name").execute()
        options["breeds"] = breed_res.data or []
        
        color_res = sb.table("color").select("id, name").execute()
        options["colors"] = color_res.data or []
        
        status_res = sb.table("post_status").select("id, name").execute()
        options["post_status"] = status_res.data or []
        
        sex_res = sb.table("sex").select("id, name").execute()
        options["sex"] = sex_res.data or []
        
    except Exception as ex:
        logger.error(f"Fehler beim Laden der Filteroptionen: {ex}", exc_info=True)
    
    return options


def toggle_favorite(sb, user_id: str, post_id: int, is_currently_favorite: bool) -> bool:
    """Schaltet den Favoriten-Status um.

    Args:
        sb: Supabase Client-Instanz
        user_id: ID des Benutzers
        post_id: ID des Posts
        is_currently_favorite: Aktueller Favoriten-Status

    Returns:
        Neuer Favoriten-Status (True/False)
    """
    try:
        if is_currently_favorite:
            # Favorit entfernen
            sb.table("favorite").delete().eq("user_id", user_id).eq("post_id", post_id).execute()
            return False
        else:
            # Favorit hinzufügen
            sb.table("favorite").insert({
                "user_id": user_id,
                "post_id": post_id
            }).execute()
            return True
    except Exception as ex:
        logger.error(f"Fehler beim Umschalten des Favoriten (User {user_id}, Post {post_id}): {ex}", exc_info=True)
        return is_currently_favorite
