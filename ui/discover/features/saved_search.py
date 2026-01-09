"""
Saved Search-Feature: UI und Logik für gespeicherte Suchaufträge.
"""

from __future__ import annotations

from typing import Optional, Callable, Dict, Any
import flet as ft

from ui.constants import PRIMARY_COLOR, MESSAGE_COLOR_ERROR
from ui.components import show_success_dialog
from services.posts import SavedSearchService
from utils.logging_config import get_logger

logger = get_logger(__name__)


def show_save_search_dialog(
    page: ft.Page,
    saved_search_service: SavedSearchService,
    current_filters: Dict[str, Any],
    on_saved: Optional[Callable[[], None]] = None,
) -> None:
    """Zeigt Dialog zum Speichern der aktuellen Suche.

    Args:
        page: Flet Page-Instanz
        saved_search_service: SavedSearchService-Instanz
        current_filters: Dictionary mit aktuellen Filterwerten
        on_saved: Optional Callback nach erfolgreichem Speichern
    """
    name_field = ft.TextField(
        label="Name des Suchauftrags",
        hint_text="z.B. 'Vermisste Katzen in Berlin'",
        width=300,
        autofocus=True,
        value="",
        key="saved_search_name_field",
    )
    error_text = ft.Text("", color=MESSAGE_COLOR_ERROR, size=12, visible=False)

    active_filters = []
    search_query = current_filters.get("search_query", "")
    if search_query:
        active_filters.append(f"Suche: {search_query[:20]}")
    if current_filters.get("status_id"):
        active_filters.append("Kategorie")
    if current_filters.get("species_id"):
        active_filters.append("Tierart")
    if current_filters.get("breed_id"):
        active_filters.append("Rasse")
    if current_filters.get("sex_id"):
        active_filters.append("Geschlecht")
    colors = current_filters.get("colors", [])
    if colors:
        active_filters.append(f"{len(colors)} Farben")

    filter_preview = ft.Text(
        ", ".join(active_filters) if active_filters else "Alle Meldungen (keine Filter aktiv)",
        size=12,
        color=ft.Colors.GREY_600,
    )

    def on_save(e):
        name = str(name_field.value or "").strip()
        
        if not name:
            error_text.value = "Bitte geben Sie einen Namen ein."
            error_text.visible = True
            page.update()
            return

        sex_id = current_filters.get("sex_id")
        breed_id = current_filters.get("breed_id")
        filters_dict = current_filters.get("filters", {})
        geschlecht_value = filters_dict.get("geschlecht")
        rasse_value = filters_dict.get("rasse")
        if geschlecht_value == "keine_angabe":
            sex_id = "keine_angabe"
        if rasse_value == "keine_angabe":
            breed_id = "keine_angabe"
        
        success, error = saved_search_service.save_search(
            name=name,
            search_query=current_filters.get("search_query"),
            status_id=current_filters.get("status_id"),
            species_id=current_filters.get("species_id"),
            breed_id=breed_id,
            sex_id=sex_id,
            colors=current_filters.get("colors"),
        )

        if success:
            page.close(dialog)
            show_success_dialog(
                page,
                "Suchauftrag gespeichert",
                f"'{name}' wurde gespeichert.\n\nSie finden ihn unter Profil → Gespeicherte Suchaufträge."
            )
            if on_saved:
                on_saved()
        else:
            logger.error(f"Fehler beim Speichern des Suchauftrags '{name}': {error}")
            error_text.value = error or "Fehler beim Speichern."
            error_text.visible = True
            page.update()

    def on_cancel(e):
        page.close(dialog)

    name_field.value = ""
    error_text.value = ""
    error_text.visible = False
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.BOOKMARK_ADD, color=PRIMARY_COLOR),
            ft.Text("Suche speichern", weight=ft.FontWeight.BOLD),
        ], spacing=8),
        content=ft.Container(
            content=ft.Column([
                ft.Text("Aktive Filter:", size=14, weight=ft.FontWeight.W_500),
                filter_preview,
                ft.Container(height=12),
                name_field,
                error_text,
            ], spacing=8, tight=True),
            width=350,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton(
                "Speichern",
                icon=ft.Icons.SAVE,
                on_click=on_save,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dialog)
