"""
Wiederverwendbare UI-Komponenten.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional, Dict, Any

from ui.constants import STATUS_COLORS, SPECIES_COLORS


# ══════════════════════════════════════════════════════════════════════
# DIALOGE
# ══════════════════════════════════════════════════════════════════════

def show_login_required_dialog(
    page: ft.Page,
    message: str,
    on_login: Callable[[], None],
    on_cancel: Optional[Callable[[], None]] = None,
    title: str = "Anmeldung erforderlich"
) -> None:
    """Zeigt einen Dialog wenn Login erforderlich ist.
    
    Args:
        page: Flet Page-Instanz
        message: Nachricht die angezeigt werden soll
        on_login: Callback-Funktion für Login-Button
        on_cancel: Optionaler Callback für Abbrechen-Button
        title: Titel des Dialogs (Standard: "Anmeldung erforderlich")
    """
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
    on_confirm: Callable[[], None],
    on_cancel: Optional[Callable[[], None]] = None,
    confirm_text: str = "Bestätigen",
    cancel_text: str = "Abbrechen"
) -> None:
    """Zeigt einen Bestätigungs-Dialog.
    
    Args:
        page: Flet Page-Instanz
        title: Titel des Dialogs
        message: Nachricht die angezeigt werden soll
        on_confirm: Callback-Funktion für Bestätigen-Button
        on_cancel: Optionaler Callback für Abbrechen-Button
        confirm_text: Text für Bestätigen-Button (Standard: "Bestätigen")
        cancel_text: Text für Abbrechen-Button (Standard: "Abbrechen")
    """
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

def status_badge(text: str, bgcolor: Optional[str] = None) -> ft.Container:
    """Erstellt ein Status-Badge.
    
    Args:
        text: Badge-Text
        bgcolor: Optionaler Hintergrundfarbe (Standard: aus STATUS_COLORS)
    
    Returns:
        Container mit Status-Badge
    """
    if bgcolor is None:
        bgcolor = STATUS_COLORS.get(text.lower(), ft.Colors.GREY_300)
    
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600),
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )


def species_badge(text: str, bgcolor: Optional[str] = None) -> ft.Container:
    """Erstellt ein Tierart-Badge.
    
    Args:
        text: Badge-Text
        bgcolor: Optionaler Hintergrundfarbe (Standard: aus SPECIES_COLORS)
    
    Returns:
        Container mit Tierart-Badge
    """
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
    """Erstellt einen Bild-Platzhalter.
    
    Args:
        height: Höhe des Platzhalters (Standard: 160)
        icon_size: Größe des Platzhalter-Icons (Standard: 48)
    
    Returns:
        Container mit Platzhalter-Icon
    """
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
    action_text: Optional[str] = None,
    on_action: Optional[Callable[[ft.ControlEvent], None]] = None
) -> ft.Column:
    """Erstellt eine Leere-Zustand-Anzeige.
    
    Args:
        icon: Icon-Name für die Anzeige
        title: Titel-Text
        subtitle: Optionaler Untertitel-Text
        action_text: Optionaler Text für Aktions-Button
        on_action: Optionaler Callback für Aktions-Button
    
    Returns:
        Column mit Leere-Zustand-Komponente
    """
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


# ══════════════════════════════════════════════════════════════════════
# DIALOGE - Zentrale Dialog-Funktionen
# ══════════════════════════════════════════════════════════════════════

def show_success_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_close: Optional[Callable[[], None]] = None
) -> None:
    """Zeigt einen Erfolgs-Dialog an.
    
    Args:
        page: Flet Page-Instanz
        title: Titel des Dialogs
        message: Nachricht die angezeigt werden soll
        on_close: Optionaler Callback der nach Schließen aufgerufen wird
    """
    def close_dialog(e: ft.ControlEvent) -> None:
        page.close(dlg)
        if on_close:
            on_close()
    
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
    
    page.open(dlg)


def show_error_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_close: Optional[Callable[[], None]] = None
) -> None:
    """Zeigt einen Fehler-Dialog an.
    
    Args:
        page: Flet Page-Instanz
        title: Titel des Dialogs
        message: Fehlermeldung die angezeigt werden soll
        on_close: Optionaler Callback der nach Schließen aufgerufen wird
    """
    def close_dialog(e: ft.ControlEvent) -> None:
        page.close(dlg)
        if on_close:
            on_close()
    
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
    
    page.open(dlg)


def show_validation_dialog(
    page: ft.Page,
    title: str,
    message: str,
    items: list[str],
    on_close: Optional[Callable[[], None]] = None
) -> None:
    """Zeigt einen Validierungs-Dialog mit Fehlermeldungen an.

    Args:
        page: Flet Page-Instanz
        title: Titel des Dialogs
        message: Hauptnachricht
        items: Liste von Validierungsfehlern die angezeigt werden sollen
        on_close: Optionaler Callback der nach Schließen aufgerufen wird
    """
    def close_dialog(e: ft.ControlEvent) -> None:
        page.close(dlg)
        if on_close:
            on_close()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_600, size=24),
                ft.Text(title, size=16, weight=ft.FontWeight.W_600),
            ],
            spacing=8,
        ),
        content=ft.Column(
            [
                ft.Text(message, size=13, color=ft.Colors.GREY_700),
                ft.Column(
                    [ft.Text(item, size=12, color=ft.Colors.GREY_800) for item in items],
                    spacing=2,
                ),
            ],
            spacing=8,
            tight=True,
        ),
        actions=[
            ft.TextButton("OK", on_click=close_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.open(dlg)


# ══════════════════════════════════════════════════════════════════════
# LOADING INDICATOR
# ══════════════════════════════════════════════════════════════════════

def loading_indicator(text: str = "Lädt...") -> ft.Row:
    """Erstellt einen Lade-Indikator mit ProgressRing und Text.

    Args:
        text: Text der neben dem Spinner angezeigt wird

    Returns:
        Row mit ProgressRing und Text
    """
    return ft.Row([
        ft.ProgressRing(width=24, height=24),
        ft.Text(text),
    ], spacing=12)
