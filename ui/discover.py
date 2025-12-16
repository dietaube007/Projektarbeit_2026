"""
Discover View - Entdecke Meldungen mit Listen- und Kartendarstellung.
"""

from __future__ import annotations

from typing import Callable, Optional
import flet as ft

from ui.theme import soft_card, chip
from services.references import ReferenceService


class DiscoverView:
    """Klasse für die Startseite mit Meldungsübersicht."""

    # Farben für Badges
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
        on_melden_click: Optional[Callable] = None,
    ):
        self.page = page
        self.sb = sb
        self.on_contact_click = on_contact_click
        self.on_melden_click = on_melden_click

        # Services
        self.ref_service = ReferenceService(self.sb)

        # Filter-Status
        self.selected_farben: list[int] = []
        self.farben_panel_visible = False
        self.view_mode = "list"  # "list" oder "grid"
        self.current_items: list[dict] = []

        # User
        self.current_user_id: Optional[str] = None
        self.refresh_user()

        # UI init
        self._init_ui_elements()

        # Referenzen laden
        self.page.run_task(self._load_references)

    # ──────────────────────────────────────────────────────────────────
    # USER / AUTH
    # ──────────────────────────────────────────────────────────────────

    def _get_current_user_id(self) -> Optional[str]:
        """Zieht die aktuelle User-ID aus Supabase (immer frisch)."""
        try:
            user_resp = self.sb.auth.get_user()
            if user_resp and getattr(user_resp, "user", None):
                return user_resp.user.id
        except Exception:
            pass
        return None

    def refresh_user(self):
        """Kann von außen (z.B. nach Login) aufgerufen werden."""
        self.current_user_id = self._get_current_user_id()

    # ──────────────────────────────────────────────────────────────────
    # INIT UI
    # ──────────────────────────────────────────────────────────────────

    def _init_ui_elements(self):
        # Suche
        self.search_q = ft.TextField(
            label="Suche",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=lambda _: self.page.run_task(self.load_posts),
        )

        # Filter
        self.filter_typ = ft.Dropdown(
            label="Kategorie",
            options=[ft.dropdown.Option("alle", "Alle")],
            value="alle",
            expand=True,
            on_change=lambda _: self.page.run_task(self.load_posts),
        )

        self.filter_art = ft.Dropdown(
            label="Tierart",
            options=[ft.dropdown.Option("alle", "Alle")],
            value="alle",
            expand=True,
            on_change=self._on_tierart_change,
        )

        self.filter_geschlecht = ft.Dropdown(
            label="Geschlecht",
            options=[
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ],
            value="alle",
            expand=True,
            on_change=lambda _: self.page.run_task(self.load_posts),
        )

        self.filter_rasse = ft.Dropdown(
            label="Rasse",
            options=[ft.dropdown.Option("alle", "Alle")],
            value="alle",
            expand=True,
            on_change=lambda _: self.page.run_task(self.load_posts),
        )

        # Farben Panel
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
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_200),
        )

        # Buttons
        self.reset_btn = ft.TextButton(
            "Filter zurücksetzen",
            icon=ft.Icons.RESTART_ALT,
            on_click=self._reset_filters,
        )

        self.search_row = ft.ResponsiveRow(
            controls=[
                ft.Container(self.search_q, col={"xs": 12, "md": 5}),
                ft.Container(self.filter_typ, col={"xs": 6, "md": 2}),
                ft.Container(self.filter_art, col={"xs": 6, "md": 2}),
                ft.Container(self.filter_geschlecht, col={"xs": 6, "md": 2}),
                ft.Container(self.filter_rasse, col={"xs": 6, "md": 1}),
                ft.Container(self.reset_btn, col={"xs": 12, "md": 12}),
                ft.Container(self.farben_header, col={"xs": 12, "md": 12}),
                ft.Container(self.farben_panel, col={"xs": 12, "md": 12}),
            ],
            spacing=10,
            run_spacing=10,
        )

        # View toggle
        self.view_toggle = ft.SegmentedButton(
            selected={"list"},
            segments=[
                ft.Segment(value="list", label=ft.Text("Liste"), icon=ft.Icon(ft.Icons.VIEW_AGENDA)),
                ft.Segment(value="grid", label=ft.Text("Kacheln"), icon=ft.Icon(ft.Icons.GRID_VIEW)),
            ],
            on_change=self._on_view_change,
        )

        # Ergebnisbereiche
        self.list_view = ft.Column(spacing=14, expand=True)
        self.grid_view = ft.ResponsiveRow(spacing=12, run_spacing=12, visible=False)

        self.empty_state_card = soft_card(
            ft.Column(
                [
                    ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Noch keine Meldungen", weight=ft.FontWeight.W_600),
                    ft.Text("Passe deine Filter an oder melde ein Tier.", color=ft.Colors.GREY_700),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            elev=1,
            pad=24,
        )

    def _on_view_change(self, e: ft.ControlEvent):
        val = next(iter(e.control.selected), "list")
        self.view_mode = val
        # neu rendern aus current_items
        self._render_items(self.current_items)

    # ──────────────────────────────────────────────────────────────────
    # REFERENCES
    # ──────────────────────────────────────────────────────────────────

    async def _load_references(self):
        try:
            def populate_dropdown(dropdown: ft.Dropdown, items, id_key="id", name_key="name"):
                dropdown.options = [ft.dropdown.Option("alle", "Alle")]
                for it in items or []:
                    dropdown.options.append(
                        ft.dropdown.Option(str(it.get(id_key)), it.get(name_key, ""))
                    )

            populate_dropdown(self.filter_typ, self.ref_service.get_post_statuses())
            populate_dropdown(self.filter_art, self.ref_service.get_species())

            # Geschlecht
            sex_options = self.ref_service.get_sex() or []
            self.filter_geschlecht.options = [
                ft.dropdown.Option("alle", "Alle"),
                ft.dropdown.Option("keine_angabe", "Keine Angabe"),
            ]
            for it in sex_options:
                self.filter_geschlecht.options.append(
                    ft.dropdown.Option(str(it.get("id")), it.get("name", ""))
                )

            # Rassen (abhängig von Art)
            self._all_breeds = self.ref_service.get_breeds_by_species() or {}
            self._update_rassen_dropdown()

            # Farben Checkboxen
            self.farben_filter_container.controls = []
            for c in self.ref_service.get_colors() or []:
                c_id = c["id"]

                def on_color_change(e, color_id=c_id):
                    if e.control.value:
                        if color_id not in self.selected_farben:
                            self.selected_farben.append(color_id)
                    else:
                        if color_id in self.selected_farben:
                            self.selected_farben.remove(color_id)
                    self.page.run_task(self.load_posts)

                cb = ft.Checkbox(label=c["name"], value=False, on_change=on_color_change)
                self.farben_filter_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
                )

            self.page.update()
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzen: {ex}")

    def _on_tierart_change(self, e: ft.ControlEvent):
        self._update_rassen_dropdown()
        self.page.run_task(self.load_posts)

    def _update_rassen_dropdown(self):
        self.filter_rasse.options = [ft.dropdown.Option("alle", "Alle")]
        try:
            if self.filter_art.value and self.filter_art.value != "alle":
                species_id = int(self.filter_art.value)
                breeds = self._all_breeds.get(species_id, []) if hasattr(self, "_all_breeds") else []
            else:
                # wenn keine Art gewählt: alle Rassen aus allen Arten
                breeds = []
                if hasattr(self, "_all_breeds"):
                    for arr in self._all_breeds.values():
                        breeds.extend(arr)

            for b in breeds:
                self.filter_rasse.options.append(
                    ft.dropdown.Option(str(b.get("id")), b.get("name", ""))
                )
        except Exception:
            pass

        if self.filter_rasse.value not in [o.key for o in self.filter_rasse.options]:
            self.filter_rasse.value = "alle"

        self.page.update()

    def _toggle_farben_panel(self, _=None):
        self.farben_panel_visible = not self.farben_panel_visible
        self.farben_panel.visible = self.farben_panel_visible
        self.farben_toggle_icon.name = (
            ft.Icons.KEYBOARD_ARROW_UP if self.farben_panel_visible else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # FAVORITEN
    # ──────────────────────────────────────────────────────────────────

    def _toggle_favorite(self, item: dict, icon_button: ft.IconButton):
        """Fügt eine Meldung zu Favoriten hinzu oder entfernt sie."""
        # User immer frisch ziehen (sonst nach Login noch None)
        self.refresh_user()

        if not self.current_user_id:
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
                (
                    self.sb.table("favorite")
                    .insert({"user_id": self.current_user_id, "post_id": post_id})
                    .execute()
                )
                item["is_favorite"] = True
                icon_button.icon = ft.Icons.FAVORITE
                icon_button.icon_color = ft.Colors.RED

            self.page.update()

        except Exception as ex:
            print(f"Fehler beim Aktualisieren der Favoriten: {ex}")

    # ──────────────────────────────────────────────────────────────────
    # DATEN LADEN
    # ──────────────────────────────────────────────────────────────────

    async def load_posts(self, _=None):
        """Lädt Meldungen aus der Datenbank mit aktiven Filteroptionen + Favoritenstatus."""
        loading_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=40, height=40),
                    ft.Text("Meldungen werden geladen…", size=14, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=40,
            alignment=ft.alignment.center,
        )
        self.list_view.controls = [loading_indicator]
        self.grid_view.controls = []
        self.list_view.visible = True
        self.grid_view.visible = False
        self.page.update()

        try:
            # User immer frisch ziehen (damit Favoriten nach Login korrekt)
            self.refresh_user()

            query = (
                self.sb.table("post")
                .select(
                    """
                    id, headline, description, location_text, event_date, created_at, is_active,
                    post_status(id, name),
                    species(id, name),
                    breed(id, name),
                    sex(id, name),
                    post_image(url),
                    post_color(color(id, name))
                    """
                )
                .order("created_at", desc=True)
            )

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

            # Farbenfilter: über join-Tabelle post_color
            # (einfacher Ansatz: nachträglich filtern – reicht für Demo)
            result = query.limit(self.MAX_POSTS_LIMIT).execute()
            items = result.data or []

            # Suche (Python-Filter, damit es robust bleibt)
            q = (self.search_q.value or "").strip().lower()
            if q:
                def matches(it: dict) -> bool:
                    h = (it.get("headline") or "").lower()
                    d = (it.get("description") or "").lower()
                    l = (it.get("location_text") or "").lower()
                    return q in h or q in d or q in l
                items = [it for it in items if matches(it)]

            # Farben (Python-Filter: post_color -> color.id)
            if self.selected_farben:
                wanted = set(self.selected_farben)

                def has_color(it: dict) -> bool:
                    pcs = it.get("post_color") or []
                    ids = set()
                    for pc in pcs:
                        c = pc.get("color") if isinstance(pc, dict) else None
                        if isinstance(c, dict) and c.get("id") is not None:
                            ids.add(c["id"])
                    return bool(ids.intersection(wanted))

                items = [it for it in items if has_color(it)]

            # Favoritenstatus markieren
            favorite_ids = set()
            if self.current_user_id:
                fav_res = (
                    self.sb.table("favorite")
                    .select("post_id")
                    .eq("user_id", self.current_user_id)
                    .execute()
                )
                favorite_ids = {row["post_id"] for row in (fav_res.data or []) if "post_id" in row}

            for it in items:
                it["is_favorite"] = it.get("id") in favorite_ids

            self.current_items = items
            self._render_items(items)

        except Exception as ex:
            print(f"Fehler beim Laden der Daten: {ex}")
            self.current_items = []
            self.list_view.controls = [self.empty_state_card]
            self.grid_view.controls = []
            self.list_view.visible = True
            self.grid_view.visible = False
            self.page.update()

    def _render_items(self, items: list[dict]):
        if not items:
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
            return

        if self.view_mode == "grid":
            self.grid_view.controls = [self._small_card(it) for it in items]
            self.list_view.controls = []
            self.list_view.visible = False
            self.grid_view.visible = True
        else:
            self.list_view.controls = [self._big_card(it) for it in items]
            self.grid_view.controls = []
            self.list_view.visible = True
            self.grid_view.visible = False

        self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # UI HELPERS / CARD BUILDER
    # ──────────────────────────────────────────────────────────────────

    def _badge_for_typ(self, typ: str) -> ft.Control:
        typ_lower = (typ or "").lower().strip()
        color = self.STATUS_COLORS.get(typ_lower, ft.Colors.GREY_700)
        label = typ.capitalize() if typ else "Unbekannt"
        return chip(label, color)

    def _badge_for_species(self, species: str) -> ft.Control:
        species_lower = (species or "").lower().strip()
        color = self.SPECIES_COLORS.get(species_lower, ft.Colors.GREY_500)
        label = species.capitalize() if species else "Unbekannt"
        return chip(label, color)

    def _meta(self, icon, text: str) -> ft.Control:
        return ft.Row(
            [ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT), ft.Text(text, color=ft.Colors.ON_SURFACE_VARIANT)],
            spacing=6,
        )

    def _build_image_placeholder(self, height: int, icon_size: int = 50) -> ft.Container:
        return ft.Container(
            height=height,
            bgcolor=ft.Colors.GREY_200,
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.GREY_400),
            expand=True,
        )

    def _extract_item_data(self, item: dict) -> dict:
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
        farben_namen = [
            pc.get("color", {}).get("name", "")
            for pc in post_colors
            if isinstance(pc, dict) and pc.get("color")
        ]
        farbe = ", ".join([x for x in farben_namen if x]) if farben_namen else ""

        ort = item.get("location_text") or ""
        when = (item.get("event_date") or item.get("created_at") or "")[:10]
        status = "Aktiv" if item.get("is_active") else "Inaktiv"

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
        }

    def _small_card(self, item: dict) -> ft.Control:
        data = self._extract_item_data(item)

        visual_content = (
            ft.Image(src=data["img_src"], height=self.CARD_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
            if data["img_src"]
            else self._build_image_placeholder(self.CARD_IMAGE_HEIGHT)
        )

        visual = ft.Container(
            content=visual_content,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_200,
        )

        badges = ft.Row(
            [self._badge_for_typ(data["typ"]), self._badge_for_species(data["art"])],
            spacing=8,
            wrap=True,
        )

        is_fav = item.get("is_favorite", False)
        favorite_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
            tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
            on_click=lambda e, it=item: self._toggle_favorite(it, e.control),
        )

        header = ft.Row(
            [
                ft.Text(data["title"], size=14, weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(expand=True),
                favorite_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        card_inner = ft.Column([visual, badges, header], spacing=8)
        card = soft_card(card_inner, pad=12, elev=2)

        wrapper = ft.Container(
            content=card,
            animate_scale=200,
            scale=ft.Scale(1.0),
            on_click=lambda _: self._show_detail_dialog(item),
        )

        def on_hover(e: ft.HoverEvent):
            wrapper.scale = ft.Scale(1.02) if e.data == "true" else ft.Scale(1.0)
            self.page.update()

        wrapper.on_hover = on_hover

        return ft.Container(content=wrapper, col={"xs": 6, "sm": 4, "md": 3, "lg": 2.4})

    def _big_card(self, item: dict) -> ft.Control:
        data = self._extract_item_data(item)

        visual_content = (
            ft.Image(src=data["img_src"], height=self.LIST_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
            if data["img_src"]
            else self._build_image_placeholder(self.LIST_IMAGE_HEIGHT, icon_size=64)
        )

        visual = ft.Container(
            content=visual_content,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.GREY_200,
        )

        badges = ft.Row(
            [self._badge_for_typ(data["typ"]), self._badge_for_species(data["art"])],
            spacing=8,
            wrap=True,
        )

        is_fav = item.get("is_favorite", False)
        favorite_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
            tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
            on_click=lambda e, it=item: self._toggle_favorite(it, e.control),
        )

        header = ft.Row(
            [
                ft.Text(data["title"], size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                badges,
                favorite_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        line1 = ft.Text(f"{data['rasse']} • {data['farbe']}".strip(" • "), color=ft.Colors.ON_SURFACE_VARIANT)

        metas = ft.Row(
            [
                self._meta(ft.Icons.LOCATION_ON, data["ort"] or self.DEFAULT_PLACEHOLDER),
                self._meta(ft.Icons.SCHEDULE, data["when"] or self.DEFAULT_PLACEHOLDER),
                self._meta(ft.Icons.LABEL, data["status"]),
            ],
            spacing=16,
            wrap=True,
        )

        actions = ft.Row(
            [
                ft.FilledButton(
                    "Kontakt",
                    icon=ft.Icons.EMAIL,
                    on_click=lambda e, it=item: self.on_contact_click(it) if self.on_contact_click else None,
                ),
            ],
            spacing=10,
        )

        card_inner = ft.Column([visual, header, line1, metas, actions], spacing=10)
        card = soft_card(card_inner, pad=12, elev=3)

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

    def _show_detail_dialog(self, item: dict):
        data = self._extract_item_data(item)

        visual = (
            ft.Image(src=data["img_src"], height=self.DIALOG_IMAGE_HEIGHT, fit=ft.ImageFit.COVER)
            if data["img_src"]
            else self._build_image_placeholder(self.DIALOG_IMAGE_HEIGHT, icon_size=72)
        )

        dlg = ft.AlertDialog(
            title=ft.Text(data["title"]),
            content=ft.Column(
                [
                    ft.Container(visual, border_radius=16, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
                    ft.Container(height=8),
                    ft.Text(item.get("description") or "Keine Beschreibung.", color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Container(height=8),
                    self._meta(ft.Icons.LOCATION_ON, data["ort"] or self.DEFAULT_PLACEHOLDER),
                    self._meta(ft.Icons.SCHEDULE, data["when"] or self.DEFAULT_PLACEHOLDER),
                    self._meta(ft.Icons.LABEL, data["status"]),
                ],
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton("Schließen", on_click=lambda _: self._close_dialog()),
                ft.FilledButton(
                    "Kontakt",
                    icon=ft.Icons.EMAIL,
                    on_click=lambda e, it=item: self.on_contact_click(it) if self.on_contact_click else None,
                ),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    # ──────────────────────────────────────────────────────────────────
    # FILTER RESET
    # ──────────────────────────────────────────────────────────────────

    def _reset_filters(self, _=None):
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

    # ──────────────────────────────────────────────────────────────────
    # BUILD
    # ──────────────────────────────────────────────────────────────────

    def build(self) -> ft.Column:
        view_toggle_row = ft.Container(
            content=ft.Row([self.view_toggle], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.only(left=4, top=12, bottom=8),
        )

        content_container = ft.Container(
            padding=4,
            content=ft.Column([view_toggle_row, self.list_view, self.grid_view], spacing=8),
        )

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

        map_container = ft.Container(padding=4, content=map_placeholder, expand=True)

        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Meldungen", icon=ft.Icons.PETS, content=content_container),
                ft.Tab(text="Karte", icon=ft.Icons.MAP, content=map_container),
            ],
            expand=True,
            animation_duration=250,
        )

        # Beim ersten Build direkt laden
        self.page.run_task(self.load_posts)

        return ft.Column([tabs], spacing=14, expand=True)
