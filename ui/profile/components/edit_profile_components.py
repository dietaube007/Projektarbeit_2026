"""
Edit Profile Components: UI-Komponenten für Profil-Bearbeitung.
Enthält Sections und Dialoge für: Profilbild, Display Name, Passwort, Konto löschen.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from ui.theme import soft_card
from utils.constants import MAX_DISPLAY_NAME_LENGTH
from .menu_components import create_section_title

# Konstanten
SECTION_PADDING: int = 20
CARD_ELEVATION: int = 2


# ============================================================================
# SECTIONS (für Bearbeiten-View)
# ============================================================================

def create_profile_image_section(
    avatar: ft.CircleAvatar,
    profile_image_picker: ft.FilePicker,
    has_profile_image: bool,
    on_file_pick: Callable,
    on_delete_image: Callable,
) -> ft.Control:
    """Erstellt die Profilbild-Section im Bearbeiten-View.
    
    Args:
        avatar: CircleAvatar-Widget
        profile_image_picker: FilePicker-Instanz
        has_profile_image: Ob bereits ein Profilbild vorhanden ist
        on_file_pick: Callback für Dateiauswahl
        on_delete_image: Callback für Bild-Löschung
    
    Returns:
        Container mit Profilbild-Section
    """
    image_buttons: list[ft.Control] = [
        ft.FilledButton("Bild ändern", icon=ft.Icons.CAMERA_ALT, on_click=on_file_pick),
        ft.OutlinedButton(
            "Bild löschen",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=on_delete_image,
            style=ft.ButtonStyle(color=ft.Colors.RED, side=ft.BorderSide(1, ft.Colors.RED)),
        ),
    ]

    return soft_card(
        ft.Column(
            [
                create_section_title("Profilbild"),
                ft.Container(height=8),
                ft.Row(
                    [
                        avatar,
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


def create_display_name_section(
    current_name: str,
    on_save: Callable[[ft.TextField], None],
    page: ft.Page,
) -> ft.Control:
    """Erstellt die Anzeigename-Section im Bearbeiten-View.
    
    Args:
        current_name: Aktueller Anzeigename
        on_save: Callback zum Speichern (erhält TextField)
        page: Flet Page-Instanz
    
    Returns:
        Container mit Anzeigename-Section
    """
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
                create_section_title("Anzeigename"),
                ft.Container(height=8),
                name_field,
                ft.Container(height=8),
                ft.FilledButton(
                    "Speichern",
                    icon=ft.Icons.SAVE,
                    on_click=lambda _: page.run_task(on_save, name_field),
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


def create_password_section(
    on_change_password: Callable,
) -> ft.Control:
    """Erstellt die Passwort-Section im Bearbeiten-View.
    
    Args:
        on_change_password: Callback zum Ändern des Passworts
    
    Returns:
        Container mit Passwort-Section
    """
    return soft_card(
        ft.Column(
            [
                create_section_title("Passwort"),
                ft.Container(height=8),
                ft.Text("Ändern Sie Ihr Passwort", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=8),
                ft.FilledButton(
                    "Passwort ändern",
                    icon=ft.Icons.LOCK,
                    on_click=on_change_password,
                ),
            ],
            spacing=8,
        ),
        pad=SECTION_PADDING,
        elev=CARD_ELEVATION,
    )


def create_delete_account_section(
    on_delete_account: Callable,
) -> ft.Control:
    """Erstellt die Konto-löschen-Section im Bearbeiten-View.
    
    Args:
        on_delete_account: Callback zum Löschen des Kontos
    
    Returns:
        Container mit Konto-löschen-Section
    """
    return soft_card(
        ft.Column(
            [
                create_section_title("Konto löschen"),
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
                    on_click=on_delete_account,
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


# ============================================================================
# DIALOGS
# ============================================================================

def create_change_password_dialog(
    page: ft.Page,
    on_save: Callable[[ft.ControlEvent], None],
    on_cancel: Callable[[ft.ControlEvent], None],
) -> ft.AlertDialog:
    """Erstellt den Dialog zum Ändern des Passworts.
    
    Args:
        page: Flet Page-Instanz
        on_save: Callback beim Speichern (erhält ControlEvent)
        on_cancel: Callback beim Abbrechen (erhält ControlEvent)
    
    Returns:
        AlertDialog für Passwort-Änderung
    """
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

    def on_save_handler(e: ft.ControlEvent) -> None:
        on_save(e)

    def on_cancel_handler(e: ft.ControlEvent) -> None:
        on_cancel(e)

    password_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Passwort ändern", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(
                [
                    current_password_field,
                    ft.Divider(height=16),
                    new_password_field,
                    confirm_password_field,
                    error_text,
                ],
                spacing=8,
                tight=True,
            ),
            width=320,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_handler),
            ft.ElevatedButton("Speichern", icon=ft.Icons.SAVE, on_click=on_save_handler),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    # Zugriff auf Fields für Validierung
    password_dialog._current_field = current_password_field
    password_dialog._new_field = new_password_field
    password_dialog._confirm_field = confirm_password_field
    password_dialog._error_text = error_text
    
    return password_dialog


def create_delete_account_dialog(
    page: ft.Page,
    on_confirm: Callable[[str], None],
) -> ft.AlertDialog:
    """Erstellt den Bestätigungsdialog zum Löschen des Kontos.
    
    Args:
        page: Flet Page-Instanz
        on_confirm: Callback mit Bestätigungstext
    
    Returns:
        AlertDialog für Konto-Löschung
    """
    confirm_field = ft.TextField(
        label="Zur Bestätigung 'LÖSCHEN' eingeben",
        width=300,
    )
    error_text = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

    def on_confirm_handler(e: ft.ControlEvent) -> None:
        if confirm_field.value != "LÖSCHEN":
            error_text.value = "Bitte geben Sie 'LÖSCHEN' ein, um fortzufahren."
            error_text.visible = True
            page.update()
            return

        page.close(delete_dialog)
        on_confirm(confirm_field.value)

    def on_cancel_handler(e: ft.ControlEvent) -> None:
        page.close(delete_dialog)

    delete_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=28),
                ft.Text("Konto wirklich löschen?", weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Diese Aktion kann nicht rückgängig gemacht werden!\n\n"
                        "Alle mit Ihrem Konto verbundenen Daten werden gelöscht.",
                        size=14,
                    ),
                    ft.Container(height=16),
                    confirm_field,
                    error_text,
                ],
                spacing=8,
                tight=True,
            ),
            width=350,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_handler),
            ft.ElevatedButton(
                "Endgültig löschen",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=on_confirm_handler,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return delete_dialog


def create_delete_profile_image_dialog(
    page: ft.Page,
    on_confirm: Callable[[], None],
) -> ft.AlertDialog:
    """Erstellt den Bestätigungsdialog zum Löschen des Profilbilds.
    
    Args:
        page: Flet Page-Instanz
        on_confirm: Callback beim Bestätigen
    
    Returns:
        AlertDialog für Profilbild-Löschung
    """
    def on_confirm_handler(e: ft.ControlEvent) -> None:
        page.close(profile_image_dialog)
        on_confirm()

    def on_cancel_handler(e: ft.ControlEvent) -> None:
        page.close(profile_image_dialog)

    profile_image_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Profilbild löschen?"),
        content=ft.Text("Möchten Sie Ihr Profilbild wirklich löschen?"),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel_handler),
            ft.ElevatedButton(
                "Löschen",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=on_confirm_handler,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return profile_image_dialog


# ============================================================================
# VIEW BUILDER
# ============================================================================

def create_edit_profile_view(
    avatar: ft.CircleAvatar,
    profile_image_picker: ft.FilePicker,
    has_profile_image: bool,
    current_name: str,
    on_file_pick: Callable,
    on_delete_image: Callable,
    on_save_display_name: Callable[[ft.TextField], None],
    page: ft.Page,
    on_change_password: Callable,
    on_delete_account: Callable,
) -> list[ft.Control]:
    """Erstellt die Profil-Bearbeiten-Ansicht.
    
    Args:
        avatar: CircleAvatar-Widget
        profile_image_picker: FilePicker-Instanz
        has_profile_image: Ob bereits ein Profilbild vorhanden ist
        current_name: Aktueller Anzeigename
        on_file_pick: Callback für Dateiauswahl
        on_delete_image: Callback für Bild-Löschung
        on_save_display_name: Callback zum Speichern (erhält TextField)
        page: Flet Page-Instanz
        on_change_password: Callback zum Ändern des Passworts
        on_delete_account: Callback zum Löschen des Kontos
    Returns:
        Liste von Controls für Edit Profile-View
    """
    change_image_section = create_profile_image_section(
        avatar=avatar,
        profile_image_picker=profile_image_picker,
        has_profile_image=has_profile_image,
        on_file_pick=on_file_pick,
        on_delete_image=on_delete_image,
    )

    change_name_section = create_display_name_section(
        current_name=current_name,
        on_save=on_save_display_name,
        page=page,
    )

    password_section = create_password_section(
        on_change_password=on_change_password,
    )

    delete_account_section = create_delete_account_section(
        on_delete_account=on_delete_account,
    )

    return [
        change_image_section,
        change_name_section,
        password_section,
        delete_account_section,
    ]
