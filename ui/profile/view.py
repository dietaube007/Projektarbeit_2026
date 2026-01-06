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

from services.profile import ProfileService

from .favorites import (
    render_favorites_list,
    ProfileFavoritesMixin,
)
from .my_posts import (
    render_my_posts_list,
    ProfileMyPostsMixin,
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

        # ProfileService initialisieren
        self.profile_service = ProfileService(sb)

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

    def _rebuild(self):
        """Baut die Ansicht basierend auf current_view neu."""
        try:
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
        except Exception as e:
            logger.error(f"Fehler beim Rebuild: {e}", exc_info=True)

    # ════════════════════════════════════════════════════════════════════
    # AKTIONEN (über ProfileService)
    # ════════════════════════════════════════════════════════════════════

    def _logout(self):
        """Meldet den Benutzer ab."""
        if self.profile_service.logout():
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

        success, error_msg = self.profile_service.send_password_reset(email)

        if success:
            show_success_dialog(self.page, "E-Mail gesendet", f"Passwort-Reset-E-Mail wurde an {email} gesendet.")
        else:
            show_error_dialog(self.page, "Fehler", error_msg or "Unbekannter Fehler.")

    def _show_change_password_dialog(self):
        """Zeigt einen Dialog zum Ändern des Passworts."""
        current_password_field = ft.TextField(
            label="Aktuelles Passwort",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            width=300,
        )
        
        new_password_field = ft.TextField(
            label="Neues Passwort",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            hint_text="Min. 8 Zeichen, Groß/Klein, Zahl, Sonderzeichen",
            width=300,
        )
        
        confirm_password_field = ft.TextField(
            label="Neues Passwort bestätigen",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            width=300,
        )
        
        error_text = ft.Text("", color=ft.Colors.RED, size=12, visible=False)
        
        def on_save(e):
            current_pw = current_password_field.value
            new_pw = new_password_field.value
            confirm_pw = confirm_password_field.value
            
            # Validierung
            if not current_pw:
                error_text.value = "Bitte aktuelles Passwort eingeben."
                error_text.visible = True
                self.page.update()
                return

            # Passwort-Anforderungen prüfen
            is_valid, pw_error = self.profile_service.validate_password(new_pw)
            if not is_valid:
                error_text.value = pw_error
                error_text.visible = True
                self.page.update()
                return

            if new_pw != confirm_pw:
                error_text.value = "Passwörter stimmen nicht überein."
                error_text.visible = True
                self.page.update()
                return
            
            # Erst mit aktuellem Passwort authentifizieren
            try:
                email = self.profile_service.get_email()
                if not email:
                    error_text.value = "E-Mail nicht gefunden."
                    error_text.visible = True
                    self.page.update()
                    return
                
                # Re-Authentifizierung mit aktuellem Passwort
                auth_result = self.sb.auth.sign_in_with_password({
                    "email": email,
                    "password": current_pw
                })
                
                if not auth_result or not auth_result.user:
                    error_text.value = "Aktuelles Passwort ist falsch."
                    error_text.visible = True
                    self.page.update()
                    return

                # Neues Passwort setzen
                success, error_msg = self.profile_service.update_password(new_pw)
                
                if success:
                    self.page.close(dialog)
                    show_success_dialog(self.page, "Erfolg", "Passwort wurde geändert!")
                else:
                    error_text.value = error_msg or "Fehler beim Ändern."
                    error_text.visible = True
                    self.page.update()

            except Exception as ex:
                logger.error(f"Fehler beim Passwort ändern: {ex}", exc_info=True)
                error_text.value = "Aktuelles Passwort ist falsch."
                error_text.visible = True
                self.page.update()

        def on_cancel(e):
            self.page.close(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Passwort ändern", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    current_password_field,
                    ft.Divider(height=16),
                    new_password_field,
                    confirm_password_field,
                    error_text,
                ], spacing=8, tight=True),
                width=320,
            ),
            actions=[
                ft.TextButton("Abbrechen", on_click=on_cancel),
                ft.ElevatedButton("Speichern", icon=ft.Icons.SAVE, on_click=on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dialog)

    async def _handle_profile_image_upload(self, e: ft.FilePickerResultEvent):
        """Behandelt den Upload eines Profilbilds."""
        logger.info(f"_handle_profile_image_upload aufgerufen, files: {e.files}")

        if not e.files:
            logger.info("Keine Dateien ausgewählt")
            return

        try:
            selected_file = e.files[0]
            logger.info(f"Datei: name={selected_file.name}, path={selected_file.path}, size={selected_file.size}")

            if selected_file.path:
                # Desktop-Modus
                await self._process_profile_image(selected_file.path)
            else:
                # Web-Modus
                if selected_file.size and selected_file.size > 5 * 1024 * 1024:
                    show_error_dialog(self.page, "Fehler", "Die Datei ist zu groß. Max. 5 MB.")
                    return

                upload_name = f"profile_{uuid.uuid4().hex}_{selected_file.name}"
                self.profile_image_picker.upload([
                    ft.FilePickerUploadFile(
                        selected_file.name,
                        upload_url=self.page.get_upload_url(upload_name, 600),
                    )
                ])

                await asyncio.sleep(1)
                upload_dir = os.path.join(os.getcwd(), "image_uploads")
                file_path = os.path.join(upload_dir, upload_name)

                for _ in range(20):
                    if os.path.exists(file_path):
                        break
                    await asyncio.sleep(0.5)

                if os.path.exists(file_path):
                    await self._process_profile_image(file_path)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                else:
                    show_error_dialog(self.page, "Fehler", "Upload fehlgeschlagen. Bitte erneut versuchen.")

        except Exception as ex:
            logger.error(f"Fehler beim Upload: {ex}", exc_info=True)
            show_error_dialog(self.page, "Fehler", f"Fehler: {str(ex)}")

    async def _process_profile_image(self, file_path: str):
        """Verarbeitet und lädt ein Profilbild hoch."""
        success, image_url, error_msg = self.profile_service.upload_profile_image(file_path)

        if success and image_url:
            self._update_avatar_image(image_url)
            await self._load_user_data()
            show_success_dialog(self.page, "Erfolg", "Profilbild aktualisiert.")
        else:
            show_error_dialog(self.page, "Fehler", error_msg or "Upload fehlgeschlagen.")

    def _update_avatar_image(self, image_url: Optional[str]):
        """Aktualisiert den Avatar."""
        if image_url:
            # Cache-Busting: Timestamp anhängen um Browser-Caching zu vermeiden
            cache_buster = f"?t={int(time.time() * 1000)}"
            self.avatar.foreground_image_src = image_url + cache_buster
            self.avatar.content = None
        else:
            self.avatar.foreground_image_src = None
            self.avatar.content = ft.Icon(ft.Icons.PERSON, size=50, color=ft.Colors.WHITE)
        self.page.update()

    def _confirm_delete_profile_image(self):
        """Zeigt Bestätigungsdialog zum Löschen des Profilbilds."""
        def on_confirm(e):
            self.page.close(dialog)
            self.page.run_task(self._delete_profile_image)

        def on_cancel(e):
            self.page.close(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Profilbild löschen?"),
            content=ft.Text("Möchten Sie Ihr Profilbild wirklich löschen?"),
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

    async def _delete_profile_image(self):
        """Löscht das Profilbild des Benutzers."""
        try:
            # Bild aus Storage löschen
            if self.profile_service.delete_profile_image():
                # URL aus user_metadata entfernen
                self.profile_service._update_profile_image_url(None)

                # Avatar zurücksetzen
                self._update_avatar_image(None)

                # View neu laden um Button zu aktualisieren
                self._rebuild()

                show_success_dialog(self.page, "Erfolg", "Profilbild wurde gelöscht.")
            else:
                show_error_dialog(self.page, "Fehler", "Profilbild konnte nicht gelöscht werden.")
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Profilbilds: {e}", exc_info=True)
            show_error_dialog(self.page, "Fehler", f"Fehler: {str(e)}")

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
                _build_menu_item(ft.Icons.FAVORITE_BORDER, "Favorisierte Meldungen", "Meldungen mit ❤️", lambda _: self._show_favorites()),
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

        # Profilbild-Section
        def handle_file_pick(_):
            logger.info("Bild ändern geklickt - öffne FilePicker")
            self.profile_image_picker.pick_files(
                dialog_title="Profilbild auswählen",
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )

        def handle_delete_image(_):
            self._confirm_delete_profile_image()

        # Prüfen ob ein Profilbild vorhanden ist
        has_profile_image = self.profile_service.get_profile_image_url() is not None

        # Buttons für Profilbild
        image_buttons = [
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

        change_image_section = soft_card(
            ft.Column([
                _build_section_title("Profilbild"),
                ft.Container(height=8),
                ft.Row([
            self.avatar,
                    ft.Column([
                        ft.Row(image_buttons, spacing=8, wrap=True),
                        ft.Text("JPG, PNG oder WebP\nMax. 5 MB", size=12, color=ft.Colors.GREY_600),
                    ], spacing=8),
                ], spacing=20),
            ], spacing=8),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        # Name-Section
        current_name = self.display_name.value or "Benutzer"
        name_field = ft.TextField(
            value=current_name,
            width=300,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            label="Anzeigename",
            hint_text=f"Max. {MAX_DISPLAY_NAME_LENGTH} Zeichen",
            max_length=MAX_DISPLAY_NAME_LENGTH,
        )

        change_name_section = soft_card(
            ft.Column([
                _build_section_title("Anzeigename"),
                ft.Container(height=8),
                name_field,
                ft.Container(height=8),
                ft.FilledButton("Speichern", icon=ft.Icons.SAVE, on_click=lambda _: self.page.run_task(self._save_display_name, name_field)),
            ], spacing=8),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        # Passwort-Section
        password_section = soft_card(
            ft.Column([
                _build_section_title("Passwort"),
                ft.Container(height=8),
                ft.Text("Ändern Sie Ihr Passwort", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=8),
                ft.FilledButton(
                    "Passwort ändern",
                    icon=ft.Icons.LOCK,
                    on_click=lambda _: self._show_change_password_dialog(),
                ),
            ], spacing=8),
            pad=SECTION_PADDING,
            elev=CARD_ELEVATION,
        )

        return [back_button, change_image_section, change_name_section, password_section]

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

    # ════════════════════════════════════════════════════════════════════
    # HELPER für Mixins
    # ════════════════════════════════════════════════════════════════════

    def _show_success_dialog(self, title: str, message: str):
        """Zeigt einen Erfolgs-Dialog."""
        show_success_dialog(self.page, title, message)

    def _show_error_dialog(self, title: str, message: str):
        """Zeigt einen Fehler-Dialog."""
        show_error_dialog(self.page, title, message)

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
