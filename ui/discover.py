"""
Discover View - Entdecke Meldungen mit Listen- und Kartendarstellung.

Dieses Modul implementiert die Haupt-Entdeckungsseite der PetBuddy-Anwendung.
Benutzer können verschiedene verlorene oder gefundene Haustier-Meldungen durchsuchen,
filtern und als sortierte Liste anzeigen lassen.

"""

from typing import Callable, Optional
import flet as ft
from ui.theme import soft_card, chip
from services.references import ReferenceService


class DiscoverView:
    """Klasse für die Startseite mit Meldungsübersicht."""
    
    # ════════════════════════════════════════════════════════════════════
    # KONSTANTEN
    # ════════════════════════════════════════════════════════════════════
    
    STATUS_COLORS: dict[str, str] = {
        "vermisst": ft.Colors.RED_200,
        "fundtier": ft.Colors.INDIGO_300,
        "wiedervereint": ft.Colors.LIGHT_GREEN_200,
    }
    
    SPECIES_COLORS: dict[str, str] = {
        "hund": ft.Colors.PURPLE_200,
        "katze": ft.Colors.PINK_200,
        "kleintier": ft.Colors.TEAL_200,
    }
    
    # UI-Konstanten
    MAX_POSTS_LIMIT = 30
    CARD_IMAGE_HEIGHT = 160
    LIST_IMAGE_HEIGHT = 220
    DIALOG_IMAGE_HEIGHT = 280
    DEFAULT_PLACEHOLDER = "—"
    
    def __init__(
        self,
        page: ft.Page,
        sb,
        on_contact_click: Optional[Callable] = None,
        on_melden_click: Optional[Callable] = None
    ):
        # Initialisiert die Discover-Ansicht.
        self.page = page
        self.sb = sb
        self.on_contact_click = on_contact_click
        self.on_melden_click = on_melden_click
        
        # Services
        self.ref_service = ReferenceService(self.sb)

        # Aktueller User (für Favoriten)
        self.current_user_id = None
        try:
            user_resp = self.sb.auth.get_user()
            if user_resp and getattr(user_resp, "user", None):
                self.current_user_id = user_resp.user.id
        except Exception as ex:
            print(f"Konnte aktuellen Benutzer nicht laden: {ex}")
        
        # Filter-Status
        self.selected_farben = []
        self.farben_panel_visible = False
        self.view_mode = "list"  # "list" oder "grid"
        self.current_items = []  # Speichert die aktuellen Meldungen
        
        # UI-Elemente initialisieren
        self._init_ui_elements()
        
        # Referenzdaten laden
        self.page.run_task(self._load_references)
    
    def _init_ui_elements(self):
        # Initialisiert alle UI-Elemente.
        # Suchfeld (kleiner für mehr Platz)
        self.search_q = ft.TextField(
            label="Suche",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
        )
        
        # Filter-Dropdowns (expand für flexible Breite)
        self.filter_typ = ft.Dropdown(
            label="Kategorie",
            options=[ft.dropdown.Option("alle", "Alle")],
            value="alle",
            expand=True,
        )
        
        self.filter_art = ft.Dropdown(
            label="Tierart",
            options=[ft.dropdown.Option("alle", "Alle")],
            value="alle",
            expand=True,
            on_change=lambda e: self._on_tierart_change(e),
        )
        
        self.filter_geschlecht = ft.Dropdown(
            label="Geschlecht",
            options=[
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ],
            value="alle",
            expand=True,
        )
        
        self.filter_rasse = ft.Dropdown(
            label="Rasse",
            options=[ft.dropdown.Option("alle", "Alle")],
            value="alle",
            expand=True,
            on_change=None,
        )
        
        # Farben-Filter
        self.farben_filter_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
        self.farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN)
        
        self.farben_panel = ft.Container(
            content=self.farben_filter_container,
            padding=12,
            visible=False,
        )
        
        self.farben_header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PALETTE, size=18),
                    ft.Text("Farben wählen", size=14),
                    ft.Container(expand=True),
                    self.farben_toggle_icon,
                ],
                spacing=12,
            ),
            padding=8,
            on_click=self._toggle_farben_panel,
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
        )
        
        # Empty State Card
        self.cta_button = ft.FilledButton(
            "Jetzt melden",
            icon=ft.Icons.ADD_CIRCLE,
            on_click=self.on_melden_click or (lambda _: None),
        )
        
        self.empty_state_card = soft_card(
            ft.Column(
                [
                    ft.Text("Noch keine Meldungen", weight=ft.FontWeight.W_600),
                    ft.Text("Erstelle die erste Meldung!", color=ft.Colors.GREY_700),
                    self.cta_button,
                ],
                spacing=8,
            ),
            elev=1,
            pad=14,
        )
        
        # Liste und Grid der Meldungen
        self.list_view = ft.Column(spacing=14, expand=False)
        self.list_view.controls = [self.empty_state_card]
        
        self.grid_view = ft.ResponsiveRow(spacing=12, run_spacing=12)
        self.grid_view.controls = []
        
        # View-Mode Toggle Buttons
        self.view_toggle = ft.SegmentedButton(
            selected={"list"},
            segments=[
                ft.Segment(
                    value="list",
                    label=ft.Text("Liste"),
                    icon=ft.Icon(ft.Icons.VIEW_LIST),
                ),
                ft.Segment(
                    value="grid",
                    label=ft.Text("Grid"),
                    icon=ft.Icon(ft.Icons.GRID_VIEW),
                ),
            ],
            on_change=self._on_view_mode_change,
        )
        
        # Suchleiste zusammenbauen
        self.search_row = ft.ResponsiveRow(
            [
                # Suchfeld und Dropdowns auf einer Zeile (Desktop)
                ft.Container(self.search_q, col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(self.filter_typ, col={"xs": 6, "sm": 3, "md": 2}),
                ft.Container(self.filter_art, col={"xs": 6, "sm": 3, "md": 2}),
                ft.Container(self.filter_geschlecht, col={"xs": 6, "sm": 3, "md": 2}),
                ft.Container(self.filter_rasse, col={"xs": 6, "sm": 3, "md": 2}),
                ft.Container(self.farben_header, col={"xs": 12, "sm": 8, "md": 6}),
                ft.Container(self.farben_panel, col={"xs": 12, "sm": 12, "md": 12}),
                ft.Container(
                    ft.Row(
                        [
                            ft.FilledButton(
                                "Suchen",
                                icon=ft.Icons.SEARCH,
                                on_click=lambda e: self.page.run_task(self.load_posts)
                            ),
                            ft.OutlinedButton(
                                "Zurücksetzen",
                                icon=ft.Icons.REFRESH,
                                on_click=lambda e: self._reset_filters(e)
                            ),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    col={"xs": 12, "sm": 12, "md": 12},
                ),
            ],
            run_spacing=10,
        )
    
    def _on_view_mode_change(self, e):
        # Wechselt zwischen Listen- und Grid-Ansicht.
        selected = e.control.selected
        if selected:
            self.view_mode = list(selected)[0]
            self._update_view()
    
    def _update_view(self):
        # Aktualisiert die Ansicht basierend auf dem aktuellen View-Mode.
        if not self.current_items:
            return
        
        if self.view_mode == "grid":
            self.grid_view.controls = [self._grid_card(it) for it in self.current_items]
            self.list_view.visible = False
            self.grid_view.visible = True
        else:
            self.list_view.controls = [self._big_card(it) for it in self.current_items]
            self.list_view.visible = True
            self.grid_view.visible = False
        
        self.page.update()
    
    def _toggle_farben_panel(self, _):
        # Toggle für das Farben-Filter-Panel.
        self.farben_panel_visible = not self.farben_panel_visible
        self.farben_panel.visible = self.farben_panel_visible
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()
    
    def _update_rassen_dropdown(self, species_id=None):
        # Aktualisiert das Rassen-Dropdown basierend auf der ausgewählten Tierart.
        self.filter_rasse.options = [ft.dropdown.Option("alle", "Alle")]
        self.filter_rasse.value = "alle"
        
        if hasattr(self, '_all_breeds') and self._all_breeds:
            breeds_to_show = []
            
            if species_id and species_id != "alle":
                # Nur Rassen der ausgewählten Tierart
                breeds_to_show = self._all_breeds.get(int(species_id), [])
            else:
                # Alle Rassen aus allen Tierarten
                for sid, breeds in self._all_breeds.items():
                    breeds_to_show.extend(breeds)
            
            # Nach Name sortieren
            breeds_to_show.sort(key=lambda b: b.get("name", "").lower())
            
            for breed in breeds_to_show:
                self.filter_rasse.options.append(
                    ft.dropdown.Option(str(breed.get("id")), breed.get("name", ""))
                )
    
    def _on_tierart_change(self, e):
        # Wird aufgerufen wenn sich die Tierart ändert.
        self._update_rassen_dropdown(self.filter_art.value)
        self.page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # REFERENZDATEN LADEN
    # ════════════════════════════════════════════════════════════════════
    
    async def _load_references(self, _=None):
        # Lädt Kategorien, Tierarten, Farben und Geschlechter.
        try:
            def populate_dropdown(dropdown, items, id_key="id", name_key="name"):
                dropdown.options = [ft.dropdown.Option("alle", "Alle")]
                for item in items:
                    dropdown.options.append(
                        ft.dropdown.Option(str(item.get(id_key)), item.get(name_key, ""))
                    )
            
            
            populate_dropdown(self.filter_typ, self.ref_service.get_post_statuses())
            populate_dropdown(self.filter_art, self.ref_service.get_species())
            
            sex_options = self.ref_service.get_sex()
            self.filter_geschlecht.options = [
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ]
            for item in sex_options:
                self.filter_geschlecht.options.append(
                    ft.dropdown.Option(str(item.get("id")), item.get("name", ""))
                )
            
            # Rassen laden (alle Rassen für den Filter)
            self._all_breeds = self.ref_service.get_breeds_by_species()
            self._update_rassen_dropdown()
            
            # Farben-Checkboxes
            self.farben_filter_container.controls = []
            for color in self.ref_service.get_colors():
                def on_color_change(e, c_id=color["id"]):
                    if e.control.value:
                        if c_id not in self.selected_farben:
                            self.selected_farben.append(c_id)
                    else:
                        if c_id in self.selected_farben:
                            self.selected_farben.remove(c_id)
                
                cb = ft.Checkbox(label=color["name"], value=False, on_change=on_color_change)
                self.farben_filter_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
                )
            
            self.page.update()
            
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzen: {ex}")
    
    # ════════════════════════════════════════════════════════════════════
    # FAVORITEN
    # ════════════════════════════════════════════════════════════════════

    def _toggle_favorite(self, item: dict, icon_button: ft.IconButton):
        """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie."""
        if not self.current_user_id:
            # Nutzer ist nicht eingeloggt
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Bitte melde dich an, um Meldungen zu favorisieren."),
                open=True,
            )
            self.page.update()
            return

        post_id = item.get("id")
        if not post_id:
            return

        try:
            if item.get("is_favorite"):
                # Aus Favoriten entfernen
                (
                    self.sb.table("favorite")
                    .delete()
                    .eq("user_id", self.current_user_id)
                    .eq("post_id", post_id)
                    .execute()
                )
                item["is_favorite"] = False
                icon_button.icon = ft.Icons.FAVORITE_BORDER
                icon_button.icon_color = ft.Colors.GREY_600
            else:
                # Zu Favoriten hinzufügen
                (
                    self.sb.table("favorite")
                    .insert(
                        {
                            "user_id": self.current_user_id,
                            "post_id": post_id,
                        }
                    )
                    .execute()
                )
                item["is_favorite"] = True
                icon_button.icon = ft.Icons.FAVORITE
                icon_button.icon_color = ft.Colors.RED

            self.page.update()

        except Exception as ex:
            print(f"Fehler beim Aktualisieren der Favoriten: {ex}")
    
    # ════════════════════════════════════════════════════════════════════
    # KARTEN-BUILDER
    # ════════════════════════════════════════════════════════════════════
    
    def _badge_for_typ(self, typ: str) -> ft.Control:
        # Erstellt einen farbigen Badge basierend auf dem Meldungsstatus.
        typ_lower = (typ or "").lower().strip()
        color = self.STATUS_COLORS.get(typ_lower, ft.Colors.GREY_700)
        label = typ.capitalize() if typ else "Unbekannt"
        return chip(label, color)
    
    def _badge_for_species(self, species: str) -> ft.Control:
        # Erstellt einen farbigen Badge basierend auf der Tierart.
        species_lower = (species or "").lower().strip()
        color = self.SPECIES_COLORS.get(species_lower, ft.Colors.GREY_500)
        label = species.capitalize() if species else "Unbekannt"
        return chip(label, color)
    
    def _meta(self, icon, text: str) -> ft.Control:
        """Erstellt eine Metainformation mit Icon und Text."""
        return ft.Row(
            [
                ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(text, color=ft.Colors.ON_SURFACE_VARIANT)
            ],
            spacing=6,
        )
    
    def _build_image_placeholder(self, height: int, icon_size: int = 50) -> ft.Container:
        """Erstellt einen Platzhalter für fehlende Bilder."""
        return ft.Container(
            height=height,
            bgcolor=ft.Colors.GREY_200,
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.GREY_400),
            expand=True,
        )
    
    def _build_detail_row(self, icon, label: str, value: str) -> ft.Row:
        """Erstellt eine Detail-Zeile mit Icon und Text."""
        return ft.Row([
            ft.Icon(icon, size=16, color=ft.Colors.GREY_600),
            ft.Text(f"{label}: {value or self.DEFAULT_PLACEHOLDER}", color=ft.Colors.ON_SURFACE_VARIANT),
        ], spacing=8)
    
    def _copy_to_clipboard(self, data: dict):
        """Kopiert Meldungsdaten in die Zwischenablage."""
        text = f"PetBuddy: {data['title']}\n{data['typ']} · {data['art']}\n{data['ort']}\n"
        self.page.set_clipboard(text)
        self.page.snack_bar = ft.SnackBar(ft.Text("Text kopiert 📋"), open=True)
        self.page.update()
    
    def _extract_item_data(self, item: dict) -> dict:
        """Extrahiert und formatiert Daten aus einem Meldungs-Item.
        
        Args:
            item: Rohdaten aus der Datenbank
            
        Returns:
            Formatiertes Dictionary mit allen Anzeigedaten
        """
        post_images = item.get("post_image") or []
        img_src = post_images[0].get("url") if post_images else None
        
        title = item.get("headline") or "Ohne Namen"
        
        post_status = item.get("post_status") or {}
        typ = post_status.get("name", "") if isinstance(post_status, dict) else ""
        
        species = item.get("species") or {}
        art = species.get("name", "") if isinstance(species, dict) else ""
        
        breed = item.get("breed") or {}
        rasse = breed.get("name", "Mischling") if isinstance(breed, dict) else "Unbekannt"
        
        post_colors = item.get("post_color") or []
        farben_namen = [pc.get("color", {}).get("name", "") for pc in post_colors if pc.get("color")]
        farbe = ", ".join(farben_namen) if farben_namen else ""
        
        ort = item.get("location_text") or ""
        when = (item.get("event_date") or item.get("created_at") or "")[:10]
        status = "Aktiv" if item.get("is_active") else "Inaktiv"
        beschreibung = item.get("description") or ""
        
        # Geschlecht
        sex_data = item.get("sex") or {}
        geschlecht = sex_data.get("name", "Keine Angabe") if isinstance(sex_data, dict) else "Keine Angabe"
        
        return {
            "img_src": img_src,
            "title": title,
            "typ": typ,
            "art": art,
            "rasse": rasse,
            "farbe": farbe,
            "ort": ort,
            "when": when,
            "status": status,
            "beschreibung": beschreibung,
            "geschlecht": geschlecht,
        }
    
    def _show_detail_dialog(self, item: dict):
        """Zeigt einen Detail-Dialog für eine Meldung."""
        data = self._extract_item_data(item)
        
        # Bild
        if data["img_src"]:
            image = ft.Image(
                src=data["img_src"],
                height=self.DIALOG_IMAGE_HEIGHT,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.only(top_left=12, top_right=12),
            )
        else:
            image = self._build_image_placeholder(self.DIALOG_IMAGE_HEIGHT, icon_size=80)
            image.border_radius = ft.border_radius.only(top_left=12, top_right=12)
        
        def close_dialog(_):
            dialog.open = False
            self.page.update()
        
        dialog_content = ft.Column(
            [
                # Bild
                ft.Container(
                    content=image,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    border_radius=ft.border_radius.only(top_left=12, top_right=12),
                ),
                # Inhalt
                ft.Container(
                    content=ft.Column(
                        [
                            # Titel und Badges
                            ft.Text(data["title"], size=20, weight=ft.FontWeight.W_600),
                            ft.Row(
                                [
                                    self._badge_for_typ(data["typ"]),
                                    self._badge_for_species(data["art"]),
                                ],
                                spacing=8,
                                wrap=True,
                            ),
                            ft.Divider(height=16),
                            # Details - verwende Hilfsmethode
                            self._build_detail_row(ft.Icons.SCHEDULE, "Datum", data["when"]),
                            self._build_detail_row(ft.Icons.CATEGORY, "Rasse", data["rasse"]),
                            self._build_detail_row(ft.Icons.MALE, "Geschlecht", data["geschlecht"]),
                            self._build_detail_row(ft.Icons.PALETTE, "Farbe", data["farbe"]),
                            self._build_detail_row(ft.Icons.LOCATION_ON, "Ort", data["ort"]),
                            self._build_detail_row(ft.Icons.LABEL, "Status", data["status"]),
                            # Beschreibung
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Beschreibung", size=14, weight=ft.FontWeight.W_600),
                                    ft.Text(
                                        data["beschreibung"] if data["beschreibung"] else "Keine Beschreibung vorhanden.",
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        size=13,
                                    ),
                                ], spacing=4),
                                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
                                padding=12,
                                border_radius=8,
                                margin=ft.margin.only(top=8),
                            ) if True else None,
                            ft.Divider(height=16),
                            # Aktionen
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        "Kontakt",
                                        icon=ft.Icons.EMAIL,
                                        on_click=lambda e, it=item: self.on_contact_click(it) if self.on_contact_click else None,
                                        height=42,
                                    ),
                                    ft.OutlinedButton(
                                        "Teilen",
                                        icon=ft.Icons.SHARE,
                                        on_click=lambda _: self._copy_to_clipboard(data),
                                        height=42,
                                        style=ft.ButtonStyle(
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                        ),
                                    ),
                                ],
                                spacing=10,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=20,
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )
        
        dialog = ft.AlertDialog(
            modal=False,
            content=ft.Container(
                content=dialog_content,
                width=400,
            ),
            actions=[
                ft.TextButton("Schließen", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _grid_card(self, item: dict) -> ft.Control:
        """Erstellt eine Grid-Karte mit Bild oben und Infos unten."""
        data = self._extract_item_data(item)
        
        # Bild-Container oben
        if data["img_src"]:
            image_content = ft.Image(
                src=data["img_src"],
                height=self.CARD_IMAGE_HEIGHT,
                width=float("inf"),
                fit=ft.ImageFit.COVER,
                gapless_playback=True,
            )
        else:
            image_content = self._build_image_placeholder(self.CARD_IMAGE_HEIGHT)
        
        image_section = ft.Container(
            content=image_content,
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_200,
        )
        
        # Info-Bereich unten
        info_section = ft.Container(
            content=ft.Column(
                [
                    # Titel
                    ft.Text(
                        data["title"],
                        size=14,
                        weight=ft.FontWeight.W_600,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    # Badges: Meldungstyp + Tierart
                    ft.Row(
                        [
                            self._badge_for_typ(data["typ"]),
                            self._badge_for_species(data["art"]),
                        ],
                        spacing=6,
                        wrap=True,
                    ),
                    # Ort
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.LOCATION_ON, size=14, color=ft.Colors.GREY_600),
                            ft.Text(
                                data["ort"] if data["ort"] else "—",
                                size=12,
                                color=ft.Colors.GREY_600,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=6,
            ),
            padding=12,
            bgcolor=ft.Colors.SURFACE,
        )
        
        # Karte zusammensetzen
        card_content = ft.Column(
            [image_section, info_section],
            spacing=0,
        )
        
        card = ft.Container(
            content=card_content,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            animate_scale=200,
            scale=ft.Scale(1.0),
            on_click=lambda _: self._show_detail_dialog(item),
        )
        
        def on_hover(e: ft.HoverEvent):
            card.scale = ft.Scale(1.02) if e.data == "true" else ft.Scale(1.0)
            self.page.update()
        
        card.on_hover = on_hover
        
        return ft.Container(
            content=card,
            col={"xs": 6, "sm": 4, "md": 3, "lg": 2.4},
        )
    
    def _big_card(self, item: dict) -> ft.Control:
        """Erstellt eine große Meldungs-Karte für die Listen-Ansicht."""
        data = self._extract_item_data(item)
        
        # Bild-Container
        if data["img_src"]:
            visual_content = ft.Image(
                src=data["img_src"],
                height=self.LIST_IMAGE_HEIGHT,
                fit=ft.ImageFit.COVER,
                gapless_playback=True,
            )
        else:
            visual_content = self._build_image_placeholder(self.LIST_IMAGE_HEIGHT, icon_size=64)
        
        visual = ft.Container(
            content=visual_content,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_200,
        )
        
        # Badges
        badges = ft.Row(
            [self._badge_for_typ(data["typ"]), self._badge_for_species(data["art"])],
            spacing=8,
            wrap=True,
        )

        # ♥-Button (Favorit)
        is_fav = item.get("is_favorite", False)
        favorite_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
            tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
            on_click=lambda e, it=item, btn=None: self._toggle_favorite(it, e.control),
        )
        
        # Header
        header = ft.Row(
            [
                ft.Text(data["title"], size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                badges,
                favorite_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # Rasse und Farbe
        line1 = ft.Text(f"{data['rasse']} • {data['farbe']}".strip(" • "), color=ft.Colors.ON_SURFACE_VARIANT)
        
        # Metadaten
        metas = ft.Row(
            [
                self._meta(ft.Icons.LOCATION_ON, data["ort"] or self.DEFAULT_PLACEHOLDER),
                self._meta(ft.Icons.SCHEDULE, data["when"] or self.DEFAULT_PLACEHOLDER),
                self._meta(ft.Icons.LABEL, data["status"]),
            ],
            spacing=16,
            wrap=True,
        )
        
        # Buttons
        actions = ft.Row(
            [
                ft.FilledButton(
                    "Kontakt",
                    icon=ft.Icons.EMAIL,
                    on_click=lambda e, it=item: self.on_contact_click(it) if self.on_contact_click else None,
                ),
                ft.IconButton(ft.Icons.SHARE, tooltip="Teilen", on_click=lambda _: self._copy_to_clipboard(data)),
            ],
            spacing=10,
        )
        
        # Karte zusammensetzen
        card_inner = ft.Column([visual, header, line1, metas, actions], spacing=10)
        card = soft_card(card_inner, pad=12, elev=3)
        
        # Hover-Animation und Klick-Handler
        wrapper = ft.Container(
            content=card,
            animate_scale=300,
            scale=ft.Scale(1.0),
            on_click=lambda _: self._show_detail_dialog(item),
        )
        
        def on_hover(e: ft.HoverEvent):
            wrapper.scale = ft.Scale(1.01) if e.data == "true" else ft.Scale(1.0)
            self.page.update()
        
        wrapper.on_hover = on_hover
        return wrapper
    
    # ════════════════════════════════════════════════════════════════════
    # DATEN LADEN
    # ════════════════════════════════════════════════════════════════════
    
    async def load_posts(self, _=None):
        """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen."""
        # Loading-Indikator anzeigen
        loading_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=40, height=40),
                    ft.Text("Meldungen werden geladen...", size=14, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )
        self.list_view.controls = [loading_indicator]
        self.page.update()
        
        try:
            query = self.sb.table("post").select("""
                id, headline, description, location_text, event_date, created_at, is_active,
                post_status(id, name),
                species(id, name),
                breed(id, name),
                sex(id, name),
                post_image(url),
                post_color(color(id, name))
            """).order("created_at", desc=True)
            
            # Filter: Kategorie (post_status)
            if self.filter_typ.value and self.filter_typ.value != "alle":
                query = query.eq("post_status_id", int(self.filter_typ.value))
            
            # Filter: Tierart (species)
            if self.filter_art.value and self.filter_art.value != "alle":
                query = query.eq("species_id", int(self.filter_art.value))
            
            # Filter: Geschlecht
            if self.filter_geschlecht.value and self.filter_geschlecht.value != "alle":
                if self.filter_geschlecht.value == "keine_angabe":
                    query = query.is_("sex_id", "null")
                else:
                    query = query.eq("sex_id", int(self.filter_geschlecht.value))
            
            # Filter: Rasse
            if self.filter_rasse.value and self.filter_rasse.value != "alle":
                query = query.eq("breed_id", int(self.filter_rasse.value))
            
            result = query.limit(self.MAX_POSTS_LIMIT).execute()
            items = result.data or []

            # Favoriten dieses Users laden
            favorite_ids = set()
            if self.current_user_id:
                fav_res = (
                    self.sb.table("favorite")
                    .select("post_id")
                    .eq("user_id", self.current_user_id)
                    .execute()
                )
                favorite_ids = {row["post_id"] for row in (fav_res.data or [])}

            # Flag is_favorite für jedes Item setzen
            for item in items:
                item["is_favorite"] = item["id"] in favorite_ids
            
            # Filter: Suchtext (client-seitig für headline, location_text, description)
            search_text = (self.search_q.value or "").strip().lower()
            if search_text:
                items = [
                    item for item in items
                    if search_text in (item.get("headline") or "").lower()
                    or search_text in (item.get("location_text") or "").lower()
                    or search_text in (item.get("description") or "").lower()
                ]
            
            # Filter: Farben (client-seitig)
            if self.selected_farben:
                def has_matching_color(item):
                    post_colors = item.get("post_color") or []
                    item_color_ids = [
                        pc.get("color", {}).get("id") 
                        for pc in post_colors 
                        if pc.get("color")
                    ]
                    return any(c_id in item_color_ids for c_id in self.selected_farben)
                
                items = [item for item in items if has_matching_color(item)]
            
            if items:
                self.current_items = items
                if self.view_mode == "grid":
                    self.grid_view.controls = [self._grid_card(it) for it in items]
                    self.list_view.controls = []
                    self.list_view.visible = False
                    self.grid_view.visible = True
                else:
                    self.list_view.controls = [self._big_card(it) for it in items]
                    self.grid_view.controls = []
                    self.list_view.visible = True
                    self.grid_view.visible = False
            else:
                self.current_items = []
                # Keine Ergebnisse gefunden
                no_results = soft_card(
                    ft.Column(
                        [
                            ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY_400),
                            ft.Text("Keine Meldungen gefunden", weight=ft.FontWeight.W_600),
                            ft.Text("Versuche andere Suchkriterien", color=ft.Colors.GREY_700),
                            ft.TextButton("Filter zurücksetzen", on_click=self._reset_filters),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    elev=1,
                    pad=24,
                )
                self.list_view.controls = [no_results]
                self.grid_view.controls = []
                self.list_view.visible = True
                self.grid_view.visible = False
            
            self.page.update()
            
        except Exception as ex:
            print(f"Fehler beim Laden der Daten: {ex}")
            self.current_items = []
            self.list_view.controls = [self.empty_state_card]
            self.grid_view.controls = []
            self.page.update()
    
    def _reset_filters(self, _=None):
        # Setzt alle Filter zurück.
        self.search_q.value = ""
        self.filter_typ.value = "alle"
        self.filter_art.value = "alle"
        self.filter_geschlecht.value = "alle"
        self.filter_rasse.value = "alle"
        self.selected_farben.clear()
        
        # Farben-Checkboxen zurücksetzen
        for container in self.farben_filter_container.controls:
            if hasattr(container, "content") and isinstance(container.content, ft.Checkbox):
                container.content.value = False
        
        self.page.update()
        self.page.run_task(self.load_posts)
    
    # ════════════════════════════════════════════════════════════════════
    # BUILD
    # ════════════════════════════════════════════════════════════════════
    
    def build(self) -> ft.Column:
        # Baut und gibt das Layout zurück.
        
        # View-Toggle Zeile (links über den Meldungen)
        view_toggle_row = ft.Container(
            content=ft.Row(
                [
                    self.view_toggle,
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.only(left=4, top=12, bottom=8),
        )
        
        # Listen- und Grid-Container
        content_container = ft.Container(
            padding=4,
            content=ft.Column([view_toggle_row, self.list_view, self.grid_view], spacing=8),
        )
        
        # Karten-Platzhalter
        map_placeholder = ft.Column(
            [
                ft.Container(height=50),
                ft.Icon(ft.Icons.MAP_OUTLINED, size=64, color=ft.Colors.GREY_400),
                ft.Text("Kartenansicht", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_600),
                ft.Text("Kommt bald!", color=ft.Colors.GREY_500),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        map_container = ft.Container(
            padding=4,
            content=map_placeholder,
            expand=True,
        )
        
        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Meldungen", icon=ft.Icons.PETS, content=content_container),
                ft.Tab(text="Karte", icon=ft.Icons.MAP, content=map_container),
            ],
            expand=True,
            animation_duration=250,
        )
        
        return ft.Column(
            [tabs],
            spacing=14,
            expand=True,
        )
