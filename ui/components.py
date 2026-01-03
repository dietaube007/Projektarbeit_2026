"""
Wiederverwendbare UI-Komponenten.
"""

import flet as ft
from typing import Callable, Optional

from ui.constants import STATUS_COLORS, SPECIES_COLORS


# ══════════════════════════════════════════════════════════════════════
# DIALOGE
# ══════════════════════════════════════════════════════════════════════

def show_login_required_dialog(
    page: ft.Page,
    message: str,
    on_login: Callable,
    on_cancel: Optional[Callable] = None,
    title: str = "Anmeldung erforderlich"
):
    """Zeigt einen Dialog wenn Login erforderlich ist."""
    def handle_login(e):
        page.close(dialog)
        on_login()
    
    def handle_cancel(e):
        page.close(dialog)
        if on_cancel:
            on_cancel()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Abbrechen", on_click=handle_cancel),
            ft.ElevatedButton("Anmelden", on_click=handle_login),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.open(dialog)


def show_confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: Callable,
    on_cancel: Optional[Callable] = None,
    confirm_text: str = "Bestätigen",
    cancel_text: str = "Abbrechen"
):
    """Zeigt einen Bestätigungs-Dialog."""
    def handle_confirm(e):
        page.close(dialog)
        on_confirm()
    
    def handle_cancel(e):
        page.close(dialog)
        if on_cancel:
            on_cancel()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton(cancel_text, on_click=handle_cancel),
            ft.ElevatedButton(confirm_text, on_click=handle_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.open(dialog)


# ══════════════════════════════════════════════════════════════════════
# BADGES
# ══════════════════════════════════════════════════════════════════════

def status_badge(text: str, bgcolor: str = None) -> ft.Container:
    """Erstellt ein Status-Badge."""
    if bgcolor is None:
        bgcolor = STATUS_COLORS.get(text.lower(), ft.Colors.GREY_300)
    
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600),
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )


def species_badge(text: str, bgcolor: str = None) -> ft.Container:
    """Erstellt ein Tierart-Badge."""
    if bgcolor is None:
        bgcolor = SPECIES_COLORS.get(text.lower(), ft.Colors.GREY_300)
    
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600),
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )


# ══════════════════════════════════════════════════════════════════════
# PLATZHALTER
# ══════════════════════════════════════════════════════════════════════

def image_placeholder(height: int = 160, icon_size: int = 48) -> ft.Container:
    """Erstellt einen Bild-Platzhalter."""
    return ft.Container(
        content=ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.GREY_400),
        height=height,
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.GREY_200,
        border_radius=12,
    )


# ══════════════════════════════════════════════════════════════════════
# BANNER
# ══════════════════════════════════════════════════════════════════════

def login_banner(on_login_click: Callable) -> ft.Container:
    """Erstellt ein Login-Banner für nicht eingeloggte Benutzer."""
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
                    on_click=on_login_click,
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


# ══════════════════════════════════════════════════════════════════════
# LEERE ZUSTÄNDE
# ══════════════════════════════════════════════════════════════════════

def empty_state(
    icon: str,
    title: str,
    subtitle: str = "",
    action_text: str = None,
    on_action: Callable = None
) -> ft.Column:
    """Erstellt eine Leere-Zustand-Anzeige."""
    controls = [
        ft.Container(height=40),
        ft.Icon(icon, size=64, color=ft.Colors.GREY_400),
        ft.Text(title, size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_600),
    ]
    
    if subtitle:
        controls.append(ft.Text(subtitle, color=ft.Colors.GREY_500))
    
    if action_text and on_action:
        controls.append(ft.Container(height=16))
        controls.append(
            ft.ElevatedButton(action_text, icon=ft.Icons.ADD, on_click=on_action)
        )
    
    return ft.Column(
        controls,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )
