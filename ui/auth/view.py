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
    create_register_username_field,
    create_login_button,
    create_register_button,
    create_continue_button,
    create_logout_button,
    create_theme_toggle,
    create_registration_modal,
    create_login_card,
)


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
        self.on_auth_success = on_auth_success
        self.on_continue_without_account = on_continue_without_account
        
        # UI-Komponenten (werden in build() initialisiert)
        self._login_email: Optional[ft.TextField] = None
        self._login_pwd: Optional[ft.TextField] = None
        self._login_info: Optional[ft.Text] = None
        self._reg_email: Optional[ft.TextField] = None
        self._reg_pwd: Optional[ft.TextField] = None
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
        
        try:
            self._show_login_message("🔐 Anmeldung läuft...", ft.Colors.BLUE)
            
            res = self.sb.auth.sign_in_with_password({
                "email": email, 
                "password": password
            })
            
            if res.user:
                self._show_login_message("✅ Erfolgreich!", ft.Colors.GREEN)
                if self.on_auth_success:
                    self.on_auth_success()
            else:
                self._show_login_message("❌ Anmeldung fehlgeschlagen.", ft.Colors.RED)
                
        except Exception as ex:
            self._handle_login_error(ex)

    async def _register(self):
        """Führt die Registrierung durch."""
        email = (self._reg_email.value or "").strip()
        password = (self._reg_pwd.value or "").strip()
        username = (self._reg_username.value or "").strip()
        
        # Validierung
        error = validate_register_form(email, password, username)
        if error:
            self._show_reg_message(error, ft.Colors.RED)
            return
        
        try:
            self._show_reg_message("📝 Registrierung läuft...", ft.Colors.BLUE)
            
            res = self.sb.auth.sign_up({
                "email": email, 
                "password": password,
                "options": {
                    "data": {
                        "display_name": username
                    }
                }
            })
            
            if res.user:
                # Prüfen ob E-Mail bereits registriert ist
                if not res.user.identities or len(res.user.identities) == 0:
                    self._show_reg_message("❌ E-Mail bereits registriert.", ft.Colors.RED)
                    return
                
                print(f"✅ User registriert: {res.user.id}")
                
                # Prüfen ob E-Mail-Bestätigung erforderlich ist
                if res.user.confirmed_at is None:
                    self._show_reg_message(
                        "✅ Bestätigungs-E-Mail gesendet! Bitte prüfe dein Postfach.",
                        ft.Colors.GREEN
                    )
                    await asyncio.sleep(3)
                    self._close_modal()
            else:
                self._show_reg_message("❌ Fehler!", ft.Colors.RED)
                
        except Exception as ex:
            self._handle_register_error(ex)

    async def _logout(self):
        """Meldet den Benutzer ab."""
        try:
            self.sb.auth.sign_out()
            self._show_login_message("✅ Abgemeldet.", ft.Colors.GREEN)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    # Error Handler
    # ─────────────────────────────────────────────────────────────

    def _handle_login_error(self, ex: Exception):
        """Behandelt Login-Fehler."""
        error_str = str(ex).lower()
        if "invalid login credentials" in error_str or "invalid credentials" in error_str:
            self._show_login_message("❌ E-Mail oder Passwort falsch.", ft.Colors.RED)
        elif "email not confirmed" in error_str:
            self._show_login_message("❌ Bitte bestätige zuerst deine E-Mail.", ft.Colors.ORANGE)
        else:
            self._show_login_message(f"❌ Fehler: {str(ex)[:50]}", ft.Colors.RED)

    def _handle_register_error(self, ex: Exception):
        """Behandelt Registrierungs-Fehler."""
        error_str = str(ex).lower()
        if "already registered" in error_str:
            self._show_reg_message("❌ E-Mail bereits registriert.", ft.Colors.RED)
        else:
            self._show_reg_message(f"❌ Fehler: {str(ex)[:50]}", ft.Colors.RED)

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
        self._reg_modal_bg.visible = True
        if self._reg_modal_bg not in self.page.overlay:
            self.page.overlay.append(self._reg_modal_bg)
        self.page.update()

    def _close_modal(self, e=None):
        """Schließt das Registrierungs-Modal und setzt Felder zurück."""
        if self._reg_modal_bg in self.page.overlay:
            self.page.overlay.remove(self._reg_modal_bg)
        
        # Felder zurücksetzen
        if self._reg_email:
            self._reg_email.value = ""
        if self._reg_pwd:
            self._reg_pwd.value = ""
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
        self._login_info = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        
        # Registrierungs-Formular Felder
        self._reg_email = create_register_email_field()
        self._reg_pwd = create_register_password_field()
        self._reg_username = create_register_username_field()
        self._reg_info = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        
        # Theme-Toggle
        self._theme_icon = create_theme_toggle(is_dark, self._toggle_theme)
        
        # Registrierungs-Modal
        self._reg_modal_card = create_registration_modal(
            email_field=self._reg_email,
            password_field=self._reg_pwd,
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
            "Melde dich an, um deine Haustierhilfe zu\nstarten 🐾",
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
