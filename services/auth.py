from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from supabase import Client


@dataclass
class AuthResult:
    success: bool
    message: str = ""
    code: Optional[str] = None


class AuthService:
    """Service-Klasse für Authentifizierung und Registrierung."""

    def __init__(self, sb: Client) -> None:
        self.sb = sb

    # ─────────────────────────────────────────────────────────────
    # Login
    # ─────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> AuthResult:
        try:
            res = self.sb.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
            if res and res.user:
                return AuthResult(success=True)
            return AuthResult(success=False, message="Anmeldung fehlgeschlagen.", code="login_failed")
        except Exception as ex:  # noqa: BLE001
            error_str = str(ex).lower()
            if "invalid login credentials" in error_str or "invalid credentials" in error_str:
                return AuthResult(success=False, message="E-Mail oder Passwort falsch.", code="invalid_credentials")
            if "email not confirmed" in error_str:
                return AuthResult(success=False, message="Bitte bestätigen Sie zuerst Ihre E-Mail.", code="email_not_confirmed")
            return AuthResult(success=False, message=f"Fehler: {str(ex)[:50]}", code="unknown_error")

    # ─────────────────────────────────────────────────────────────
    # Registrierung
    # ─────────────────────────────────────────────────────────────

    def register(self, email: str, password: str, username: str) -> AuthResult:
        try:
            # Redirect-URL für E-Mail-Bestätigung bestimmen
            if os.getenv("FLY_APP_NAME"):
                redirect_url = "https://petbuddy.fly.dev/login"
            else:
                redirect_url = "http://localhost:8550/login"

            res = self.sb.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "display_name": username,
                        },
                        "email_redirect_to": redirect_url,
                    },
                }
            )

            if not res or not res.user:
                return AuthResult(success=False, message="Fehler!", code="unknown_error")

            # Prüfen ob E-Mail bereits registriert ist
            if not res.user.identities or len(res.user.identities) == 0:
                return AuthResult(
                    success=False,
                    message="E-Mail bereits registriert. Bitte melden Sie sich an!",
                    code="email_exists",
                )

            # Prüfen ob E-Mail-Bestätigung erforderlich ist
            if res.user.confirmed_at is None:
                return AuthResult(
                    success=True,
                    message="Bestätigungs-E-Mail gesendet! Bitte prüfen Sie Ihr Postfach.",
                    code="confirm_email",
                )

            return AuthResult(success=True)

        except Exception as ex:  # noqa: BLE001
            error_str = str(ex).lower()
            if "already registered" in error_str or "user already registered" in error_str:
                return AuthResult(
                    success=False,
                    message="E-Mail bereits registriert.",
                    code="email_exists",
                )
            return AuthResult(
                success=False,
                message=f"Fehler: {str(ex)[:50]}",
                code="unknown_error",
            )

    # ─────────────────────────────────────────────────────────────
    # Logout
    # ─────────────────────────────────────────────────────────────

    def logout(self) -> AuthResult:
        try:
            self.sb.auth.sign_out()
            return AuthResult(success=True, message="Abgemeldet.")
        except Exception as ex:  # noqa: BLE001
            return AuthResult(success=False, message=f"Fehler: {str(ex)[:50]}")

    # ─────────────────────────────────────────────────────────────
    # Passwort zurücksetzen
    # ─────────────────────────────────────────────────────────────

    def send_reset_password_email(self, email: str) -> AuthResult:
        try:
            if os.getenv("FLY_APP_NAME"):
                redirect_url = "https://petbuddy.fly.dev/"
            else:
                redirect_url = "http://localhost:8550/"

            self.sb.auth.reset_password_email(
                email.lower(),
                options={"redirect_to": redirect_url},
            )
            return AuthResult(
                success=True,
                message=(
                    f"Eine E-Mail wurde an {email} gesendet.\n\n"
                    "Bitte prüfen Sie auch Ihren Spam-Ordner."
                ),
            )
        except Exception as ex:  # noqa: BLE001
            return AuthResult(
                success=False,
                message=f"Fehler: {str(ex)[:50]}",
            )


