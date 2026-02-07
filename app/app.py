"""
PetBuddy App - Hauptklasse der Anwendung.

Diese Klasse steuert:
- Initialisierung und Theme
- Navigation zwischen Tabs
- Login/Logout Workflow
- UI-Bereiche (Start, Melden, Profil)
"""

from __future__ import annotations

from typing import Optional, Callable
import flet as ft

from services.supabase_client import get_client
from supabase import Client
from utils.logging_config import get_logger

logger = get_logger(__name__)
from ui.theme import ThemeManager
from ui.post_form import PostForm
from ui.discover import DiscoverView
from ui.profile import ProfileView
from ui.shared_components import show_confirm_dialog
from ui.constants import (
    WINDOW_MIN_WIDTH,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_DEFAULT_HEIGHT,
)

from app.dialogs import (
    show_comment_login_dialog,
    show_favorite_login_dialog,
    show_login_required_dialog,
    show_saved_search_login_dialog,
)
from app.auth_flow import AuthFlow
from app.navigation import (
    TAB_START,
    TAB_MELDEN,
    TAB_PROFIL,
    DRAWER_KEY_FAVORITES,
    DRAWER_KEY_LOGIN,
    DRAWER_KEY_LOGOUT,
    DRAWER_KEY_MELDEN,
    DRAWER_KEY_MY_POSTS,
    DRAWER_KEY_PROFILE_EDIT,
    DRAWER_KEY_SAVED_SEARCHES,
    DRAWER_KEY_SETTINGS,
    DRAWER_KEY_START,
    create_app_bar,
    build_drawer_items,
    create_navigation_drawer,
    DrawerItem,
    get_profile_drawer_key,
    set_drawer_selection,
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
        self.body: ft.Container = ft.Container(
            padding=ft.padding.only(left=16, right=16, top=16, bottom=0),
            expand=True,
        )
        self.nav: Optional[ft.NavigationBar] = None
        self._nav_drawer: Optional[ft.NavigationDrawer] = None
        self._drawer_actions: list[Callable[[], None]] = []
        self._drawer_index_map: dict[str, int] = {}
        self._app_bar_control: Optional[ft.Control] = None
        self._content_scroll: Optional[ft.Column] = None
        self._main_column: Optional[ft.Column] = None
        self.start_section: Optional[ft.Control] = None
        self.post_form: Optional[PostForm] = None
        self.discover_view: Optional[DiscoverView] = None
        self.profile_view: Optional[ProfileView] = None
        self._auth_flow: Optional[AuthFlow] = None
        self._profile_routes: dict[str, str] = {
            ProfileView.VIEW_EDIT_PROFILE: "/profile/edit",
            ProfileView.VIEW_MY_POSTS: "/profile/my_posts",
            ProfileView.VIEW_FAVORITES: "/profile/favorites",
            ProfileView.VIEW_SAVED_SEARCHES: "/profile/saved_searches",
            ProfileView.VIEW_SETTINGS: "/profile/settings",
        }
    
    # ════════════════════════════════════════════════════════════════════
    # INITIALISIERUNG
    # ════════════════════════════════════════════════════════════════════
    
    def initialize(self) -> bool:
        """Initialisiert die Seite und Supabase-Client."""
        try:
            self.page.title = "PetBuddy"
            self.page.padding = 0
            self.page.scroll = None
            self.page.window_min_width = WINDOW_MIN_WIDTH
            self.page.window_width = WINDOW_DEFAULT_WIDTH
            self.page.window_height = WINDOW_DEFAULT_HEIGHT

            # Routing einrichten
            self.page.on_route_change = self._handle_route_change
            self.page.on_disconnect = self._handle_disconnect
            
            # Theme anwenden
            self.theme_manager = ThemeManager(self.page)
            self.theme_manager.apply_theme("light")
            
            # Page-Hintergrund Theme-bewusst setzen
            from ui.theme import get_theme_color
            is_dark = self.page.theme_mode == ft.ThemeMode.DARK
            self.page.bgcolor = get_theme_color("background", is_dark)
            
            # Supabase-Client initialisieren
            self.sb = get_client()

            # Auth-Flow initialisieren
            self._auth_flow = AuthFlow(
                page=self.page,
                sb=self.sb,
                set_logged_in=self._set_logged_in,
                clear_pending_tab=self._clear_pending_tab,
            )

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
        # Route verarbeiten
        self._navigate_to(route)

    def _handle_disconnect(self, _e: ft.ControlEvent) -> None:
        """Cleanup bei App-Schliessen oder Verbindungsabbruch."""
        self._cleanup_post_form_uploads()

    def _cleanup_post_form_uploads(self) -> None:
        """Entfernt lokale Uploads aus dem Meldeformular, falls vorhanden."""
        if self.post_form:
            self.post_form.cleanup_local_uploads()
    
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
        
        # Route-Handler aufrufen
        if route_path == "/" or route_path == "/home":
            # Startseite leitet zu /discover weiter
            self.page.go("/discover")
            return
        elif route_path == "/login":
            self._open_login()
        elif route_path == "/discover":
            self._show_discover()
        elif route_path == "/profile":
            self._show_profile()
        elif route_path == "/profile/edit":
            self._show_profile_view(ProfileView.VIEW_EDIT_PROFILE)
        elif route_path == "/profile/my_posts":
            self._show_profile_view(ProfileView.VIEW_MY_POSTS)
        elif route_path == "/profile/favorites":
            self._show_profile_view(ProfileView.VIEW_FAVORITES)
        elif route_path == "/profile/saved_searches":
            self._show_profile_view(ProfileView.VIEW_SAVED_SEARCHES)
        elif route_path == "/profile/settings":
            self._show_profile_view(ProfileView.VIEW_SETTINGS)
        elif route_path == "/post/new":
            self._show_new_post()
        else:
            # 404 - Route nicht gefunden
            logger.warning(f"Unbekannte Route: {route_path}")
            self.page.go("/discover")  # Fallback zu Discover

    def _show_discover(self) -> None:
        """Zeigt die Discover-Seite."""
        try:
            if not self.discover_view:
                if not self.build_ui():
                    logger.error("_show_discover: build_ui() fehlgeschlagen")
                    return

            self.current_tab = TAB_START
            profile_key = get_profile_drawer_key(
                self.profile_view.current_view if self.profile_view else None
            )
            set_drawer_selection(
                self._nav_drawer,
                self._drawer_index_map,
                TAB_START,
                profile_key,
            )

            self._show_main_app()

            # Gespeicherten Suchauftrag anwenden falls vorhanden
            saved_search = self.page.session.get("apply_saved_search")
            if saved_search and self.discover_view:
                self.page.session.remove("apply_saved_search")
                self.discover_view.apply_saved_search(saved_search)
        except Exception as e:
            logger.error(f"Fehler in _show_discover: {e}", exc_info=True)
    
    def _show_profile(self) -> None:
        """Zeigt die Profil-Seite."""
        self._show_profile_view(None)

    def _show_profile_view(self, view_name: Optional[str]) -> None:
        """Zeigt eine Profil-Unterseite anhand der View-ID."""
        if not self.is_logged_in:
            self.page.go("/login")
            return
        
        if not self.profile_view:
            if not self.build_ui():
                return
        else:
            self.page.run_task(self.profile_view.refresh_user_data)
        
        if view_name and self.profile_view:
            self.profile_view.navigate_to(view_name)

        self.current_tab = TAB_PROFIL
        profile_key = get_profile_drawer_key(
            self.profile_view.current_view if self.profile_view else None
        )
        set_drawer_selection(
            self._nav_drawer,
            self._drawer_index_map,
            profile_key or DRAWER_KEY_PROFILE_EDIT,
            profile_key,
        )
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
        profile_key = get_profile_drawer_key(
            self.profile_view.current_view if self.profile_view else None
        )
        set_drawer_selection(
            self._nav_drawer,
            self._drawer_index_map,
            TAB_MELDEN,
            profile_key,
        )
        self._show_main_app()

    def _show_error(self, message: str) -> None:
        """Zeigt eine Fehlermeldung als Dialog.
        
        Args:
            message: Fehlermeldung die angezeigt werden soll
        """
        from ui.shared_components import show_error_dialog
        show_error_dialog(self.page, "Fehler", message)
    
    
    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ════════════════════════════════════════════════════════════════════
    
    def render_tab(self) -> None:
        """Rendert den aktuellen Tab."""
        try:
            content = {
                TAB_START: self.start_section,
                TAB_MELDEN: self.post_form.build() if self.post_form else None,
                TAB_PROFIL: self.profile_view.build() if self.profile_view else None,
            }.get(self.current_tab, self.start_section)
            
            if content is None:
                logger.error(f"Content für Tab {self.current_tab} ist None")
                content = ft.Container(
                    content=ft.Text("Fehler: Tab-Inhalt nicht verfügbar"),
                    padding=20
                )
            
            self.body.content = content
            self.page.update()
        except Exception as e:
            logger.error(f"Fehler in render_tab: {e}", exc_info=True)
            self.body.content = ft.Container(
                content=ft.Text(f"Fehler beim Rendern: {str(e)}"),
                padding=20
            )
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
        if self.post_form:
            self.post_form.cleanup_local_uploads()
        # Zur Startseite navigieren
        self.page.go("/")
    
    def _on_nav_change(self, e: ft.ControlEvent) -> None:
        """Event-Handler für Navigationsänderung.
        
        Args:
            e: ControlEvent von der Navigation
        """
        new_tab = e.control.selected_index
        self._navigate_to_tab(new_tab)

    def _on_drawer_change(self, e: ft.ControlEvent) -> None:
        if self._nav_drawer:
            self._nav_drawer.open = False
        self.page.update()
        new_tab = e.control.selected_index
        if 0 <= new_tab < len(self._drawer_actions):
            self._drawer_actions[new_tab]()

    def _navigate_to_tab(self, new_tab: int) -> None:
        # Login erforderlich für Melden und Profil
        if new_tab in [TAB_MELDEN, TAB_PROFIL] and not self.is_logged_in:
            def on_login() -> None:
                self.pending_tab_after_login = new_tab
                self._open_login()

            def on_cancel() -> None:
                profile_key = get_profile_drawer_key(
                    self.profile_view.current_view if self.profile_view else None
                )
                set_drawer_selection(
                    self._nav_drawer,
                    self._drawer_index_map,
                    TAB_START,
                    profile_key,
                )
                self.page.update()

            show_login_required_dialog(
                self.page,
                new_tab,
                on_login=on_login,
                on_cancel=on_cancel,
            )
            return

        # Cleanup wenn Melden verlassen wird
        if self.current_tab == TAB_MELDEN and new_tab != TAB_MELDEN and self.post_form:
            self.post_form.cleanup_local_uploads()

        # Navigation zu Routen
        if new_tab == TAB_START:
            self.page.go("/")
        elif new_tab == TAB_MELDEN:
            self.page.go("/post/new")
        elif new_tab == TAB_PROFIL:
            self.page.go("/profile")

        self.current_tab = new_tab
        profile_key = get_profile_drawer_key(
            self.profile_view.current_view if self.profile_view else None
        )
        set_drawer_selection(
            self._nav_drawer,
            self._drawer_index_map,
            new_tab,
            profile_key,
        )
        self.render_tab()

    def _open_profile_section(self, view_name: str, _drawer_key: str) -> None:
        if not self.is_logged_in:
            def on_login() -> None:
                self.pending_tab_after_login = TAB_PROFIL
                self._open_login()

            def on_cancel() -> None:
                profile_key = get_profile_drawer_key(
                    self.profile_view.current_view if self.profile_view else None
                )
                set_drawer_selection(
                    self._nav_drawer,
                    self._drawer_index_map,
                    TAB_START,
                    profile_key,
                )
                self.page.update()

            show_login_required_dialog(
                self.page,
                TAB_PROFIL,
                on_login=on_login,
                on_cancel=on_cancel,
            )
            return
        route = self._profile_routes.get(view_name, "/profile")
        self.page.go(route)
    
    def _go_to_start(self, _e: ft.ControlEvent) -> None:
        """Navigiert zur Startseite (z. B. beim Klick auf die PetBuddy-Überschrift)."""
        if self.current_tab == TAB_MELDEN and self.post_form:
            self.post_form.cleanup_local_uploads()
        self.current_tab = TAB_START
        profile_key = get_profile_drawer_key(
            self.profile_view.current_view if self.profile_view else None
        )
        set_drawer_selection(
            self._nav_drawer,
            self._drawer_index_map,
            TAB_START,
            profile_key,
        )
        self.page.go("/")
        self.render_tab()
    
    def _logout(self) -> None:
        """Meldet den Benutzer ab."""
        try:
            self._cleanup_post_form_uploads()
            self.sb.auth.sign_out()
            self.is_logged_in = False
            
            # Zur Login-Seite navigieren
            self.page.go("/login")
        except Exception as e:
            logger.error(f"Fehler beim Abmelden: {e}", exc_info=True)

    def _confirm_logout(self, _e: Optional[ft.ControlEvent] = None) -> None:
        """Zeigt einen Bestatigungsdialog vor dem Abmelden."""
        show_confirm_dialog(
            page=self.page,
            title="Abmelden?",
            message="Mochten Sie sich wirklich abmelden?",
            confirm_text="Abmelden",
            on_confirm=self._logout,
        )
    
    # ════════════════════════════════════════════════════════════════════
    # UI-BEREICHE LADEN
    # ════════════════════════════════════════════════════════════════════
    
    def build_ui(self) -> bool:
        """Baut die UI-Bereiche auf."""
        try:
            # DiscoverView erstellen
            if self.discover_view is None:
                self.discover_view = DiscoverView(
                    page=self.page,
                    sb=self.sb,
                    on_contact_click=None,
                    on_melden_click=self.go_to_melden_tab,
                    on_login_required=lambda: show_favorite_login_dialog(
                        self.page,
                        on_login=self._open_login,
                    ),
                    on_save_search_login_required=lambda: show_saved_search_login_dialog(
                        self.page,
                        on_login=self._open_login,
                    ),
                    on_comment_login_required=lambda: show_comment_login_dialog(
                        self.page,
                        on_login=self._open_login,
                    ),
                )

            # PostForm erstellen
            if self.post_form is None:
                self.post_form = PostForm(
                    page=self.page,
                    sb=self.sb,
                    on_saved_callback=self.on_post_saved
                )

            # ProfileView erstellen
            if self.profile_view is None:
                self.profile_view = ProfileView(
                    page=self.page,
                    sb=self.sb,
                    on_logout=self._logout,
                    on_favorites_changed=self._on_favorites_changed,
                    on_posts_changed=self._on_posts_changed,
                )

            return True
        except Exception as e:
            logger.error(f"Fehler in build_ui: {e}", exc_info=True)
            self._show_error(f"Fehler beim Laden der UI: {str(e)}")
            return False

    def _on_favorites_changed(self) -> None:
        """Callback wenn sich Favoriten aendern."""
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)

    def _on_posts_changed(self) -> None:
        """Callback wenn Meldungen bearbeitet/geloscht werden."""
        if self.discover_view:
            self.page.run_task(self.discover_view.load_posts)

    # ════════════════════════════════════════════════════════════════════
    # APP STARTEN
    # ════════════════════════════════════════════════════════════════════
    
    def _show_main_app(self) -> None:
        """Zeigt die Hauptanwendung."""
        try:
            # Komponenten erstellen
            if not self.discover_view:
                if not self.build_ui():
                    logger.error("_show_main_app: build_ui() fehlgeschlagen")
                    return

            self.start_section = self.discover_view.build_start_section(
                is_logged_in=self.is_logged_in,
                on_login_click=lambda _: self._open_login(),
            )
            if self.start_section is None:
                logger.error("_show_main_app: start_section ist None")
                return

            if self._auth_flow:
                overlay = self._auth_flow.redirect_loading_overlay
                if overlay and overlay in self.page.overlay:
                    self.page.overlay.remove(overlay)
                auth_view = self._auth_flow.auth_view
            else:
                auth_view = None
            if auth_view and getattr(auth_view, "_login_loading_overlay", None):
                lo = auth_view._login_loading_overlay
                if lo and lo in self.page.overlay:
                    self.page.overlay.remove(lo)
            
            actions: dict[str, Callable[[], None]] = {
                DRAWER_KEY_START: lambda: self._navigate_to_tab(TAB_START),
                DRAWER_KEY_MELDEN: lambda: self._navigate_to_tab(TAB_MELDEN),
                DRAWER_KEY_PROFILE_EDIT: lambda: self._open_profile_section(
                    ProfileView.VIEW_EDIT_PROFILE,
                    DRAWER_KEY_PROFILE_EDIT,
                ),
                DRAWER_KEY_MY_POSTS: lambda: self._open_profile_section(
                    ProfileView.VIEW_MY_POSTS,
                    DRAWER_KEY_MY_POSTS,
                ),
                DRAWER_KEY_FAVORITES: lambda: self._open_profile_section(
                    ProfileView.VIEW_FAVORITES,
                    DRAWER_KEY_FAVORITES,
                ),
                DRAWER_KEY_SAVED_SEARCHES: lambda: self._open_profile_section(
                    ProfileView.VIEW_SAVED_SEARCHES,
                    DRAWER_KEY_SAVED_SEARCHES,
                ),
                DRAWER_KEY_SETTINGS: lambda: self._open_profile_section(
                    ProfileView.VIEW_SETTINGS,
                    DRAWER_KEY_SETTINGS,
                ),
                DRAWER_KEY_LOGOUT: self._confirm_logout,
                DRAWER_KEY_LOGIN: self._open_login,
            }

            drawer_items: list[DrawerItem] = build_drawer_items(
                self.is_logged_in,
                actions,
            )

            (
                self._nav_drawer,
                self._drawer_index_map,
                self._drawer_actions,
            ) = create_navigation_drawer(
                items=drawer_items,
                selected_index=self.current_tab,
                on_change=self._on_drawer_change,
            )
            profile_key = get_profile_drawer_key(
                self.profile_view.current_view if self.profile_view else None
            )
            set_drawer_selection(
                self._nav_drawer,
                self._drawer_index_map,
                self.current_tab,
                profile_key,
            )
            
            # Seite leeren und neu aufbauen
            self.page.controls.clear()
            
            # Callback für Theme-Wechsel erstellen
            def on_theme_toggle(is_dark: bool) -> None:
                if self.discover_view:
                    self.discover_view._update_farben_colors()
                # Alle offenen Kommentarbereiche aktualisieren
                for control in getattr(self.page, "_theme_listeners", []):
                    if hasattr(control, "_apply_theme"):
                        control._apply_theme()
                # AppBar mit neuer Hintergrundfarbe neu erstellen
                if self._main_column:
                    self._app_bar_control = create_app_bar(
                        self.is_logged_in,
                        self._confirm_logout,
                        self.theme_manager.create_toggle_button(on_after_toggle=on_theme_toggle),
                        on_menu=self._open_drawer,
                        page=self.page,
                        on_title_click=self._go_to_start,
                        on_login=lambda _: self._open_login(),
                    )
                    self._main_column.controls[0] = self._app_bar_control
                    self.page.update()
            
            self._app_bar_control = create_app_bar(
                self.is_logged_in,
                self._confirm_logout,
                self.theme_manager.create_toggle_button(on_after_toggle=on_theme_toggle),
                on_menu=self._open_drawer,
                page=self.page,
                on_title_click=self._go_to_start,
                on_login=lambda _: self._open_login(),
            )
            self._content_scroll = ft.Column(
                [self.body],
                spacing=0,
                expand=True,
            )
            self._main_column = ft.Column(
                [self._app_bar_control, self._content_scroll],
                spacing=0,
                expand=True,
            )
            self.page.appbar = None
            self.page.navigation_bar = None
            self.page.drawer = self._nav_drawer
            self.page.add(self._main_column)
            
            # Tab rendern und Daten laden
            self.render_tab()
            
            if self.discover_view:
                self.page.run_task(self.discover_view.ensure_loaded)
            else:
                logger.error("_show_main_app: discover_view ist None")
            
            self.page.update()
        except Exception as e:
            logger.error(f"Fehler in _show_main_app: {e}", exc_info=True)

    def _open_login(self) -> None:
        """Startet den Login-Flow."""
        if not self._auth_flow:
            logger.error("AuthFlow ist nicht initialisiert")
            return
        self._auth_flow.show_login()

    def _set_logged_in(self, is_logged_in: bool) -> None:
        self.is_logged_in = is_logged_in

    def _clear_pending_tab(self) -> None:
        self.pending_tab_after_login = None

    def _open_drawer(self, _e: Optional[ft.ControlEvent] = None) -> None:
        if self._nav_drawer:
            self._nav_drawer.open = True
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
        if not self.page.route:
            self.page.route = initial_route
        self._navigate_to(initial_route)

