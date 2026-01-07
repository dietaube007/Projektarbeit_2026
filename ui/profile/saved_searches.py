"""UI-Komponente für gespeicherte Suchaufträge im Profilbereich."""

from __future__ import annotations

from typing import Callable, Optional, List, Dict, Any
from datetime import datetime
import flet as ft

from ui.theme import soft_card
from ui.components import show_error_dialog, show_success_dialog
from services.saved_search import SavedSearchService
from services.references import ReferenceService


def build_saved_searches_list(
    page: ft.Page,
    saved_search_service: SavedSearchService,
    on_apply_search: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_back: Optional[Callable[[], None]] = None,
) -> ft.Column:
    """Erstellt die Liste der gespeicherten Suchaufträge.

    Args:
        page: Flet Page-Instanz
        saved_search_service: Service für Suchaufträge
        on_apply_search: Callback wenn ein Suchauftrag angewendet werden soll
        on_back: Callback für Zurück-Button

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
                    _build_search_card(
                        page,
                        search,
                        saved_search_service,
                        ref_service,
                        on_apply_search,
                        load_searches,
                    )
                )

        page.update()

    # Zurück-Button
    back_button = ft.Container(
        content=ft.Row([
            ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: on_back() if on_back else None,
            ),
            ft.Text("Gespeicherte Suchaufträge", size=18, weight=ft.FontWeight.BOLD),
        ], spacing=8),
        padding=ft.padding.only(bottom=8),
    )

    # Initial laden
    load_searches()

    return ft.Column([
        back_button,
        searches_container,
    ], spacing=12, expand=True)


def _build_search_card(
    page: ft.Page,
    search: Dict[str, Any],
    service: SavedSearchService,
    ref_service: ReferenceService,
    on_apply: Optional[Callable[[Dict[str, Any]], None]],
    on_reload: Callable[[], None],
) -> ft.Container:
    """Erstellt eine Karte für einen gespeicherten Suchauftrag."""
    search_id = search.get("id")
    name = search.get("name", "Unbekannt")
    created_at = search.get("created_at", "")

    # Datum formatieren
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
        filter_chips.append(_create_filter_chip(f"🔍 {str(search_query)[:20]}"))

    # Referenzdaten für Namen laden
    post_statuses = {s["id"]: s for s in ref_service.get_post_statuses()}
    species_list = {s["id"]: s for s in ref_service.get_species()}
    breeds_by_species = ref_service.get_breeds_by_species()
    sex_list = {s["id"]: s for s in ref_service.get_sex()}

    # Status
    status_id = filters.get("status_id")
    if status_id:
        status = post_statuses.get(int(status_id)) if isinstance(status_id, (int, str)) else None
        name = status.get("name") if status else f"Status #{status_id}"
        filter_chips.append(_create_filter_chip(f"📋 {name}"))

    # Tierart
    species_id = filters.get("species_id")
    if species_id:
        species = species_list.get(int(species_id)) if isinstance(species_id, (int, str)) else None
        name = species.get("name") if species else f"Tierart #{species_id}"
        filter_chips.append(_create_filter_chip(f"🐾 {name}"))

    # Rasse
    breed_id = filters.get("breed_id")
    if breed_id:
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
        name = breed_obj.get("name") if breed_obj else f"Rasse #{breed_id}"
        filter_chips.append(_create_filter_chip(f"🏷️ {name}"))

    # Geschlecht
    sex_id = filters.get("sex_id")
    if sex_id:
        sex = sex_list.get(int(sex_id)) if isinstance(sex_id, (int, str)) else None
        name = sex.get("name") if sex else f"Geschlecht #{sex_id}"
        filter_chips.append(_create_filter_chip(f"⚥ {name}"))

    # Farben
    colors = filters.get("colors", [])
    if colors and len(colors) > 0:
        filter_chips.append(_create_filter_chip(f"🎨 {len(colors)} Farben"))

    # Falls keine Filter aktiv
    if not filter_chips:
        filter_chips.append(_create_filter_chip("Alle Meldungen", ft.Colors.GREY_400))

    def on_delete_click(e):
        """Löscht den Suchauftrag nach Bestätigung."""
        def confirm_delete(e):
            page.close(dialog)
            success, error = service.delete_search(search_id)
            if success:
                on_reload()
            else:
                show_error_dialog(page, "Fehler", error or "Konnte nicht gelöscht werden.")

        def cancel_delete(e):
            page.close(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Suchauftrag löschen?"),
            content=ft.Text(f"Möchten Sie den Suchauftrag '{name}' wirklich löschen?"),
            actions=[
                ft.TextButton("Abbrechen", on_click=cancel_delete),
                ft.ElevatedButton(
                    "Löschen",
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=confirm_delete,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialog)

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


def _create_filter_chip(text: str, color: str = ft.Colors.BLUE_100) -> ft.Container:
    """Erstellt einen Filter-Chip."""
    return ft.Container(
        content=ft.Text(text, size=12, color=ft.Colors.GREY_800),
        bgcolor=color,
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )
