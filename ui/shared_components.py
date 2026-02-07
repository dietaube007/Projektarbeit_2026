"""
Wiederverwendbare UI-Komponenten.
"""

from __future__ import annotations

import flet as ft
from typing import Callable, Optional, Dict, Any

from ui.constants import STATUS_COLORS, SPECIES_COLORS, PRIMARY_COLOR
from ui.theme import soft_card, chip


# ══════════════════════════════════════════════════════════════════════
# BADGES
# ══════════════════════════════════════════════════════════════════════

def badge_for_typ(typ: str) -> ft.Control:
    """Erstellt ein Badge für den Meldungstyp (Vermisst/Fundtier).
    
    Args:
        typ: Meldungstyp (z.B. "Vermisst", "Fundtier")
    
    Returns:
        Control-Widget mit Badge für den Typ (verwendet chip() für konsistentes Design)
    """
    typ_lower = (typ or "").lower().strip()
    color = STATUS_COLORS.get(typ_lower, ft.Colors.GREY_700)
    label = typ.capitalize() if typ else "Unbekannt"
    return chip(label, color)


def badge_for_species(species: str) -> ft.Control:
    """Erstellt ein Badge für die Tierart.
    
    Args:
        species: Tierart (z.B. "Hund", "Katze")
    
    Returns:
        Control-Widget mit Badge für die Tierart (verwendet chip() für konsistentes Design)
    """
    species_lower = (species or "").lower().strip()
    color = SPECIES_COLORS.get(species_lower, ft.Colors.GREY_500)
    label = species.capitalize() if species else "Unbekannt"
    return chip(label, color)


# ══════════════════════════════════════════════════════════════════════
# PLATZHALTER
# ══════════════════════════════════════════════════════════════════════

def image_placeholder(height: int = 160, icon_size: int = 48, expand: bool = False, page: Optional[ft.Page] = None) -> ft.Container:
    """Erstellt einen Bild-Platzhalter.
    
    Args:
        height: Höhe des Platzhalters (Standard: 160)
        icon_size: Größe des Platzhalter-Icons (Standard: 48)
        expand: Ob der Container expandieren soll (Standard: False)
        page: Optional Page-Instanz für Theme-Erkennung
    
    Returns:
        Container mit Platzhalter-Icon
    """
    from ui.theme import get_theme_color
    
    is_dark = page.theme_mode == ft.ThemeMode.DARK if page else False
    bg_color = get_theme_color("card", is_dark) if page else ft.Colors.GREY_200
    
    return ft.Container(
        content=ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.GREY_400),
        height=height,
        alignment=ft.alignment.center,
        bgcolor=bg_color,
        border_radius=12,
        expand=expand,
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


