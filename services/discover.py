"""Service für die Discover-View: Post-Abfragen mit Filtern."""

from __future__ import annotations

from typing import Optional, Dict, List, Set, Any
from supabase import Client

from utils.logging_config import get_logger
from ui.constants import MAX_POSTS_LIMIT, MAX_SEARCH_QUERY_LENGTH
from ui.discover.data import (
    filter_by_search,
    filter_by_colors,
    sort_by_event_date,
    mark_favorites,
    enrich_posts_with_usernames,
)

logger = get_logger(__name__)


class DiscoverService:
    """Service für Post-Abfragen mit Filtern in der Discover-View."""

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb

    def _build_query(
        self,
        filters: Dict[str, Any],
        sort_option: str = "created_at_desc",
    ) -> Any:
        """Baut die Supabase-Abfrage mit den aktiven Filtern.

        Args:
            filters: Dictionary mit Filterwerten (typ, art, geschlecht, rasse)
            sort_option: Sortier-Option (z.B. "created_at_desc", "event_date_asc", "headline_asc")

        Returns:
            Supabase Query-Objekt mit angewendeten Filtern
        """
        # Basis-Select mit allen benötigten Relationen
        query = (
            self.sb.table("post")
            .select(
                """
                id, headline, description, location_text, event_date, created_at, is_active, user_id,
                post_status(id, name),
                species(id, name),
                breed(id, name),
                sex(id, name),
                post_image(url),
                post_color(color(id, name))
                """
            )
        )

        # Sortierung anwenden
        if sort_option == "created_at_desc":
            query = query.order("created_at", desc=True)
        elif sort_option == "created_at_asc":
            query = query.order("created_at", desc=False)
        elif sort_option in ("event_date_desc", "event_date_asc"):
            # Für Event-Datum Sortierung: Zuerst nach created_at laden, dann in Python sortieren
            query = query.order("created_at", desc=True)
        else:
            # Fallback: Neueste zuerst
            query = query.order("created_at", desc=True)

        # Filter: Kategorie (post_status)
        filter_typ = filters.get("typ")
        if filter_typ and filter_typ != "alle":
            try:
                typ_id = int(filter_typ)
                if typ_id > 0:
                    query = query.eq("post_status_id", typ_id)
            except (ValueError, TypeError):
                logger.warning(f"Ungültiger Filter-Typ: {filter_typ}")

        # Filter: Tierart (species)
        filter_art = filters.get("art")
        if filter_art and filter_art != "alle":
            try:
                art_id = int(filter_art)
                if art_id > 0:
                    query = query.eq("species_id", art_id)
            except (ValueError, TypeError):
                logger.warning(f"Ungültiger Filter-Art: {filter_art}")

        # Filter: Geschlecht
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

        # Filter: Rasse
        filter_rasse = filters.get("rasse")
        if filter_rasse and filter_rasse != "alle":
            if filter_rasse == "keine_angabe":
                query = query.is_("breed_id", "null")
            else:
                try:
                    rasse_id = int(filter_rasse)
                    if rasse_id > 0:
                        query = query.eq("breed_id", rasse_id)
                except (ValueError, TypeError):
                    logger.warning(f"Ungültiger Filter-Rasse: {filter_rasse}")

        return query

    def search_posts(
        self,
        filters: Dict[str, Any],
        search_query: Optional[str] = None,
        selected_colors: Optional[Set[int]] = None,
        sort_option: str = "created_at_desc",
        favorite_ids: Optional[Set[int]] = None,
        limit: int = MAX_POSTS_LIMIT,
    ) -> List[Dict[str, Any]]:
        """Sucht Posts mit Filtern, Suche, Farben und Sortierung.

        Args:
            filters: Dictionary mit Filterwerten (typ, art, geschlecht, rasse)
            search_query: Optionaler Suchbegriff
            selected_colors: Optional Set mit Farb-IDs
            sort_option: Sortier-Option
            favorite_ids: Optional Set mit Post-IDs der Favoriten (für Markierung)
            limit: Maximale Anzahl der Posts

        Returns:
            Liste von Post-Dictionaries mit is_favorite Flag
        """
        try:
            # Query bauen und ausführen
            query = self._build_query(filters, sort_option)
            result = query.limit(limit).execute()
            items = result.data or []

            # Suche (Python-Filter)
            if search_query:
                items = filter_by_search(items, search_query)

            # Farben (Python-Filter)
            if selected_colors:
                items = filter_by_colors(items, selected_colors)

            # Event-Datum Sortierung in Python (falls gewählt)
            if sort_option == "event_date_desc":
                items = sort_by_event_date(items, desc=True)
            elif sort_option == "event_date_asc":
                items = sort_by_event_date(items, desc=False)

            # Favoritenstatus markieren
            if favorite_ids is not None:
                items = mark_favorites(items, favorite_ids)

            # Benutzernamen anreichern
            items = enrich_posts_with_usernames(self.sb, items)

            return items

        except Exception as ex:
            logger.error(f"Fehler beim Suchen von Posts: {ex}", exc_info=True)
            return []

