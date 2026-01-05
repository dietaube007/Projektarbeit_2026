"""
PetBuddy App - Hauptklasse der Anwendung.

Diese Klasse steuert:
- Initialisierung und Theme
- Navigation zwischen Tabs
- Login/Logout Workflow
- UI-Bereiche (Start, Melden, Profil)
"""

from __future__ import annotations

import os
from typing import Optional, Callable
import flet as ft

from services.supabase_client import get_client
from supabase import Client
from utils.logging_config import get_logger

logger = get_logger(__name__)
from ui.theme import ThemeManager, soft_card
from ui.post_form import PostForm
from ui.discover import DiscoverView
from ui.profile import ProfileView
from ui.auth import AuthView
from ui.constants import (
    WINDOW_MIN_WIDTH,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_HEIGHT,
    PRIMARY_COLOR,
)

from app.dialogs import (
    create_login_required_dialog,
    create_favorite_login_dialog,
    create_login_banner,
)
from app.navigation import (
    TAB_START,
    TAB_MELDEN,
    TAB_PROFIL,
    create_navigation_bar,
    create_app_bar,
)


class PetBuddyApp:
    """Hauptklasse der PetBuddy-Anwendung."""
    
    def __init__(self, page: ft.Page) -> None:
        """Initialisiert die Anwendung.
        
        Args:
            page: Flet Page-Instanz
        """
        self.page: ft.Page = page
        self.current_tab: int = TAB_START
        self.sb: Optional[Client] = None
        self.theme_manager: Optional[ThemeManager] = None
        self.is_logged_in: bool = False
        # Merkt sich gewünschten Tab nach Login
        self.pending_tab_after_login: Optional[int] = None
        
        # UI-Komponenten
        self.body: ft.Container = ft.Container(padding=16, expand=True)
        self.nav: Optional[ft.NavigationBar] = None
        self.start_section: Optional[ft.Control] = None
        self.post_form: Optional[PostForm] = None
        self.discover_view: Optional[DiscoverView] = None
        self.profile_view: Optional[ProfileView] = None
        self.auth_view: Optional[AuthView] = None
    
    # ════════════════════════════════════════════════════════════════════
    # INITIALISIERUNG
    # ════════════════════════════════════════════════════════════════════
    
    def initialize(self) -> bool:
        """Initialisiert die Seite und Supabase-Client."""
        try:
            self.page.title = "PetBuddy"
            self.page.padding = 0
            self.page.scroll = ft.ScrollMode.ADAPTIVE
            self.page.window_min_width = WINDOW_MIN_WIDTH
            self.page.window_width = WINDOW_DEFAULT_WIDTH
            self.page.window_height = WINDOW_DEFAULT_HEIGHT

            # Routing einrichten
            self.page.on_route_change = self._handle_route_change
            
            # Theme anwenden
            self.theme_manager = ThemeManager(self.page)
            self.theme_manager.apply_theme("light")
            
            # Supabase-Client initialisieren
            self.sb = get_client()


            return True
            
        except Exception as e:
            self._show_error(f"Fehler beim Laden: {str(e)}")
            return False
    
    def _handle_route_change(self, e: ft.RouteChangeEvent) -> None:
        """Behandelt Routenänderungen.
        
        Args:
            e: RouteChangeEvent mit der neuen Route
        """
        route = e.route or "/"
        logger.info(f"Route geändert: {route}")
        
        # Route verarbeiten
        self._navigate_to(route)
    
    def _navigate_to(self, route: str) -> None:
        """Navigiert zu einer bestimmten Route.
        
        Args:
            route: Die Ziel-Route (kann Query-Parameter enthalten)
        """
        # Route normalisieren
        if not route or route == "":
            route = "/"
        
        # Route normalisieren
        route_path = route
        if "?" in route:
            route_path = route.split("?")[0]
        
        logger.info(f"Navigiere zu: {route_path} (Query-Parameter: {'Ja' if '?' in route else 'Nein'})")
        
        # Route-Handler aufrufen
        if route_path == "/" or route_path == "/home":
            # Startseite leitet zu /discover weiter
            self.page.go("/discover")
            return
        elif route_path == "/login":
            self._show_login()
        elif route_path == "/discover":
            self._show_discover()
        elif route_path == "/profile":
            self._show_profile()
        elif route_path == "/post/new":
            self._show_new_post()
        else:
            # 404 - Route nicht gefunden
            logger.warning(f"Unbekannte Route: {route_path}")
            self.page.go("/discover")  # Fallback zu Discover
    
    def _show_home(self) -> None:
        """Zeigt die Startseite (Home) mit Discover-View."""
        if not self.discover_view:
            if not self.build_ui():
                return
        
        self.current_tab = TAB_START
        if self.nav:
            self.nav.selected_index = TAB_START
        
        self._show_main_app()
    
    def _show_discover(self) -> None:
        """Zeigt die Discover-Seite."""
        if not self.discover_view:
            if not self.build_ui():
                return
        
        self.current_tab = TAB_START
        if self.nav:
            self.nav.selected_index = TAB_START
        
        self._show_main_app()
    
    def _show_profile(self) -> None:
        """Zeigt die Profil-Seite."""
        if not self.is_logged_in:
            self.page.go("/login")
            return
        
        if not self.profile_view:
            if not self.build_ui():
                return
        
        self.current_tab = TAB_PROFIL
        if self.nav:
            self.nav.selected_index = TAB_PROFIL
        self._show_main_app()
    
    def _show_new_post(self) -> None:
        """Zeigt die Seite zum Erstellen eines neuen Posts."""
        if not self.is_logged_in:
            self.page.go("/login")
            return
        
        if not self.post_form:
            if not self.build_ui():
                return
        
        self.current_tab = TAB_MELDEN
        if self.nav:
            self.nav.selected_index = TAB_MELDEN
        self._show_main_app()
    
        """Zeigt die Seite zum Setzen eines neuen Passworts."""
        from services.profile import ProfileService
        from ui.components import show_success_dialog, show_error_dialog
        
        profile_service = ProfileService(self.sb)
        
        # UI-Elemente
        new_password_field = ft.TextField(
            label="Neues Passwort",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            hint_text="Min. 8 Zeichen, Groß/Klein, Zahl, Sonderzeichen",
            width=350,
            autofocus=True,
        )
        
        confirm_password_field = ft.TextField(
            label="Passwort bestätigen",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            width=350,
        )
        
        error_text = ft.Text("", color=ft.Colors.RED, size=13, visible=False)
        success_text = ft.Text("", color=ft.Colors.GREEN, size=13, visible=False)
        
        def on_save(e):
            new_pw = new_password_field.value or ""
            confirm_pw = confirm_password_field.value or ""
            
            # Validierung
            is_valid, pw_error = profile_service.validate_password(new_pw)
            if not is_valid:
                error_text.value = pw_error
                error_text.visible = True
                success_text.visible = False
                self.page.update()
                return
            
            if new_pw != confirm_pw:
                error_text.value = "Passwörter stimmen nicht überein."
                error_text.visible = True
                success_text.visible = False
                self.page.update()
                return
            
            # Passwort setzen
            success, error_msg = profile_service.update_password(new_pw)
            
            if success:
                error_text.visible = False
                success_text.value = "✅ Passwort erfolgreich geändert!"
                success_text.visible = True
                self.page.update()
                
                # Nach 2 Sekunden zur Startseite
                import time
                time.sleep(2)
                self.page.go("/discover")
            else:
                error_text.value = error_msg or "Fehler beim Speichern."
                error_text.visible = True
                success_text.visible = False
                self.page.update()
        
        def on_cancel(e):
            # Zur Startseite, wenn eingeloggt, sonst zur Login-Seite
            if self.is_logged_in:
                self.page.go("/discover")
            else:
                # Ausloggen und zur Login-Seite
                try:
                    self.sb.auth.sign_out()
                except Exception:
                    pass
                self.is_logged_in = False
                self.page.go("/login")
        
        # Reset-Seite UI
        card_content = [
            ft.Icon(ft.Icons.LOCK_RESET, size=60, color=PRIMARY_COLOR),
            ft.Container(height=16),
            ft.Text("Neues Passwort setzen", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=8),
            ft.Text(
                "Gib dein neues Passwort ein.",
                size=14,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=24),
        ]
        
        card_content.extend([
            new_password_field,
            ft.Container(height=12),
            confirm_password_field,
            ft.Container(height=8),
            error_text,
            success_text,
            ft.Container(height=24),
            ft.Row([
                ft.TextButton("Abbrechen", on_click=on_cancel),
                ft.ElevatedButton(
                    "Passwort speichern",
                    icon=ft.Icons.SAVE,
                    bgcolor=PRIMARY_COLOR,
                    color=ft.Colors.WHITE,
                    on_click=on_save,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
        ])
        
        reset_card = ft.Container(
            content=ft.Column(
                card_content,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=40,
            border_radius=20,
            bgcolor=ft.Colors.WHITE,
            width=450,
            shadow=ft.BoxShadow(
                blur_radius=30,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )
        
        # Seite aufbauen
        self.page.appbar = None
        self.page.navigation_bar = None
        self.page.controls.clear()
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    reset_card,
                    ft.Container(expand=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                bgcolor=ft.Colors.GREY_100,
                expand=True,
            )
        )
        self.page.update()
    
    def _show_error(self, message: str) -> None:
        """Zeigt eine Fehlermeldung in der Snackbar.
        
        Args:
            message: Fehlermeldung die angezeigt werden soll
        """
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # DIALOGE
    # ════════════════════════════════════════════════════════════════════
    
    def _show_login_required_dialog(self, target_tab: int) -> None:
        """Zeigt ein Pop-up Dialog für nicht eingeloggte Benutzer.
        
        Args:
            target_tab: Tab-Index zu dem navigiert werden soll
        """
        def on_login_click(e: ft.ControlEvent) -> None:
            self.page.close(dialog)
            self.pending_tab_after_login = target_tab
            self._show_login()
        
        def on_cancel_click(e: ft.ControlEvent) -> None:
            self.page.close(dialog)
            # Navigation zurücksetzen auf Start
            if self.nav:
                self.nav.selected_index = TAB_START
            self.page.update()
        
        dialog = create_login_required_dialog(
            self.page, target_tab, on_login_click, on_cancel_click
        )
        self.page.open(dialog)
    
    def _show_favorite_login_dialog(self) -> None:
        """Zeigt ein Pop-up Dialog wenn Gast auf Favorit klickt."""
        def on_login_click(e: ft.ControlEvent) -> None:
            self.page.close(dialog)
            self._show_login()
        
        def on_cancel_click(e: ft.ControlEvent) -> None:
            self.page.close(dialog)
        
        dialog = create_favorite_login_dialog(
            self.page, on_login_click, on_cancel_click
        )
        self.page.open(dialog)
    
    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ════════════════════════════════════════════════════════════════════
    
    def render_tab(self) -> None:
        """Rendert den aktuellen Tab."""
        self.body.content = {
            TAB_START: self.start_section,
            TAB_MELDEN: self.post_form.build() if self.post_form else None,
            TAB_PROFIL: self.profile_view.build() if self.profile_view else None,
        }.get(self.current_tab, self.start_section)
        self.page.update()
    
    def go_to_melden_tab(self, _: Optional[ft.ControlEvent] = None) -> None:
        """Navigiert zum Melden-Tab (prüft Login)."""
        if not self.is_logged_in:
            self.page.go("/login")
            return
        self.page.go("/post/new")
    
    def on_post_saved(self, post_id: Optional[str] = None) -> None:
        """Callback nach erfolgreicher Meldung.
        
        Args:
            post_id: Optional ID des erstellten Posts
        """
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)
        # Zur Startseite navigieren
        self.page.go("/")
    
    def _on_nav_change(self, e: ft.ControlEvent) -> None:
        """Event-Handler für Navigationsänderung.
        
        Args:
            e: ControlEvent von der Navigation
        """
        new_tab = e.control.selected_index
        
        # Login erforderlich für Melden und Profil
        if new_tab in [TAB_MELDEN, TAB_PROFIL] and not self.is_logged_in:
            self._show_login_required_dialog(new_tab)
            return
        
        # Navigation zu Routen
        if new_tab == TAB_START:
            self.page.go("/")
        elif new_tab == TAB_MELDEN:
            self.page.go("/post/new")
        elif new_tab == TAB_PROFIL:
            self.page.go("/profile")
        
        self.current_tab = new_tab
        self.render_tab()
    
    def _logout(self) -> None:
        """Meldet den Benutzer ab."""
        try:
            self.sb.auth.sign_out()
            self.is_logged_in = False
            
            # Zur Login-Seite navigieren
            self.page.go("/login")
        except Exception as e:
            logger.error(f"Fehler beim Abmelden: {e}", exc_info=True)
    
    # ════════════════════════════════════════════════════════════════════
    # UI-BEREICHE LADEN
    # ════════════════════════════════════════════════════════════════════
    
    def build_ui(self) -> bool:
        """Baut die UI-Bereiche auf."""
        try:
            # DiscoverView erstellen
            self.discover_view = DiscoverView(
                page=self.page,
                sb=self.sb,
                on_contact_click=None,
                on_melden_click=self.go_to_melden_tab,
                on_login_required=self._show_favorite_login_dialog
            )
            
            # PostForm erstellen
            self.post_form = PostForm(
                page=self.page,
                sb=self.sb,
                on_saved_callback=self.on_post_saved
            )
            
            # ProfileView erstellen
            self.profile_view = ProfileView(
                page=self.page,
                sb=self.sb,
                on_logout=self._logout,
                on_favorites_changed=self._on_favorites_changed,
                on_posts_changed=self._on_posts_changed,
            )
            
            return True
            
        except Exception as e:
            self._show_error(f"Fehler beim Laden der UI: {str(e)}")
            return False
    
    def _on_favorites_changed(self) -> None:
        """Callback wenn sich Favoriten ändern."""
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)
    
    def _on_posts_changed(self) -> None:
        """Callback wenn Meldungen bearbeitet/gelöscht werden."""
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)
    
    def _build_start_section(self) -> ft.Control:
        """Erstellt den Start-Tab mit Suchleiste und Liste."""
        controls = []
        
        # Login-Banner für nicht eingeloggte Benutzer
        if not self.is_logged_in:
            controls.append(create_login_banner(lambda _: self._show_login()))
        
        controls.extend([
            soft_card(
                ft.Column([self.discover_view.search_row], spacing=8),
                pad=12,
                elev=2
            ),
            self.discover_view.build(),
        ])
        
        return ft.Column(
            controls,
            spacing=14,
            expand=True,
        )
    
    # ════════════════════════════════════════════════════════════════════
    # APP STARTEN
    # ════════════════════════════════════════════════════════════════════
    
    def _show_main_app(self) -> None:
        """Zeigt die Hauptanwendung."""
        if not self.build_ui():
            return
        
        # Komponenten erstellen
        self.start_section = self._build_start_section()
        self.nav = create_navigation_bar(self.current_tab, self._on_nav_change)
        
        # Seite leeren und neu aufbauen
        self.page.controls.clear()
        self.page.appbar = create_app_bar(
            self.is_logged_in,
            lambda _: self._logout(),
            self.theme_manager.create_toggle_button()
        )
        self.page.navigation_bar = self.nav
        self.page.add(self.body)
        
        # Tab rendern und Daten laden
        self.render_tab()
        self.page.run_task(self.discover_view.load_posts)
        self.page.update()
    
    def _show_login(self) -> None:
        """Zeigt die Login-Maske."""
        def on_login_success() -> None:
            self.is_logged_in = True
            self.pending_tab_after_login = None
            
            # Zur Startseite navigieren
            self.page.go("/")
        
        def on_continue_without_account() -> None:
            self.is_logged_in = False
            self.pending_tab_after_login = None
            self.page.go("/")
        
        self.auth_view = AuthView(
            page=self.page,
            sb=self.sb,
            on_auth_success=on_login_success,
            on_continue_without_account=on_continue_without_account
        )
        
        # Seite für Login vorbereiten
        self.page.appbar = None
        self.page.navigation_bar = None
        self.page.controls.clear()
        self.page.add(self.auth_view.build())
        self.page.update()
    
    def run(self):
        """Startet die Anwendung."""
        if not self.initialize():
            return
        
        # Prüfen ob bereits eingeloggt (nur für is_logged_in Status)
        try:
            user = self.sb.auth.get_user()
            if user and user.user:
                self.is_logged_in = True
        except Exception:
            self.is_logged_in = False
        
        # Initiale Route setzen und navigieren
        initial_route = self.page.route or "/"
        self._navigate_to(initial_route)

