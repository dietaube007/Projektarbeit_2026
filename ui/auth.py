# Login-/Registrier-Bereich

import flet as ft
import asyncio
import re
from typing import Callable, Optional


# ─────────────────────────────────────────────────────────────────
# Konstanten
# ─────────────────────────────────────────────────────────────────

# Validierung
MIN_PASSWORD_LENGTH = 8
MAX_DISPLAY_NAME_LENGTH = 30
SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Farben - Minimalistisches Design
PRIMARY_COLOR = "#5B6EE1"       # Blau für Buttons
BACKGROUND_COLOR = "#F5F7FA"    # Heller grauer Hintergrund
CARD_COLOR = ft.Colors.WHITE     # Weiße Card
TEXT_PRIMARY = "#1F2937"         # Dunkler Text
TEXT_SECONDARY = "#6B7280"       # Grauer Text
BORDER_COLOR = "#E5E7EB"         # Hellgrauer Rahmen
BUTTON_SUCCESS = "#5B6EE1"       # Grün für Registrieren


class AuthView:

    # Authentifizierungs-View mit Login, Registrierung und Theme-Toggle.

    def __init__(self, page: ft.Page, sb, on_auth_success: Optional[Callable] = None, on_continue_without_account: Optional[Callable] = None):
        
        # Initialisiert die AuthView.

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
    
    # ─────────────────────────────────────────────────────────────
    # Validierungs-Methoden
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        # Prüft ob die E-Mail-Adresse gültig ist.
        return bool(re.match(EMAIL_REGEX, email))
    
    @staticmethod
    def _validate_password(password: str) -> Optional[str]:
        # Validiert das Passwort. Gibt Fehlermeldung oder None zurück.
        if len(password) < MIN_PASSWORD_LENGTH:
            return f"❌ Passwort mind. {MIN_PASSWORD_LENGTH} Zeichen."
        if not any(c.isdigit() for c in password):
            return "❌ Passwort muss mind. eine Ziffer enthalten."
        if not any(c in SPECIAL_CHARS for c in password):
            return "❌ Passwort muss mind. ein Sonderzeichen enthalten."
        return None
    
    # ─────────────────────────────────────────────────────────────
    # Authentifizierungs-Methoden
    # ─────────────────────────────────────────────────────────────
    
    async def _login(self):
        # Führt die Anmeldung durch.
        email = (self._login_email.value or "").strip()
        password = (self._login_pwd.value or "").strip()
        
        # Validierung
        if not email:
            self._show_login_message("❌ Bitte E-Mail eingeben.", ft.Colors.RED)
            return
        
        if not self._is_valid_email(email):
            self._show_login_message("❌ Bitte gültige E-Mail eingeben.", ft.Colors.RED)
            return
        
        if not password:
            self._show_login_message("❌ Bitte Passwort eingeben.", ft.Colors.RED)
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
            error_str = str(ex).lower()
            if "invalid login credentials" in error_str or "invalid credentials" in error_str:
                self._show_login_message("❌ E-Mail oder Passwort falsch.", ft.Colors.RED)
            elif "email not confirmed" in error_str:
                self._show_login_message("❌ Bitte bestätige zuerst deine E-Mail.", ft.Colors.ORANGE)
            else:
                self._show_login_message(f"❌ Fehler: {str(ex)[:50]}", ft.Colors.RED)
    
    async def _register(self):
        # Führt die Registrierung durch.
        email = (self._reg_email.value or "").strip()
        password = (self._reg_pwd.value or "").strip()
        username = (self._reg_username.value or "").strip()
        
        # Validierung
        if not email:
            self._show_reg_message("❌ Bitte E-Mail eingeben.", ft.Colors.RED)
            return
        
        if not self._is_valid_email(email):
            self._show_reg_message("❌ Bitte gültige E-Mail eingeben.", ft.Colors.RED)
            return
        
        if not password:
            self._show_reg_message("❌ Bitte Passwort eingeben.", ft.Colors.RED)
            return
        
        password_error = self._validate_password(password)
        if password_error:
            self._show_reg_message(password_error, ft.Colors.RED)
            return
        
        if not username:
            self._show_reg_message("❌ Bitte Anzeigename eingeben.", ft.Colors.RED)
            return
        
        if len(username) > MAX_DISPLAY_NAME_LENGTH:
            self._show_reg_message(f"❌ Anzeigename max. {MAX_DISPLAY_NAME_LENGTH} Zeichen.", ft.Colors.RED)
            return
        
        try:
            self._show_reg_message("📝 Registrierung läuft...", ft.Colors.BLUE)
            
            # display_name wird in user_metadata gespeichert für den Trigger
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
                # Bei bereits registrierten E-Mails ist identities leer
                if not res.user.identities or len(res.user.identities) == 0:
                    self._show_reg_message("❌ E-Mail bereits registriert.", ft.Colors.RED)
                    return
                
                # User wird automatisch durch Database Trigger erstellt
                print(f"✅ User registriert: {res.user.id}")
                
                # Prüfen ob E-Mail-Bestätigung erforderlich ist
                if res.user.confirmed_at is None:
                    # E-Mail-Bestätigung aktiviert in Supabase
                    self._show_reg_message("✅ Bestätigungs-E-Mail gesendet! Bitte prüfe dein Postfach.", ft.Colors.GREEN)
                else:
                    # Keine E-Mail-Bestätigung erforderlich
                    self._show_reg_message("✅ Erfolgreich! Du kannst dich jetzt anmelden.", ft.Colors.GREEN)
                
                await asyncio.sleep(3)
                self._close_modal()
            else:
                self._show_reg_message("❌ Fehler!", ft.Colors.RED)
                
        except Exception as ex:
            error_str = str(ex).lower()
            if "already registered" in error_str:
                self._show_reg_message("❌ E-Mail bereits registriert.", ft.Colors.RED)
            else:
                self._show_reg_message(f"❌ Fehler: {str(ex)[:50]}", ft.Colors.RED)
    
    async def _logout(self):
        # Meldet den Benutzer ab.
        try:
            self.sb.auth.sign_out()
            self._show_login_message("✅ Abgemeldet.", ft.Colors.GREEN)
        except:
            pass
    
    # ─────────────────────────────────────────────────────────────
    # UI-Hilfsmethoden
    # ─────────────────────────────────────────────────────────────
    
    def _show_login_message(self, message: str, color):
        # Zeigt eine Nachricht im Login-Bereich.
        self._login_info.value = message
        self._login_info.color = color
        self.page.update()
    
    def _show_reg_message(self, message: str, color):
        # Zeigt eine Nachricht im Registrierungs-Bereich.
        self._reg_info.value = message
        self._reg_info.color = color
        self.page.update()
    
    def _toggle_theme(self, e):
        # Wechselt zwischen Hell- und Dunkelmodus.
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
        
        self.page.update()
    
    def _open_modal(self, e=None):
        # Öffnet das Registrierungs-Modal.
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
        # Prüft, ob ein Benutzer angemeldet ist.
        try:
            user = self.sb.auth.get_user()
            return user is not None and user.user is not None
        except:
            return False
    
    def get_current_user(self):
        # Gibt den aktuell angemeldeten Benutzer zurück.
        try:
            return self.sb.auth.get_user()
        except:
            return None
    
    def build(self) -> ft.Control:
        # Erstellt und gibt die komplette Auth-UI zurück.

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Login-Formular - minimalistisch
        self._login_email = ft.TextField(
            label="E-Mail",
            hint_text="beispiel@mail.com",
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=8,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY_COLOR,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        
        self._login_pwd = ft.TextField(
            label="Passwort",
            hint_text="••••••••",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY_COLOR,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )
        
        self._login_info = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        
        # Registrierungs-Formular
        self._reg_email = ft.TextField(
            label="E-Mail",
            hint_text="deine@email.de",
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=12,
        )
        
        self._reg_pwd = ft.TextField(
            label="Passwort",
            hint_text="Mind. 8 Zeichen, Ziffer & Sonderzeichen",
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )
        
        self._reg_username = ft.TextField(
            label="Anzeigename",
            hint_text="Dein Name",
            border_radius=12,
            max_length=MAX_DISPLAY_NAME_LENGTH,
        )
        
        self._reg_info = ft.Text("", size=12, weight=ft.FontWeight.W_500)
        
        # Theme-Toggle
        self._theme_icon = ft.IconButton(
            icon=ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE,
            on_click=self._toggle_theme,
            tooltip="Theme wechseln",
            icon_color=ft.Colors.WHITE if is_dark else TEXT_SECONDARY,
        )
        
        # Registrierungs-Modal
        self._reg_modal_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Registrierung", size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(ft.Icons.CLOSE, on_click=self._close_modal)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                self._reg_email,
                ft.Container(height=8),
                self._reg_pwd,
                ft.Container(height=8),
                self._reg_username,
                ft.Container(height=12),
                self._reg_info,
                ft.Container(height=12),
                ft.Row([
                    ft.TextButton("Abbrechen", on_click=self._close_modal),
                    ft.ElevatedButton(
                        "Registrieren",
                        on_click=lambda e: self.page.run_task(self._register),
                        bgcolor=BUTTON_SUCCESS,
                        color=ft.Colors.WHITE,
                    ),
                ], alignment=ft.MainAxisAlignment.END),
            ], tight=True, spacing=0),
            padding=24,
            border_radius=16,
            bgcolor=ft.Colors.GREY_800 if is_dark else CARD_COLOR,
            width=400,
            shadow=ft.BoxShadow(
                blur_radius=20,
                spread_radius=3,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            ),
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
        login_btn = ft.ElevatedButton(
            "Einloggen",
            on_click=lambda e: self.page.run_task(self._login),
            expand=True,
            height=48,
            bgcolor=PRIMARY_COLOR,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=24),
            ),
        )
        
        register_btn = ft.TextButton(
            "Registrieren",
            on_click=self._open_modal,
            style=ft.ButtonStyle(color=PRIMARY_COLOR),
        )
        
        logout_btn = ft.TextButton(
            "Abmelden",
            icon=ft.Icons.LOGOUT,
            on_click=lambda e: self.page.run_task(self._logout),
            style=ft.ButtonStyle(color=ft.Colors.RED_400),
        )
        
        # Ohne Account fortsetzen (zentriert)
        continue_btn = ft.TextButton(
            "Ohne Account fortsetzen",
            on_click=lambda e: (self.on_continue_without_account() if self.on_continue_without_account else None),
            style=ft.ButtonStyle(color=PRIMARY_COLOR),
        )
        
        # Login-Card
        card_content = [
            self._login_email,
            ft.Container(height=16),
            self._login_pwd,
            ft.Container(height=24),
            login_btn,
            ft.Container(height=16),
            self._login_info,
            ft.Container(height=8),
            ft.Row(
                [ft.Text("Noch kein Konto?", color=TEXT_SECONDARY), register_btn], 
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=12),
            ft.Row([continue_btn], alignment=ft.MainAxisAlignment.CENTER),
        ]
        
        # Logout-Button nur anzeigen wenn eingeloggt
        if self.is_logged_in():
            card_content.append(logout_btn)
        
        self._form_card = ft.Container(
            content=ft.Column(card_content, tight=True, spacing=0),
            padding=40,
            border_radius=20,
            bgcolor=ft.Colors.GREY_800 if is_dark else CARD_COLOR,
            width=420,
            shadow=ft.BoxShadow(
                blur_radius=40,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )
        
        # Pfote-Icon
        paw_icon = ft.Container(
            content=ft.Icon(
                ft.Icons.PETS,
                size=40,
                color=PRIMARY_COLOR,
            ),
            bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
            padding=16,
            border_radius=50,
        )
        
        # Haupt-Layout - vertikal zentriert, minimalistisch
        self._background = ft.Container(
            content=ft.Stack([
                # Hauptinhalt zentriert
                ft.Column([
                    ft.Container(expand=True),  # Spacer oben
                    ft.Column([
                        paw_icon,
                        ft.Container(height=24),
                        ft.Text(
                            "Willkommen bei",
                            size=16,
                            color=TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "PetBuddy",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY if not is_dark else ft.Colors.WHITE,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Melde dich an, um deine Haustierhilfe zu\nstarten 🐾",
                            size=14,
                            color=TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=32),
                        self._form_card,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(expand=True),  # Spacer unten
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

