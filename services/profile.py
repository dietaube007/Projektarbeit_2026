"""Profil-Service für Benutzerverwaltung.

Dieses Modul verwaltet alle Datenbankoperationen für Benutzerprofile:
- Benutzerdaten laden
- Anzeigename aktualisieren
- Profilbild hochladen/löschen
- Passwort-Reset senden
- Favoriten verwalten
"""

from __future__ import annotations

import os
import io
from typing import Optional, List, Dict, Any, Tuple

from PIL import Image
from supabase import Client

from utils.logging_config import get_logger
from utils.validators import validate_not_empty, validate_length, sanitize_string, validate_email

logger = get_logger(__name__)

# Konstante hier definiert um Circular Import zu vermeiden
MAX_DISPLAY_NAME_LENGTH: int = 50


# ════════════════════════════════════════════════════════════════════════════════
# KONSTANTEN
# ════════════════════════════════════════════════════════════════════════════════

PROFILE_IMAGE_BUCKET: str = "profile-images"
PROFILE_IMAGE_SIZE: Tuple[int, int] = (400, 400)
IMAGE_QUALITY: int = 85
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB


class ProfileService:
    """Service-Klasse für Benutzer-Profil-Operationen."""

    def __init__(self, sb: Client) -> None:
        """Initialisiert den Service mit dem Supabase-Client.

        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb

    # ════════════════════════════════════════════════════════════════════
    # BENUTZERDATEN
    # ════════════════════════════════════════════════════════════════════

    def get_current_user(self) -> Optional[Any]:
        """Gibt den aktuell eingeloggten Benutzer zurück.

        Returns:
            User-Objekt oder None wenn nicht eingeloggt
        """
        try:
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                return user_response.user
            return None
        except Exception as e:
            logger.error(f"Fehler beim Laden des Benutzers: {e}", exc_info=True)
            return None

    def get_user_id(self) -> Optional[str]:
        """Gibt die ID des aktuell eingeloggten Benutzers zurück.

        Returns:
            User-ID als String oder None
        """
        user = self.get_current_user()
        return user.id if user else None

    def get_display_name(self) -> str:
        """Gibt den Anzeigenamen des aktuellen Benutzers zurück.

        Returns:
            Anzeigename oder "Benutzer" als Fallback
        """
        user = self.get_current_user()
        if user and user.user_metadata:
            return user.user_metadata.get("display_name", "Benutzer")
        return "Benutzer"

    def get_email(self) -> Optional[str]:
        """Gibt die E-Mail des aktuellen Benutzers zurück.

        Returns:
            E-Mail oder None
        """
        user = self.get_current_user()
        return user.email if user else None

    def get_profile_image_url(self) -> Optional[str]:
        """Gibt die Profilbild-URL des aktuellen Benutzers zurück.

        Returns:
            Profilbild-URL oder None
        """
        user = self.get_current_user()
        if user and user.user_metadata:
            return user.user_metadata.get("profile_image_url")
        return None

    # ════════════════════════════════════════════════════════════════════
    # ANZEIGENAME
    # ════════════════════════════════════════════════════════════════════

    def update_display_name(self, new_name: str) -> Tuple[bool, str]:
        """Aktualisiert den Anzeigenamen des aktuellen Benutzers.

        Args:
            new_name: Neuer Anzeigename

        Returns:
            Tuple (Erfolg, Fehlermeldung oder leerer String)
        """
        # Validierung
        name_valid, name_error = validate_not_empty(new_name, "Anzeigename")
        if not name_valid:
            return False, name_error or "Anzeigename darf nicht leer sein."

        length_valid, length_error = validate_length(new_name, max_length=MAX_DISPLAY_NAME_LENGTH)
        if not length_valid:
            return False, length_error or f"Max. {MAX_DISPLAY_NAME_LENGTH} Zeichen."

        try:
            sanitized_name = sanitize_string(new_name, max_length=MAX_DISPLAY_NAME_LENGTH)

            # Aktuelle Metadaten holen
            user = self.get_current_user()
            if not user:
                return False, "Nicht eingeloggt."

            current_metadata = dict(user.user_metadata) if user.user_metadata else {}
            current_metadata["display_name"] = sanitized_name

            # Metadaten aktualisieren
            self.sb.auth.update_user({"data": current_metadata})
            logger.info(f"Display-Name aktualisiert für User {user.id}")
            return True, ""

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Anzeigenamens: {e}", exc_info=True)
            return False, str(e)

    # ════════════════════════════════════════════════════════════════════
    # PASSWORT-RESET
    # ════════════════════════════════════════════════════════════════════

    def send_password_reset(self, email: str) -> Tuple[bool, str]:
        """Sendet eine Passwort-Zurücksetzen-E-Mail.

        Args:
            email: E-Mail-Adresse

        Returns:
            Tuple (Erfolg, Fehlermeldung oder leerer String)
        """
        email_valid, email_error = validate_email(email)
        if not email_valid:
            return False, email_error or "Ungültige E-Mail-Adresse."

        try:
            normalized_email = email.strip().lower()
            self.sb.auth.reset_password_email(normalized_email)
            logger.info(f"Passwort-Reset E-Mail gesendet an {normalized_email}")
            return True, ""

        except Exception as e:
            logger.error(f"Fehler beim Senden der Passwort-Reset E-Mail: {e}", exc_info=True)
            return False, str(e)

    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validiert ein Passwort nach den Sicherheitsanforderungen.

        Anforderungen:
        - Mindestens 8 Zeichen
        - Mindestens ein Großbuchstabe
        - Mindestens ein Kleinbuchstabe
        - Mindestens eine Zahl
        - Mindestens ein Sonderzeichen

        Args:
            password: Zu validierendes Passwort

        Returns:
            Tuple (Gültig, Fehlermeldung oder leerer String)
        """
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
        """Aktualisiert das Passwort des aktuellen Benutzers.

        Args:
            new_password: Neues Passwort

        Returns:
            Tuple (Erfolg, Fehlermeldung oder leerer String)
        """
        # Passwort validieren
        is_valid, error_msg = self.validate_password(new_password)
        if not is_valid:
            return False, error_msg

        try:
            self.sb.auth.update_user({"password": new_password})
            logger.info("Passwort erfolgreich aktualisiert")
            return True, ""

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Passworts: {e}", exc_info=True)
            return False, str(e)

    # ════════════════════════════════════════════════════════════════════
    # PROFILBILD
    # ════════════════════════════════════════════════════════════════════

    def compress_profile_image(self, file_path: str) -> bytes:
        """Komprimiert ein Profilbild auf 400x400px.

        Args:
            file_path: Pfad zur Bilddatei

        Returns:
            Komprimierte Bilddaten als Bytes

        Raises:
            IOError: Bei Fehler beim Lesen/Verarbeiten des Bildes
        """
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            img.thumbnail(PROFILE_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Quadratisches Bild erstellen
            square_img = Image.new("RGB", PROFILE_IMAGE_SIZE, (255, 255, 255))
            paste_x = (PROFILE_IMAGE_SIZE[0] - img.width) // 2
            paste_y = (PROFILE_IMAGE_SIZE[1] - img.height) // 2
            square_img.paste(img, (paste_x, paste_y))

            buffer = io.BytesIO()
            square_img.save(buffer, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
            buffer.seek(0)
            return buffer.read()

    def upload_profile_image(self, file_path: str) -> Tuple[bool, Optional[str], str]:
        """Lädt ein Profilbild zu Supabase Storage hoch.

        Args:
            file_path: Pfad zur Bilddatei

        Returns:
            Tuple (Erfolg, Public-URL oder None, Fehlermeldung)
        """
        # Validierungen
        if not os.path.exists(file_path):
            return False, None, "Datei nicht gefunden."

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            return False, None, "Datei zu groß. Max. 5 MB."

        user = self.get_current_user()
        if not user:
            return False, None, "Nicht eingeloggt."

        try:
            # Altes Bild löschen
            self.delete_profile_image()

            # Bild komprimieren
            compressed_bytes = self.compress_profile_image(file_path)
            storage_path = f"{user.id}/avatar.jpg"

            # Hochladen
            self.sb.storage.from_(PROFILE_IMAGE_BUCKET).upload(
                path=storage_path,
                file=compressed_bytes,
                file_options={"content-type": "image/jpeg", "upsert": "true"}
            )

            # Public URL holen
            public_url = self.sb.storage.from_(PROFILE_IMAGE_BUCKET).get_public_url(storage_path)

            # URL in Metadaten speichern
            success = self._update_profile_image_url(public_url)
            if not success:
                return False, None, "Konnte URL nicht speichern."

            logger.info(f"Profilbild hochgeladen für User {user.id}")
            return True, public_url, ""

        except Exception as e:
            logger.error(f"Fehler beim Upload des Profilbilds: {e}", exc_info=True)
            return False, None, str(e)

    def delete_profile_image(self) -> bool:
        """Löscht das Profilbild des aktuellen Benutzers aus Storage.

        Returns:
            True bei Erfolg, False bei Fehler
        """
        user = self.get_current_user()
        if not user:
            return False

        try:
            storage_path = f"{user.id}/avatar.jpg"
            self.sb.storage.from_(PROFILE_IMAGE_BUCKET).remove([storage_path])
            logger.info(f"Profilbild gelöscht für User {user.id}")
            return True
        except Exception as e:
            logger.warning(f"Fehler beim Löschen des Profilbilds: {e}")
            return False

    def _update_profile_image_url(self, image_url: Optional[str]) -> bool:
        """Aktualisiert die Profilbild-URL in user_metadata.

        Args:
            image_url: Neue Profilbild-URL oder None zum Entfernen

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            user = self.get_current_user()
            if not user:
                return False

            current_metadata = dict(user.user_metadata) if user.user_metadata else {}

            if image_url:
                current_metadata["profile_image_url"] = image_url
            else:
                current_metadata.pop("profile_image_url", None)

            self.sb.auth.update_user({"data": current_metadata})
            return True

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Profilbild-URL: {e}", exc_info=True)
            return False

    # ════════════════════════════════════════════════════════════════════
    # FAVORITEN
    # ════════════════════════════════════════════════════════════════════

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Lädt alle favorisierten Meldungen des aktuellen Benutzers.

        Returns:
            Liste von Post-Dictionaries
        """
        user = self.get_current_user()
        if not user:
            return []

        try:
            # Favoriten-IDs laden
            fav_res = (
                self.sb.table("favorite")
                .select("post_id")
                .eq("user_id", user.id)
                .execute()
            )
            fav_rows = fav_res.data or []
            post_ids = [row["post_id"] for row in fav_rows if row.get("post_id")]

            if not post_ids:
                return []

            # Posts laden
            posts_res = (
                self.sb.table("post")
                .select(
                    """
                    id,
                    headline,
                    location_text,
                    event_date,
                    created_at,
                    is_active,
                    post_status(id, name),
                    species(id, name),
                    breed(id, name),
                    post_image(url),
                    post_color(color(id, name))
                    """
                )
                .in_("id", post_ids)
                .order("created_at", desc=True)
                .execute()
            )

            return posts_res.data or []

        except Exception as e:
            logger.error(f"Fehler beim Laden der Favoriten: {e}", exc_info=True)
            return []

    def add_favorite(self, post_id: int) -> bool:
        """Fügt einen Post zu den Favoriten hinzu.

        Args:
            post_id: ID des Posts

        Returns:
            True bei Erfolg, False bei Fehler
        """
        user = self.get_current_user()
        if not user:
            return False

        try:
            self.sb.table("favorite").insert({
                "user_id": user.id,
                "post_id": post_id,
            }).execute()
            logger.info(f"Favorit hinzugefügt: User {user.id}, Post {post_id}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen zu Favoriten: {e}", exc_info=True)
            return False

    def remove_favorite(self, post_id: int) -> bool:
        """Entfernt einen Post aus den Favoriten.

        Args:
            post_id: ID des Posts

        Returns:
            True bei Erfolg, False bei Fehler
        """
        user = self.get_current_user()
        if not user:
            return False

        try:
            (
                self.sb.table("favorite")
                .delete()
                .eq("user_id", user.id)
                .eq("post_id", post_id)
                .execute()
            )
            logger.info(f"Favorit entfernt: User {user.id}, Post {post_id}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Entfernen aus Favoriten: {e}", exc_info=True)
            return False

    def is_favorite(self, post_id: int) -> bool:
        """Prüft ob ein Post in den Favoriten ist.

        Args:
            post_id: ID des Posts

        Returns:
            True wenn favorisiert, sonst False
        """
        user = self.get_current_user()
        if not user:
            return False

        try:
            res = (
                self.sb.table("favorite")
                .select("id")
                .eq("user_id", user.id)
                .eq("post_id", post_id)
                .maybe_single()
                .execute()
            )
            return res.data is not None
        except Exception:
            return False

    # ════════════════════════════════════════════════════════════════════
    # MEINE MELDUNGEN
    # ════════════════════════════════════════════════════════════════════

    def get_my_posts(self) -> List[Dict[str, Any]]:
        """Lädt alle Meldungen des aktuellen Benutzers.

        Returns:
            Liste von Post-Dictionaries
        """
        user = self.get_current_user()
        if not user:
            return []

        try:
            res = (
                self.sb.table("post")
                .select(
                    """
                    id,
                    headline,
                    description,
                    location_text,
                    event_date,
                    created_at,
                    is_active,
                    post_status(id, name),
                    species(id, name),
                    breed(id, name),
                    sex(id, name),
                    post_image(url),
                    post_color(color(id, name))
                    """
                )
                .eq("user_id", user.id)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []

        except Exception as e:
            logger.error(f"Fehler beim Laden der eigenen Meldungen: {e}", exc_info=True)
            return []

    # ════════════════════════════════════════════════════════════════════
    # LOGOUT
    # ════════════════════════════════════════════════════════════════════

    def logout(self) -> bool:
        """Meldet den aktuellen Benutzer ab.

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            self.sb.auth.sign_out()
            logger.info("Benutzer abgemeldet")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Abmelden: {e}", exc_info=True)
            return False

