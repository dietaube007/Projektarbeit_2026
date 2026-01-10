"""Service für Benutzer-Profil-Verwaltung."""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Tuple, Iterable

from supabase import Client

from utils.logging_config import get_logger
from utils.validators import validate_not_empty, validate_length, sanitize_string
from utils.constants import MAX_DISPLAY_NAME_LENGTH

logger = get_logger(__name__)


class ProfileService:
    """Service-Klasse für Benutzer-Profil-Daten."""

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb

    def get_current_user(self) -> Optional[Any]:
        """Gibt den aktuell eingeloggten Benutzer zurück."""
        try:
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                return user_response.user
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden des Benutzers: {e}", exc_info=True)
            return None

    def get_user_id(self) -> Optional[str]:
        """Gibt die ID des aktuell eingeloggten Benutzers zurück."""
        user = self.get_current_user()
        return user.id if user else None

    def get_display_name(self) -> str:
        """Gibt den Anzeigenamen des aktuellen Benutzers zurück."""
        user = self.get_current_user()
        if user and user.user_metadata:
            return user.user_metadata.get("display_name", "Benutzer")
        return "Benutzer"

    def get_email(self) -> Optional[str]:
        """Gibt die E-Mail des aktuellen Benutzers zurück."""
        user = self.get_current_user()
        return user.email if user else None

    def get_profile_image_url(self) -> Optional[str]:
        """Gibt die Profilbild-URL des aktuellen Benutzers zurück."""
        user = self.get_current_user()
        if user and user.user_metadata:
            return user.user_metadata.get("profile_image_url")
        return None

    def update_display_name(self, new_name: str) -> Tuple[bool, str]:
        """Aktualisiert den Anzeigenamen des aktuellen Benutzers."""
        name_valid, name_error = validate_not_empty(new_name, "Anzeigename")
        if not name_valid:
            return False, name_error or "Anzeigename darf nicht leer sein."

        length_valid, length_error = validate_length(new_name, max_length=MAX_DISPLAY_NAME_LENGTH)
        if not length_valid:
            return False, length_error or f"Max. {MAX_DISPLAY_NAME_LENGTH} Zeichen."

        try:
            sanitized_name = sanitize_string(new_name, max_length=MAX_DISPLAY_NAME_LENGTH)

            user = self.get_current_user()
            if not user:
                return False, "Nicht eingeloggt."

            current_metadata = dict(user.user_metadata) if user.user_metadata else {}
            current_metadata["display_name"] = sanitized_name

            self.sb.auth.update_user({"data": current_metadata})
            logger.info(f"Display-Name aktualisiert für User {user.id}")
            return True, ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Aktualisieren des Anzeigenamens: {e}", exc_info=True)
            return False, str(e)

    def _prepare_user_ids(self, user_ids: Iterable[str]) -> List[str]:
        """Bereitet User-IDs für Queries vor (dedupliziert, validiert).
        
        Args:
            user_ids: Iterable mit User-IDs
        
        Returns:
            Liste von deduplizierten User-IDs, leere Liste wenn ungültig
        """
        if not user_ids:
            return []
        user_ids_list = list(set(user_ids))
        return user_ids_list if user_ids_list else []

    def get_user_display_names(self, user_ids: Iterable[str]) -> Dict[str, str]:
        """Lädt die Anzeigenamen für eine Liste von User-IDs.

        Args:
            user_ids: Iterable mit User-IDs (wird automatisch dedupliziert)

        Returns:
            Dictionary mit user_id -> display_name Mapping
        """
        # Nutze get_user_profiles() und extrahiere nur display_name
        profiles = self.get_user_profiles(user_ids)
        return {
            user_id: profile.get("display_name", "")
            for user_id, profile in profiles.items()
        }

    def get_user_profiles(self, user_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        """Lädt Profil-Daten (display_name + profile_image) für mehrere User-IDs.
        
        Args:
            user_ids: Iterable mit User-IDs (wird automatisch dedupliziert)
        
        Returns:
            Dictionary: user_id -> {"display_name": str, "profile_image": str | None}
            Leeres Dictionary bei Fehler oder wenn keine user_ids vorhanden.
        """
        user_ids_list = self._prepare_user_ids(user_ids)
        if not user_ids_list:
            return {}
        
        try:
            # Nutze direkt user_profiles View (hat nur display_name)
            result = (
                self.sb.table("user_profiles")
                .select("id, display_name")
                .in_("id", user_ids_list)
                .execute()
            )
            
            profiles = {}
            for row in (result.data or []):
                user_id = row.get("id")
                if user_id:
                    profiles[user_id] = {
                        "display_name": row.get("display_name") or "Unbekannt",
                        "profile_image": None,  # profile_image_url ist in auth.users user_metadata, nicht direkt abfragbar
                    }
            
            return profiles
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der Benutzerprofile: {e}", exc_info=True)
            return {}
    
