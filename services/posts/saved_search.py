"""Service für gespeicherte Suchaufträge."""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Tuple, TYPE_CHECKING
import json
from supabase import Client

from utils.logging_config import get_logger
from utils.validators import validate_not_empty, validate_length, sanitize_string

if TYPE_CHECKING:
    from services.account.profile import ProfileService

logger = get_logger(__name__)


class SavedSearchService:
    """Service-Klasse für gespeicherte Suchaufträge."""

    MAX_SEARCH_NAME_LENGTH: int = 100
    MAX_SAVED_SEARCHES: int = 20

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

    def _parse_filters(self, filters_value: Any) -> Dict[str, Any]:
        """Konvertiert das filters-Feld von JSON-String in ein Dictionary.
        
        Args:
            filters_value: Das filters-Feld aus der Datenbank (kann str, dict oder None sein)
        
        Returns:
            Dictionary mit Filterwerten, leeres Dict bei Fehler oder None
        """
        if isinstance(filters_value, str):
            try:
                return json.loads(filters_value)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Ungültiges JSON im filters-Feld: {e}")
                return {}
        elif isinstance(filters_value, dict):
            return filters_value
        else:
            return {}

    def _prepare_filters(
        self,
        search_query: Optional[str] = None,
        status_id: Optional[int] = None,
        species_id: Optional[int] = None,
        breed_id: Optional[Any] = None,
        sex_id: Optional[Any] = None,
        colors: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Bereitet die Filter für die Speicherung vor.
        
        Args:
            search_query: Suchbegriff
            status_id: Status-Filter (Vermisst/Gefunden)
            species_id: Tierart-Filter
            breed_id: Rasse-Filter (kann int oder "keine_angabe" sein)
            sex_id: Geschlechts-Filter (kann int oder "keine_angabe" sein)
            colors: Liste der Farb-IDs
        
        Returns:
            Dictionary mit bereinigten Filterwerten
        """
        filters: Dict[str, Any] = {
            "search_query": search_query.strip() if search_query else None,
            "status_id": status_id if status_id and status_id != 0 else None,
            "species_id": species_id if species_id and species_id != 0 else None,
            "breed_id": breed_id if breed_id and breed_id != 0 and breed_id != "keine_angabe" else None,
            "sex_id": sex_id if sex_id and sex_id != 0 and sex_id != "keine_angabe" else None,
            "colors": colors if colors else [],
        }
        
        # "keine_angabe" als speziellen Wert speichern
        if sex_id == "keine_angabe":
            filters["geschlecht"] = "keine_angabe"
        if breed_id == "keine_angabe":
            filters["rasse"] = "keine_angabe"
        
        # None-Werte aus dem JSON entfernen, um es schlank zu halten
        return {k: v for k, v in filters.items() if v not in (None, [], "")}

    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """Lädt alle gespeicherten Suchaufträge des aktuellen Benutzers.

        Returns:
            Liste von Suchaufträgen mit allen Filterkriterien.
            Leere Liste wenn Benutzer nicht eingeloggt ist oder bei Fehler.
        """
        user_id = self._profile_service.get_user_id()
        if not user_id:
            return []

        try:
            # Aktuelle Tabellenstruktur:
            # id, user_id, name, filters (jsonb), location_lat, location_lon,
            # radius_meters, created_at
            # Wir laden nur die Felder, die wir benötigen.
            res = (
                self.sb.table("saved_search")
                .select(
                    """
                    id,
                    name,
                    filters,
                    created_at
                    """
                )
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            items = res.data or []

            # filters-Feld von JSON-String in Dict umwandeln
            for item in items:
                item["filters"] = self._parse_filters(item.get("filters"))

            return items

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der gespeicherten Suchen: {e}", exc_info=True)
            return []

    def save_search(
        self,
        name: str,
        search_query: Optional[str] = None,
        status_id: Optional[int] = None,
        species_id: Optional[int] = None,
        breed_id: Optional[Any] = None,  # Kann int oder "keine_angabe" sein
        sex_id: Optional[Any] = None,  # Kann int oder "keine_angabe" sein
        colors: Optional[List[int]] = None,
    ) -> Tuple[bool, str]:
        """Speichert einen neuen Suchauftrag.

        Args:
            name: Name des Suchauftrags
            search_query: Suchbegriff
            status_id: Status-Filter (Vermisst/Gefunden)
            species_id: Tierart-Filter
            breed_id: Rasse-Filter
            sex_id: Geschlechts-Filter
            colors: Liste der Farb-IDs

        Returns:
            Tuple (Erfolg, Fehlermeldung oder leerer String)
        """
        user_id = self._profile_service.get_user_id()
        if not user_id:
            return False, "Nicht eingeloggt."

        # Validierung
        name_valid, name_error = validate_not_empty(name, "Name")
        if not name_valid:
            return False, name_error or "Name darf nicht leer sein."

        length_valid, length_error = validate_length(name, max_length=self.MAX_SEARCH_NAME_LENGTH)
        if not length_valid:
            return False, length_error or f"Max. {self.MAX_SEARCH_NAME_LENGTH} Zeichen."

        try:
            # Prüfen ob max. Anzahl erreicht
            count_res = (
                self.sb.table("saved_search")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            if count_res.count and count_res.count >= self.MAX_SAVED_SEARCHES:
                return False, f"Maximal {self.MAX_SAVED_SEARCHES} Suchaufträge erlaubt."

            # Name bereinigen
            sanitized_name = sanitize_string(name, max_length=self.MAX_SEARCH_NAME_LENGTH)

            # Filter-JSON vorbereiten
            filters = self._prepare_filters(
                search_query=search_query,
                status_id=status_id,
                species_id=species_id,
                breed_id=breed_id,
                sex_id=sex_id,
                colors=colors,
            )

            # Daten vorbereiten
            data = {
                "user_id": user_id,
                "name": sanitized_name,
                "filters": filters,
            }

            self.sb.table("saved_search").insert(data).execute()
            logger.info(f"Suchauftrag '{sanitized_name}' gespeichert für User {user_id}")
            return True, ""

        except Exception as e:  # noqa: BLE001
            error_str = str(e).lower()
            if "duplicate" in error_str or "unique" in error_str:
                return False, f"Ein Suchauftrag mit dem Namen '{name}' existiert bereits."
            logger.error(f"Fehler beim Speichern des Suchauftrags: {e}", exc_info=True)
            return False, str(e)

    def delete_search(self, search_id: int) -> Tuple[bool, str]:
        """Löscht einen gespeicherten Suchauftrag.

        Args:
            search_id: ID des zu löschenden Suchauftrags

        Returns:
            Tuple (Erfolg, Fehlermeldung oder leerer String)
        """
        if not search_id or search_id <= 0:
            return False, "Ungültige Suchauftrag-ID."

        user_id = self._profile_service.get_user_id()
        if not user_id:
            return False, "Nicht eingeloggt."

        try:
            # Prüfen ob der Suchauftrag dem Benutzer gehört
            res = (
                self.sb.table("saved_search")
                .select("id")
                .eq("id", search_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )

            if not res.data:
                return False, "Suchauftrag nicht gefunden."

            # Löschen
            self.sb.table("saved_search").delete().eq("id", search_id).execute()
            logger.info(f"Suchauftrag {search_id} gelöscht für User {user_id}")
            return True, ""

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Löschen des Suchauftrags: {e}", exc_info=True)
            return False, str(e)

    def get_search_by_id(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Lädt einen einzelnen Suchauftrag anhand der ID.

        Args:
            search_id: ID des Suchauftrags

        Returns:
            Suchauftrag-Dictionary oder None wenn nicht gefunden, ungültige ID oder bei Fehler
        """
        if not search_id or search_id <= 0:
            logger.warning(f"Ungültige search_id beim Laden: {search_id}")
            return None

        user_id = self._profile_service.get_user_id()
        if not user_id:
            return None

        try:
            res = (
                self.sb.table("saved_search")
                .select(
                    """
                    id,
                    name,
                    filters,
                    created_at
                    """
                )
                .eq("id", search_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            item = res.data

            if not item:
                return None

            # filters-Feld von JSON-String in Dict umwandeln
            item["filters"] = self._parse_filters(item.get("filters"))

            return item

        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden des Suchauftrags: {e}", exc_info=True)
            return None
