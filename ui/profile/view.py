"""
ui/profile/view.py
Benutzer-Profilbereich.

Dieses Modul implementiert die Profilseite der PetBuddy-Anwendung.
Benutzer können ihre Profildaten einsehen, bearbeiten, Favoriten ansehen und sich abmelden.
"""

from __future__ import annotations

import os
import time
import uuid
import asyncio
from typing import Callable, Optional, List

import flet as ft

from ui.theme import soft_card
from ui.constants import PRIMARY_COLOR, MAX_DISPLAY_NAME_LENGTH
from utils.logging_config import get_logger
from ui.components import show_success_dialog, show_error_dialog

from services.account import ProfileService, AuthService, ProfileImageService, AccountDeletionService
from services.posts import SavedSearchService

from .favorites import (
    render_favorites_list,
    ProfileFavoritesMixin,
)
from .my_posts import (
    render_my_posts_list,
    ProfileMyPostsMixin,
)
from .saved_searches import build_saved_searches_list
from .profile_image_helpers import (
    handle_profile_image_upload,
    process_profile_image,
    update_avatar_image,
    confirm_delete_profile_image,
    delete_profile_image,
)
from .profile_security import (
    show_change_password_dialog,
    confirm_delete_account,
    delete_account,
)

logger = get_logger(__name__)

# ════════════════════════════════════════════════════════════════════════════════
# KONSTANTEN
# ════════════════════════════════════════════════════════════════════════════════

SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


# ════════════════════════════════════════════════════════════════════════════════
# UI-KOMPONENTEN (Hilfsfunktionen)
# ════════════════════════════════════════════════════════════════════════════════

def _build_back_button(on_click: Callable) -> ft.Container:
    """Erstellt einen Zurück-Button."""
    return ft.Container(
        content=ft.TextButton("← Zurück", on_click=on_click),
        padding=ft.padding.only(bottom=8),
    )


def _build_section_title(title: str) -> ft.Text:
    """Erstellt einen Abschnitts-Titel."""
    return ft.Text(title, size=18, weight=ft.FontWeight.W_600)


