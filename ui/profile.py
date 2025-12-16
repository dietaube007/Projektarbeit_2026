"""
Profile View - Benutzer-Profilbereich.

Dieses Modul implementiert die Profilseite der PetBuddy-Anwendung.
Benutzer können ihre Profildaten einsehen, bearbeiten, Favoriten ansehen und sich abmelden.
"""

from typing import Callable, Optional, List
import flet as ft
from ui.theme import soft_card


class ProfileView:
    """Benutzer-Profilbereich mit Einstellungen und Profilverwaltung."""

    # ════════════════════════════════════════════════════════════════════
    # KONSTANTEN
    # ════════════════════════════════════════════════════════════════════

    PRIMARY_COLOR: str = "#5B6EE1"
    AVATAR_RADIUS: int = 50
    SECTION_PADDING: int = 20
    CARD_ELEVATION: int = 2

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
        """Initialisiert die Profil-Ansicht.

        Args:
            page: Flet Page-Instanz
            sb: Supabase Client
            on_logout: Callback nach Logout
            on_favorites_changed: Callback, wenn sich Favoriten ändern
        """
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
            radius=self.AVATAR_RADIUS,
            bgcolor=self.PRIMARY_COLOR,
            content=ft.Icon(
                ft.Icons.PERSON,
                size=self.AVATAR_RADIUS,
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
            self.favorites_list.controls = [
                ft.Row([ft.ProgressRing(), ft.Text("Favoriten werden geladen...")], spacing=12)
            ]
            self.page.update()

            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                self.favorites_items = []
                self._render_favorites_list(not_logged_in=True)
                return

            user_id = user_resp.user.id

            # 1) Favoriten-Einträge lesen
            fav_res = (
                self.sb.table("favorite")
                .select("post_id")
                .eq("user_id", user_id)
                .execute()
            )
            fav_rows = fav_res.data or []

            post_ids = [row["post_id"] for row in fav_rows if row.get("post_id")]

            if not post_ids:
                self.favorites_items = []
                self._render_favorites_list()
                return

            # 2) Dazu passende Posts laden
            posts_res = (
                self.sb.table("post")
                .select(
                    """
                    id,
                    headline,
                    location_text,
                    event_date,
                    created_at,
                    is_active,
                    post_status(id, name),
                    species(id, name),
                    breed(id, name),
                    post_image(url),
                    post_color(color(id, name))
                    """
                )
                .in_("id", post_ids)
                .order("created_at", desc=True)
                .execute()
            )

            self.favorites_items = posts_res.data or []
            self._render_favorites_list()

        except Exception as e:
            print(f"Fehler beim Laden der Favoriten: {e}")
            self.favorites_items = []
            self._render_favorites_list()

    def _render_favorites_list(self, not_logged_in: bool = False):
        """Rendert die Favoriten-Liste."""
        self.favorites_list.controls.clear()

        if not_logged_in:
            self.favorites_list.controls.append(
                ft.Text("Bitte einloggen um Favoriten zu sehen.", color=ft.Colors.GREY_600)
            )
        elif not self.favorites_items:
            self.favorites_list.controls.append(
                ft.Text("Du hast noch keine Meldungen favorisiert.", color=ft.Colors.GREY_600)
            )
        else:
            for post in self.favorites_items:
                self.favorites_list.controls.append(self._favorite_card(post))
        
        self.page.update()

    def _favorite_card(self, post: dict) -> ft.Control:
        """Erstellt eine Karte für eine favorisierte Meldung."""
        # Daten extrahieren
        post_id = post.get("id")
        title = post.get("headline") or "Ohne Namen"
        
        post_status = post.get("post_status") or {}
        typ = post_status.get("name", "Unbekannt") if isinstance(post_status, dict) else "Unbekannt"
        
        species = post.get("species") or {}
        art = species.get("name", "Unbekannt") if isinstance(species, dict) else "Unbekannt"
        
        breed = post.get("breed") or {}
        rasse = breed.get("name", "Mischling") if isinstance(breed, dict) else "Unbekannt"
        
        post_colors = post.get("post_color") or []
        farben_namen = [
            pc.get("color", {}).get("name", "")
            for pc in post_colors
            if pc.get("color")
        ]
        farbe = ", ".join(farben_namen) if farben_namen else ""
        
        ort = post.get("location_text") or ""
        when = (post.get("event_date") or post.get("created_at") or "")[:10]
        status = "Aktiv" if post.get("is_active") else "Inaktiv"
        
        # Bild
        post_images = post.get("post_image") or []
        img_src = post_images[0].get("url") if post_images else None
        
        if img_src:
            visual_content = ft.Image(
                src=img_src,
                height=220,
                fit=ft.ImageFit.COVER,
                gapless_playback=True,
            )
        else:
            visual_content = ft.Container(
                height=220,
                bgcolor=ft.Colors.GREY_100,
                alignment=ft.alignment.center,
                content=ft.Icon(
                    ft.Icons.PETS,
                    size=64,
                    color=ft.Colors.GREY_500,
                ),
            )
        
        visual = ft.Container(
            content=visual_content,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_200,
        )
        
        # Badges
        def badge(label: str, color: str) -> ft.Control:
            return ft.Container(
                content=ft.Text(label, size=12),
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=20,
                bgcolor=color,
            )
        
        badges = ft.Row(
            [
                badge(typ, "#C5CAE9"),
                badge(art, "#B2DFDB"),
            ],
            spacing=8,
            wrap=True,
        )
        
        # Entfernen-Button
        remove_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE,
            icon_color=ft.Colors.RED,
            tooltip="Aus Favoriten entfernen",
            on_click=lambda e, pid=post_id: self._remove_favorite(pid),
        )
        
        header = ft.Row(
            [
                ft.Text(title, size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                badges,
                remove_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        meta_row = ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(ort if ort else "—", color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SCHEDULE, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(when if when else "—", color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LABEL, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(status, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=6,
                ),
            ],
            spacing=16,
            wrap=True,
        )
        
        line1 = ft.Text(
            f"{rasse} • {farbe}".strip(" • "),
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        
        card_inner = ft.Column(
            [visual, header, line1, meta_row],
            spacing=10,
        )
        
        return soft_card(card_inner, pad=12, elev=3)

    def _remove_favorite(self, post_id):
        """Entfernt einen Post aus den Favoriten."""
        try:
            user_resp = self.sb.auth.get_user()
            if not user_resp or not user_resp.user:
                return
            
            user_id = user_resp.user.id
            
            # Aus Datenbank löschen
            (
                self.sb.table("favorite")
                .delete()
                .eq("user_id", user_id)
                .eq("post_id", post_id)
                .execute()
            )
            
            # Lokal entfernen
            self.favorites_items = [
                p for p in self.favorites_items if p.get("id") != post_id
            ]
            self._render_favorites_list()
            
            # Startseite informieren
            if self.on_favorites_changed:
                self.on_favorites_changed()
        
        except Exception as e:
            print(f"Fehler beim Entfernen aus Favoriten: {e}")

    def _build_favorites(self) -> list:
        """Baut die Favoriten-Ansicht."""
        back_button = self._build_back_button()
        
        favorites_card = soft_card(
            ft.Column(
                [
                    self._build_section_title("Favorisierte Meldungen"),
                    ft.Container(height=8),
                    self.favorites_list,
                ],
                spacing=12,
            ),
            pad=self.SECTION_PADDING,
            elev=self.CARD_ELEVATION,
        )
        
        return [back_button, favorites_card]

    # ════════════════════════════════════════════════════════════════════
    # UI KOMPONENTEN
    # ════════════════════════════════════════════════════════════════════

    def _build_back_button(self) -> ft.Container:
        """Erstellt einen Zurück-Button."""
        return ft.Container(
            content=ft.TextButton(
                "← Zurück",
                on_click=lambda _: self._show_main_menu(),
            ),
            padding=ft.padding.only(bottom=8),
        )

    def _build_section_title(self, title: str) -> ft.Text:
        """Erstellt einen Abschnitts-Titel."""
        return ft.Text(title, size=18, weight=ft.FontWeight.W_600)

    def _build_setting_row(
        self, icon, title: str, subtitle: str, control: ft.Control
    ) -> ft.Row:
        """Erstellt eine Einstellungs-Zeile."""
        return ft.Row(
            [
                ft.Icon(icon, color=self.PRIMARY_COLOR),
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

    def _build_menu_item(
        self,
        icon: str,
        title: str,
        subtitle: str = "",
        on_click=None,
    ) -> ft.Container:
        """Erstellt einen Menüpunkt."""
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
                            ft.Text(subtitle, size=12, color=ft.Colors.GREY_600)
                            if subtitle
                            else ft.Container(),
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
            pad=self.SECTION_PADDING,
            elev=self.CARD_ELEVATION,
        )

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
                        subtitle="Meldungen, die du mit ❤️ markiert hast",
                        on_click=lambda _: self._show_favorites(),
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
        """Baut die Profil-Bearbeiten-Ansicht."""
        change_image_section = soft_card(
            ft.Column(
                [
                    self._build_section_title("Profilbild"),
                    ft.Container(height=8),
                    ft.Row(
                        [
                            self.avatar,
                            ft.FilledButton(
                                "Bild ändern",
                                icon=ft.Icons.CAMERA_ALT,
                                on_click=lambda _: print("Bild ändern"),
                            ),
                        ],
                        spacing=20,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
                spacing=8,
            ),
            pad=self.SECTION_PADDING,
            elev=self.CARD_ELEVATION,
        )

        change_name_section = soft_card(
            ft.Column(
                [
                    self._build_section_title("Anzeigename"),
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
                        on_click=lambda _: print("Name speichern"),
                    ),
                ],
                spacing=8,
            ),
            pad=self.SECTION_PADDING,
            elev=self.CARD_ELEVATION,
        )

        password_section = soft_card(
            ft.Column(
                [
                    self._build_section_title("Passwort"),
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
                        on_click=lambda _: print("Passwort zurücksetzen"),
                    ),
                ],
                spacing=8,
            ),
            pad=self.SECTION_PADDING,
            elev=self.CARD_ELEVATION,
        )

        return [
            self._build_back_button(),
            change_image_section,
            change_name_section,
            password_section,
        ]

    # ════════════════════════════════════════════════════════════════════
    # BUILD - EINSTELLUNGEN
    # ════════════════════════════════════════════════════════════════════

    def _build_settings(self) -> list:
        """Baut die Einstellungen-Ansicht."""
        notifications_section = soft_card(
            ft.Column(
                [
                    self._build_section_title("Benachrichtigungen"),
                    ft.Container(height=12),
                    self._build_setting_row(
                        ft.Icons.NOTIFICATIONS_OUTLINED,
                        "Push-Benachrichtigungen",
                        "Erhalte Updates zu deinen Meldungen",
                        ft.Switch(
                            value=True,
                            on_change=lambda _: print("Benachrichtigung geändert"),
                        ),
                    ),
                    ft.Divider(height=20),
                    self._build_setting_row(
                        ft.Icons.EMAIL_OUTLINED,
                        "E-Mail-Benachrichtigungen",
                        "Erhalte wichtige Updates per E-Mail",
                        ft.Switch(
                            value=False,
                            on_change=lambda _: print("E-Mail geändert"),
                        ),
                    ),
                ],
                spacing=8,
            ),
            pad=self.SECTION_PADDING,
            elev=self.CARD_ELEVATION,
        )

        return [self._build_back_button(), notifications_section]

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