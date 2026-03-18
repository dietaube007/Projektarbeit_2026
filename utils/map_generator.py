"""
Karten-Generator: Erstellt interaktive HTML-Karten mit Folium + OpenStreetMap.

Features:
- Marker mit runden Bild-Thumbnails (50x50px)
- Farbkodierung: Rot = Vermisst, Orange = Gefunden/Fundtier, Gruen = Wiedervereint
- Marker-Clustering bei vielen Posts
- Click-Handler für Detail-Ansicht
- Zoom + Pan Funktionalität
"""

from __future__ import annotations

import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

import folium
from folium import plugins

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Farb-Schema für Meldungstypen
COLORS = {
    "vermisst": "#EF4444",      # Rot (Tailwind Red-500)
    "gefunden": "#F59E0B",      # Orange (Tailwind Amber-500)
    "wiedervereint": "#22C55E", # Gruen (Tailwind Green-500)
}
DEFAULT_COLOR = "#3B82F6"  # Blau als Fallback


def _normalize_status_key(status_name: str) -> str:
    """Normalisiert Statusnamen auf interne Marker-Farbkeys."""
    status_lower = (status_name or "").strip().lower()
    if "wiedervereint" in status_lower:
        return "wiedervereint"
    if "fundtier" in status_lower or "gefunden" in status_lower or "zugelaufen" in status_lower:
        return "gefunden"
    return "vermisst"


def create_marker_icon_html(
    image_url: Optional[str],
    post_type: str,
    species_emoji: str = "🐾",
    size: int = 50,
) -> str:
    """Erstellt HTML für einen runden Marker mit Bild oder Icon.

    Args:
        image_url: URL zum Post-Bild (oder None)
        post_type: "vermisst", "gefunden" oder "wiedervereint"
        species_emoji: Fallback-Emoji wenn kein Bild
        size: Größe in Pixeln

    Returns:
        HTML-String für das Marker-Icon
    """
    color = COLORS.get(post_type, DEFAULT_COLOR)

    # Prüfe ob Bild-URL vorhanden
    has_image = image_url and image_url.strip() not in {"", "null", "None", "undefined"}

    if has_image:
        # Marker mit Bild (rund)
        html = f"""
        <div style="
            width: {size}px;
            height: {size}px;
            border-radius: 50%;
            overflow: hidden;
            border: 3px solid {color};
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            background: white;
            cursor: pointer;
        ">
            <img 
                src="{image_url}" 
                style="width: 100%; height: 100%; object-fit: cover;"
                onerror="this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;width:100%;height:100%;font-size:28px;\\'>{species_emoji}</div>';"
            />
        </div>
        """
    else:
        # Marker ohne Bild: Emoji/Icon
        html = f"""
        <div style="
            width: {size}px;
            height: {size}px;
            border-radius: 50%;
            background-color: {color};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: white;
            border: 3px solid white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            cursor: pointer;
        ">{species_emoji}</div>
        """

    return html


