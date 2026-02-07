"""
Profile-View mit Benutzer-Profilbereich.

Enthält UI-Komposition und koordiniert Profile-Features.
"""

from __future__ import annotations

from typing import Callable, Optional, List

import flet as ft

from ui.constants import PRIMARY_COLOR
from utils.logging_config import get_logger
from ui.shared_components import show_success_dialog, show_error_dialog, show_confirm_dialog

from services.account import ProfileService, AuthService
from services.posts import SavedSearchService

from .components import (
    build_saved_searches_list,
    create_settings_view,
    create_edit_profile_view,
    create_favorites_view,
    create_my_posts_view,
)
from .handlers.my_favorites_handler import (
    load_favorites,
    remove_favorite,
)
from .handlers.my_posts_handler import (
    load_my_posts,
    edit_post as edit_post_feature,
    confirm_delete_post,
    handle_delete_post,
    handle_mark_reunited,
)
from .handlers.edit_profile_handler import (
    handle_change_password,
    handle_delete_account_confirmation,
    handle_profile_image_upload,
    update_avatar_image,
    handle_delete_profile_image_confirmation,
    handle_delete_profile_image,
    handle_save_display_name,
)
from .handlers.my_saved_search_handler import (
    handle_apply_saved_search,
)

logger = get_logger(__name__)

# ════════════════════════════════════════════════════════════════════════════════
# PROFILE VIEW KLASSE
# ════════════════════════════════════════════════════════════════════════════════

