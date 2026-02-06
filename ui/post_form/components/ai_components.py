"""
AI-Komponenten: UI-Komponenten für KI-Rassenerkennung.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any

import flet as ft


def create_ai_recognition_button(on_click: Callable) -> ft.ElevatedButton:
    """Erstellt den Button für die KI-Rassenerkennung."""
    return ft.ElevatedButton(
        "🤖 KI-Rassenerkennung starten",
        icon=ft.Icons.AUTO_AWESOME,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.PURPLE_600,
        )
    )


def create_ai_result_container() -> ft.Container:
    """Erstellt den Container für KI-Erkennungsergebnisse."""
    outline = getattr(ft.Colors, "OUTLINE_VARIANT", None) or ft.Colors.PURPLE_200
    surface_low = getattr(ft.Colors, "SURFACE_CONTAINER_LOW", None) or ft.Colors.PURPLE_50
    return ft.Container(
        key="ai_result_container",
        content=ft.Column([], spacing=8),
        visible=False,
        padding=15,
        border=ft.border.all(2, outline),
        border_radius=8,
        bgcolor=surface_low,
    )


def create_consent_dialog(
    page: ft.Page,
    on_accept: Callable[[], None],
) -> ft.AlertDialog:
    """Erstellt den Einverständnisdialog für die KI-Erkennung.
    
    Args:
        page: Flet Page-Instanz
        on_accept: Callback der aufgerufen wird wenn Nutzer akzeptiert
    
    Returns:
        AlertDialog für Einverständnis
    """
    consent_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PURPLE_600, size=24),
                ft.Text("KI-Rassenerkennung", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Einverständniserklärung:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Text(
                        "Das hochgeladene Bild wird durch eine KI analysiert, um die Tierart und Rasse zu erkennen. "
                        "Die Analyse erfolgt lokal und das Bild wird nicht an externe Dienste gesendet.",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Wichtige Hinweise:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Text(
                        "• Die KI-Erkennung dient nur als Vorschlag\n"
                        "• Es gibt keine Garantie für die Richtigkeit\n"
                        "• Sie können den Vorschlag ablehnen und selbst eintragen\n"
                        "• Bei Unsicherheit kontaktieren Sie ein Tierheim",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            width=400,
        ),
        actions=[
            ft.TextButton(
                "Abbrechen",
                on_click=lambda e: page.close(consent_dlg)
            ),
            ft.FilledButton(
                "Akzeptieren & Starten",
                on_click=lambda e: (
                    page.close(consent_dlg),
                    on_accept()
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return consent_dlg


def create_ai_result_content(
    result: Dict[str, Any],
    on_accept: Callable[[], None],
    on_reject: Callable[[], None],
) -> ft.Column:
    """Erstellt den Content für das KI-Erkennungsergebnis.
    
    Args:
        result: Ergebnis-Dictionary von der Erkennung
        on_accept: Callback wenn Nutzer Ergebnis übernimmt
        on_reject: Callback wenn Nutzer Ergebnis ablehnt
    
    Returns:
        Column mit Ergebnis-Anzeige
    """
    confidence = result.get("confidence", 0.0)
    species = result.get("species") or "—"
    breed = result.get("breed") or "—"
    confidence_percent = int(confidence * 100)
    outline = getattr(ft.Colors, "OUTLINE_VARIANT", None) or ft.Colors.PURPLE_200
    surface_low = getattr(ft.Colors, "SURFACE_CONTAINER_LOW", None) or ft.Colors.ORANGE_50

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.PURPLE_600, size=20),
                    ft.Text(
                        "KI-Erkennungsergebnis",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                ],
                spacing=8,
            ),
            ft.Divider(height=10, color=outline),
            ft.Text(
                f"Tierart: {species}",
                size=13,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Text(
                f"Rasse: {breed}",
                size=13,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Text(
                f"Konfidenz: {confidence_percent}%",
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Container(
                content=ft.Text(
                    "Hinweis: Dies ist nur ein KI-Vorschlag ohne Garantie auf Richtigkeit.",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    italic=True,
                ),
                padding=8,
                bgcolor=surface_low,
                border_radius=4,
            ),
            ft.Divider(height=10, color=outline),
            ft.Row(
                [
                    ft.TextButton(
                        "Ablehnen",
                        icon=ft.Icons.CLOSE,
                        on_click=lambda _: on_reject(),
                    ),
                    ft.FilledButton(
                        "Übernehmen",
                        icon=ft.Icons.CHECK,
                        on_click=lambda _: on_accept(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
                spacing=10,
            ),
        ],
        spacing=8,
    )


def create_ai_suggestion_dialog(
    page: ft.Page,
    error_message: str,
    suggested_breed: str,
    suggested_species: Optional[str],
    confidence: float,
    on_accept: Callable[[str, Optional[str]], None],
) -> ft.AlertDialog:
    """Erstellt einen Dialog mit KI-Vorschlag bei niedriger Konfidenz.
    
    Args:
        page: Flet Page-Instanz
        error_message: Fehlermeldung
        suggested_breed: Vorgeschlagene Rasse
        suggested_species: Vorgeschlagene Tierart
        confidence: Konfidenz-Wert
        on_accept: Callback wenn Nutzer Vorschlag übernimmt
    
    Returns:
        AlertDialog mit KI-Vorschlag
    """
    confidence_percent = int(confidence * 100)
    
    content_controls = [
        ft.Text(error_message, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
        ft.Divider(),
        ft.Text(f"Vorgeschlagene Rasse: {suggested_breed}", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
    ]
    if suggested_species:
        content_controls.append(
            ft.Text(f"Vorgeschlagene Tierart: {suggested_species}", size=13, color=ft.Colors.ON_SURFACE)
        )
    content_controls.extend([
        ft.Text(f"Konfidenz: {confidence_percent}%", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
        ft.Container(
            content=ft.Text(
                "Hinweis: Die Konfidenz ist niedrig. Bitte prüfen Sie den Vorschlag sorgfältig.",
                size=11,
                color=ft.Colors.ON_SURFACE_VARIANT,
                italic=True,
            ),
            padding=8,
            bgcolor=getattr(ft.Colors, "SURFACE_CONTAINER_LOW", None) or ft.Colors.ORANGE_50,
            border_radius=4,
        ),
    ])
    suggestion_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("KI-Vorschlag (niedrige Konfidenz)", color=ft.Colors.ON_SURFACE),
        content=ft.Container(
            content=ft.Column(
                content_controls,
                spacing=8,
                tight=True,
            ),
            width=400,
        ),
        actions=[
            ft.TextButton(
                "Abbrechen",
                on_click=lambda e: page.close(suggestion_dlg)
            ),
            ft.FilledButton(
                "Trotzdem übernehmen",
                on_click=lambda e: (
                    page.close(suggestion_dlg),
                    on_accept(suggested_breed, suggested_species)
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return suggestion_dlg
