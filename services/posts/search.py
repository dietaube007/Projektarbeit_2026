"""Service für Post-Suche mit Filtern."""

from __future__ import annotations

from typing import Optional, Dict, List, Set, Any, TYPE_CHECKING
from supabase import Client

from utils.logging_config import get_logger
from utils.constants import MAX_POSTS_LIMIT, MAX_SEARCH_QUERY_LENGTH
from utils.filters import (
    filter_by_search,
    filter_by_colors,
    sort_by_event_date,
    mark_favorites,
)
from .queries import POST_SELECT_FULL

if TYPE_CHECKING:
    from services.account.profile import ProfileService

logger = get_logger(__name__)

SORT_CREATED_DESC = "created_at_desc"
SORT_CREATED_ASC = "created_at_asc"
SORT_EVENT_DESC = "event_date_desc"
SORT_EVENT_ASC = "event_date_asc"


class SearchService:
    """Service für Post-Suche mit Filtern."""

    def __init__(
        self,
        sb: Client,
        profile_service: Optional["ProfileService"] = None,
    ) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
            profile_service: Optional ProfileService (wird bei Bedarf erstellt)
        """
        self.sb = sb
        if profile_service is None:
            from services.account.profile import ProfileService
            self._profile_service = ProfileService(sb)
        else:
            self._profile_service = profile_service

    def _apply_id_filter(
        self,
        query: Any,
        filter_value: Any,
        column_name: str,
        filter_name: str,
    ) -> Any:
        """Wendet einen ID-basierten Filter auf die Query an.
        
        Args:
            query: Supabase Query-Objekt
            filter_value: Filter-Wert (kann int, str oder None sein)
            column_name: Name der Datenbank-Spalte
            filter_name: Name des Filters (für Logging)
        
        Returns:
            Query-Objekt mit angewendetem Filter
        """
        if not filter_value or filter_value == "alle":
            return query
        
        try:
            filter_id = int(filter_value)
            if filter_id > 0:
                return query.eq(column_name, filter_id)
        except (ValueError, TypeError):
            logger.warning(f"Ungültiger Filter-{filter_name}: {filter_value}")
        
        return query

    def _apply_nullable_filter(
        self,
        query: Any,
        filter_value: Any,
        column_name: str,
        filter_name: str,
    ) -> Any:
        """Wendet einen Filter an, der auch "keine_angabe" (NULL) unterstützt.
        
        Args:
            query: Supabase Query-Objekt
            filter_value: Filter-Wert (kann int, str "keine_angabe", oder None sein)
            column_name: Name der Datenbank-Spalte
            filter_name: Name des Filters (für Logging)
        
        Returns:
            Query-Objekt mit angewendetem Filter
        """
        if not filter_value or filter_value == "alle":
            return query
        
        if filter_value == "keine_angabe":
            return query.is_(column_name, "null")
        
        try:
            filter_id = int(filter_value)
            if filter_id > 0:
                return query.eq(column_name, filter_id)
        except (ValueError, TypeError):
            logger.warning(f"Ungültiger Filter-{filter_name}: {filter_value}")
        
        return query

    def _build_query(
        self,
        filters: Dict[str, Any],
        sort_option: str = SORT_CREATED_DESC,
    ) -> Any:
        """Baut die Supabase-Abfrage mit den aktiven Filtern.

        Args:
            filters: Dictionary mit Filterwerten (typ, art, geschlecht, rasse)
            sort_option: Sortier-Option (z.B. "created_at_desc", "event_date_asc")

        Returns:
            Supabase Query-Objekt mit angewendeten Filtern
        """
        query = (
            self.sb.table("post")
            .select(POST_SELECT_FULL)
        )

        # Sortierung anwenden
        if sort_option == SORT_CREATED_DESC:
            query = query.order("created_at", desc=True)
        elif sort_option == SORT_CREATED_ASC:
            query = query.order("created_at", desc=False)
        elif sort_option in (SORT_EVENT_DESC, SORT_EVENT_ASC):
            # Für Event-Datum Sortierung: Zuerst nach created_at laden, dann in Python sortieren
            query = query.order("created_at", desc=True)
        else:
            query = query.order("created_at", desc=True)

        # Filter anwenden
        query = self._apply_id_filter(query, filters.get("typ"), "post_status_id", "Typ")
        query = self._apply_id_filter(query, filters.get("art"), "species_id", "Art")
        query = self._apply_nullable_filter(query, filters.get("geschlecht"), "sex_id", "Geschlecht")
        query = self._apply_nullable_filter(query, filters.get("rasse"), "breed_id", "Rasse")

        return query

    def search_posts(
        self,
        filters: Dict[str, Any],
        search_query: Optional[str] = None,
        selected_colors: Optional[Set[int]] = None,
        sort_option: str = SORT_CREATED_DESC,
        favorite_ids: Optional[Set[str]] = None,
        limit: int = MAX_POSTS_LIMIT,
    ) -> List[Dict[str, Any]]:
        """Sucht Posts mit Filtern, Suche, Farben und Sortierung.

        Args:
            filters: Dictionary mit Filterwerten (typ, art, geschlecht, rasse)
            search_query: Optionaler Suchbegriff (max. MAX_SEARCH_QUERY_LENGTH Zeichen)
            selected_colors: Optional Set mit Farb-IDs
            sort_option: Sortier-Option (created_at_desc, created_at_asc, event_date_desc, event_date_asc)
            favorite_ids: Optional Set mit Post-IDs der Favoriten (für Markierung)
            limit: Maximale Anzahl der Posts (Standard: MAX_POSTS_LIMIT)

        Returns:
            Liste von Post-Dictionaries mit is_favorite Flag und user_display_name.
            Leere Liste bei Fehler.
        """
        # Input-Validierung
        if search_query:
            search_query = search_query.strip()
            if len(search_query) > MAX_SEARCH_QUERY_LENGTH:
                logger.warning(f"Suchbegriff zu lang ({len(search_query)} Zeichen), wird gekürzt")
                search_query = search_query[:MAX_SEARCH_QUERY_LENGTH]
            if not search_query:
                search_query = None

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
            if sort_option == SORT_EVENT_DESC:
                items = sort_by_event_date(items, desc=True)
            elif sort_option == SORT_EVENT_ASC:
                items = sort_by_event_date(items, desc=False)

            # Favoritenstatus markieren
            if favorite_ids is not None:
                items = mark_favorites(items, favorite_ids)

            # Benutzernamen anreichern
            items = self._enrich_with_usernames(items)

            return items

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Suchen von Posts: {e}", exc_info=True)
            return []

    def _enrich_with_usernames(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reichert Posts mit Benutzernamen an.

        Args:
            items: Liste von Post-Dictionaries

        Returns:
            Liste von Posts mit user_display_name Feld (leerer String wenn nicht gefunden)
        """
        if not items:
            return items

        user_ids = {
            item.get("user_id")
            for item in items
            if item.get("user_id")
        }

        display_names = self._profile_service.get_user_display_names(user_ids) if user_ids else {}

        for item in items:
            item["user_display_name"] = display_names.get(item.get("user_id"), "")

        return items