def create_popup_html(post: Dict[str, Any], image_url: Optional[str], post_id: str, is_favorite: bool = False) -> str:
    """Erstellt HTML für das Popup beim Hover über Marker.

    Args:
        post: Post-Dictionary
        image_url: URL zum Bild
        post_id: ID des Posts
        is_favorite: Ob der Post favorisiert ist

    Returns:
        HTML-String für das Popup
    """
    import html as html_module
    from datetime import datetime
    
    headline = html_module.escape(post.get("headline", "Ohne Titel"))
    location = html_module.escape(post.get("location_text", "Ort unbekannt"))
    description = html_module.escape(post.get("description", "")[:100] + "..." if len(post.get("description", "")) > 100 else post.get("description", ""))
    
    # Species extrahieren
    species = post.get("species") or {}
    species_name = html_module.escape(species.get("name", "") if isinstance(species, dict) else "")
    
    # Rasse extrahieren
    breed = post.get("breed") or {}
    breed_name = html_module.escape(breed.get("name", "") if isinstance(breed, dict) else "")
    
    # Geschlecht extrahieren  
    sex = post.get("sex") or {}
    sex_name = html_module.escape(sex.get("name", "") if isinstance(sex, dict) else "")
    
    # Typ bestimmen
    post_status = post.get("post_status") or {}
    status_name = post_status.get("name", "") if isinstance(post_status, dict) else ""
    status_key = _normalize_status_key(status_name)
    if status_key == "wiedervereint":
        post_type = "Wiedervereint"
    elif status_key == "gefunden":
        post_type = "Gefunden"
    else:
        post_type = "Vermisst"
    
    # Datum formatieren
    created_at = post.get("created_at", "")
    try:
        if created_at:
            date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = date_obj.strftime("%d.%m.%Y")
        else:
            date_str = ""
    except:
        date_str = ""

    safe_post_id = html_module.escape(post_id)
    
    # Herz-Symbol basierend auf Favoriten-Status
    heart_icon = "❤️" if is_favorite else "♡"
    heart_color = "#ef4444" if is_favorite else "#6b7280"

    # Zusätzliche Details nur wenn vorhanden
    extra_info = ""
    if breed_name:
        extra_info += f"""        <p style="margin: 4px 0; font-size: 13px; color: #4b5563;">
            <strong>Rasse:</strong> {breed_name}
        </p>
"""
    if sex_name:
        extra_info += f"""        <p style="margin: 4px 0; font-size: 13px; color: #4b5563;">
            <strong>Geschlecht:</strong> {sex_name}
        </p>
"""
    if description:
        extra_info += f"""        <p style="margin: 8px 0 4px 0; font-size: 12px; color: #6b7280; font-style: italic;">
            {description}
        </p>
"""

    html_str = f"""
    <div style="width: 260px; font-family: 'Segoe UI', Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; color: #1f2937; font-size: 15px; font-weight: 600;">
            {headline}
        </h4>
        <p style="margin: 4px 0; font-size: 13px; color: #4b5563;">
            <strong>Typ:</strong> {post_type}
        </p>
        <p style="margin: 4px 0; font-size: 13px; color: #4b5563;">
            <strong>Tierart:</strong> {species_name}
        </p>
{extra_info}        <p style="margin: 4px 0; font-size: 13px; color: #6b7280;">
            📍 {location}
        </p>
        {f'<p style="margin: 4px 0; font-size: 12px; color: #9ca3af;">📅 {date_str}</p>' if date_str else ''}
        <p style="margin: 12px 0 0 0; font-size: 16px; font-weight: 500;">
            <a href="#" onclick="return false;" style="color:{heart_color}; text-decoration:none; cursor: default;">{heart_icon} Favorisieren</a>
        </p>
    </div>
    """
    return html_str


