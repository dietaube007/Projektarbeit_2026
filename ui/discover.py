"""
Discover View - Entdecke Meldungen mit Listen- und Kartendarstellung.

Dieses Modul implementiert die Haupt-Entdeckungsseite der PetBuddy-Anwendung.
Benutzer können verschiedene verlorene oder gefundene Haustier-Meldungen durchsuchen,
filtern und als sortierte Liste anzeigen lassen.

"""

import flet as ft
from ui.theme import soft_card, chip
from services.references import get_species, get_colors, get_sex, get_post_statuses


def build_list_and_map(page: ft.Page, sb, on_contact_click, on_melden_click=None):
    """
    Baut die Discover-Ansicht (Liste) mit dynamischen Suchfiltern.
    
    Diese Funktion erstellt die gesamte Entdeckungsseite bestehend aus:
    - Suchleiste mit Textfilter
    - Vier Dropdown-Filter (Kategorie, Tierart, Farbe, Geschlecht)
    - List-View mit Meldungskarten
    - Responsive Layout

    """

    # ════════════════════════════════════════════════════════════════════
    # SUCHLEISTE UND FILTER-DROPDOWNS
    # ════════════════════════════════════════════════════════════════════

    search_q = ft.TextField(
        label="Suche",
        prefix_icon=ft.Icons.SEARCH,
        width=420,
    )
    
    # Filter: Meldungstyp (Vermisst/Gefunden) aus post_status Tabelle
    filter_typ = ft.Dropdown(
        label="Kategorie",
        options=[ft.dropdown.Option("alle", "Alle")],
        value="alle",
        width=180,
    )
    
    # Filter: Tierart (Hund, Katze, etc.) aus species Tabelle
    filter_art = ft.Dropdown(
        label="Tierart",
        options=[ft.dropdown.Option("alle", "Alle")],
        value="alle",
        width=180,
    )
    
    # Filter: Farbe/Farbmuster - Checkboxes in expandierbarem Panel
    farben_checkboxes = {}
    selected_farben = []
    farben_filter_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    
    # Filter: Geschlecht des Tieres aus sex Tabelle
    filter_geschlecht = ft.Dropdown(
        label="Geschlecht",
        options=[ft.dropdown.Option("alle", "Alle")],
        value="alle",
        width=180,
    )
    
    # ════════════════════════════════════════════════════════════════════
    # LOAD_REFERENCES - LÄDT FILTER-OPTIONEN AUS DATENBANK
    # ════════════════════════════════════════════════════════════════════
    
    async def load_references():
        
        # Lädt Kategorien, Tierarten, Farben und Geschlechter aus der Datenbank.

        try:
            # HELPER-FUNKTION: Füllt ein Dropdown mit Daten
            def populate_dropdown(dropdown, items, id_key="id", name_key="name"):
                # Füllt ein Dropdown-Menü mit Optionen aus einer Liste von Daten.
                dropdown.options = [ft.dropdown.Option("alle", "Alle")]
                for item in items:
                    dropdown.options.append(
                        ft.dropdown.Option(str(item.get(id_key)), item.get(name_key, ""))
                    )
            
            # Lade alle Referenzdaten
            populate_dropdown(filter_typ, get_post_statuses(sb))
            populate_dropdown(filter_art, get_species(sb))
            populate_dropdown(filter_geschlecht, get_sex(sb))
            
            # Lade Farben als Checkboxes
            farben_filter_container.controls = []
            for color in get_colors(sb):
                def on_color_change(e, c_id=color["id"], c_name=color["name"]):
                    if e.control.value:
                        if c_id not in selected_farben:
                            selected_farben.append(c_id)
                    else:
                        if c_id in selected_farben:
                            selected_farben.remove(c_id)
                
                cb = ft.Checkbox(label=color["name"], value=False, on_change=on_color_change)
                farben_checkboxes[color["id"]] = cb
                farben_filter_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
                )
            
            page.update()
            
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzen: {ex}")

    # Empty State Card für "Noch keine Meldungen"
    cta_button = ft.FilledButton(
        "Jetzt melden",
        icon=ft.Icons.ADD_CIRCLE,
        on_click=on_melden_click or (lambda _: None),
    )
    empty_state_card = soft_card(
        ft.Column(
            [
                ft.Text("Noch keine Meldungen", weight=ft.FontWeight.W_600),
                ft.Text("Erstelle die erste Meldung!", color=ft.Colors.GREY_700),
                cta_button,
            ],
            spacing=8,
        ),
        elev=1,
        pad=14,
    )

    # Initialisiere list_view mit Empty State Card
    list_view = ft.Column(spacing=14, expand=False)
    list_view.controls = [empty_state_card]

    # ════════════════════════════════════════════════════════════════════
    # MELDUNGS-KARTEN-BUILDER
    # ════════════════════════════════════════════════════════════════════
    # Erstellt die visuellen Karten für die Listen-Ansicht.
    # Jede Karte zeigt Bild, Überschrift, Metadaten und Aktions-Buttons.
    # ════════════════════════════════════════════════════════════════════
    
    def _badge_for_typ(typ: str) -> ft.Control:
        """
        Erstellt einen farbigen Badge basierend auf dem Meldungsstatus.
        
        Mögliche Status aus der Datenbank:
        - "vermisst": ROT (jemand sucht ein Tier)
        - "gefunden": BLAU (jemand hat ein Tier gefunden, sucht Besitzer)
        - "wiedervereint": GRÜN (Tier wurde gefunden & Besitzer benachrichtigt)
        """
        typ_lower = (typ or "").lower().strip()
        if typ_lower == "vermisst":
            return chip("Vermisst", ft.Colors.RED_400)
        if typ_lower == "gefunden":
            return chip("Gefunden", ft.Colors.BLUE_400)
        if typ_lower == "wiedervereint":
            return chip("Wiedervereint", ft.Colors.GREEN_400)
        # Fallback für unerwartete Status
        return chip(typ.capitalize() if typ else "Unknown", ft.Colors.GREY_700)

    def _meta(icon, text: str) -> ft.Control:
        """
        Erstellt eine Metainformation mit Icon und Text.
        
        Diese Funktion wird benutzt für kleine Informations-Zeilen
        wie Ort, Datum, Status. Icon + Text nebeneinander angeordnet.
        """
        return ft.Row(
            [ft.Icon(icon, size=16, color=ft.Colors.GREY_700), 
             ft.Text(text, color=ft.Colors.GREY_700)],
            spacing=6,
        )

    def big_card(item: dict) -> ft.Control:
        """
        Erstellt eine große Meldungs-Karte für die Listen-Ansicht.
        
        Jede Karte enthält:
        - Tier-Bild oder Placeholder-Icon
        - Überschrift und Badges (Kategorie, Tierart)
        - Rasse und Farbe
        - Metadaten: Ort, Datum, Status
        - Buttons: "Kontakt" und "Teilen"
        
        Die Karte hat Hover-Effekte (leicht Vergrößerung bei Mouse-Over).
        """
        # EXTRAHIERE MELDUNGS-DATEN
        imgs = item.get("images") or []
        img_src = imgs[0] if isinstance(imgs, list) and imgs else None
        rid = str(item.get("id"))
        title = item.get("headline") or "Ohne Namen"
        typ = item.get("post_status", {}).get("name", "")
        art = item.get("species", {}).get("name", "")
        rasse = item.get("breed", {}).get("name") or "Mischling"
        farbe = item.get("color", {}).get("name") or ""
        ort = item.get("location_text") or ""
        when = (item.get("event_date") or item.get("created_at") or "")[:10]
        status = item.get("is_active") and "Aktiv" or "Inaktiv"

        # BILD-CONTAINER
        visual = ft.Container(
            content=(
                ft.Image(src=img_src, height=220, fit=ft.ImageFit.COVER)
                if img_src
                else ft.Container(
                    height=220,
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.PETS, size=64, color=ft.Colors.GREY_500),
                )
            ),
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        # BADGES (Kategorie, Tierart)
        badges = ft.Row(
            [_badge_for_typ(typ), chip(art.capitalize(), ft.Colors.GREY_700)],
            spacing=8,
            wrap=True,
        )

        # KOPFZEILE (Titel + Badges)
        header = ft.Row(
            [
                ft.Text(title, size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                badges,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # RASSE UND FARBE
        line1 = ft.Text(f"{rasse} • {farbe}".strip(" • "), color=ft.Colors.GREY_700)
        
        # METADATEN (Ort, Datum, Status)
        metas = ft.Row(
            [
                _meta(ft.Icons.LOCATION_ON, ort if ort else "—"),
                _meta(ft.Icons.SCHEDULE, when if when else "—"),
                _meta(ft.Icons.LABEL, status),
            ],
            spacing=16,
            wrap=True,
        )

        # TEILEN-CALLBACK
        def share(_):
            """Kopiert Meldungs-Text in Zwischenablage."""
            text = f"PetBuddy: {title}\n{typ} · {art}\n{ort}\n"
            page.set_clipboard(text)
            page.snack_bar = ft.SnackBar(ft.Text("Text kopiert 📋"), open=True)
            page.update()

        # BUTTONS (Kontakt, Teilen)
        actions = ft.Row(
            [
                ft.FilledButton(
                    "Kontakt",
                    icon=ft.Icons.EMAIL,
                    on_click=lambda e, it=item: on_contact_click(it),
                ),
                ft.IconButton(ft.Icons.SHARE, tooltip="Teilen", on_click=share),
            ],
            spacing=10,
        )

        # ZUSAMMENSETZEN ZUR KARTE
        card_inner = ft.Column([visual, header, line1, metas, actions], spacing=10)
        card = soft_card(card_inner, pad=12, elev=3)
        
        # HOVER-ANIMATION
        wrapper = ft.Container(content=card, animate_scale=300, scale=ft.Scale(1.0))
        
        def on_hover(e: ft.HoverEvent):
            """Vergrößere Karte leicht bei Mouse-Over."""
            wrapper.scale = ft.Scale(1.01) if e.data == "true" else ft.Scale(1.0)
            page.update()
        
        wrapper.on_hover = on_hover
        return wrapper

    # ════════════════════════════════════════════════════════════════════
    # DATEN LADEN UND FILTERN
    # ════════════════════════════════════════════════════════════════════
    
    async def load():
        """
        Lädt Meldungen aus der Datenbank.

        """
        try:
            # KONSTRUIERE SUPABASE QUERY
            query = sb.table("post").select("*")
            
            # FÜHRE QUERY AUS
            result = query.limit(200).execute()
            items = result.data
            
            # GENERIERE UI
            # Zeige immer die Empty State Card oben, dann die Meldungen
            if items:
                list_view.controls = [empty_state_card] + [big_card(it) for it in items]
            else:
                list_view.controls = [empty_state_card]
            
            page.update()
            
        except Exception as ex:
            print(f"Fehler beim Laden der Daten: {ex}")
            page.update()

    # ════════════════════════════════════════════════════════════════════
    # UI LAYOUT
    # ════════════════════════════════════════════════════════════════════
    
    # Farben-Panel togglebar machen
    farben_panel_visible = False
    farben_panel = ft.Container(
        content=farben_filter_container,
        padding=12,
        visible=False,
    )
    
    farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
    
    def toggle_farben_panel(_):
        nonlocal farben_panel_visible
        farben_panel_visible = not farben_panel_visible
        farben_panel.visible = farben_panel_visible
        farben_toggle_icon.name = ft.Icons.KEYBOARD_ARROW_UP if farben_panel_visible else ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()
    
    farben_header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18),
                ft.Text("Farben wählen", size=14),
                ft.Container(expand=True),
                farben_toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=toggle_farben_panel,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
    )
    
    # SUCHLEISTE: Responsive Reihe mit Filter-Dropdowns
    search_row = ft.ResponsiveRow(
        [
            ft.Container(search_q, col={"xs": 12, "sm": 12, "md": 6}),
            ft.Container(filter_typ, col={"xs": 6, "sm": 6, "md": 2}),
            ft.Container(filter_art, col={"xs": 6, "sm": 6, "md": 2}),
            ft.Container(filter_geschlecht, col={"xs": 6, "sm": 6, "md": 2}),
            ft.Container(farben_header, col={"xs": 12, "sm": 12, "md": 12}),
            ft.Container(farben_panel, col={"xs": 12, "sm": 12, "md": 12}),
            ft.Container(
                ft.FilledButton("Suchen", icon=ft.Icons.SEARCH, on_click=lambda e: page.run_task(load)),
                col={"xs": 12, "sm": 12, "md": 12},
            ),
        ],
        run_spacing=10,
    )

    # LISTEN-CONTAINER: Container mit scrollbar für Meldungs-Karten
    list_container = ft.Container(
        padding=4,
        content=ft.Column([list_view], spacing=12),
    )
    
    # KARTEN-CONTAINER: Zeigt gleiche Liste (Kartenfunktionen entfernt)
    map_container = ft.Container(
        padding=4,
        content=ft.Column([list_view], spacing=12),
    )
    
    # TABS: Wähle zwischen Liste und Karte
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Liste", icon=ft.Icons.VIEW_LIST, content=list_container),
            ft.Tab(text="Karte", icon=ft.Icons.MAP, content=map_container),
        ],
        expand=True,
        animation_duration=250,
    )

    # HAUPT-CONTAINER: Tabs als Hauptinhalt der Ansicht
    controls = ft.Column(
        [
            tabs,
        ],
        spacing=14,
        expand=True,
    )

    # ════════════════════════════════════════════════════════════════════
    # INITIALISIERUNG
    # ════════════════════════════════════════════════════════════════════
    
    # Starte asynchrones Laden der Filter-Optionen
    page.run_task(load_references)

    # ════════════════════════════════════════════════════════════════════
    # RÜCKGABE AN MAIN.PY
    # ════════════════════════════════════════════════════════════════════
    
    return controls, load, search_row