def create_loading_indicator(
    text: str = "Laden...",
    size: int = 40,
    text_size: int = 14,
    padding: int = 40,
) -> ft.Container:
    """Erstellt einen zentrierten Loading-Indikator-Container.
    
    Args:
        text: Text der angezeigt wird (Standard: "Laden...")
        size: Größe des ProgressRing (Standard: 40)
        text_size: Schriftgröße des Textes (Standard: 14)
        padding: Padding des Containers (Standard: 40)
    
    Returns:
        Container mit zentriertem Loading-Indikator
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=size, height=size),
                ft.Text(text, size=text_size, color=ft.Colors.GREY_600),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=padding,
        alignment=ft.alignment.center,
    )


# ══════════════════════════════════════════════════════════════════════
# META-KOMPONENTEN
# ══════════════════════════════════════════════════════════════════════

def meta_row(icon: str, text: str) -> ft.Control:
    """Erstellt eine Zeile mit Icon und Text für Metadaten.
    
    Args:
        icon: Icon-Name (z.B. ft.Icons.LOCATION_ON)
        text: Anzuzeigender Text
    
    Returns:
        Row-Widget mit Icon und Text
    """
    return ft.Row(
        [
            ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(
                text,
                color=ft.Colors.ON_SURFACE_VARIANT,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                no_wrap=True,
                expand=True,
            ),
        ],
        spacing=6,
    )


# ══════════════════════════════════════════════════════════════════════
# CHIPS
# ══════════════════════════════════════════════════════════════════════

def filter_chip(text: str, color: Optional[str] = None) -> ft.Container:
    """Erstellt einen rechteckigen Filter-Chip für Filter-Anzeigen.
    
    Unterschied zu chip() aus theme.py:
    - Rechteckige Form (border_radius=12) statt Pille-Form
    - Dunkler Text (GREY_800) statt weißer Text
    - Größere Schrift (12px) und anderes Padding
    - Verwendet für Filter-Darstellung in gespeicherten Suchen
    
    Args:
        text: Text des Chips
        color: Hintergrundfarbe (Standard: Primary mit leichter Deckkraft)
    
    Returns:
        Container mit Filter-Chip
    """
    chip_color = color or ft.Colors.with_opacity(0.12, PRIMARY_COLOR)
    return ft.Container(
        content=ft.Text(text, size=12, color=ft.Colors.GREY_800),
        bgcolor=chip_color,
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )


# ══════════════════════════════════════════════════════════════════════
# EMPTY STATES (als Cards)
# ══════════════════════════════════════════════════════════════════════

def create_empty_state_card(message: str = "Noch keine Meldungen", subtitle: str = "") -> ft.Container:
    """Erstellt eine Empty-State-Karte.

    Args:
        message: Haupttext
        subtitle: Untertitel

    Returns:
        Container mit Empty-State (verwendet soft_card für konsistentes Design)
    """
    return soft_card(
        ft.Column(
            [
                ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
                ft.Text(message, weight=ft.FontWeight.W_600),
                ft.Text(subtitle, color=ft.Colors.GREY_700) if subtitle else ft.Container(),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        elev=1,
        pad=24,
    )


def create_no_results_card(on_reset: Optional[Callable] = None) -> ft.Container:
    """Erstellt eine "Keine Ergebnisse"-Karte.

    Args:
        on_reset: Optional Callback für Reset-Button

    Returns:
        Container mit No-Results-State (verwendet soft_card für konsistentes Design)
    """
    controls = [
        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY_400),
        ft.Text("Keine Meldungen gefunden", weight=ft.FontWeight.W_600),
        ft.Text("Versuchen Sie andere Suchkriterien", color=ft.Colors.GREY_700),
    ]
    
    if on_reset:
        controls.append(ft.TextButton("Filter zurücksetzen", on_click=on_reset))

    return soft_card(
        ft.Column(
            controls,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        elev=1,
        pad=24,
    )


# ══════════════════════════════════════════════════════════════════════
# SNACKBAR HELPER
# ══════════════════════════════════════════════════════════════════════

def show_login_required_snackbar(
    page: ft.Page,
    message: str = "Bitte melden Sie sich an, um diese Aktion durchzuführen.",
) -> None:
    """Zeigt eine SnackBar-Nachricht für Login-Required-Fälle.
    
    Args:
        page: Flet Page-Instanz
        message: Nachricht die angezeigt werden soll
    """
    page.snack_bar = ft.SnackBar(
        ft.Text(message),
        open=True,
    )
    page.update()


# ══════════════════════════════════════════════════════════════════════
# PROGRESS DIALOGS
# ══════════════════════════════════════════════════════════════════════

def show_progress_dialog(page: ft.Page, message: str = "Lädt...") -> ft.AlertDialog:
    """Zeigt einen modalen Fortschrittsdialog an.
    
    Args:
        page: Flet Page-Instanz
        message: Nachricht die angezeigt werden soll
    
    Returns:
        AlertDialog-Instanz (zum Schließen mit page.close())
    """
    dlg = ft.AlertDialog(
        modal=True,
        content=ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(width=24, height=24),
                    ft.Text(message, size=14),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            height=56,
            padding=0,
        ),
    )
    page.open(dlg)
    return dlg
