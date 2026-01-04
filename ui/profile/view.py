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
from .my_posts import (
    load_my_posts,
    delete_post,
    render_my_posts_list,
)
from .edit_post import EditPostDialog
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
    VIEW_MY_POSTS: str = "my_posts"

    def __init__(
        self,
        page: ft.Page,
        sb,
        on_logout: Optional[Callable] = None,
        on_favorites_changed: Optional[Callable] = None,
        on_posts_changed: Optional[Callable] = None,
    ):
        """Initialisiert die Profil-Ansicht."""
        self.page = page
        self.sb = sb
        self.on_logout = on_logout
        self.on_favorites_changed = on_favorites_changed
        self.on_posts_changed = on_posts_changed

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

        # Meine Meldungen Ansicht
        self.my_posts_list = ft.Column(spacing=14)
        self.my_posts_items: List[dict] = []

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

    def _show_success_dialog(self, title: str, message: str):
        """Zeigt einen Erfolgs-Dialog an."""
        def close_dialog(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.GREEN_600, size=28),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Text(message, size=13, color=ft.Colors.GREY_700),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)
    
    def _show_error_dialog(self, title: str, message: str):
        """Zeigt einen Fehler-Dialog an."""
        def close_dialog(e):
            self.page.close(dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_600, size=24),
                    ft.Text(title, size=16, weight=ft.FontWeight.W_600),
                ],
                spacing=8,
            ),
            content=ft.Text(message, size=13, color=ft.Colors.GREY_700),
            actions=[
                ft.TextButton("OK", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)

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

    def _show_my_posts(self):
        """Zeigt die Meine Meldungen Ansicht."""
        self.current_view = self.VIEW_MY_POSTS
        self._rebuild()
        self.page.run_task(self._load_my_posts)

    def _rebuild(self):
        """Baut die Ansicht basierend auf current_view neu."""
        self.main_container.controls.clear()

        view_builders = {
            self.VIEW_MAIN: self._build_main_menu,
            self.VIEW_EDIT_PROFILE: self._build_edit_profile,
            self.VIEW_SETTINGS: self._build_settings,
            self.VIEW_FAVORITES: self._build_favorites,
            self.VIEW_MY_POSTS: self._build_my_posts,
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

    # ════════════════════════════════════════════════════════════════════
    # MEINE MELDUNGEN
    # ════════════════════════════════════════════════════════════════════

    async def _load_my_posts(self):
        """Lädt alle eigenen Meldungen des aktuellen Benutzers."""
        try:
            self.my_posts_list.controls = [loading_indicator("Meldungen werden geladen...")]
            self.page.update()

            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                self.my_posts_items = []
                render_my_posts_list(
                    self.my_posts_list,
                    self.my_posts_items,
                    page=self.page,
                    on_edit=self._edit_post,
                    on_delete=self._confirm_delete_post,
                    not_logged_in=True,
                )
                self.page.update()
                return

            user_id = user_resp.user.id
            self.my_posts_items = await load_my_posts(self.sb, user_id)
            render_my_posts_list(
                self.my_posts_list,
                self.my_posts_items,
                page=self.page,
                on_edit=self._edit_post,
                on_delete=self._confirm_delete_post,
            )
            self.page.update()

        except Exception as e:
            print(f"Fehler beim Laden der eigenen Meldungen: {e}")
            self.my_posts_items = []
            render_my_posts_list(
                self.my_posts_list,
                self.my_posts_items,
                page=self.page,
                on_edit=self._edit_post,
                on_delete=self._confirm_delete_post,
            )
            self.page.update()

    def _edit_post(self, post: dict):
        """Bearbeiten einer Meldung."""
        def on_save():
            # Meldungen neu laden
            self.page.run_task(self._load_my_posts)
            # Startseite aktualisieren
            if self.on_posts_changed:
                self.on_posts_changed()
        
        # Bearbeitungsdialog öffnen
        dialog = EditPostDialog(
            page=self.page,
            sb=self.sb,
            post=post,
            on_save_callback=on_save,
        )
        dialog.show()

    def _confirm_delete_post(self, post_id: int):
        """Zeigt Bestätigungsdialog zum Löschen."""
        def on_confirm(e):
            self.page.close(dialog)
            self._delete_post(post_id)

        def on_cancel(e):
            self.page.close(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Meldung löschen?"),
            content=ft.Text(
                "Möchtest du diese Meldung wirklich löschen?\nDiese Aktion kann nicht rückgängig gemacht werden."
            ),
            actions=[
                ft.TextButton("Abbrechen", on_click=on_cancel),
                ft.ElevatedButton(
                    "Löschen",
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=on_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)

    def _delete_post(self, post_id: int):
        """Löscht einen Post."""
        try:
            if delete_post(self.sb, post_id):
                # Lokal entfernen
                self.my_posts_items = [
                    p for p in self.my_posts_items if p.get("id") != post_id
                ]
                render_my_posts_list(
                    self.my_posts_list,
                    self.my_posts_items,
                    page=self.page,
                    on_edit=self._edit_post,
                    on_delete=self._confirm_delete_post,
                )
                self._show_success_dialog("Meldung gelöscht", "Die Meldung wurde erfolgreich gelöscht.")
                self.page.update()

                # Startseite aktualisieren
                if self.on_posts_changed:
                    self.on_posts_changed()
            else:
                self._show_error_dialog("Löschen fehlgeschlagen", "Die Meldung konnte nicht gelöscht werden.")
                self.page.update()

        except Exception as e:
            print(f"Fehler beim Löschen des Posts: {e}")

    def _build_my_posts(self) -> list:
        """Baut die Meine Meldungen Ansicht."""
        back_button = build_back_button(lambda _: self._show_main_menu())

        # Anzahl der Meldungen
        count_text = f"{len(self.my_posts_items)} Meldung(en)" if self.my_posts_items else ""

        my_posts_card = soft_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            build_section_title("Meine Meldungen"),
                            ft.Container(expand=True),
                            ft.Text(count_text, size=12, color=ft.Colors.GREY_600),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=8),
                    self.my_posts_list,
                ],
                spacing=12,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        return [back_button, my_posts_card]

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
                        subtitle="Deine erstellten Meldungen",
                        on_click=lambda _: self._show_my_posts(),
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
