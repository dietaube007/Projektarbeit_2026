"""Profil-Service für Benutzerverwaltung.

Dieses Modul verwaltet alle Datenbankoperationen für Benutzerprofile:
- Benutzerdaten laden
- Anzeigename aktualisieren
- Profilbild hochladen/löschen (Delegation)
- Passwort-Reset senden (Delegation)
- Favoriten verwalten (Delegation)
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Tuple

from supabase import Client

from utils.logging_config import get_logger
from utils.validators import validate_not_empty, validate_length, sanitize_string
from services.profile.image_service import ProfileImageService
from services.profile.favorites_service import FavoritesService
from services.profile.account_deletion import AccountDeletionService
from services.auth import AuthService

logger = get_logger(__name__)

# Konstante hier definiert um Circular Import zu vermeiden
MAX_DISPLAY_NAME_LENGTH: int = 50


class ProfileService:
    """Service-Klasse für Benutzer-Profil-Operationen."""

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb
        self.image_service = ProfileImageService(sb)
        self.favorites_service = FavoritesService(sb)
        self.account_deletion_service = AccountDeletionService(sb)

    # ─════════════════════════════════════════════════════════════════════
    # BENUTZERDATEN
    # ─════════════════════════════════════════════════════════════════════

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

    # ─════════════════════════════════════════════════════════════════════
    # ANZEIGENAME
    # ─════════════════════════════════════════════════════════════════════

    def update_display_name(self, new_name: str) -> Tuple[bool, str]:
        """Aktualisiert den Anzeigenamen des aktuellen Benutzers."""
        # Validierung
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

    # ─════════════════════════════════════════════════════════════════════
    # PASSWORT-RESET & PASSWORT-ÄNDERUNG
    # ─════════════════════════════════════════════════════════════════════

    def send_password_reset(self, email: str) -> Tuple[bool, str]:
        """Sendet eine Passwort-Zurücksetzen-E-Mail (Delegation an AuthService)."""
        auth_service = AuthService(self.sb)
        result = auth_service.send_reset_password_email(email)
        return result.success, result.message or ""

    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validiert ein Passwort nach den Sicherheitsanforderungen."""
        import re

        if not password:
            return False, "Passwort darf nicht leer sein."
        if len(password) < 8:
            return False, "Passwort muss mindestens 8 Zeichen haben."
        if not re.search(r"[A-Z]", password):
            return False, "Passwort muss mindestens einen Großbuchstaben enthalten."
        if not re.search(r"[a-z]", password):
            return False, "Passwort muss mindestens einen Kleinbuchstaben enthalten."
        if not re.search(r"[0-9]", password):
            return False, "Passwort muss mindestens eine Zahl enthalten."
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password):
            return False, "Passwort muss mindestens ein Sonderzeichen enthalten."

        return True, ""

    def update_password(self, new_password: str) -> Tuple[bool, str]:
        """Aktualisiert das Passwort des aktuellen Benutzers."""
        is_valid, error_msg = self.validate_password(new_password)
        if not is_valid:
            return False, error_msg

        try:
            self.sb.auth.update_user({"password": new_password})
            logger.info("Passwort erfolgreich aktualisiert")
            return True, ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Aktualisieren des Passworts: {e}", exc_info=True)
            return False, str(e)

    # ─════════════════════════════════════════════════════════════════════
    # PROFILBILD (Delegation)
    # ─════════════════════════════════════════════════════════════════════

    def upload_profile_image(self, file_path: str) -> Tuple[bool, Optional[str], str]:
        return self.image_service.upload_profile_image(file_path)

    def delete_profile_image(self) -> bool:
        success, _ = self.image_service.delete_profile_image()
        return success

    # ─════════════════════════════════════════════════════════════════════
    # FAVORITEN (Delegation)
    # ─════════════════════════════════════════════════════════════════════

    def get_favorites(self) -> List[Dict[str, Any]]:
        return self.favorites_service.get_favorites()

    def add_favorite(self, post_id: int) -> bool:
        return self.favorites_service.add_favorite(post_id)

    def remove_favorite(self, post_id: int) -> bool:
        return self.favorites_service.remove_favorite(post_id)

    def is_favorite(self, post_id: int) -> bool:
        return self.favorites_service.is_favorite(post_id)

    # ─════════════════════════════════════════════════════════════════════
    # MEINE MELDUNGEN (Delegation an PostService)
    # ─════════════════════════════════════════════════════════════════════

    def get_my_posts(self) -> List[Dict[str, Any]]:
        user_id = self.get_user_id()
        if not user_id:
            return []
        from services.posts import PostService

        post_service = PostService(self.sb)
        return post_service.get_my_posts(user_id)

    # ─════════════════════════════════════════════════════════════════════
    # LOGOUT & KONTO-LÖSCHEN
    # ─════════════════════════════════════════════════════════════════════

    def logout(self) -> bool:
        try:
            self.sb.auth.sign_out()
            logger.info("Benutzer abgemeldet")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Abmelden: {e}", exc_info=True)
            return False

    def delete_account(self) -> Tuple[bool, str]:
        """Löscht das Konto des aktuellen Benutzers über den AccountDeletionService."""
        return self.account_deletion_service.delete_account()


