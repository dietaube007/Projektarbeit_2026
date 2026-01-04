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
            
            # Theme anwenden
            self.theme_manager = ThemeManager(self.page)
            self.theme_manager.apply_theme("light")
            
            # Supabase-Client initialisieren
            self.sb = get_client()
            return True
            
        except Exception as e:
            self._show_error(f"Fehler beim Laden: {str(e)}")
            return False
    
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
            self._show_login_required_dialog(TAB_MELDEN)
            return
        self.current_tab = TAB_MELDEN
        if self.nav:
            self.nav.selected_index = TAB_MELDEN
        self.render_tab()
    
    def on_post_saved(self, post_id: Optional[str] = None) -> None:
        """Callback nach erfolgreicher Meldung.
        
        Args:
            post_id: Optional ID des erstellten Posts
        """
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)
        self.current_tab = TAB_START
        if self.nav:
            self.nav.selected_index = TAB_START
        self.render_tab()
    
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
        
        self.current_tab = new_tab
        self.render_tab()
    
    def _logout(self) -> None:
        """Meldet den Benutzer ab."""
        try:
            self.sb.auth.sign_out()
            self.is_logged_in = False
            
            # Bei Logout im Profil: nach Login dorthin zurück
            if self.current_tab == TAB_PROFIL:
                self.pending_tab_after_login = TAB_PROFIL
            else:
                self.pending_tab_after_login = None
            self._show_login()
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
            self._show_main_app()
            
            # User in DiscoverView aktualisieren
            if self.discover_view:
                self.discover_view.refresh_user()
                self.page.run_task(self.discover_view.load_posts)
            
            # Favoriten im Profil laden
            if self.profile_view:
                self.page.run_task(self.profile_view.load_favorites)
            
            # Zur Startseite navigieren
            self.current_tab = TAB_START
            if self.nav:
                self.nav.selected_index = TAB_START
            self.render_tab()
        
        def on_continue_without_account() -> None:
            self.is_logged_in = False
            self.pending_tab_after_login = None
            self._show_main_app()
            self.current_tab = TAB_START
            if self.nav:
                self.nav.selected_index = TAB_START
            self.render_tab()
        
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
        
        # Prüfen ob bereits eingeloggt
        try:
            user = self.sb.auth.get_user()
            if user and user.user:
                self.is_logged_in = True
        except Exception:
            self.is_logged_in = False
        
        # Startseite zeigen
        self._show_main_app()
