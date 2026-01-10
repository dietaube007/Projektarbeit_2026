"""
My Saved Search Handler: Logik für gespeicherte Suchaufträge.
"""

from __future__ import annotations

from typing import Dict, Any
import flet as ft


def handle_apply_saved_search(
    page: ft.Page,
    search: Dict[str, Any],
) -> None:
    """Wendet einen gespeicherten Suchauftrag an und navigiert zur Startseite.
    
    Args:
        page: Flet Page-Instanz
        search: Suchauftrag-Dictionary
    """
    # Die Suche wird über die App angewendet
    # Speichern in session_storage zur Verwendung in DiscoverView
    page.session.set("apply_saved_search", search)
    page.go("/")

# build_saved_searches_list und build_search_card werden aus components.my_saved_search_components importiert
