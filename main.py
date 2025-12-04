# PetBuddy - Hauptanwendung.

import os
import flet as ft
from services.supabase_client import get_client
from ui.theme import ThemeManager, soft_card
from ui.post_form import PostForm
from ui.discover import DiscoverView
from ui.profile import ProfileView
from ui.auth import AuthView
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Secret Key für Flet Uploads aus .env laden
os.environ["FLET_SECRET_KEY"] = os.getenv("FLET_SECRET_KEY", "")


class PetBuddyApp:
    # Hauptklasse der PetBuddy-Anwendung.
    
    # Tab-Indices als Klassenkonstanten
    TAB_START = 0
    TAB_MELDEN = 1
    TAB_PROFIL = 2
    
    def __init__(self, page: ft.Page):
        # Initialisiert die Anwendung.
        self.page = page
        self.current_tab = self.TAB_START
        self.sb = None
        self.theme_manager = None
        self.is_logged_in = False
        # Merkt sich gewünschten Tab nach Login
        self.pending_tab_after_login = None
        
        # UI-Komponenten
        self.body = ft.Container(padding=16, expand=True)
        self.nav = None
        self.start_section = None
        self.post_form = None
        self.discover_view = None
        self.profile_view = None
        self.auth_view = None
        
    def initialize(self) -> bool:
        # Initialisiert die Seite und Supabase-Client. Gibt False bei Fehler zurück.
        try:
            self.page.title = "PetBuddy"
            self.page.padding = 0
            self.page.scroll = ft.ScrollMode.ADAPTIVE
            self.page.window_min_width = 420
            self.page.window_width = 1100
            self.page.window_height = 820
            
            # Theme anwenden
            self.theme_manager = ThemeManager(self.page)
            self.theme_manager.apply_theme("light")
            
            # Supabase-Client initialisieren
            self.sb = get_client()
            return True
            
        except Exception as e:
            self._show_error(f"Fehler beim Laden: {str(e)}")
            return False
    
    def _show_error(self, message: str):
        """Zeigt eine Fehlermeldung in der Snackbar."""
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ════════════════════════════════════════════════════════════════════
    
    def render_tab(self):
        # Rendert den aktuellen Tab.
        self.body.content = {
            self.TAB_START: self.start_section,
            self.TAB_MELDEN: self.post_form.build() if self.post_form else None,
            self.TAB_PROFIL: self.profile_view.build() if self.profile_view else None,
        }.get(self.current_tab, self.start_section)
        self.page.update()
    
    def go_to_melden_tab(self, _=None):
        # Navigiert zum Melden-Tab.
        if not self.is_logged_in:
            # Direkt zur Login-Seite wechseln und nach Login zum Melden-Tab
            self.pending_tab_after_login = self.TAB_MELDEN
            self._show_login()
            return
        self.current_tab = self.TAB_MELDEN
        if self.nav:
            self.nav.selected_index = self.TAB_MELDEN
        self.render_tab()
    
    def on_post_saved(self, post_id=None):
        # Callback nach erfolgreicher Meldung - lädt Liste neu und navigiert zur Startseite.
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)
        self.current_tab = self.TAB_START
        if self.nav:
            self.nav.selected_index = self.TAB_START
        self.render_tab()
    
    def _on_nav_change(self, e):
        # Event-Handler für Navigationsänderung.
        new_tab = e.control.selected_index

        # Login erforderlich für Melden und Profil
        if new_tab in [self.TAB_MELDEN, self.TAB_PROFIL] and not self.is_logged_in:
            # Direkt zur Login-Seite wechseln und nach Login zum gewählten Tab
            self.pending_tab_after_login = new_tab
            self._show_login()
            return

        self.current_tab = new_tab
        self.render_tab()
    
    def _logout(self):
        # Meldet den Benutzer ab.
        try:
            self.sb.auth.sign_out()
            self.is_logged_in = False
            # Immer Login-Seite anzeigen nach Logout
            # Optional: Wenn aktuell im Profil, nach Login dorthin zurückkehren
            if self.current_tab == self.TAB_PROFIL:
                self.pending_tab_after_login = self.TAB_PROFIL
            else:
                self.pending_tab_after_login = None
            self._show_login()
            return
        except Exception as e:
            print(f"Fehler beim Abmelden: {e}")
        
    # ════════════════════════════════════════════════════════════════════
    # UI-BEREICHE LADEN
    # ════════════════════════════════════════════════════════════════════
    
    def build_ui(self) -> bool:
        # Baut die UI-Bereiche auf. Gibt False bei Fehler zurück.
        try:
            # DiscoverView erstellen
            self.discover_view = DiscoverView(
                page=self.page,
                sb=self.sb,
                on_contact_click=None,
                on_melden_click=self.go_to_melden_tab
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
                on_logout=self._logout
            )
            
            return True
            
        except Exception as e:
            self._show_error(f"Fehler beim Laden der UI: {str(e)}")
            return False
    
    def _build_login_banner(self) -> ft.Control:
        # Erstellt ein Banner für nicht eingeloggte Benutzer.
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
                    ft.Text(
                        "Melden Sie sich an, um Tiere zu melden oder Ihr Profil zu verwalten.",
                        color=ft.Colors.BLUE_900,
                        size=14,
                        expand=True,
                    ),
                    ft.TextButton(
                        "Anmelden",
                        icon=ft.Icons.LOGIN,
                        on_click=lambda _: self._show_login(),
                    ),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
        )
    
    def _build_start_section(self) -> ft.Control:
        # Erstellt den Start-Tab mit Suchleiste und Liste/Karte.
        controls = []
        
        # Login-Banner für nicht eingeloggte Benutzer
        if not self.is_logged_in:
            controls.append(self._build_login_banner())
        
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
    
    def _build_navigation(self) -> ft.NavigationBar:
        # Erstellt die Navigationsleiste.
        return ft.NavigationBar(
            selected_index=self.current_tab,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Start"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    selected_icon=ft.Icons.ADD_CIRCLE,
                    label="Melden"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PERSON,
                    label="Profil"
                ),
            ],
            on_change=self._on_nav_change,
        )
    
    def _build_appbar(self) -> ft.AppBar:
        # Erstellt die App-Bar.
        actions = [self.theme_manager.create_toggle_button()]

        if self.is_logged_in:
            actions.insert(0, ft.IconButton(
                ft.Icons.LOGOUT,
                tooltip="Abmelden",
                on_click=lambda _: self._logout()
            ))
        
        return ft.AppBar(
            title=ft.Text("PetBuddy", size=20, weight=ft.FontWeight.W_600),
            center_title=True,
            actions=actions,
        )
    
    # ════════════════════════════════════════════════════════════════════
    # APP STARTEN
    # ════════════════════════════════════════════════════════════════════
    
    def _show_main_app(self):
        # Zeigt die Hauptanwendung.
        # UI aufbauen
        if not self.build_ui():
            return
        
        # Komponenten erstellen
        self.start_section = self._build_start_section()
        self.nav = self._build_navigation()
        
        # Seite leeren und neu aufbauen
        self.page.controls.clear()
        self.page.appbar = self._build_appbar()
        self.page.navigation_bar = self.nav
        self.page.add(self.body)
        
        # Tab rendern und Daten laden
        self.render_tab()
        self.page.run_task(self.discover_view.load_posts)
        self.page.update()
    
    def _show_login(self):
        # Zeigt die Login-Maske.
        def on_login_success():
            # Nach dem Einloggen immer Startseite zeigen
            self.is_logged_in = True
            self.pending_tab_after_login = None
            self._show_main_app()
            self.current_tab = self.TAB_START
            if self.nav:
                self.nav.selected_index = self.TAB_START
            self.render_tab()
        
        def on_continue_without_account():
            # Nutzer möchte ohne Anmeldung weiter zur Startseite
            self.is_logged_in = False
            self.pending_tab_after_login = None
            self._show_main_app()
            # Immer Start anzeigen
            self.current_tab = self.TAB_START
            if self.nav:
                self.nav.selected_index = self.TAB_START
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
        # Startet die Anwendung.
        # Initialisierung
        if not self.initialize():
            return
        
        # Prüfen ob bereits eingeloggt
        try:
            user = self.sb.auth.get_user()
            if user and user.user:
                self.is_logged_in = True
        except Exception:
            self.is_logged_in = False
        
        # Immer Hauptapp zeigen (Startseite verfügbar ohne Login)
        self._show_main_app()


def main(page: ft.Page):
    # Einstiegspunkt der Anwendung.
    app = PetBuddyApp(page)
    app.run()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8550))
    ft.app(
        target=main,
        upload_dir="image_uploads",
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0"
    )