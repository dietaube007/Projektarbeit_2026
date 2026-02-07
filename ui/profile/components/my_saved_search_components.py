"""
My Saved Search Components: UI-Komponenten für gespeicherte Suchaufträge.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
from datetime import datetime

import flet as ft

from ui.theme import soft_card
from ui.shared_components import filter_chip, show_error_dialog
from services.posts.references import ReferenceService
from services.posts import SavedSearchService


def build_search_card(
    page: ft.Page,
    search: Dict[str, Any],
    service: SavedSearchService,
    ref_service: ReferenceService,
    on_apply: Optional[Callable[[Dict[str, Any]], None]],
    on_reload: Callable[[], None],
) -> ft.Container:
    """Erstellt eine Karte für einen gespeicherten Suchauftrag.
    
    Args:
        page: Flet Page-Instanz
        search: Suchauftrag-Dictionary
        service: SavedSearchService-Instanz
        ref_service: ReferenceService-Instanz
        on_apply: Optionaler Callback zum Anwenden der Suche
        on_reload: Callback zum Neuladen der Liste
    
    Returns:
        Container mit Suchauftrag-Karte
    """
    search_id = search.get("id")
    name = search.get("name", "Unbekannt")
    created_at = search.get("created_at", "")

    # Datum formatieren (TT.MM.JJJJ)
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%d.%m.%Y")
    except Exception:
        date_str = ""

    # Filter-Chips erstellen
    filter_chips = []

    # Filter liegen als JSON in search["filters"]
    filters = search.get("filters") or {}

    # Suchbegriff
    search_query = filters.get("search_query")
    if search_query:
        filter_chips.append(filter_chip(f"Suche: {str(search_query)[:20]}"))

    # Referenzdaten für Namen laden
    post_statuses = {s["id"]: s for s in ref_service.get_post_statuses()}
    species_list = {s["id"]: s for s in ref_service.get_species()}
    breeds_by_species = ref_service.get_breeds_by_species()
    sex_list = {s["id"]: s for s in ref_service.get_sex()}

    # Status
    status_id = filters.get("status_id")
    if status_id:
        status = post_statuses.get(int(status_id)) if isinstance(status_id, (int, str)) else None
        status_name = status.get("name") if status else f"Status #{status_id}"
        filter_chips.append(filter_chip(f"Status: {status_name}"))

    # Tierart
    species_id = filters.get("species_id")
    if species_id:
        species = species_list.get(int(species_id)) if isinstance(species_id, (int, str)) else None
        species_name = species.get("name") if species else f"Tierart #{species_id}"
        filter_chips.append(filter_chip(f"Tierart: {species_name}"))

    # Rasse
    rasse_value = filters.get("rasse")
    breed_id = filters.get("breed_id")
    # Prüfen, ob "keine_angabe" gespeichert ist
    if rasse_value == "keine_angabe":
        filter_chips.append(filter_chip("Rasse: Keine Angabe"))
    elif breed_id:
        breed_obj = None
        # Versuchen, über species_id -> breeds_by_species zu finden
        try:
            sid_int = int(species_id) if species_id is not None else None
            bid_int = int(breed_id)
        except (TypeError, ValueError):
            sid_int = None
            bid_int = None
        if sid_int is not None and bid_int is not None:
            for b in breeds_by_species.get(sid_int, []):
                if b.get("id") == bid_int:
                    breed_obj = b
                    break
        breed_name = breed_obj.get("name") if breed_obj else f"Rasse #{breed_id}"
        filter_chips.append(filter_chip(f"Rasse: {breed_name}"))

    # Geschlecht
    geschlecht_value = filters.get("geschlecht")
    sex_id = filters.get("sex_id")
    # Prüfen, ob "keine_angabe" gespeichert ist
    if geschlecht_value == "keine_angabe":
        filter_chips.append(filter_chip("Geschlecht: Keine Angabe"))
    elif sex_id:
        sex = sex_list.get(int(sex_id)) if isinstance(sex_id, (int, str)) else None
        sex_name = sex.get("name") if sex else f"Geschlecht #{sex_id}"
        filter_chips.append(filter_chip(f"Geschlecht: {sex_name}"))

    # Farben
    colors = filters.get("colors", [])
    if colors and len(colors) > 0:
        filter_chips.append(filter_chip(f"{len(colors)} Farben"))

    # Falls keine Filter aktiv
    if not filter_chips:
        filter_chips.append(filter_chip("Alle Meldungen", ft.Colors.GREY_400))

    def on_delete_click(e):
        """Löscht den Suchauftrag nach Bestätigung."""
        def confirm_delete(e):
            page.close(delete_dialog)
            success, error = service.delete_search(search_id)
            if success:
                on_reload()
            else:
                show_error_dialog(page, "Fehler", error or "Konnte nicht gelöscht werden.")

        def cancel_delete(e):
            page.close(delete_dialog)

        delete_dialog = create_delete_search_dialog(
            page=page,
            search_name=name,
            on_confirm=confirm_delete,
            on_cancel=cancel_delete,
        )
        page.open(delete_dialog)

    def on_apply_click(e):
        """Wendet den Suchauftrag an."""
        if on_apply:
            on_apply(search)

    return soft_card(
        ft.Column([
            # Header mit Name und Datum
            ft.Row([
                ft.Column([
                    ft.Text(name, size=16, weight=ft.FontWeight.W_600),
                    ft.Text(f"Erstellt am {date_str}", size=12, color=ft.Colors.GREY_600) if date_str else ft.Container(),
                ], spacing=2, expand=True),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    tooltip="Löschen",
                    on_click=on_delete_click,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            # Filter-Chips
            ft.Container(
                content=ft.Row(filter_chips, wrap=True, spacing=6, run_spacing=6),
                padding=ft.padding.only(top=8, bottom=8),
            ),

            # Anwenden-Button
            ft.Row([
                ft.FilledButton(
                    "Suche anwenden",
                    icon=ft.Icons.SEARCH,
                    on_click=on_apply_click,
                ),
            ], alignment=ft.MainAxisAlignment.END),
        ], spacing=4),
        pad=16,
        elev=2,
    )


def create_delete_search_dialog(
    page: ft.Page,
    search_name: str,
    on_confirm: Callable,
    on_cancel: Callable,
) -> ft.AlertDialog:
    """Erstellt den Bestätigungsdialog zum Löschen eines Suchauftrags.
    
    Args:
        page: Flet Page-Instanz
        search_name: Name des Suchauftrags
        on_confirm: Callback beim Bestätigen
        on_cancel: Callback beim Abbrechen
    
    Returns:
        AlertDialog für Löschung
    """
    delete_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Suchauftrag löschen?"),
        content=ft.Text(f"Möchten Sie den Suchauftrag '{search_name}' wirklich löschen?"),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton(
                "Löschen",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=on_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return delete_dialog


def build_saved_searches_list(
    page: ft.Page,
    saved_search_service: SavedSearchService,
    on_apply_search: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> ft.Column:
    """Erstellt die Liste der gespeicherten Suchaufträge (UI-Komponente).

    Args:
        page: Flet Page-Instanz
        saved_search_service: Service für Suchaufträge
        on_apply_search: Callback wenn ein Suchauftrag angewendet werden soll
    Returns:
        Column mit der Suchaufträge-Liste
    """
    searches_container = ft.Column(spacing=12)
    ref_service = ReferenceService(saved_search_service.sb)

    def load_searches():
        """Lädt die gespeicherten Suchen."""
        searches = saved_search_service.get_saved_searches()
        searches_container.controls.clear()

        if not searches:
            searches_container.controls.append(
                soft_card(
                    ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY_400),
                        ft.Text("Keine gespeicherten Suchaufträge", weight=ft.FontWeight.W_600),
                        ft.Text(
                            "Speichern Sie Ihre Suchfilter auf der Startseite,\num sie hier wiederzufinden.",
                            color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    pad=24,
                    elev=1,
                )
            )
        else:
            for search in searches:
                searches_container.controls.append(
                    build_search_card(
                        page,
                        search,
                        saved_search_service,
                        ref_service,
                        on_apply_search,
                        load_searches,
                    )
                )

        page.update()

    header = ft.Container(
        content=ft.Text("Gespeicherte Suchaufträge", size=18, weight=ft.FontWeight.BOLD),
        padding=ft.padding.only(bottom=8),
    )

    # Initial laden
    load_searches()

    return ft.Column([
        header,
        searches_container,
    ], spacing=12, expand=True)
