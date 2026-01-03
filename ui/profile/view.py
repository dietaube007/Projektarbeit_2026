"""
ui/profile/view.py
Benutzer-Profilbereich.

Dieses Modul implementiert die Profilseite der PetBuddy-Anwendung.
Benutzer können ihre Profildaten einsehen, bearbeiten, Favoriten ansehen und sich abmelden.
"""

from typing import Callable, Optional, List
import flet as ft

from ui.theme import soft_card

from .components import (
    PRIMARY_COLOR,
    SECTION_PADDING,
    CARD_ELEVATION,
    build_back_button,
    build_section_title,
    build_menu_item,
    build_logout_button,
    loading_indicator,
)
from .favorites import (
    load_favorites,
    remove_favorite,
    render_favorites_list,
)
from .edit_profile import (
    build_change_image_section,
    build_change_name_section,
    build_password_section,
)
from .settings import build_notifications_section


class ProfileView:
    """Benutzer-Profilbereich mit Einstellungen und Profilverwaltung."""

    # View-Namen als Konstanten
    VIEW_MAIN: str = "main"
    VIEW_EDIT_PROFILE: str = "edit_profile"
    VIEW_SETTINGS: str = "settings"
    VIEW_FAVORITES: str = "favorites"

    def __init__(
        self,
        page: ft.Page,
        sb,
        on_logout: Optional[Callable] = None,
        on_favorites_changed: Optional[Callable] = None,
    ):
        """Initialisiert die Profil-Ansicht."""
        self.page = page
        self.sb = sb
        self.on_logout = on_logout
        self.on_favorites_changed = on_favorites_changed

        # Benutzerdaten
        self.user_data = None
        self.user_profile = None

        # Aktueller Bereich
        self.current_view = self.VIEW_MAIN
        self.main_container = ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Favoriten-Ansicht
        self.favorites_list = ft.Column(spacing=14)
        self.favorites_items: List[dict] = []

        # UI-Elemente initialisieren
        self._init_ui_elements()

        # Daten laden
        self.page.run_task(self._load_user_data)

    # ════════════════════════════════════════════════════════════════════
    # INIT UI
    # ════════════════════════════════════════════════════════════════════

    def _init_ui_elements(self):
        """Initialisiert alle UI-Elemente."""
        self.avatar = ft.CircleAvatar(
            radius=50,
            bgcolor=PRIMARY_COLOR,
            content=ft.Icon(
                ft.Icons.PERSON,
                size=50,
                color=ft.Colors.WHITE,
            ),
        )

        self.display_name = ft.Text(
            "Lädt...",
            size=24,
            weight=ft.FontWeight.W_600,
        )

        self.email_text = ft.Text(
            "",
            size=14,
            color=ft.Colors.GREY_600,
        )

    # ════════════════════════════════════════════════════════════════════
    # DATEN LADEN
    # ════════════════════════════════════════════════════════════════════

    async def _load_user_data(self):
        """Lädt den aktuell eingeloggten Benutzer und Profildaten."""
        try:
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                self.user_data = user_response.user
                self.email_text.value = self.user_data.email or ""

                profile = (
                    self.sb.table("user")
                    .select("*")
                    .eq("id", self.user_data.id)
                    .single()
                    .execute()
                )

                if profile.data:
                    self.user_profile = profile.data
                    self.display_name.value = profile.data.get(
                        "display_name", "Benutzer"
                    )
                else:
                    self.display_name.value = "Benutzer"

                self.page.update()

        except Exception as e:
            print(f"Fehler beim Laden der Benutzerdaten: {e}")
            self.display_name.value = "Fehler beim Laden"
            self.page.update()

    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ════════════════════════════════════════════════════════════════════

    def _show_main_menu(self):
        """Zeigt das Hauptmenü."""
        self.current_view = self.VIEW_MAIN
        self._rebuild()

    def _show_edit_profile(self):
        """Zeigt das Profil-Bearbeiten-Menü."""
        self.current_view = self.VIEW_EDIT_PROFILE
        self._rebuild()

    def _show_settings(self):
        """Zeigt die Einstellungen."""
        self.current_view = self.VIEW_SETTINGS
        self._rebuild()

    def _show_favorites(self):
        """Zeigt die Favoriten-Ansicht."""
        self.current_view = self.VIEW_FAVORITES
        self._rebuild()
        self.page.run_task(self._load_favorites)

    def _rebuild(self):
        """Baut die Ansicht basierend auf current_view neu."""
        self.main_container.controls.clear()

        view_builders = {
            self.VIEW_MAIN: self._build_main_menu,
            self.VIEW_EDIT_PROFILE: self._build_edit_profile,
            self.VIEW_SETTINGS: self._build_settings,
            self.VIEW_FAVORITES: self._build_favorites,
        }

        builder = view_builders.get(self.current_view, self._build_main_menu)
        self.main_container.controls = builder()
        self.page.update()

    # ════════════════════════════════════════════════════════════════════
    # AKTIONEN
    # ════════════════════════════════════════════════════════════════════

    def _logout(self):
        """Meldet den Benutzer ab."""
        try:
            self.sb.auth.sign_out()
            if self.on_logout:
                self.on_logout()
        except Exception as e:
            print(f"Fehler beim Abmelden: {e}")

    # ════════════════════════════════════════════════════════════════════
    # FAVORITEN
    # ════════════════════════════════════════════════════════════════════

    async def _load_favorites(self):
        """Lädt alle favorisierten Meldungen des aktuellen Benutzers."""
        try:
            self.favorites_list.controls = [loading_indicator("Favoriten werden geladen...")]
            self.page.update()

            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                self.favorites_items = []
                render_favorites_list(
                    self.favorites_list,
                    self.favorites_items,
                    self._remove_favorite,
                    not_logged_in=True,
                )
                self.page.update()
                return

            user_id = user_resp.user.id
            self.favorites_items = await load_favorites(self.sb, user_id)
            render_favorites_list(
                self.favorites_list,
                self.favorites_items,
                self._remove_favorite,
            )
            self.page.update()

        except Exception as e:
            print(f"Fehler beim Laden der Favoriten: {e}")
            self.favorites_items = []
            render_favorites_list(
                self.favorites_list,
                self.favorites_items,
                self._remove_favorite,
            )
            self.page.update()

    def _remove_favorite(self, post_id: int):
        """Entfernt einen Post aus den Favoriten."""
        try:
            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                return

            user_id = user_resp.user.id

            # Aus Datenbank löschen
            if remove_favorite(self.sb, user_id, post_id):
                # Lokal entfernen
                self.favorites_items = [
                    p for p in self.favorites_items if p.get("id") != post_id
                ]
                render_favorites_list(
                    self.favorites_list,
                    self.favorites_items,
                    self._remove_favorite,
                )
                self.page.update()

                # Startseite informieren
                if self.on_favorites_changed:
                    self.on_favorites_changed()

        except Exception as e:
            print(f"Fehler beim Entfernen aus Favoriten: {e}")

    def _build_favorites(self) -> list:
        """Baut die Favoriten-Ansicht."""
        back_button = build_back_button(lambda _: self._show_main_menu())

        favorites_card = soft_card(
            ft.Column(
                [
                    build_section_title("Favorisierte Meldungen"),
                    ft.Container(height=8),
                    self.favorites_list,
                ],
                spacing=12,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        return [back_button, favorites_card]

    # ════════════════════════════════════════════════════════════════════
    # BUILD - HAUPTMENÜ
    # ════════════════════════════════════════════════════════════════════

    def _build_main_menu(self) -> list:
        """Baut das Hauptmenü."""
        profile_header = soft_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            self.avatar,
                            ft.Column(
                                [self.display_name, self.email_text],
                                spacing=4,
                                expand=True,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=16,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        menu_list = soft_card(
            ft.Column(
                [
                    build_menu_item(
                        ft.Icons.EDIT_OUTLINED,
                        "Profil bearbeiten",
                        on_click=lambda _: self._show_edit_profile(),
                    ),
                    ft.Divider(height=1),
                    build_menu_item(
                        ft.Icons.ARTICLE_OUTLINED,
                        "Meine Meldungen",
                        on_click=lambda _: print("Meine Meldungen"),
                    ),
                    ft.Divider(height=1),
                    build_menu_item(
                        ft.Icons.FAVORITE_BORDER,
                        "Favorisierte Meldungen",
                        subtitle="Meldungen, die du mit ❤️ markiert hast",
                        on_click=lambda _: self._show_favorites(),
                    ),
                    ft.Divider(height=1),
                    build_menu_item(
                        ft.Icons.SETTINGS_OUTLINED,
                        "Einstellungen",
                        on_click=lambda _: self._show_settings(),
                    ),
                    ft.Divider(height=1),
                    build_menu_item(
                        ft.Icons.HELP_OUTLINE,
                        "Hilfe & Support",
                        on_click=lambda _: print("Hilfe & Support"),
                    ),
                    ft.Divider(height=1),
                    build_menu_item(
                        ft.Icons.INFO_OUTLINE,
                        "Über PetBuddy",
                        on_click=lambda _: print("Über PetBuddy"),
                    ),
                ],
                spacing=0,
            ),
            pad=12,
            elev=2,
        )

        logout_button = build_logout_button(lambda _: self._logout())

        return [profile_header, menu_list, logout_button]

    # ════════════════════════════════════════════════════════════════════
    # BUILD - PROFIL BEARBEITEN
    # ════════════════════════════════════════════════════════════════════

    def _build_edit_profile(self) -> list:
        """Baut die Profil-Bearbeiten-Ansicht."""
        back_button = build_back_button(lambda _: self._show_main_menu())
        
        change_image_section = build_change_image_section(
            self.avatar,
            on_change_image=lambda _: print("Bild ändern"),
        )
        
        change_name_section = build_change_name_section(
            self.display_name.value,
            on_save=lambda _: print("Name speichern"),
        )
        
        password_section = build_password_section(
            on_reset=lambda _: print("Passwort zurücksetzen"),
        )

        return [back_button, change_image_section, change_name_section, password_section]

    # ════════════════════════════════════════════════════════════════════
    # BUILD - EINSTELLUNGEN
    # ════════════════════════════════════════════════════════════════════

    def _build_settings(self) -> list:
        """Baut die Einstellungen-Ansicht."""
        back_button = build_back_button(lambda _: self._show_main_menu())
        
        notifications_section = build_notifications_section(
            push_enabled=True,
            email_enabled=False,
            on_push_change=lambda _: print("Push geändert"),
            on_email_change=lambda _: print("E-Mail geändert"),
        )

        return [back_button, notifications_section]

    # ════════════════════════════════════════════════════════════════════
    # BUILD
    # ════════════════════════════════════════════════════════════════════

    def build(self) -> ft.Column:
        """Baut und gibt das Profil-Layout zurück."""
        self.main_container.controls = self._build_main_menu()
        return self.main_container

    async def refresh(self):
        """Aktualisiert die Profildaten."""
        await self._load_user_data()
        self._show_main_menu()
