"""
Profile View - Benutzer-Profilbereich.

Dieses Modul implementiert die Profilseite der PetBuddy-Anwendung.
Benutzer können ihre Profildaten einsehen, bearbeiten und sich abmelden.

"""

from typing import Callable, Optional
import flet as ft
from ui.theme import soft_card


class ProfileView:
    # Klasse für den Profilbereich.
    
    # ════════════════════════════════════════════════════════════════════
    # KONSTANTEN
    # ════════════════════════════════════════════════════════════════════
    
    PRIMARY_COLOR = "#5B6EE1"
    
    def __init__(
        self,
        page: ft.Page,
        sb,
        on_logout: Optional[Callable] = None
    ):
        # Initialisiert die Profil-Ansicht.
        self.page = page
        self.sb = sb
        self.on_logout = on_logout
        
        # Benutzerdaten
        self.user_data = None
        self.user_profile = None
        
        # Aktueller Bereich (Hauptmenü oder Untermenü)
        self.current_view = "main"
        self.main_container = ft.Column(spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # UI-Elemente initialisieren
        self._init_ui_elements()
        
        # Daten laden
        self.page.run_task(self._load_user_data)
    
    def _init_ui_elements(self):
        # Initialisiert alle UI-Elemente.
        # Profilbild
        self.avatar = ft.CircleAvatar(
            radius=50,
            bgcolor=self.PRIMARY_COLOR,
            content=ft.Icon(ft.Icons.PERSON, size=50, color=ft.Colors.WHITE),
        )
        
        # Benutzerinfo
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
        # Lädt die Benutzerdaten.
        try:
            # Auth-User holen
            user_response = self.sb.auth.get_user()
            if user_response and user_response.user:
                self.user_data = user_response.user
                
                # E-Mail anzeigen
                self.email_text.value = self.user_data.email or ""
                
                # Profildaten aus public.user laden
                profile = self.sb.table("user").select("*").eq(
                    "id", self.user_data.id
                ).single().execute()
                
                if profile.data:
                    self.user_profile = profile.data
                    self.display_name.value = profile.data.get("display_name", "Benutzer")
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
        # Zeigt das Hauptmenü.
        self.current_view = "main"
        self._rebuild()
    
    def _show_edit_profile(self):
        # Zeigt das Profil-Bearbeiten-Menü.
        self.current_view = "edit_profile"
        self._rebuild()
    
    def _show_settings(self):
        # Zeigt die Einstellungen.
        self.current_view = "settings"
        self._rebuild()
    
    def _rebuild(self):
        # Baut die Ansicht neu.
        self.main_container.controls.clear()
        
        if self.current_view == "main":
            self.main_container.controls = self._build_main_menu()
        elif self.current_view == "edit_profile":
            self.main_container.controls = self._build_edit_profile()
        elif self.current_view == "settings":
            self.main_container.controls = self._build_settings()
        
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # AKTIONEN
    # ════════════════════════════════════════════════════════════════════
    
    def _logout(self):
        # Meldet den Benutzer ab.
        try:
            self.sb.auth.sign_out()
            if self.on_logout:
                self.on_logout()
        except Exception as e:
            print(f"Fehler beim Abmelden: {e}")
    
    # ════════════════════════════════════════════════════════════════════
    # UI KOMPONENTEN
    # ════════════════════════════════════════════════════════════════════
    
    def _build_menu_item(self, icon: str, title: str, subtitle: str = "", on_click=None) -> ft.Container:
        # Erstellt einen Menüpunkt.
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=self.PRIMARY_COLOR),
                        padding=12,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.1, self.PRIMARY_COLOR),
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
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD - HAUPTMENÜ
    # ════════════════════════════════════════════════════════════════════
    
    def _build_main_menu(self) -> list:
        # Baut das Hauptmenü.
        # Profil-Header
        profile_header = soft_card(
            ft.Column(
                [
                    # Avatar und Name
                    ft.Row(
                        [
                            self.avatar,
                            ft.Column(
                                [
                                    self.display_name,
                                    self.email_text,
                                ],
                                spacing=4,
                                expand=True,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=16,
            ),
            pad=20,
            elev=2,
        )
        
        # Menü-Liste
        menu_list = soft_card(
            ft.Column(
                [
                    self._build_menu_item(
                        ft.Icons.EDIT_OUTLINED,
                        "Profil bearbeiten",
                        on_click=lambda _: self._show_edit_profile(),
                    ),
                    ft.Divider(height=1),
                    self._build_menu_item(
                        ft.Icons.ARTICLE_OUTLINED,
                        "Meine Meldungen",
                        on_click=lambda _: print("Meine Meldungen"),
                    ),
                    ft.Divider(height=1),
                    self._build_menu_item(
                        ft.Icons.FAVORITE_BORDER,
                        "Favorisierte Meldungen",
                        on_click=lambda _: print("Favorisierte Meldungen"),
                    ),
                    ft.Divider(height=1),
                    self._build_menu_item(
                        ft.Icons.SETTINGS_OUTLINED,
                        "Einstellungen",
                        on_click=lambda _: self._show_settings(),
                    ),
                    ft.Divider(height=1),
                    self._build_menu_item(
                        ft.Icons.HELP_OUTLINE,
                        "Hilfe & Support",
                        on_click=lambda _: print("Hilfe & Support"),
                    ),
                    ft.Divider(height=1),
                    self._build_menu_item(
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
        
        # Abmelden-Button
        logout_button = ft.Container(
            content=ft.OutlinedButton(
                "Abmelden",
                icon=ft.Icons.LOGOUT,
                on_click=lambda _: self._logout(),
                style=ft.ButtonStyle(
                    color=ft.Colors.RED,
                    side=ft.BorderSide(1, ft.Colors.RED),
                ),
                width=200,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=8, bottom=24),
        )
        
        return [profile_header, menu_list, logout_button]
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD - PROFIL BEARBEITEN
    # ════════════════════════════════════════════════════════════════════
    
    def _build_edit_profile(self) -> list:
        # Baut die Profil-Bearbeiten-Ansicht.
        # Zurück-Button
        back_button = ft.Container(
            content=ft.TextButton(
                "← Zurück",
                on_click=lambda _: self._show_main_menu(),
            ),
            padding=ft.padding.only(bottom=8),
        )
        
        # Bild ändern
        change_image_section = soft_card(
            ft.Column(
                [
                    ft.Text("Profilbild", size=18, weight=ft.FontWeight.W_600),
                    ft.Container(height=8),
                    ft.Row(
                        [
                            self.avatar,
                            ft.FilledButton(
                                "Bild ändern",
                                icon=ft.Icons.CAMERA_ALT,
                                on_click=lambda _: print("Bild ändern - Funktion kommt später"),
                            ),
                        ],
                        spacing=20,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
                spacing=8,
            ),
            pad=20,
            elev=2,
        )
        
        # Name ändern
        change_name_section = soft_card(
            ft.Column(
                [
                    ft.Text("Anzeigename", size=18, weight=ft.FontWeight.W_600),
                    ft.Container(height=8),
                    ft.TextField(
                        value=self.display_name.value,
                        width=300,
                        prefix_icon=ft.Icons.PERSON_OUTLINE,
                    ),
                    ft.Container(height=8),
                    ft.FilledButton(
                        "Speichern",
                        icon=ft.Icons.SAVE,
                        on_click=lambda _: print("Name speichern - Funktion kommt später"),
                    ),
                ],
                spacing=8,
            ),
            pad=20,
            elev=2,
        )
        
        # Passwort zurücksetzen
        password_section = soft_card(
            ft.Column(
                [
                    ft.Text("Passwort", size=18, weight=ft.FontWeight.W_600),
                    ft.Container(height=8),
                    ft.Text(
                        "Setze dein Passwort zurück",
                        size=14,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Container(height=8),
                    ft.OutlinedButton(
                        "Passwort zurücksetzen",
                        icon=ft.Icons.LOCK_RESET,
                        on_click=lambda _: print("Passwort zurücksetzen - Funktion kommt später"),
                    ),
                ],
                spacing=8,
            ),
            pad=20,
            elev=2,
        )
        
        return [back_button, change_image_section, change_name_section, password_section]
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD - EINSTELLUNGEN
    # ════════════════════════════════════════════════════════════════════
    
    def _build_settings(self) -> list:
        # Baut die Einstellungen-Ansicht.
        # Zurück-Button
        back_button = ft.Container(
            content=ft.TextButton(
                "← Zurück",
                on_click=lambda _: self._show_main_menu(),
            ),
            padding=ft.padding.only(bottom=8),
        )
        
        # Benachrichtigungen
        notifications_section = soft_card(
            ft.Column(
                [
                    ft.Text("Benachrichtigungen", size=18, weight=ft.FontWeight.W_600),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.NOTIFICATIONS_OUTLINED, color=self.PRIMARY_COLOR),
                            ft.Column(
                                [
                                    ft.Text("Push-Benachrichtigungen", size=14),
                                    ft.Text("Erhalte Updates zu deinen Meldungen", size=12, color=ft.Colors.GREY_600),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Switch(value=True, on_change=lambda _: print("Benachrichtigung geändert")),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=20),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.EMAIL_OUTLINED, color=self.PRIMARY_COLOR),
                            ft.Column(
                                [
                                    ft.Text("E-Mail-Benachrichtigungen", size=14),
                                    ft.Text("Erhalte wichtige Updates per E-Mail", size=12, color=ft.Colors.GREY_600),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Switch(value=False, on_change=lambda _: print("E-Mail geändert")),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=8,
            ),
            pad=20,
            elev=2,
        )
        
        return [back_button, notifications_section]
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD
    # ════════════════════════════════════════════════════════════════════
    
    def build(self) -> ft.Column:
        # Baut und gibt das Layout zurück.
        self.main_container.controls = self._build_main_menu()
        return self.main_container
    
    async def refresh(self):
        # Aktualisiert die Profildaten.
        await self._load_user_data()
        self._show_main_menu()
