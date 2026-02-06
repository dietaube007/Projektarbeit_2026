"""
Authentifizierungs-View mit Login, Registrierung und Theme-Toggle.
"""

from typing import Callable, Optional

import flet as ft

from ui.constants import (
    PRIMARY_COLOR,
    TEXT_SECONDARY,
    MESSAGE_TYPE_ERROR,
    MESSAGE_TYPE_SUCCESS,
    MESSAGE_TYPE_INFO,
    MESSAGE_COLOR_MAP,
    MESSAGE_COLOR_INFO,
)
from services.account import AuthService, ProfileService
from ui.theme import ThemeManager, get_theme_color
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
    create_registration_error_banner,
    create_registration_modal,
    create_login_card,
)
from .handlers import handle_login, handle_logout, handle_register, show_password_reset_dialog_feature


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
        
        # UI-Komponenten-Referenzen (werden in _init_ui_elements() initialisiert)
        self._login_email: Optional[ft.TextField] = None
        self._login_pwd: Optional[ft.TextField] = None
        self._login_info: Optional[ft.Text] = None
        self._reg_email: Optional[ft.TextField] = None
        self._reg_pwd: Optional[ft.TextField] = None
        self._reg_pwd_confirm: Optional[ft.TextField] = None
        self._reg_username: Optional[ft.TextField] = None
        self._reg_info: Optional[ft.Text] = None
        self._reg_error_banner: Optional[ft.Container] = None
        self._reg_error_text: Optional[ft.Text] = None
        self._form_card: Optional[ft.Container] = None
        self._reg_modal_card: Optional[ft.Container] = None
        self._reg_modal_bg: Optional[ft.Container] = None
        self._background: Optional[ft.Container] = None
        self._theme_icon: Optional[ft.IconButton] = None
        self._welcome_text: Optional[ft.Text] = None
        self._title_text: Optional[ft.Text] = None
        # Button-Referenzen für Deaktivierung beim Modal-Öffnen
        self._login_btn: Optional[ft.ElevatedButton] = None
        self._register_btn: Optional[ft.TextButton] = None
        self._continue_btn: Optional[ft.TextButton] = None
        self._forgot_password_btn: Optional[ft.TextButton] = None
        
        # UI wird sofort initialisiert (konsistent mit discover/view.py)
        self._init_ui_elements()

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
            on_success_callback=self._on_login_success,
        )
    
    def _on_login_success(self) -> None:
        """Wird nach erfolgreichem Login aufgerufen."""
        self._update_login_card()
        if self.on_auth_success:
            self.on_auth_success()

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
        self._update_login_card()

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
        if message_type == MESSAGE_TYPE_ERROR:
            # Fehler als roter Banner oben anzeigen
            if self._reg_error_text:
                self._reg_error_text.value = message
            if self._reg_error_banner:
                self._reg_error_banner.visible = True
            # Info-Text leeren
            if self._reg_info:
                self._reg_info.value = ""
        else:
            # Info/Success als Text unten anzeigen
            if self._reg_error_banner:
                self._reg_error_banner.visible = False
            if self._reg_error_text:
                self._reg_error_text.value = ""
            self._show_message(self._reg_info, message, message_type)
        
        self.page.update()

    def _update_login_card(self) -> None:
        """Aktualisiert die Login-Card basierend auf dem aktuellen Login-Status."""
        if not self._form_card:
            return
        
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Login-Felder zurücksetzen, wenn nicht eingeloggt
        if not self.is_logged_in():
            if self._login_email:
                self._login_email.value = ""
                self._login_email.visible = True
            if self._login_pwd:
                self._login_pwd.value = ""
                self._login_pwd.visible = True
        
        # Buttons neu erstellen
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
        
        # Neue Card erstellen und Content aktualisieren
        new_card = create_login_card(
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
        
        # Card-Content und Eigenschaften aktualisieren
        self._form_card.content = new_card.content
        self._form_card.bgcolor = new_card.bgcolor
        self._form_card.shadow = new_card.shadow
        
        self.page.update()

    def _update_ui_colors(self, is_dark: bool):
        """Aktualisiert View-spezifische UI-Farben nach Theme-Wechsel.

        Args:
            is_dark: True wenn Dark-Modus aktiv, False für Light-Modus
        """
        # Icon-Farbe
        if self._theme_icon:
            self._theme_icon.icon_color = ft.Colors.WHITE if is_dark else ft.Colors.GREY_700

        # Hintergrund-Farben aktualisieren
        if self._background:
            self._background.bgcolor = get_theme_color("background", is_dark)
        if self._form_card:
            self._form_card.bgcolor = get_theme_color("card", is_dark)
        if self._reg_modal_card:
            self._reg_modal_card.bgcolor = get_theme_color("card", is_dark)

        # Überschriften-Farben aktualisieren
        if self._welcome_text:
            self._welcome_text.color = get_theme_color("text_secondary", is_dark)
        if self._title_text:
            self._title_text.color = get_theme_color("text_primary", is_dark)
    
    def _open_modal(self, e=None):
        """Öffnet das Registrierungs-Modal."""
        # Login-Felder deaktivieren damit Tab nicht dorthin springt
        if self._login_email:
            self._login_email.disabled = True
        if self._login_pwd:
            self._login_pwd.disabled = True
        
        # Alle Buttons im Hintergrund deaktivieren damit Tab nicht dorthin springt
        if self._login_btn:
            self._login_btn.disabled = True
        if self._register_btn:
            self._register_btn.disabled = True
        if self._continue_btn:
            self._continue_btn.disabled = True
        if self._forgot_password_btn:
            self._forgot_password_btn.disabled = True
        if self._theme_icon:
            self._theme_icon.disabled = True
        
        # Fehler-Banner beim Öffnen verstecken
        if self._reg_error_banner:
            self._reg_error_banner.visible = False
        if self._reg_error_text:
            self._reg_error_text.value = ""
        if self._reg_info:
            self._reg_info.value = ""
        
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
        
        # Alle Buttons im Hintergrund wieder aktivieren
        if self._login_btn:
            self._login_btn.disabled = False
        if self._register_btn:
            self._register_btn.disabled = False
        if self._continue_btn:
            self._continue_btn.disabled = False
        if self._forgot_password_btn:
            self._forgot_password_btn.disabled = False
        if self._theme_icon:
            self._theme_icon.disabled = False
        
        # Fehler-Banner verstecken
        if self._reg_error_banner:
            self._reg_error_banner.visible = False
        if self._reg_error_text:
            self._reg_error_text.value = ""
        
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

    def _init_ui_elements(self) -> None:
        """Initialisiert alle UI-Elemente."""
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
        
        # Fehler-Banner für Registrierung (aus Komponente)
        self._reg_error_banner, self._reg_error_text = create_registration_error_banner()
        
        # Theme-Toggle
        self._theme_icon = self.theme_manager.create_toggle_button(
            on_after_toggle=self._update_ui_colors,
        )
        
        # Registrierungs-Modal
        self._reg_modal_card = create_registration_modal(
            email_field=self._reg_email,
            password_field=self._reg_pwd,
            password_confirm_field=self._reg_pwd_confirm,
            username_field=self._reg_username,
            error_banner=self._reg_error_banner,
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
        
        # Button-Referenzen speichern (für Deaktivierung beim Modal-Öffnen)
        self._login_btn = login_btn
        self._register_btn = register_btn
        self._continue_btn = continue_btn
        self._forgot_password_btn = forgot_password_btn
        
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
            color=get_theme_color("text_secondary", is_dark),
        )
        self._title_text = ft.Text(
            "PetBuddy",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=get_theme_color("text_primary", is_dark),
        )
        # Haupt-Layout
        self._background = ft.Container(
            content=ft.Stack([
                ft.Column([
                    ft.Container(height=40),
                    ft.Column([
                        paw_icon,
                        ft.Container(height=16),
                        self._welcome_text,
                        self._title_text,
                        ft.Container(height=24),
                        self._form_card,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True,
                   scroll=ft.ScrollMode.AUTO),
                ft.Container(
                    content=ft.Row([self._theme_icon], spacing=8),
                    top=0,
                    right=0,
                    padding=ft.padding.only(
                        top=8,
                        right=0
                    ),
                    alignment=ft.alignment.top_right,
                ),
            ]),
            bgcolor=get_theme_color("background", is_dark),
            expand=True,
        )
    
    def build(self) -> ft.Control:
        """Erstellt und gibt die komplette Auth-UI zurück."""
        return self._background
