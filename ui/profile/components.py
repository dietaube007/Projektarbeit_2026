"""
ui/profile/components.py
Gemeinsame UI-Komponenten für die Profil-Ansicht.
"""

import flet as ft


PRIMARY_COLOR: str = "#5B6EE1"
AVATAR_RADIUS: int = 50
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


def build_back_button(on_click) -> ft.Container:
    """Erstellt einen Zurück-Button."""
    return ft.Container(
        content=ft.TextButton(
            "← Zurück",
            on_click=on_click,
        ),
        padding=ft.padding.only(bottom=8),
    )


def build_section_title(title: str) -> ft.Text:
    """Erstellt einen Abschnitts-Titel."""
    return ft.Text(title, size=18, weight=ft.FontWeight.W_600)


def build_setting_row(
    icon,
    title: str,
    subtitle: str,
    control: ft.Control,
) -> ft.Row:
    """Erstellt eine Einstellungs-Zeile. """
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


def build_menu_item(
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
                    content=ft.Icon(icon, size=24, color=PRIMARY_COLOR),
                    padding=12,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY_COLOR),
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


def build_logout_button(on_click) -> ft.Container:
    """Erstellt den Logout-Button."""
    return ft.Container(
        content=ft.OutlinedButton(
            "Abmelden",
            icon=ft.Icons.LOGOUT,
            on_click=on_click,
            style=ft.ButtonStyle(
                color=ft.Colors.RED,
                side=ft.BorderSide(1, ft.Colors.RED),
            ),
            width=200,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.only(top=8, bottom=24),
    )


def build_avatar(display_name: str = "") -> ft.CircleAvatar:
    """Erstellt einen Avatar."""
    # Falls Name vorhanden, könnten wir Initialen anzeigen
    # Für jetzt: Standard-Icon
    return ft.CircleAvatar(
        radius=AVATAR_RADIUS,
        bgcolor=PRIMARY_COLOR,
        content=ft.Icon(
            ft.Icons.PERSON,
            size=AVATAR_RADIUS,
            color=ft.Colors.WHITE,
        ),
    )


def loading_indicator(text: str = "Lädt...") -> ft.Row:
    """Erstellt einen Lade-Indikator."""
    return ft.Row(
        [
            ft.ProgressRing(width=24, height=24),
            ft.Text(text),
        ],
        spacing=12,
    )
