"""
ui/auth/view.py
Authentifizierungs-View mit Login, Registrierung und Theme-Toggle.
"""

import asyncio
from typing import Callable, Optional

import flet as ft

from .constants import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    CARD_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from .validators import validate_login_form, validate_register_form
from .forms import (
    create_login_email_field,
    create_login_password_field,
    create_register_email_field,
    create_register_password_field,
    create_register_password_confirm_field,
    create_register_username_field,
    create_login_button,
    create_register_button,
    create_continue_button,
    create_logout_button,
    create_theme_toggle,
    create_registration_modal,
    create_login_card,
    create_password_reset_dialog,
)
from ui.components import show_success_dialog, show_error_dialog
from utils.validators import validate_email
from services.auth import AuthService, AuthResult


class AuthView:
    """Authentifizierungs-View mit Login, Registrierung und Theme-Toggle."""

    def __init__(
        self,
        page: ft.Page,
        sb,
        on_auth_success: Optional[Callable] = None,
        on_continue_without_account: Optional[Callable] = None,
    ):
        """Initialisiert die AuthView."""
        self.page = page
        self.sb = sb
        self.auth_service = AuthService(sb)
        self.on_auth_success = on_auth_success
        self.on_continue_without_account = on_continue_without_account
        
        # UI-Komponenten (werden in build() initialisiert)
        self._login_email: Optional[ft.TextField] = None
        self._login_pwd: Optional[ft.TextField] = None
        self._login_info: Optional[ft.Text] = None
        self._reg_email: Optional[ft.TextField] = None
        self._reg_pwd: Optional[ft.TextField] = None
        self._reg_pwd_confirm: Optional[ft.TextField] = None
        self._reg_username: Optional[ft.TextField] = None
        self._reg_info: Optional[ft.Text] = None
        self._form_card: Optional[ft.Container] = None
        self._reg_modal_card: Optional[ft.Container] = None
        self._reg_modal_bg: Optional[ft.Container] = None
        self._background: Optional[ft.Container] = None
        self._theme_icon: Optional[ft.IconButton] = None
        self._welcome_text: Optional[ft.Text] = None
        self._title_text: Optional[ft.Text] = None
        self._subtitle_text: Optional[ft.Text] = None

    # ─────────────────────────────────────────────────────────────
    # Authentifizierungs-Methoden
    # ─────────────────────────────────────────────────────────────

    async def _login(self):
        """Führt die Anmeldung durch."""
        email = (self._login_email.value or "").strip()
        password = (self._login_pwd.value or "").strip()
        
        # Validierung
        error = validate_login_form(email, password)
        if error:
            self._show_login_message(error, ft.Colors.RED)
            return
        
        self._show_login_message("Anmeldung läuft...", ft.Colors.BLUE)

        result: AuthResult = self.auth_service.login(email, password)

        if result.success:
            self._show_login_message("Erfolgreich!", ft.Colors.GREEN)
            if self.on_auth_success:
                self.on_auth_success()
        else:
            self._show_login_message(result.message or "Anmeldung fehlgeschlagen.", ft.Colors.RED)

    async def _register(self):
        """Führt die Registrierung durch."""
        email = (self._reg_email.value or "").strip()
        password = (self._reg_pwd.value or "").strip()
        password_confirm = (self._reg_pwd_confirm.value or "").strip()
        username = (self._reg_username.value or "").strip()
        
        # Passwörter vergleichen
        if password != password_confirm:
            self._show_reg_message("Passwörter stimmen nicht überein.", ft.Colors.RED)
            return
        
        # Validierung
        error = validate_register_form(email, password, username)
        if error:
            self._show_reg_message(error, ft.Colors.RED)
            return
        
        self._show_reg_message("Registrierung läuft...", ft.Colors.BLUE)

        result: AuthResult = self.auth_service.register(
            email=email,
            password=password,
            username=username,
        )

        if result.success:
            if result.code == "confirm_email":
                self._show_success_dialog(
                    result.message
                    or "Bestätigungs-E-Mail gesendet! Bitte prüfen Sie Ihr Postfach."
                )
            else:
                self._show_success_dialog("Registrierung erfolgreich.")
        else:
            self._show_reg_message(result.message or "Fehler!", ft.Colors.RED)

    async def _logout(self):
        """Meldet den Benutzer ab."""
        result = self.auth_service.logout()
        if result.success:
            self._show_login_message(result.message or "Abgemeldet.", ft.Colors.GREEN)

    # ─────────────────────────────────────────────────────────────
    # Passwort vergessen
    # ─────────────────────────────────────────────────────────────

    def _show_forgot_password_dialog(self, e=None):
        """Zeigt den Dialog zum Zurücksetzen des Passworts."""
        import os

        email_field = ft.TextField(
            label="E-Mail-Adresse",
            prefix_icon=ft.Icons.EMAIL,
            keyboard_type=ft.KeyboardType.EMAIL,
            width=300,
            hint_text="Ihre registrierte E-Mail",
        )

        # Vorausfüllen mit Login-E-Mail falls vorhanden
        if self._login_email and self._login_email.value:
            email_field.value = self._login_email.value

        error_text = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

        def on_send(e):
            email = (email_field.value or "").strip()

            # Validierung
            is_valid, error_msg = validate_email(email)
            if not is_valid:
                error_text.value = error_msg or "Bitte gültige E-Mail eingeben."
                error_text.visible = True
                self.page.update()
                return

            result = self.auth_service.send_reset_password_email(email)
            if result.success:
                self.page.close(dialog)
                show_success_dialog(
                    self.page,
                    "E-Mail gesendet",
                    result.message,
                )
            else:
                error_text.value = result.message or "Fehler beim Senden der E-Mail."
                error_text.visible = True
                self.page.update()

        def on_cancel(e):
            self.page.close(dialog)

        dialog = create_password_reset_dialog(
            email_field=email_field,
            error_text=error_text,
            on_send=on_send,
            on_cancel=on_cancel,
        )
        self.page.open(dialog)

    # ─────────────────────────────────────────────────────────────
    # UI-Hilfsmethoden
    # ─────────────────────────────────────────────────────────────

    def _show_login_message(self, message: str, color):
        """Zeigt eine Nachricht im Login-Bereich."""
        self._login_info.value = message
        self._login_info.color = color
        self.page.update()

    def _show_reg_message(self, message: str, color):
        """Zeigt eine Nachricht im Registrierungs-Bereich."""
        self._reg_info.value = message
        self._reg_info.color = color
        self.page.update()

    def _show_success_dialog(self, message: str):
        """Zeigt einen Erfolgs-Dialog."""
        show_success_dialog(
            self.page,
            "Erfolg",
            message,
            on_close=self._close_modal
        )

    def _toggle_theme(self, e):
        """Wechselt zwischen Hell- und Dunkelmodus."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Icons aktualisieren
        self._theme_icon.icon = ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE
        self._theme_icon.icon_color = ft.Colors.WHITE if is_dark else TEXT_SECONDARY
        
        # Farben aktualisieren
        self._background.bgcolor = ft.Colors.GREY_900 if is_dark else BACKGROUND_COLOR
        self._form_card.bgcolor = ft.Colors.GREY_800 if is_dark else CARD_COLOR
        self._reg_modal_card.bgcolor = ft.Colors.GREY_800 if is_dark else CARD_COLOR
        
        # Überschriften-Farben aktualisieren
        self._welcome_text.color = ft.Colors.GREY_400 if is_dark else TEXT_SECONDARY
        self._title_text.color = ft.Colors.WHITE if is_dark else TEXT_PRIMARY
        self._subtitle_text.color = ft.Colors.GREY_400 if is_dark else TEXT_SECONDARY
        
        self.page.update()

    def _open_modal(self, e=None):
        """Öffnet das Registrierungs-Modal."""
        # Login-Felder deaktivieren damit Tab nicht dorthin springt
        if self._login_email:
            self._login_email.disabled = True
        if self._login_pwd:
            self._login_pwd.disabled = True
        
        self._reg_modal_bg.visible = True
        if self._reg_modal_bg not in self.page.overlay:
            self.page.overlay.append(self._reg_modal_bg)
        
        self.page.update()
        
        # Fokus auf erstes Feld im Modal (nach update!)
        if self._reg_email:
            self._reg_email.focus()

    def _close_modal(self, e=None):
        """Schließt das Registrierungs-Modal und setzt Felder zurück."""
        if self._reg_modal_bg in self.page.overlay:
            self.page.overlay.remove(self._reg_modal_bg)
        
        # Login-Felder wieder aktivieren
        if self._login_email:
            self._login_email.disabled = False
        if self._login_pwd:
            self._login_pwd.disabled = False
        
        # Felder zurücksetzen
        if self._reg_email:
            self._reg_email.value = ""
        if self._reg_pwd:
            self._reg_pwd.value = ""
        if self._reg_pwd_confirm:
            self._reg_pwd_confirm.value = ""
        if self._reg_username:
            self._reg_username.value = ""
        if self._reg_info:
            self._reg_info.value = ""
        
        self.page.update()

    # ─────────────────────────────────────────────────────────────
    # Öffentliche Methoden
    # ─────────────────────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        """Prüft, ob ein Benutzer angemeldet ist."""
        try:
            user = self.sb.auth.get_user()
            return user is not None and user.user is not None
        except Exception:
            return False

    def get_current_user(self):
        """Gibt den aktuell angemeldeten Benutzer zurück."""
        try:
            return self.sb.auth.get_user()
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        """Erstellt und gibt die komplette Auth-UI zurück."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Login-Formular Felder
        self._login_email = create_login_email_field()
        self._login_pwd = create_login_password_field()
        # Enter-Taste für Login aktivieren
        self._login_email.on_submit = lambda e: self.page.run_task(self._login)
        self._login_pwd.on_submit = lambda e: self.page.run_task(self._login)
        self._login_info = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        
        # Registrierungs-Formular Felder
        self._reg_email = create_register_email_field()
        self._reg_pwd = create_register_password_field()
        self._reg_pwd_confirm = create_register_password_confirm_field()
        self._reg_username = create_register_username_field()
        self._reg_info = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        
        # Theme-Toggle
        self._theme_icon = create_theme_toggle(is_dark, self._toggle_theme)
        
        # Registrierungs-Modal
        self._reg_modal_card = create_registration_modal(
            email_field=self._reg_email,
            password_field=self._reg_pwd,
            password_confirm_field=self._reg_pwd_confirm,
            username_field=self._reg_username,
            info_text=self._reg_info,
            on_register=lambda e: self.page.run_task(self._register),
            on_close=self._close_modal,
            is_dark=is_dark,
        )
        
        self._reg_modal_bg = ft.Container(
            content=ft.Column([
                ft.Container(expand=True, on_click=self._close_modal),
                ft.Row([self._reg_modal_card], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(expand=True, on_click=self._close_modal),
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
            visible=False,
            expand=True,
        )
        
        # Buttons
        login_btn = create_login_button(lambda e: self.page.run_task(self._login))
        register_btn = create_register_button(self._open_modal)
        continue_btn = create_continue_button(
            lambda e: self.on_continue_without_account() if self.on_continue_without_account else None
        )
        logout_btn = create_logout_button(lambda e: self.page.run_task(self._logout))
        forgot_password_btn = ft.TextButton(
            "Passwort vergessen?",
            on_click=self._show_forgot_password_dialog,
            style=ft.ButtonStyle(color=PRIMARY_COLOR),
        )
        
        # Login-Card
        self._form_card = create_login_card(
            email_field=self._login_email,
            password_field=self._login_pwd,
            info_text=self._login_info,
            login_btn=login_btn,
            register_btn=register_btn,
            continue_btn=continue_btn,
            is_logged_in=self.is_logged_in(),
            logout_btn=logout_btn,
            forgot_password_btn=forgot_password_btn,
            is_dark=is_dark,
        )
        
        # Pfote-Icon
        paw_icon = ft.Container(
            content=ft.Icon(ft.Icons.PETS, size=40, color=PRIMARY_COLOR),
            bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
            padding=16,
            border_radius=50,
        )
        
        # Überschriften-Texte
        self._welcome_text = ft.Text(
            "Willkommen bei",
            size=16,
            color=ft.Colors.GREY_400 if is_dark else TEXT_SECONDARY,
        )
        self._title_text = ft.Text(
            "PetBuddy",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE if is_dark else TEXT_PRIMARY,
        )
        self._subtitle_text = ft.Text(
            "Melden Sie sich an, um Ihre Haustierhilfe zu\nstarten.",
            size=14,
            color=ft.Colors.GREY_400 if is_dark else TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Haupt-Layout
        self._background = ft.Container(
            content=ft.Stack([
                # Hauptinhalt zentriert
                ft.Column([
                    ft.Container(expand=True),
                    ft.Column([
                        paw_icon,
                        ft.Container(height=24),
                        self._welcome_text,
                        self._title_text,
                        ft.Container(height=8),
                        self._subtitle_text,
                        ft.Container(height=32),
                        self._form_card,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(expand=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                # Theme-Toggle oben rechts
                ft.Container(
                    content=self._theme_icon,
                    alignment=ft.alignment.top_right,
                    padding=ft.padding.only(top=16, right=16),
                ),
            ]),
            bgcolor=ft.Colors.GREY_900 if is_dark else BACKGROUND_COLOR,
            expand=True,
        )
        
        return self._background
