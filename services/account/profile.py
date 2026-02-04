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
            self._sync_user_display_to_table(display_name=sanitized_name)
            logger.info(f"Display-Name aktualisiert für User {user.id}")
            return True, ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Aktualisieren des Anzeigenamens: {e}", exc_info=True)
            return False, str(e)

    def _sync_user_display_to_table(
        self,
        display_name: Optional[str] = None,
        profile_image: Optional[str] = None,
    ) -> None:
        """Synchronisiert display_name/profile_image in public.user."""
        user = self.get_current_user()
        if not user:
            return
        payload: Dict[str, Any] = {}
        if display_name is not None:
            payload["display_name"] = display_name
        else:
            payload["display_name"] = (user.user_metadata or {}).get("display_name") or "Benutzer"
        if profile_image is not None:
            payload["profile_image"] = profile_image
        else:
            payload["profile_image"] = (user.user_metadata or {}).get("profile_image_url")
        if not payload:
            return
        try:
            self.sb.table("user").update(payload).eq("id", str(user.id)).execute()
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Sync public.user übersprungen: {e}")

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
            result = (
                self.sb.table("user")
                .select("id, display_name")
                .in_("id", user_ids_list)
                .execute()
            )
            
            profiles = {}
            PROFILE_IMAGE_BUCKET = "profile-images"
            
            for row in (result.data or []):
                user_id = row.get("id")
                if user_id:
                    # Profilbild-URL aus Storage generieren
                    # Format: {user_id}/avatar.jpg (wie in ProfileImageService)
                    storage_path = f"{user_id}/avatar.jpg"
                    try:
                        profile_image_url = self.sb.storage.from_(PROFILE_IMAGE_BUCKET).get_public_url(storage_path)
                    except Exception as e:  # noqa: BLE001
                        logger.debug(f"Konnte Profilbild-URL nicht generieren für User {user_id}: {e}")
                        profile_image_url = None
                    
                    profiles[user_id] = {
                        "display_name": row.get("display_name") or "Unbekannt",
                        "profile_image": profile_image_url,
                    }
            
            return profiles
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Laden der Benutzerprofile: {e}", exc_info=True)
            return {}
    