def _build_menu_item(
    icon: str,
    title: str,
    subtitle: str = "",
    on_click: Optional[Callable] = None,
) -> ft.Container:
    """Erstellt einen Menüpunkt."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, size=24, color=PRIMARY_COLOR),
                    padding=12,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
                ),
                ft.Column(
                    [
                        ft.Text(title, size=16, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=12, color=ft.Colors.GREY_600) if subtitle else ft.Container(),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400),
            ],
            spacing=16,
        ),
        padding=12,
        border_radius=12,
        on_click=on_click,
        ink=True,
    )


def _build_setting_row(icon: str, title: str, subtitle: str, control: ft.Control) -> ft.Row:
    """Erstellt eine Einstellungs-Zeile."""
    return ft.Row(
        [
            ft.Icon(icon, color=PRIMARY_COLOR),
            ft.Column(
                [
                    ft.Text(title, size=14),
                    ft.Text(subtitle, size=12, color=ft.Colors.GREY_600),
                ],
                spacing=2,
                expand=True,
            ),
            control,
        ],
        spacing=12,
    )


# ════════════════════════════════════════════════════════════════════════════════
# PROFILE VIEW KLASSE
# ════════════════════════════════════════════════════════════════════════════════

class ProfileView(ProfileFavoritesMixin, ProfileMyPostsMixin):
    """Benutzer-Profilbereich mit Einstellungen und Profilverwaltung."""

    VIEW_MAIN: str = "main"
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
        self.image_service = ProfileImageService(sb)
        self.account_deletion_service = AccountDeletionService(sb)
        self.profile_service = ProfileService(sb)
        self.saved_search_service = SavedSearchService(sb)

        self.user_data = None
        self.current_view = self.VIEW_MAIN

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

    # ════════════════════════════════════════════════════════════════════
    # INIT
    # ════════════════════════════════════════════════════════════════════

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

    # ════════════════════════════════════════════════════════════════════
    # DATEN LADEN
    # ════════════════════════════════════════════════════════════════════

    async def _load_user_data(self):
        """Lädt den aktuell eingeloggten Benutzer."""
        try:
            self.user_data = self.profile_service.get_current_user()

            if self.user_data:
                self.email_text.value = self.profile_service.get_email() or ""
                self.display_name.value = self.profile_service.get_display_name()

                profile_image_url = self.profile_service.get_profile_image_url()
                self._update_avatar_image(profile_image_url)

                self.page.update()
            else:
                self.display_name.value = "Nicht eingeloggt"
                self.page.update()

        except Exception as e:
            logger.error(f"Fehler beim Laden der Benutzerdaten: {e}", exc_info=True)
            self.display_name.value = "Fehler beim Laden"
            self.page.update()

    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ════════════════════════════════════════════════════════════════════

    def _show_main_menu(self):
        self.current_view = self.VIEW_MAIN
        self._rebuild()

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

    def _rebuild(self):
        """Baut die Ansicht basierend auf current_view neu."""
        self.main_container.controls.clear()

        view_builders = {
            self.VIEW_MAIN: self._build_main_menu,
            self.VIEW_EDIT_PROFILE: self._build_edit_profile,
            self.VIEW_SETTINGS: self._build_settings,
            self.VIEW_FAVORITES: self._build_favorites,
            self.VIEW_MY_POSTS: self._build_my_posts,
            self.VIEW_SAVED_SEARCHES: self._build_saved_searches,
        }

        builder = view_builders.get(self.current_view, self._build_main_menu)
        self.main_container.controls = builder()
        self.page.update()

    # ════════════════════════════════════════════════════════════════════
    # AKTIONEN (über ProfileService)
    # ════════════════════════════════════════════════════════════════════

    def _logout(self):
        """Meldet den Benutzer ab."""
        result = self.auth_service.logout()
        if result.success:
            if self.on_logout:
                self.on_logout()

    async def _save_display_name(self, name_field: ft.TextField):
        """Speichert den neuen Anzeigenamen."""
        new_name = name_field.value
        if not new_name or not new_name.strip():
            show_error_dialog(self.page, "Fehler", "Der Anzeigename darf nicht leer sein.")
            return

        success, error_msg = self.profile_service.update_display_name(new_name)

        if success:
            self.display_name.value = new_name.strip()
            self.page.update()
            show_success_dialog(self.page, "Erfolg", "Der Anzeigename wurde aktualisiert.")
        else:
            show_error_dialog(self.page, "Fehler", error_msg or "Unbekannter Fehler.")

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
        show_change_password_dialog(self)

    async def _handle_profile_image_upload(self, e: ft.FilePickerResultEvent):
        """Behandelt den Upload eines Profilbilds."""
        await handle_profile_image_upload(self, e)

    async def _process_profile_image(self, file_path: str):
        """Verarbeitet und lädt ein Profilbild hoch."""
        await process_profile_image(self, file_path)

    def _update_avatar_image(self, image_url: Optional[str]):
        """Aktualisiert den Avatar."""
        update_avatar_image(self, image_url)

    def _confirm_delete_profile_image(self):
        """Zeigt Bestätigungsdialog zum Löschen des Profilbilds."""
        confirm_delete_profile_image(self)

    async def _delete_profile_image(self):
        """Löscht das Profilbild des Benutzers."""
        await delete_profile_image(self)

    # ════════════════════════════════════════════════════════════════════
    # VIEW BUILDER
    # ════════════════════════════════════════════════════════════════════

    def _build_main_menu(self) -> list:
        """Baut das Hauptmenü."""
        profile_header = soft_card(
            ft.Column([
                ft.Row([
                            self.avatar,
                    ft.Column([self.display_name, self.email_text], spacing=4, expand=True),
                ], spacing=20),
            ], spacing=16),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        menu_list = soft_card(
            ft.Column([
                _build_menu_item(ft.Icons.EDIT_OUTLINED, "Profil bearbeiten", on_click=lambda _: self._show_edit_profile()),
                ft.Divider(height=1),
                _build_menu_item(ft.Icons.ARTICLE_OUTLINED, "Meine Meldungen", "Ihre erstellten Meldungen", lambda _: self._show_my_posts()),
                ft.Divider(height=1),
                _build_menu_item(ft.Icons.FAVORITE_BORDER, "Favorisierte Meldungen", "Meldungen mit Favorit-Markierung", lambda _: self._show_favorites()),
                ft.Divider(height=1),
                _build_menu_item(ft.Icons.BOOKMARK_BORDER, "Gespeicherte Suchaufträge", "Ihre Filter-Vorlagen", lambda _: self._show_saved_searches()),
                ft.Divider(height=1),
                _build_menu_item(ft.Icons.SETTINGS_OUTLINED, "Einstellungen", on_click=lambda _: self._show_settings()),
            ], spacing=0),
            pad=12,
            elev=2,
        )

        logout_button = ft.Container(
            content=ft.OutlinedButton(
                "Abmelden",
                icon=ft.Icons.LOGOUT,
                on_click=lambda _: self._logout(),
                style=ft.ButtonStyle(color=ft.Colors.RED, side=ft.BorderSide(1, ft.Colors.RED)),
                width=200,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=8, bottom=24),
        )

        return [profile_header, menu_list, logout_button]

    def _build_edit_profile(self) -> list:
        """Baut die Profil-Bearbeiten-Ansicht."""
        back_button = _build_back_button(lambda _: self._show_main_menu())

        change_image_section = self._build_edit_profile_image_section()
        change_name_section = self._build_edit_display_name_section()
        password_section = self._build_edit_password_section()
        delete_account_section = self._build_delete_account_section()

        return [
            back_button,
            change_image_section,
            change_name_section,
            password_section,
            delete_account_section,
        ]

    def _build_edit_profile_image_section(self) -> ft.Control:
        """Profilbild-Section im Bearbeiten-View."""

        def handle_file_pick(_):
            logger.info("Bild ändern geklickt - öffne FilePicker")
            self.profile_image_picker.pick_files(
                dialog_title="Profilbild auswählen",
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )

        def handle_delete_image(_):
            self._confirm_delete_profile_image()

        has_profile_image = self.profile_service.get_profile_image_url() is not None

        image_buttons: list[ft.Control] = [
            ft.FilledButton("Bild ändern", icon=ft.Icons.CAMERA_ALT, on_click=handle_file_pick),
        ]
        if has_profile_image:
            image_buttons.append(
                ft.OutlinedButton(
                    "Bild löschen",
                    icon=ft.Icons.DELETE_OUTLINE,
                    on_click=handle_delete_image,
                    style=ft.ButtonStyle(color=ft.Colors.RED, side=ft.BorderSide(1, ft.Colors.RED)),
                )
            )

        return soft_card(
            ft.Column(
                [
                    _build_section_title("Profilbild"),
                    ft.Container(height=8),
                    ft.Row(
                        [
                            self.avatar,
                            ft.Column(
                                [
                                    ft.Row(image_buttons, spacing=8, wrap=True),
                                    ft.Text("JPG, PNG oder WebP\nMax. 5 MB", size=12, color=ft.Colors.GREY_600),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=8,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

    def _build_edit_display_name_section(self) -> ft.Control:
        """Anzeigename-Section im Bearbeiten-View."""
        current_name = self.display_name.value or "Benutzer"
        name_field = ft.TextField(
            value=current_name,
            width=300,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            label="Anzeigename",
            hint_text=f"Max. {MAX_DISPLAY_NAME_LENGTH} Zeichen",
            max_length=MAX_DISPLAY_NAME_LENGTH,
        )

        return soft_card(
            ft.Column(
                [
                    _build_section_title("Anzeigename"),
                    ft.Container(height=8),
                    name_field,
                    ft.Container(height=8),
                    ft.FilledButton(
                        "Speichern",
                        icon=ft.Icons.SAVE,
                        on_click=lambda _: self.page.run_task(self._save_display_name, name_field),
                    ),
                ],
                spacing=8,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

    def _build_edit_password_section(self) -> ft.Control:
        """Passwort-Section im Bearbeiten-View."""
        return soft_card(
            ft.Column(
                [
                    _build_section_title("Passwort"),
                    ft.Container(height=8),
                    ft.Text("Ändern Sie Ihr Passwort", size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=8),
                    ft.FilledButton(
                        "Passwort ändern",
                        icon=ft.Icons.LOCK,
                        on_click=lambda _: self._show_change_password_dialog(),
                    ),
                ],
                spacing=8,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

    def _build_delete_account_section(self) -> ft.Control:
        """Konto-löschen-Section im Bearbeiten-View."""
        return soft_card(
            ft.Column(
                [
                    _build_section_title("Konto löschen"),
                    ft.Container(height=8),
                    ft.Text(
                        "Wenn Sie Ihr Konto löschen, werden alle Ihre Daten unwiderruflich entfernt.",
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Container(height=8),
                    ft.OutlinedButton(
                        "Konto löschen",
                        icon=ft.Icons.DELETE_FOREVER,
                        on_click=lambda _: self._confirm_delete_account(),
                        style=ft.ButtonStyle(
                            color=ft.Colors.RED,
                            side=ft.BorderSide(1, ft.Colors.RED),
                        ),
                    ),
                ],
                spacing=8,
            ),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

    def _confirm_delete_account(self):
        """Zeigt Bestätigungsdialog zum Löschen des Kontos."""
        confirm_delete_account(self)

    def _delete_account(self):
        """Löscht das Benutzerkonto."""
        delete_account(self)

    def _build_settings(self) -> list:
        """Baut die Einstellungen-Ansicht."""
        back_button = _build_back_button(lambda _: self._show_main_menu())

        notifications_section = soft_card(
            ft.Column([
                _build_section_title("Benachrichtigungen"),
                ft.Container(height=12),
                _build_setting_row(
                    ft.Icons.NOTIFICATIONS_OUTLINED,
                    "Push-Benachrichtigungen",
                    "Erhalten Sie Updates zu Ihren Meldungen",
                    ft.Switch(value=True),
                ),
                ft.Divider(height=20),
                _build_setting_row(
                    ft.Icons.EMAIL_OUTLINED,
                    "E-Mail-Benachrichtigungen",
                    "Erhalte wichtige Updates per E-Mail",
                    ft.Switch(value=False),
                ),
            ], spacing=8),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        return [back_button, notifications_section]

    def _build_favorites(self) -> list:
        """Baut die Favoriten-Ansicht."""
        back_button = _build_back_button(lambda _: self._show_main_menu())

        favorites_card = soft_card(
            ft.Column([
                _build_section_title("Favorisierte Meldungen"),
                ft.Container(height=8),
                self.favorites_list,
            ], spacing=12),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        return [back_button, favorites_card]

    def _build_my_posts(self) -> list:
        """Baut die Meine Posts-Ansicht."""
        back_button = _build_back_button(lambda _: self._show_main_menu())
        count_text = f"{len(self.my_posts_items)} Meldung(en)" if self.my_posts_items else ""

        my_posts_card = soft_card(
            ft.Column([
                ft.Row([
                    _build_section_title("Meine Meldungen"),
                    ft.Container(expand=True),
                    ft.Text(count_text, size=12, color=ft.Colors.GREY_600),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                self.my_posts_list,
            ], spacing=12),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        return [back_button, my_posts_card]

    def _build_saved_searches(self) -> list:
        """Baut die Gespeicherte-Suchaufträge-Ansicht."""
        return [
            build_saved_searches_list(
                page=self.page,
                saved_search_service=self.saved_search_service,
                on_apply_search=self._on_apply_saved_search,
                on_back=self._show_main_menu,
            )
        ]

    def _on_apply_saved_search(self, search: dict):
        """Wendet einen gespeicherten Suchauftrag an und navigiert zur Startseite."""
        # Die Suche wird über die App angewendet
        # Speichern in session_storage zur Verwendung in DiscoverView
        self.page.session.set("apply_saved_search", search)
        self.page.go("/")

    # ════════════════════════════════════════════════════════════════════
    # HELPER für Mixins
    # ════════════════════════════════════════════════════════════════════


    # ════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ════════════════════════════════════════════════════════════════════

    def build(self) -> ft.Column:
        """Baut und gibt das Profil-Layout zurück."""
        self.main_container.controls = self._build_main_menu()
        return self.main_container

    async def refresh(self):
        """Aktualisiert die Profildaten."""
        await self._load_user_data()
        self._show_main_menu()
