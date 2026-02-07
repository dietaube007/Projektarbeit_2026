"""
Auth-Flow fuer Login in PetBuddy.

Enthaelt das Login-Overlay und die Login-Logik.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft
from supabase import Client

from ui.auth import AuthView
from ui.constants import PRIMARY_COLOR


class AuthFlow:
    """Kapselt Login-Flow inkl. Overlay und Navigation."""

    def __init__(
        self,
        page: ft.Page,
        sb: Client,
        set_logged_in: Callable[[bool], None],
        clear_pending_tab: Callable[[], None],
    ) -> None:
        self.page = page
        self.sb = sb
        self._set_logged_in = set_logged_in
        self._clear_pending_tab = clear_pending_tab
        self._auth_view: Optional[AuthView] = None
        self._redirect_loading_overlay: Optional[ft.Container] = None

    @property
    def auth_view(self) -> Optional[AuthView]:
        return self._auth_view

    @property
    def redirect_loading_overlay(self) -> Optional[ft.Container]:
        return self._redirect_loading_overlay

    async def _navigate_after_login(self) -> None:
        """Kurze Verzoegerung, dann Navigation zur Startseite (nach Login)."""
        import asyncio

        await asyncio.sleep(1.2)
        self.page.go("/")

    def _build_loading_overlay(self) -> ft.Container:
        """Erstellt das Lade-Overlay passend zum aktuellen Theme-Modus (Light/Dark)."""
        from ui.theme import get_theme_color

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        return ft.Container(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(
                            width=48, height=48, stroke_width=3, color=PRIMARY_COLOR
                        ),
                        ft.Container(height=16),
                        ft.Text(
                            "Einen Moment, Sie werden weitergeleitet...",
                            size=16,
                            weight=ft.FontWeight.W_500,
                            color=get_theme_color("text_primary", is_dark),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=12),
                        ft.ProgressBar(
                            width=200,
                            color=PRIMARY_COLOR,
                            bgcolor=ft.Colors.with_opacity(0.2, PRIMARY_COLOR),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=get_theme_color("card", is_dark),
                padding=32,
                border_radius=0,
                shadow=ft.BoxShadow(
                    blur_radius=24,
                    spread_radius=0,
                    color=ft.Colors.with_opacity(
                        0.25 if is_dark else 0.15, ft.Colors.BLACK
                    ),
                ),
            ),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.with_opacity(
                0.7 if is_dark else 0.5, ft.Colors.BLACK
            ),
        )

    def show_login(self) -> None:
        """Zeigt die Login-Maske inkl. Redirect-Overlay."""
        # Setze Route direkt, um Endlosschleife zu vermeiden
        self.page.route = "/login"

        def on_login_success() -> None:
            self._set_logged_in(True)
            self._clear_pending_tab()
            # Overlay immer neu erstellen, damit es den aktuellen Theme-Modus widerspiegelt
            self._redirect_loading_overlay = self._build_loading_overlay()
            if self._redirect_loading_overlay not in self.page.overlay:
                self.page.overlay.append(self._redirect_loading_overlay)
            self.page.update()
            self.page.run_task(self._navigate_after_login)

        def on_continue_without_account() -> None:
            self._set_logged_in(False)
            self._clear_pending_tab()
            self.page.go("/")

        self._auth_view = AuthView(
            page=self.page,
            sb=self.sb,
            on_auth_success=on_login_success,
            on_continue_without_account=on_continue_without_account,
        )

        # Seite fuer Login vorbereiten
        self.page.appbar = None
        self.page.navigation_bar = None
        self.page.controls.clear()
        self.page.add(self._auth_view.build())
        self.page.update()
