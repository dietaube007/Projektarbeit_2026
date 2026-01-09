"""Authentifizierungs-Service für Login, Registrierung und Passwort-Verwaltung."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from supabase import Client

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AuthResult:
    """Ergebnis einer Authentifizierungsoperation."""
    success: bool
    message: str = ""
    code: Optional[str] = None


class AuthErrorCode:
    """Fehlercodes für Authentifizierungsoperationen."""
    LOGIN_FAILED = "login_failed"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_NOT_CONFIRMED = "email_not_confirmed"
    EMAIL_CONFIRMATION_REQUIRED = "confirm_email"
    EMAIL_EXISTS = "email_exists"
    INVALID_EMAIL = "invalid_email"
    INVALID_PASSWORD = "invalid_password"
    UNKNOWN_ERROR = "unknown_error"


class AuthService:
    """Service-Klasse für Authentifizierung und Registrierung."""

    def __init__(self, sb: Client) -> None:
        """Initialisiert den AuthService mit einem Supabase-Client.
        
        Args:
            sb: Supabase Client-Instanz
        """
        self.sb = sb

    def _get_redirect_url(self, path: str = "/") -> str:
        """Bestimmt die Redirect-URL basierend auf der Umgebung.
        
        Args:
            path: Pfad, der an die Base-URL angehängt wird (Standard: "/")
        
        Returns:
            Vollständige Redirect-URL
        """
        base_url = (
            "https://petbuddy.fly.dev"
            if os.getenv("FLY_APP_NAME")
            else "http://localhost:8550"
        )
        return f"{base_url}{path}"

    def _normalize_email(self, email: str) -> str:
        """Normalisiert eine E-Mail-Adresse (lowercase, trim).
        
        Args:
            email: E-Mail-Adresse
        
        Returns:
            Normalisierte E-Mail-Adresse
        """
        return email.lower().strip()

    def login(self, email: str, password: str) -> AuthResult:
        """Meldet einen Benutzer an.
        
        Args:
            email: E-Mail-Adresse des Benutzers
            password: Passwort des Benutzers
        
        Returns:
            AuthResult mit Erfolg/Fehler-Status
        """
        if not email or not email.strip():
            return AuthResult(
                success=False,
                message="E-Mail darf nicht leer sein.",
                code=AuthErrorCode.INVALID_EMAIL,
            )
        if not password:
            return AuthResult(
                success=False,
                message="Passwort darf nicht leer sein.",
                code=AuthErrorCode.INVALID_PASSWORD,
            )

        try:
            normalized_email = self._normalize_email(email)
            res = self.sb.auth.sign_in_with_password(
                {
                    "email": normalized_email,
                    "password": password,
                }
            )
            if res and res.user:
                logger.info(f"Benutzer erfolgreich angemeldet: {normalized_email}")
                return AuthResult(success=True)
            
            logger.warning(f"Anmeldung fehlgeschlagen für: {normalized_email}")
            return AuthResult(
                success=False,
                message="Anmeldung fehlgeschlagen.",
                code=AuthErrorCode.LOGIN_FAILED,
            )
        except Exception as e:  # noqa: BLE001
            error_str = str(e).lower()
            if "invalid login credentials" in error_str or "invalid credentials" in error_str:
                logger.warning(f"Ungültige Anmeldedaten für: {self._normalize_email(email)}")
                return AuthResult(
                    success=False,
                    message="E-Mail oder Passwort falsch.",
                    code=AuthErrorCode.INVALID_CREDENTIALS,
                )
            if "email not confirmed" in error_str:
                logger.warning(f"E-Mail nicht bestätigt für: {self._normalize_email(email)}")
                return AuthResult(
                    success=False,
                    message="Bitte bestätigen Sie zuerst Ihre E-Mail.",
                    code=AuthErrorCode.EMAIL_NOT_CONFIRMED,
                )
            logger.error(f"Fehler beim Login: {e}", exc_info=True)
            return AuthResult(
                success=False,
                message=f"Fehler: {str(e)[:50]}",
                code=AuthErrorCode.UNKNOWN_ERROR,
            )

    def register(self, email: str, password: str, username: str) -> AuthResult:
        """Registriert einen neuen Benutzer.
        
        Args:
            email: E-Mail-Adresse des neuen Benutzers
            password: Passwort des neuen Benutzers
            username: Anzeigename des neuen Benutzers
        
        Returns:
            AuthResult mit Erfolg/Fehler-Status
        """
        if not email or not email.strip():
            return AuthResult(
                success=False,
                message="E-Mail darf nicht leer sein.",
                code=AuthErrorCode.INVALID_EMAIL,
            )
        if not password:
            return AuthResult(
                success=False,
                message="Passwort darf nicht leer sein.",
                code=AuthErrorCode.INVALID_PASSWORD,
            )
        if not username or not username.strip():
            return AuthResult(
                success=False,
                message="Benutzername darf nicht leer sein.",
                code=AuthErrorCode.UNKNOWN_ERROR,
            )

        try:
            normalized_email = self._normalize_email(email)
            redirect_url = self._get_redirect_url("/login")

            res = self.sb.auth.sign_up(
                {
                    "email": normalized_email,
                    "password": password,
                    "options": {
                        "data": {
                            "display_name": username.strip(),
                        },
                        "email_redirect_to": redirect_url,
                    },
                }
            )

            if not res or not res.user:
                logger.error(f"Registrierung fehlgeschlagen für: {normalized_email}")
                return AuthResult(
                    success=False,
                    message="Fehler bei der Registrierung!",
                    code=AuthErrorCode.UNKNOWN_ERROR,
                )

            # Prüfen ob E-Mail bereits registriert ist
            if not res.user.identities or len(res.user.identities) == 0:
                logger.warning(f"E-Mail bereits registriert: {normalized_email}")
                return AuthResult(
                    success=False,
                    message="E-Mail bereits registriert. Bitte melden Sie sich an!",
                    code=AuthErrorCode.EMAIL_EXISTS,
                )

            # Prüfen ob E-Mail-Bestätigung erforderlich ist
            if res.user.confirmed_at is None:
                logger.info(f"Bestätigungs-E-Mail gesendet für: {normalized_email}")
                return AuthResult(
                    success=True,
                    message="Bestätigungs-E-Mail gesendet! Bitte prüfen Sie Ihr Postfach.",
                    code=AuthErrorCode.EMAIL_CONFIRMATION_REQUIRED,
                )

            logger.info(f"Benutzer erfolgreich registriert: {normalized_email}")
            return AuthResult(success=True)

        except Exception as e:  # noqa: BLE001
            error_str = str(e).lower()
            if "already registered" in error_str or "user already registered" in error_str:
                logger.warning(f"E-Mail bereits registriert (Exception): {self._normalize_email(email)}")
                return AuthResult(
                    success=False,
                    message="E-Mail bereits registriert.",
                    code=AuthErrorCode.EMAIL_EXISTS,
                )
            logger.error(f"Fehler bei der Registrierung: {e}", exc_info=True)
            return AuthResult(
                success=False,
                message=f"Fehler: {str(e)[:50]}",
                code=AuthErrorCode.UNKNOWN_ERROR,
            )

    def logout(self) -> AuthResult:
        """Meldet den aktuellen Benutzer ab.
        
        Returns:
            AuthResult mit Erfolg/Fehler-Status
        """
        try:
            self.sb.auth.sign_out()
            logger.info("Benutzer erfolgreich abgemeldet")
            return AuthResult(success=True, message="Abgemeldet.")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Abmelden: {e}", exc_info=True)
            return AuthResult(
                success=False,
                message=f"Fehler: {str(e)[:50]}",
                code=AuthErrorCode.UNKNOWN_ERROR,
            )

    def reset_password(self, email: str) -> AuthResult:
        """Sendet eine Passwort-Zurücksetzen-E-Mail an den Benutzer.
        
        Args:
            email: E-Mail-Adresse des Benutzers
        
        Returns:
            AuthResult mit Erfolg/Fehler-Status
        
        Note:
            Die Redirect-URL nach dem Passwort-Reset führt zur Startseite (/),
            da der Benutzer dort nach dem Reset landen soll.
        """
        # Validierung
        if not email or not email.strip():
            return AuthResult(
                success=False,
                message="E-Mail darf nicht leer sein.",
                code=AuthErrorCode.INVALID_EMAIL,
            )

        try:
            normalized_email = self._normalize_email(email)
            redirect_url = self._get_redirect_url("/")  # Startseite nach Reset

            self.sb.auth.reset_password_email(
                normalized_email,
                options={"redirect_to": redirect_url},
            )
            logger.info(f"Passwort-Reset-E-Mail gesendet an: {normalized_email}")
            return AuthResult(
                success=True,
                message=(
                    f"Eine E-Mail wurde an {email} gesendet.\n\n"
                    "Bitte prüfen Sie auch Ihren Spam-Ordner."
                ),
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Senden der Passwort-Reset-E-Mail: {e}", exc_info=True)
            return AuthResult(
                success=False,
                message=f"Fehler: {str(e)[:50]}",
                code=AuthErrorCode.UNKNOWN_ERROR,
            )

    def change_password(self, new_password: str) -> AuthResult:
        """Ändert das Passwort des aktuellen Benutzers.
        
        Args:
            new_password: Neues Passwort (sollte bereits validiert sein)
        
        Returns:
            AuthResult mit Erfolg/Fehler-Status
        
        Note:
            Die Validierung des Passworts sollte vor dem Aufruf dieser Methode
            erfolgen (z.B. mit utils.validators.validate_password).
        """
        # Validierung
        if not new_password:
            return AuthResult(
                success=False,
                message="Passwort darf nicht leer sein.",
                code=AuthErrorCode.INVALID_PASSWORD,
            )

        try:
            self.sb.auth.update_user({"password": new_password})
            logger.info("Passwort erfolgreich geändert")
            return AuthResult(success=True, message="Passwort erfolgreich geändert.")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Fehler beim Ändern des Passworts: {e}", exc_info=True)
            return AuthResult(
                success=False,
                message=f"Fehler beim Ändern des Passworts: {str(e)[:50]}",
                code=AuthErrorCode.UNKNOWN_ERROR,
            )