def generate_map_html(
    posts: List[Dict[str, Any]],
    center_lat: float = 51.1657,
    center_lon: float = 10.4515,
    zoom_level: int = 5,
    use_clustering: bool = True,
    output_path: Optional[str] = None,
) -> str:
    """Generiert eine interaktive Karte mit Folium + OpenStreetMap.

    Args:
        posts: Liste von Post-Dictionaries mit location_lat/lon
        center_lat: Zentrum-Breitengrad
        center_lon: Zentrum-Längengrad
        zoom_level: Standard-Zoom-Level (1-20)
        use_clustering: Marker-Clustering aktivieren
        output_path: Optional Pfad zum Speichern der HTML-Datei

    Returns:
        HTML-String der Karte
    """
    # Karte initialisieren mit 100% Größe.
    # Hinweis: Die Karte wird in einer WebView per data:-URL gerendert.
    # Direkte OSM-Tiles erfordern einen Referer-Header und liefern sonst 403.
    # CartoDB Voyager ist optisch naeher am klassischen OSM-Design,
    # bleibt in dieser Einbettung aber robuster als direkte OSM-Tiles.
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles="CartoDB Voyager",
        prefer_canvas=True,  # Performance-Optimierung
        control_scale=True,
        width="100%",
        height="100%",
    )

    # UTF-8 + Layout für volle Flächennutzung im WebView
    m.get_root().header.add_child(folium.Element('<meta charset="utf-8">'))
    m.get_root().header.add_child(
        folium.Element('<meta name="referrer" content="strict-origin-when-cross-origin">')
    )
    map_name = m.get_name()
    m.get_root().header.add_child(
        folium.Element(
            f"""
            <style>
                html, body {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }}
                #{map_name} {{
                    width: 100% !important;
                    height: 100% !important;
                }}
            </style>
            """
        )
    )

    # MarkerCluster hinzufügen (optional)
    if use_clustering and len(posts) > 10:
        marker_cluster = plugins.MarkerCluster(
            name="Meldungen",
            overlay=True,
            control=False,
        )
        marker_container = marker_cluster
    else:
        marker_container = m

    # Counter für Debug
    marker_count = 0

    # Marker für jeden Post erstellen
    for post in posts:
        lat = post.get("location_lat")
        lon = post.get("location_lon")

        if lat is None or lon is None:
            continue

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            logger.warning(f"Ungültige Koordinaten bei Post {post.get('id')}")
            continue

        # Post-Daten extrahieren
        # Bild aus post_image[] Array extrahieren (wie in UI helpers)
        post_images = post.get("post_image") or []
        image_url = post_images[0].get("url") if post_images else None
        
        # Typ bestimmen
        post_status = post.get("post_status") or {}
        status_name = post_status.get("name", "") if isinstance(post_status, dict) else ""
        post_type = _normalize_status_key(status_name)
        
        # Species extrahieren
        species = post.get("species") or {}
        species_id = species.get("id") if isinstance(species, dict) else post.get("species_id")

        # Tierart-Emoji bestimmen
        from services.posts.map_service import MapDataService
        species_emoji = MapDataService.get_species_emoji(species_id)

        # Icon-HTML erstellen
        icon_html = create_marker_icon_html(
            image_url=image_url,
            post_type=post_type,
            species_emoji=species_emoji,
            size=50,
        )

        post_id = str(post.get("id", ""))
        is_favorite = post.get("is_favorite", False)

        # Popup-HTML
        popup_html = create_popup_html(post, image_url, post_id, is_favorite)

        # Marker-HTML ohne direkten Click-Handler,
        # damit Leaflet-Popup beim Marker-Klick zuverlässig geöffnet wird
        marker_html = f"""
        <div style="cursor: pointer;">
            {icon_html}
        </div>
        """

        # Tooltip (beim Hover): nur Meldungstitel 
        
        tooltip_text = post.get("headline", "Post")

        # Marker erstellen
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=tooltip_text,
            icon=folium.DivIcon(html=marker_html, icon_size=(50, 50)),
        ).add_to(marker_container)

        marker_count += 1

    # MarkerCluster zur Karte hinzufügen
    if use_clustering and len(posts) > 10:
        marker_cluster.add_to(m)

    logger.info(f"{marker_count} Marker zur Karte hinzugefügt")

    # JavaScript für Click-Handler
    click_script = """
    <script>
        // Global Click Handler für Marker
        window.postMarkerClick = function(postId) {
            console.log('Marker geklickt:', postId);
            // DNS-freie URL-Navigation erzwingen, damit Flet WebView sicher ein Change-Event auslöst
            var payload = encodeURIComponent(String(postId));
            var clickUrl = 'about:blank?map_pin_click=' + payload + '&t=' + Date.now();
            window.location.href = clickUrl;
        };
        
        // Hash-Change-Event für Debugging
        window.addEventListener('hashchange', function() {
            console.log('Hash geändert:', window.location.hash);
        });
    </script>
    """

    # Script zur Karte hinzufügen
    m.get_root().html.add_child(folium.Element(click_script))

    # HTML exportieren (vollständiges HTML statt Notebook-Embed)
    html_string = m.get_root().render()

    # Optional: Datei speichern
    if output_path:
        try:
            Path(output_path).write_text(html_string, encoding="utf-8")
            logger.info(f"Karte gespeichert: {output_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Karte: {e}")

    return html_string
