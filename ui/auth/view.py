"""
Authentifizierungs-View mit Login, Registrierung und Theme-Toggle.

Enthält UI-Komposition und koordiniert Auth-Features.
"""

from typing import Callable, Optional

import flet as ft

from ui.constants import (
    PRIMARY_COLOR,
    BACKGROUND_COLOR,
    CARD_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    MESSAGE_TYPE_ERROR,
    MESSAGE_TYPE_SUCCESS,
    MESSAGE_TYPE_INFO,
    MESSAGE_COLOR_MAP,
    MESSAGE_COLOR_INFO,
    DARK_BACKGROUND,
    DARK_CARD,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
)
from services.account import AuthService, ProfileService
from ui.theme import ThemeManager
from .components import (
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
    create_forgot_password_button,
    create_registration_modal,
    create_login_card,
)
from .features.login import handle_login, handle_logout
from .features.register import handle_register
from .features.password_reset import show_password_reset_dialog_feature


class AuthView:
    """Authentifizierungs-View mit Login, Registrierung und Theme-Toggle."""

    def __init__(
        self,
        page: ft.Page,
        sb,
        on_auth_success: Optional[Callable[[], None]] = None,
        on_continue_without_account: Optional[Callable[[], None]] = None,
    ):
        """Initialisiert die AuthView."""
        self.page = page
        self.sb = sb
        self.auth_service = AuthService(sb)
        self.profile_service = ProfileService(sb)
        self.on_auth_success = on_auth_success
        self.on_continue_without_account = on_continue_without_account
        
        self.theme_manager = ThemeManager(page)
        
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

    def _login(self):
        """Führt die Anmeldung durch."""
        email = (self._login_email.value or "").strip()
        password = (self._login_pwd.value or "").strip()
        handle_login(
            auth_service=self.auth_service,
            email=email,
            password=password,
            show_message_callback=self._show_login_message,
            on_success_callback=self.on_auth_success,
        )

    def _register(self):
        """Führt die Registrierung durch."""
        email = (self._reg_email.value or "").strip()
        password = (self._reg_pwd.value or "").strip()
        password_confirm = (self._reg_pwd_confirm.value or "").strip()
        username = (self._reg_username.value or "").strip()
        
        handle_register(
            auth_service=self.auth_service,
            email=email,
            password=password,
            password_confirm=password_confirm,
            username=username,
            page=self.page,
            show_message_callback=self._show_reg_message,
            on_close_modal_callback=self._close_modal,
        )

    def _logout(self):
        """Meldet den Benutzer ab."""
        handle_logout(
            auth_service=self.auth_service,
            show_message_callback=self._show_login_message,
        )

    # ─────────────────────────────────────────────────────────────
    # Passwort vergessen
    # ─────────────────────────────────────────────────────────────

    def _show_forgot_password_dialog(self, e=None):
        """Zeigt den Dialog zum Zurücksetzen des Passworts."""
        initial_email = None
        if self._login_email and self._login_email.value:
            initial_email = self._login_email.value
        
        show_password_reset_dialog_feature(
            page=self.page,
            auth_service=self.auth_service,
            initial_email=initial_email,
        )

    # ─────────────────────────────────────────────────────────────
    # UI-Hilfsmethoden
    # ─────────────────────────────────────────────────────────────

    def _show_message(
        self,
        info_widget: ft.Text,
        message: str,
        message_type: str = MESSAGE_TYPE_INFO,
    ) -> None:
        """Zeigt eine Nachricht in einem Info-Widget.
        
        Args:
            info_widget: Text-Widget für die Nachricht
            message: Nachrichtentext
            message_type: "error", "success", "info"
        """
        info_widget.value = message
        info_widget.color = MESSAGE_COLOR_MAP.get(message_type, MESSAGE_COLOR_INFO)
        self.page.update()

    def _show_login_message(self, message: str, message_type: str = MESSAGE_TYPE_INFO):
        """Zeigt eine Nachricht im Login-Bereich.
        
        Args:
            message: Nachricht
            message_type: "info", "success", "error"
        """
        self._show_message(self._login_info, message, message_type)

    def _show_reg_message(self, message: str, message_type: str = MESSAGE_TYPE_INFO):
        """Zeigt eine Nachricht im Registrierungs-Bereich.
        
        Args:
            message: Nachricht
            message_type: "info", "success", "error"
        """
        self._show_message(self._reg_info, message, message_type)


    def _update_ui_colors(self, is_dark: bool):
        """Aktualisiert View-spezifische UI-Farben nach Theme-Wechsel.
        
        Args:
            is_dark: True wenn Dark-Modus aktiv, False für Light-Modus
        """
        # Icon-Farbe aktualisieren (ThemeManager aktualisiert Icon/Tooltip bereits)
        if self._theme_icon:
            self._theme_icon.icon_color = DARK_TEXT_PRIMARY if is_dark else TEXT_SECONDARY
        
        # Hintergrund-Farben aktualisieren
        if self._background:
            self._background.bgcolor = DARK_BACKGROUND if is_dark else BACKGROUND_COLOR
        if self._form_card:
            self._form_card.bgcolor = DARK_CARD if is_dark else CARD_COLOR
        if self._reg_modal_card:
            self._reg_modal_card.bgcolor = DARK_CARD if is_dark else CARD_COLOR
        
        # Überschriften-Farben aktualisieren
        if self._welcome_text:
            self._welcome_text.color = DARK_TEXT_SECONDARY if is_dark else TEXT_SECONDARY
        if self._title_text:
            self._title_text.color = DARK_TEXT_PRIMARY if is_dark else TEXT_PRIMARY
        if self._subtitle_text:
            self._subtitle_text.color = DARK_TEXT_SECONDARY if is_dark else TEXT_SECONDARY
    
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
            user = self.profile_service.get_current_user()
            return user is not None and user.user is not None
        except Exception:
            return False

    def get_current_user(self):
        """Gibt den aktuell angemeldeten Benutzer zurück."""
        try:
            return self.profile_service.get_current_user()
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
        self._login_email.on_submit = lambda e: self._login()
        self._login_pwd.on_submit = lambda e: self._login()
        self._login_info = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        
        # Registrierungs-Formular Felder
        self._reg_email = create_register_email_field()
        self._reg_pwd = create_register_password_field()
        self._reg_pwd_confirm = create_register_password_confirm_field()
        self._reg_username = create_register_username_field()
        self._reg_info = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        
        # Theme-Toggle (mit Callback für View-spezifische UI-Updates)
        self._theme_icon = self.theme_manager.create_toggle_button(
            on_after_toggle=self._update_ui_colors,
            icon_color=ft.Colors.WHITE if is_dark else TEXT_SECONDARY,
        )
        
        # Registrierungs-Modal
        self._reg_modal_card = create_registration_modal(
            email_field=self._reg_email,
            password_field=self._reg_pwd,
            password_confirm_field=self._reg_pwd_confirm,
            username_field=self._reg_username,
            info_text=self._reg_info,
            on_register=lambda e: self._register(),
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
        login_btn = create_login_button(lambda e: self._login())
        register_btn = create_register_button(self._open_modal)
        continue_btn = create_continue_button(
            lambda e: self.on_continue_without_account() if self.on_continue_without_account else None
        )
        logout_btn = create_logout_button(lambda e: self._logout())
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
            color=DARK_TEXT_SECONDARY if is_dark else TEXT_SECONDARY,
        )
        self._title_text = ft.Text(
            "PetBuddy",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=DARK_TEXT_PRIMARY if is_dark else TEXT_PRIMARY,
        )
        self._subtitle_text = ft.Text(
            "Melden Sie sich an, um Ihre Haustierhilfe zu\nstarten.",
            size=14,
            color=DARK_TEXT_SECONDARY if is_dark else TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Haupt-Layout
        self._background = ft.Container(
            content=ft.Stack([
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
                ft.Container(
                    content=ft.Row([self._theme_icon], spacing=8),
                    top=16,
                    right=16,
                ),
            ]),
            bgcolor=DARK_BACKGROUND if is_dark else BACKGROUND_COLOR,
            expand=True,
        )
        
        return self._background