class ProfileView:
    """Benutzer-Profilbereich mit Einstellungen und Profilverwaltung."""

    VIEW_EDIT_PROFILE: str = "edit_profile"
    VIEW_SETTINGS: str = "settings"
    VIEW_FAVORITES: str = "favorites"
    VIEW_MY_POSTS: str = "my_posts"
    VIEW_SAVED_SEARCHES: str = "saved_searches"

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

        # Services initialisieren
        self.profile_service = ProfileService(sb)
        self.auth_service = AuthService(sb)
        self.saved_search_service = SavedSearchService(sb)

        self.user_data = None
        self.current_view = self.VIEW_EDIT_PROFILE

        self.main_container = ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # Favoriten
        self.favorites_list = ft.Column(spacing=14)
        self.favorites_items: List[dict] = []

        # Meine Meldungen
        self.my_posts_list = ft.Column(spacing=14)
        self.my_posts_items: List[dict] = []

        # UI-Elemente
        self._init_ui_elements()

        # FilePicker zum Overlay hinzufügen
        if self.profile_image_picker not in self.page.overlay:
            self.page.overlay.append(self.profile_image_picker)

        # Daten laden
        self.page.run_task(self._load_user_data)

    # ─────────────────────────────────────────────────────────────
    # INIT
    # ─────────────────────────────────────────────────────────────

    def _init_ui_elements(self):
        """Initialisiert alle UI-Elemente."""
        self.avatar = ft.CircleAvatar(
            radius=50,
            bgcolor=PRIMARY_COLOR,
            content=ft.Icon(ft.Icons.PERSON, size=50, color=ft.Colors.WHITE),
        )

        self.profile_image_picker = ft.FilePicker(
            on_result=lambda e: self.page.run_task(self._handle_profile_image_upload, e),
        )

        self.display_name = ft.Text("Lädt...", size=24, weight=ft.FontWeight.W_600)
        self.email_text = ft.Text("", size=14, color=ft.Colors.GREY_600)

    # ─────────────────────────────────────────────────────────────
    # DATEN LADEN
    # ─────────────────────────────────────────────────────────────

    async def _load_user_data(self):
        """Lädt den aktuell eingeloggten Benutzer."""
        try:
            self.user_data = self.profile_service.get_current_user()

            if self.user_data:
                self.email_text.value = self.profile_service.get_email() or ""
                self.display_name.value = self.profile_service.get_display_name()

                profile_image_url = self.profile_service.get_profile_image_url()
                if isinstance(profile_image_url, str):
                    profile_image_url = profile_image_url.strip()
                    if profile_image_url.lower() in {"", "null", "none", "undefined"}:
                        profile_image_url = None
                update_avatar_image(self, profile_image_url)

                self.page.update()
            else:
                self.display_name.value = "Nicht eingeloggt"
                self.page.update()

        except Exception as e:
            logger.error(f"Fehler beim Laden der Benutzerdaten: {e}", exc_info=True)
            self.display_name.value = "Fehler beim Laden"
            self.page.update()

    async def refresh_user_data(self) -> None:
        """Öffentliches Refresh für Benutzer-Daten (z. B. nach Login)."""
        await self._load_user_data()

    # ─────────────────────────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────────────────────────

    def _show_edit_profile(self):
        self.current_view = self.VIEW_EDIT_PROFILE
        self._rebuild()

    def _show_settings(self):
        self.current_view = self.VIEW_SETTINGS
        self._rebuild()

    def _show_favorites(self):
        self.current_view = self.VIEW_FAVORITES
        self._rebuild()
        self.page.run_task(self._load_favorites)

    def _show_my_posts(self):
        self.current_view = self.VIEW_MY_POSTS
        self._rebuild()
        self.page.run_task(self._load_my_posts)

    def _show_saved_searches(self):
        self.current_view = self.VIEW_SAVED_SEARCHES
        self._rebuild()

    def navigate_to(self, view_name: str) -> None:
        """Wechselt direkt zu einer Profil-Teilansicht."""
        if view_name == self.VIEW_EDIT_PROFILE:
            self._show_edit_profile()
        elif view_name == self.VIEW_MY_POSTS:
            self._show_my_posts()
        elif view_name == self.VIEW_FAVORITES:
            self._show_favorites()
        elif view_name == self.VIEW_SAVED_SEARCHES:
            self._show_saved_searches()
        elif view_name == self.VIEW_SETTINGS:
            self._show_settings()
        else:
            self._show_edit_profile()

    def _rebuild(self):
        """Baut die Ansicht basierend auf current_view neu."""
        self.main_container.controls.clear()

        view_builders = {
            self.VIEW_EDIT_PROFILE: self._build_edit_profile,
            self.VIEW_SETTINGS: self._build_settings,
            self.VIEW_FAVORITES: self._build_favorites,
            self.VIEW_MY_POSTS: self._build_my_posts,
            self.VIEW_SAVED_SEARCHES: self._build_saved_searches,
        }

        builder = view_builders.get(self.current_view, self._build_edit_profile)
        self.main_container.controls = builder()
        self.page.update()

    # ─────────────────────────────────────────────────────────────
    # AKTIONEN
    # ─────────────────────────────────────────────────────────────

    def _logout(self):
        """Meldet den Benutzer ab."""
        def on_confirm() -> None:
            result = self.auth_service.logout()
            if result.success:
                if self.on_logout:
                    self.on_logout()

        show_confirm_dialog(
            page=self.page,
            title="Abmelden?",
            message="Mochten Sie sich wirklich abmelden?",
            confirm_text="Abmelden",
            on_confirm=on_confirm,
        )

    async def _save_display_name(self, name_field: ft.TextField):
        """Speichert den neuen Anzeigenamen."""
        await handle_save_display_name(self, name_field)

    async def _handle_password_reset(self, email: str):
        """Sendet eine Passwort-Zurücksetzen-E-Mail."""
        if not email:
            show_error_dialog(self.page, "Fehler", "Keine E-Mail-Adresse gefunden.")
            return

        result = self.auth_service.reset_password(email)

        if result.success:
            show_success_dialog(self.page, "E-Mail gesendet", result.message or f"Passwort-Reset-E-Mail wurde an {email} gesendet.")
        else:
            show_error_dialog(self.page, "Fehler", result.message or "Unbekannter Fehler.")

    def _show_change_password_dialog(self):
        """Zeigt einen Dialog zum Ändern des Passworts."""
        handle_change_password(self)

    async def _handle_profile_image_upload(self, e: ft.FilePickerResultEvent):
        """Behandelt den Upload eines Profilbilds."""
        await handle_profile_image_upload(self, e)

    def _confirm_delete_profile_image(self):
        """Zeigt Bestätigungsdialog zum Löschen des Profilbilds."""
        if self.profile_service.get_profile_image_url() is None:
            show_error_dialog(self.page, "Kein Profilbild", "Es ist kein Profilbild vorhanden.")
            return
        handle_delete_profile_image_confirmation(self)

    async def _delete_profile_image(self):
        """Löscht das Profilbild des Benutzers."""
        await handle_delete_profile_image(self)

    async def _load_favorites(self):
        """Lädt alle favorisierten Meldungen."""
        self.favorites_items = await load_favorites(
            favorites_list=self.favorites_list,
            favorites_items=self.favorites_items,
            page=self.page,
            sb=self.sb,
            on_favorites_changed=self.on_favorites_changed,
        )

    def _remove_favorite(self, post_id: str):
        """Entfernt einen Post aus den Favoriten."""
        remove_favorite(
            post_id=post_id,
            favorites_items=self.favorites_items,
            favorites_list=self.favorites_list,
            page=self.page,
            sb=self.sb,
            on_favorites_changed=self.on_favorites_changed,
        )

    async def _load_my_posts(self):
        """Lädt alle eigenen Meldungen."""
        self.my_posts_items = await load_my_posts(
            my_posts_list=self.my_posts_list,
            my_posts_items=self.my_posts_items,
            page=self.page,
            sb=self.sb,
            on_posts_changed=self.on_posts_changed,
            on_edit=self._edit_post,
            on_delete=self._confirm_delete_post,
            on_mark_reunited=self._mark_reunited,
        )

    def _edit_post(self, post: dict):
        """Bearbeitet einen Post."""
        def on_save():
            # Meldungen neu laden
            self.page.run_task(self._load_my_posts)
            # Startseite aktualisieren
            if self.on_posts_changed:
                self.on_posts_changed()
        
        edit_post_feature(
            post=post,
            page=self.page,
            sb=self.sb,
            on_save_callback=on_save,
        )

    def _confirm_delete_post(self, post_id: int):
        """Zeigt Bestätigungsdialog zum Löschen."""
        confirm_delete_post(
            post_id=post_id,
            page=self.page,
            on_confirm=self._delete_post,
        )

    def _delete_post(self, post_id: int):
        """Löscht einen Post."""
        handle_delete_post(
            post_id=post_id,
            my_posts_items=self.my_posts_items,
            my_posts_list=self.my_posts_list,
            page=self.page,
            sb=self.sb,
            on_posts_changed=self.on_posts_changed,
            on_edit=self._edit_post,
            on_delete=self._confirm_delete_post,
            on_mark_reunited=self._mark_reunited,
        )

    def _mark_reunited(self, post: dict):
        """Setzt eine Meldung auf 'Wiedervereint'."""
        handle_mark_reunited(
            post=post,
            page=self.page,
            sb=self.sb,
            on_posts_changed=self.on_posts_changed,
        )
        # Liste neu laden, damit Status-Badge aktualisiert wird
        self.page.run_task(self._load_my_posts)

    def _confirm_delete_account(self):
        """Zeigt Bestätigungsdialog zum Löschen des Kontos."""
        handle_delete_account_confirmation(self)

    def _on_apply_saved_search(self, search: dict):
        """Wendet einen gespeicherten Suchauftrag an und navigiert zur Startseite."""
        handle_apply_saved_search(self.page, search)

    # ─────────────────────────────────────────────────────────────
    # VIEW BUILDER
    # ─────────────────────────────────────────────────────────────

    def _build_edit_profile(self) -> list:
        """Baut die Profil-Bearbeiten-Ansicht."""
        def handle_file_pick(_):
            logger.info("Bild ändern geklickt - öffne FilePicker")
            self.profile_image_picker.pick_files(
                dialog_title="Profilbild auswählen",
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )

        has_profile_image = self.profile_service.get_profile_image_url() is not None
        current_name = self.display_name.value or "Benutzer"

        return create_edit_profile_view(
            avatar=self.avatar,
            profile_image_picker=self.profile_image_picker,
            has_profile_image=has_profile_image,
            current_name=current_name,
            on_file_pick=handle_file_pick,
            on_delete_image=lambda _: self._confirm_delete_profile_image(),
            on_save_display_name=self._save_display_name,
            page=self.page,
            on_change_password=lambda _: self._show_change_password_dialog(),
            on_delete_account=lambda _: self._confirm_delete_account(),
        )

    def _build_settings(self) -> list:
        """Baut die Einstellungen-Ansicht."""
        def on_notification_change(value: bool):
            # TODO: Implementierung in settings_handler
            pass

        def on_email_notification_change(value: bool):
            # TODO: Implementierung in settings_handler
            pass

        return create_settings_view(
            on_notification_change=on_notification_change,
            on_email_notification_change=on_email_notification_change,
        )

    def _build_favorites(self) -> list:
        """Baut die Favoriten-Ansicht."""
        return create_favorites_view(
            favorites_list=self.favorites_list,
        )

    def _build_my_posts(self) -> list:
        """Baut die Meine Posts-Ansicht."""
        return create_my_posts_view(
            my_posts_list=self.my_posts_list,
            my_posts_items=self.my_posts_items,
        )

    def _build_saved_searches(self) -> list:
        """Baut die Gespeicherte-Suchaufträge-Ansicht."""
        return [
            build_saved_searches_list(
                page=self.page,
                saved_search_service=self.saved_search_service,
                on_apply_search=self._on_apply_saved_search,
            )
        ]

    # ─────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────

    def build(self) -> ft.Column:
        """Baut und gibt das Profil-Layout zurück."""
        view_builders = {
            self.VIEW_EDIT_PROFILE: self._build_edit_profile,
            self.VIEW_SETTINGS: self._build_settings,
            self.VIEW_FAVORITES: self._build_favorites,
            self.VIEW_MY_POSTS: self._build_my_posts,
            self.VIEW_SAVED_SEARCHES: self._build_saved_searches,
        }
        builder = view_builders.get(self.current_view, self._build_edit_profile)
        self.main_container.controls = builder()
        return self.main_container

    async def refresh(self):
        """Aktualisiert die Profildaten."""
        await self._load_user_data()
        self._show_edit_profile()
