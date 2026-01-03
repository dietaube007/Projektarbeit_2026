"""
ui/discover/data.py
Datenladen und Filterlogik für die Discover-View.
"""

from typing import Optional


def build_query(sb, filters: dict):
    """Baut die Supabase-Abfrage mit den aktiven Filtern."""
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
    
    # Filter: Kategorie (post_status)
    filter_typ = filters.get("typ")
    if filter_typ and filter_typ != "alle":
        query = query.eq("post_status_id", int(filter_typ))
    
    # Filter: Tierart (species)
    filter_art = filters.get("art")
    if filter_art and filter_art != "alle":
        query = query.eq("species_id", int(filter_art))
    
    # Filter: Geschlecht
    filter_geschlecht = filters.get("geschlecht")
    if filter_geschlecht and filter_geschlecht != "alle":
        if filter_geschlecht == "keine_angabe":
            query = query.is_("sex_id", "null")
        else:
            query = query.eq("sex_id", int(filter_geschlecht))
    
    # Filter: Rasse
    filter_rasse = filters.get("rasse")
    if filter_rasse and filter_rasse != "alle":
        query = query.eq("breed_id", int(filter_rasse))
    
    return query


def filter_by_search(items: list[dict], search_query: str) -> list[dict]:
    """ Filtert Einträge nach Suchbegriff (headline, description, location_text."""
    q = (search_query or "").strip().lower()
    if not q:
        return items
    
    def matches(it: dict) -> bool:
        h = (it.get("headline") or "").lower()
        d = (it.get("description") or "").lower()
        loc = (it.get("location_text") or "").lower()
        return q in h or q in d or q in loc
    
    return [it for it in items if matches(it)]


def filter_by_colors(items: list[dict], selected_color_ids: set[int]) -> list[dict]:
    """Filtert Einträge nach ausgewählten Farben."""
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


def get_favorite_ids(sb, user_id: Optional[str]) -> set[int]:
    """Holt die Favoriten-IDs eines Benutzers."""
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


def mark_favorites(items: list[dict], favorite_ids: set[int]) -> list[dict]:
    """Markiert Einträge mit is_favorite Flag."""
    for it in items:
        it["is_favorite"] = it.get("id") in favorite_ids
    return items


async def load_filter_options(sb) -> dict:
    """Lädt alle Filteroptionen aus der Datenbank."""
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
        print(f"Fehler beim Laden der Filteroptionen: {ex}")
    
    return options


def toggle_favorite(sb, user_id: str, post_id: int, is_currently_favorite: bool) -> bool:
    """Schaltet den Favoriten-Status um."""
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
        print(f"Fehler beim Umschalten des Favoriten: {ex}")
        return is_currently_favorite
