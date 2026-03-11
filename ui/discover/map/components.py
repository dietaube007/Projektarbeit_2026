"""
Map-Komponenten: UI-Builder für die Kartenansicht in der Discover-View.
"""

from __future__ import annotations

import base64
from urllib.parse import unquote
from typing import List, Dict, Any, Optional, Callable

import flet as ft

from utils.map_generator import generate_map_html
from utils.logging_config import get_logger

logger = get_logger(__name__)


def build_map_container(
    posts: List[Dict[str, Any]],
    page: ft.Page,
    on_marker_click: Optional[Callable[[str], None]] = None,
    on_favorite_click: Optional[Callable[[str], None]] = None,
    center_lat: float = 51.1657,
    center_lon: float = 10.4515,
    zoom_level: int = 5,
    use_clustering: bool = True,
    map_height: Optional[float] = None,
) -> ft.Container:
    """Erstellt einen Container mit der interaktiven Karte.

    Args:
        posts: Liste von Post-Dictionaries mit Geokoordinaten
        page: Flet Page-Instanz
        on_marker_click: Callback wenn auf Marker geklickt wird (post_id)
        center_lat: Breitengrad des Zentrums
        center_lon: Längengrad des Zentrums
        zoom_level: Standard Zoom-Level (1-20)
        use_clustering: Marker-Clustering aktivieren

    Returns:
        Container mit WebView für die Karte
    """
    try:
        # Karten-HTML generieren
        logger.info(f"Generiere Karte mit {len(posts)} Posts...")
        html_map = generate_map_html(
            posts=posts,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom_level=zoom_level,
            use_clustering=use_clustering,
        )

        # Base64-Encoding für WebView
        html_bytes = html_map.encode("utf-8")
        html_b64 = base64.b64encode(html_bytes).decode("utf-8")
        data_url = f"data:text/html;charset=utf-8;base64,{html_b64}"

        # WebView erstellen
        webview = ft.WebView(
            url=data_url,
            expand=True,
            height=map_height,
            on_page_started=lambda e: on_url_change(e),
            on_page_ended=lambda e: on_url_change(e),
        )

        # URL-Change-Handler für Marker-/Favoriten-Klicks
        last_event_key = {"value": ""}

        def on_url_change(e):
            """Wird aufgerufen wenn URL sich ändert (Marker-/Favoriten-Click)."""
            try:
                raw_data = (
                    getattr(e, "data", None)
                    or getattr(e, "url", None)
                    or getattr(webview, "url", None)
                    or ""
                )

                post_id = ""
                action = ""

                if ("map_pin_click=" not in raw_data and "map_pin_click:" not in raw_data):
                    return

                if raw_data == last_event_key["value"]:
                    return
                last_event_key["value"] = raw_data

                if "map_pin_click=" in raw_data:
                    query_part = raw_data.split("map_pin_click=", 1)[-1]
                    post_id_encoded = query_part.split("&", 1)[0].strip()
                    post_id = unquote(post_id_encoded)
                    action = "detail"
                elif "map_pin_click:" in raw_data:
                    hash_part = raw_data.split("#")[-1] if "#" in raw_data else raw_data
                    payload = hash_part.split("map_pin_click:", 1)[-1].strip()
                    post_id_encoded = payload.split(":", 1)[0].strip()
                    post_id = unquote(post_id_encoded)
                    action = "detail"

                if post_id:
                    logger.info(f"Map-Event ({action}) für Post: {post_id}")
                    if action == "detail" and on_marker_click:
                        on_marker_click(post_id)

                    # Nach Klick zurück auf die Karten-URL, damit die Karte sichtbar bleibt
                    webview.url = data_url
                    page.update()
            except Exception as ex:
                logger.error(f"Fehler beim Verarbeiten des Marker-Klicks: {ex}")

        webview.on_change = on_url_change
        if hasattr(webview, "on_url_change"):
            webview.on_url_change = on_url_change

        # Container mit Karte
        container = ft.Container(
            content=webview,
            expand=True,
            height=map_height,
            bgcolor=ft.Colors.SURFACE,
        )

        logger.info("Karte erfolgreich erstellt")
        return container

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Karte: {e}", exc_info=True)
        # Fallback auf Error-Container
        return ft.Container(
            content=build_map_error(str(e)),
            expand=True,
        )


def build_map_loading_indicator() -> ft.Control:
    """Erstellt einen Loading-Indikator für die Karte.

    Returns:
        Loading-UI Element
    """
    return ft.Column(
        [
            ft.Container(height=80),
            ft.ProgressRing(
                width=60,
                height=60,
                stroke_width=4,
                color=ft.Colors.PRIMARY,
            ),
            ft.Container(height=20),
            ft.Text(
                "Karte wird geladen...",
                size=16,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Text(
                "Bitte warten",
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
    )


def build_map_empty_state() -> ft.Control:
    """Erstellt einen Empty-State wenn keine Posts auf der Karte.

    Returns:
        Empty-State UI Element
    """
    return ft.Column(
        [
            ft.Container(height=80),
            ft.Icon(
                ft.Icons.MAP_OUTLINED,
                size=100,
                color=ft.Colors.GREY_400,
            ),
            ft.Container(height=20),
            ft.Text(
                "Keine Meldungen zur Anzeige",
                size=20,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Container(height=8),
            ft.Text(
                "Passe deine Filter an oder erstelle eine neue Meldung",
                size=14,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
        spacing=0,
    )


def build_map_error(error_message: str = "Unbekannter Fehler") -> ft.Control:
    """Erstellt einen Error-State bei Karten-Fehlern.

    Args:
        error_message: Fehlermeldung

    Returns:
        Error-State UI Element
    """
    return ft.Column(
        [
            ft.Container(height=60),
            ft.Icon(
                ft.Icons.ERROR_OUTLINE,
                size=80,
                color=ft.Colors.ERROR,
            ),
            ft.Container(height=16),
            ft.Text(
                "Fehler beim Laden der Karte",
                size=18,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Container(height=8),
            ft.Text(
                error_message,
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=16),
            ft.Text(
                "Bitte wechsle zurück zur Listenansicht",
                size=12,
                color=ft.Colors.PRIMARY,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
        spacing=0,
    )
