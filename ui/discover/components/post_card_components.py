"""
Meldung-Komponenten für die Discover-View.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any
import flet as ft

from ui.theme import soft_card, get_theme_color
from ui.constants import (
    CARD_IMAGE_HEIGHT, LIST_IMAGE_HEIGHT, DIALOG_IMAGE_HEIGHT,
    DEFAULT_PLACEHOLDER, PRIMARY_COLOR
)
from ui.helpers import extract_item_data
from .comment_components import CommentSection
from ui.shared_components import (
    badge_for_typ,
    badge_for_species,
    meta_row,
    image_placeholder,
)


def build_small_card(
    item: Dict[str, Any],
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.Control], None],
    on_card_click: Callable[[Dict[str, Any]], None]
) -> ft.Control:
    """Erstellt eine kleine Kachel-Karte für die Grid-Ansicht.
    
    Args:
        item: Post-Dictionary mit allen Daten
        page: Flet Page-Instanz
        on_favorite_click: Callback (item, control) für Favoriten-Toggle
        on_card_click: Callback (item) für Karten-Klick
    
    Returns:
        Container mit kleiner Karten-Komponente
    """
    data = extract_item_data(item)
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    screen_width = page.width or getattr(page, "window_width", None) or 0
    is_mobile = bool(screen_width and screen_width < 720)

    visual_content = (
        ft.Image(src=data["img_src"], height=CARD_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(CARD_IMAGE_HEIGHT, expand=True, page=page)
    )

    visual = ft.Container(
        content=visual_content,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=get_theme_color("card", is_dark),
    )

    badges = ft.Row(
        [badge_for_typ(data["typ"]), badge_for_species(data["art"])],
        spacing=8,
        wrap=True,
    )

    is_fav = item.get("is_favorite", False)
    favorite_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
        icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
        tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
        on_click=lambda e, it=item: on_favorite_click(it, e.control),
    )

    header = ft.Row(
        [
            ft.Text(data["title"], size=14, weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Container(expand=True),
            favorite_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Ersteller mit Profilbild
    profile_img_sm = data.get("user_profile_image")
    if isinstance(profile_img_sm, str):
        profile_img_sm = profile_img_sm.strip()
        if profile_img_sm.lower() in {"", "null", "none", "undefined"}:
            profile_img_sm = None
    user_row = ft.Row(
        [
            ft.CircleAvatar(
                foreground_image_src=profile_img_sm if profile_img_sm else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=8)
                if not profile_img_sm
                else None,
                bgcolor=PRIMARY_COLOR,
                radius=8,
            ),
            ft.Text(data["username"], size=11, color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        ],
        spacing=4,
    )

    card_inner = ft.Column([visual, badges, header, user_row], spacing=8)
    card = soft_card(card_inner, pad=12, elev=2)

    wrapper = ft.Container(
        content=card,
        animate_scale=200,
        scale=ft.Scale(1.0),
        on_click=lambda _, it=item: on_card_click(it),
    )

    def on_hover(e: ft.HoverEvent):
        wrapper.scale = ft.Scale(1.02) if e.data == "true" else ft.Scale(1.0)
        page.update()

    wrapper.on_hover = on_hover

    return ft.Container(content=wrapper, col={"xs": 6, "sm": 4, "md": 3, "lg": 2.4})


def build_big_card(
    item: Dict[str, Any],
    page: ft.Page,
    on_favorite_click: Callable[[Dict[str, Any], ft.Control], None],
    on_card_click: Callable[[Dict[str, Any]], None],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    supabase=None,
    profile_service=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> ft.Control:
    """Erstellt eine große Listen-Karte für die Listen-Ansicht.
    
    Kommentare werden nur im Detail-Dialog angezeigt.
    
    Args:
        item: Post-Dictionary mit allen Daten
        page: Flet Page-Instanz
        on_favorite_click: Callback (item, control) für Favoriten-Toggle
        on_card_click: Callback (item) für Karten-Klick
        on_contact_click: Optionaler Callback (item) für Kontakt-Button
        supabase: Optional Supabase-Client (für Detail-Dialog)
        profile_service: Optional ProfileService (für Detail-Dialog)
        on_comment_login_required: Optional Callback wenn Login zum Kommentieren erforderlich
    
    Returns:
        Container mit großer Karten-Komponente
    """
    data = extract_item_data(item)
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    current_user_id = profile_service.get_user_id() if profile_service else None
    is_own_post = bool(current_user_id and str(item.get("user_id") or "") == str(current_user_id))
    can_contact = bool(on_contact_click and not is_own_post)

    # --- Bild ---
    visual_content = (
        ft.Image(src=data["img_src"], height=LIST_IMAGE_HEIGHT, fit=ft.ImageFit.COVER, gapless_playback=True)
        if data["img_src"]
        else image_placeholder(LIST_IMAGE_HEIGHT, icon_size=64, expand=True, page=page)
    )

    image_col = ft.Container(
        content=visual_content,
        height=LIST_IMAGE_HEIGHT,
        border_radius=16,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=get_theme_color("card", is_dark),
        col={"xs": 12, "md": 5},  # Volle Breite mobil, ~40% Desktop
    )

    # --- Infos ---
    title_text = ft.Text(data["title"], size=18, weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

    badges = ft.Row(
        [badge_for_typ(data["typ"]), badge_for_species(data["art"])],
        spacing=8,
        wrap=True,
    )

    line1 = ft.Text(f"{data['rasse']} • {data['farbe']}".strip(" • "), color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

    # Ersteller mit Profilbild
    profile_img = data.get("user_profile_image")
    user_chip = ft.Row(
        [
            ft.CircleAvatar(
                foreground_image_src=profile_img if profile_img else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=10) if not profile_img else None,
                bgcolor=ft.Colors.with_opacity(0.6, PRIMARY_COLOR),
                radius=10,
            ),
            ft.Text(data["username"], color=ft.Colors.ON_SURFACE_VARIANT, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        ],
        spacing=6,
    )

    metas = ft.Column(
        [
            meta_row(ft.Icons.LOCATION_ON, data["ort"] or DEFAULT_PLACEHOLDER),
            user_chip,
            meta_row(ft.Icons.SCHEDULE, f"Erstellt am: {data['created_at']}"),
        ],
        spacing=4,
    )

    # Herz rechts neben Kontakt
    is_fav = item.get("is_favorite", False)
    favorite_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
        icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
        tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
        on_click=lambda e, it=item: on_favorite_click(it, e.control),
    )

    actions = ft.Row(
        [
            ft.FilledButton(
                "Kontakt",
                icon=ft.Icons.EMAIL,
                disabled=not can_contact,
                on_click=(lambda e, it=item: on_contact_click(it)) if can_contact else None,
                style=ft.ButtonStyle(
                    bgcolor=PRIMARY_COLOR if can_contact else ft.Colors.GREY_300,
                    color=ft.Colors.WHITE if can_contact else ft.Colors.GREY_700,
                    icon_color=ft.Colors.WHITE if can_contact else ft.Colors.GREY_700,
                ),
            ),
            favorite_btn,
        ],
        spacing=4,
    )

    info_col = ft.Container(
        content=ft.Column(
            [title_text, badges, line1, metas, actions],
            spacing=8,
        ),
        col={"xs": 12, "md": 7},  # Volle Breite mobil, ~60% Desktop
    )

    # Responsives Layout: Mobil vertikal, Desktop horizontal
    card_inner = ft.ResponsiveRow(
        [image_col, info_col],
        spacing=12,
        run_spacing=10,
    )
    card = soft_card(card_inner, pad=12, elev=3)

    wrapper = ft.Container(
        content=card,
        animate_scale=300,
        scale=ft.Scale(1.0),
        on_click=lambda e, it=item: on_card_click(it) if on_card_click else None,
        col={"xs": 12, "md": 6},  # 2 Karten pro Zeile ab mittlerer Breite
    )

    def on_hover(e: ft.HoverEvent):
        wrapper.scale = ft.Scale(1.01) if e.data == "true" else ft.Scale(1.0)
        page.update()

    wrapper.on_hover = on_hover
    return wrapper


def show_detail_dialog(
    page: ft.Page,
    item: Dict[str, Any],
    on_contact_click: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_favorite_click: Optional[Callable[[Dict[str, Any], ft.Control], None]] = None,
    profile_service=None,
    supabase=None,
    on_comment_login_required: Optional[Callable[[], None]] = None,
) -> None:
    """Zeigt den Detail-Dialog für eine Meldung inkl. Kommentarbereich."""
    data = extract_item_data(item)
    current_user_id = profile_service.get_user_id() if profile_service else None
    is_own_post = bool(current_user_id and str(item.get("user_id") or "") == str(current_user_id))
    can_contact = bool(on_contact_click and not is_own_post)

    sex = item.get("sex") or {}
    geschlecht = sex.get("name", "Keine Angabe") if isinstance(sex, dict) else "Keine Angabe"
    if isinstance(geschlecht, str):
        geschlecht = geschlecht.strip() or "Keine Angabe"

    is_dark = page.theme_mode == ft.ThemeMode.DARK
    screen_width = page.width or getattr(page, "window_width", None) or 0
    is_mobile = bool(screen_width and screen_width < 720)
    
    dialog_img_width = None if is_mobile else 480
    visual = (
        ft.Image(src=data["img_src"], width=dialog_img_width, height=DIALOG_IMAGE_HEIGHT, fit=ft.ImageFit.CONTAIN)
        if data["img_src"]
        else image_placeholder(DIALOG_IMAGE_HEIGHT, icon_size=72, page=page)
    )

    # Favoriten-Button
    is_fav = item.get("is_favorite", False)
    favorite_btn = None
    if on_favorite_click:
        favorite_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE if is_fav else ft.Icons.FAVORITE_BORDER,
            icon_color=ft.Colors.RED if is_fav else ft.Colors.GREY_600,
            tooltip="Aus Favoriten entfernen" if is_fav else "Zu Favoriten hinzufügen",
            on_click=lambda e, it=item: on_favorite_click(it, e.control),
        )

    # X-Button oben rechts (on_click wird nach dlg-Erstellung gesetzt)
    close_btn = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_size=20,
        tooltip="Schließen",
    )
    title_row = ft.Row(
        [ft.Container(expand=True), close_btn],
        alignment=ft.MainAxisAlignment.END,
    )

    # Eventdatum-Label je nach Meldungstyp
    typ_lower = (data["typ"] or "").lower().strip()
    if "fundtier" in typ_lower or "gefunden" in typ_lower or "zugelaufen" in typ_lower:
        event_label = "Gefunden am"
    elif "vermisst" in typ_lower or "entlaufen" in typ_lower:
        event_label = "Vermisst seit"
    elif "wiedervereint" in typ_lower:
        event_label = "Wiedervereint am"
    else:
        event_label = "Ereignis am"

    # Aktions-Controls: Kontakt + Herz (werden in Ersteller-Zeile eingebaut)
    action_controls = []
    action_controls.append(
        ft.FilledButton(
            "Kontakt",
            icon=ft.Icons.EMAIL,
            disabled=not can_contact,
            on_click=(lambda e, it=item: on_contact_click(it)) if can_contact else None,
            style=ft.ButtonStyle(
                bgcolor=PRIMARY_COLOR if can_contact else ft.Colors.GREY_300,
                color=ft.Colors.WHITE if can_contact else ft.Colors.GREY_700,
                icon_color=ft.Colors.WHITE if can_contact else ft.Colors.GREY_700,
            ),
        )
    )
    if favorite_btn:
        action_controls.append(favorite_btn)

    # Links: Infos (Bild, Beschreibung, Metadaten) | Rechts: Kommentare
    post_id = str(item.get("id") or "")
    details_column = ft.Column(
        [
            ft.Container(
                visual,
                border_radius=16,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                alignment=ft.alignment.center,
            ),
            ft.Container(height=2),
            ft.Row(
                [
                    ft.Row(
                        [
                            ft.CircleAvatar(
                                foreground_image_src=(data.get("user_profile_image") or "").strip() or None,
                                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=18)
                                if (data.get("user_profile_image") or "").strip().lower() in {"", "null", "none", "undefined"}
                                else None,
                                bgcolor=PRIMARY_COLOR,
                                radius=18,
                            ),
                            ft.Text(data["username"], color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=10,
                    ),
                    ft.Row(action_controls, spacing=4),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=10),
            ft.Text(
                data["title"],
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.ON_SURFACE,
            ),
            ft.Text(
                item.get("description") or "Keine Beschreibung.",
                color=ft.Colors.ON_SURFACE_VARIANT,
                width=None if is_mobile else 480,
                text_align=ft.TextAlign.JUSTIFY,
            ),
            ft.Divider(height=16, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)),
            ft.Column(
                [
                    meta_row(ft.Icons.PETS, f"Tierart: {data['art']}"),
                    meta_row(
                        ft.Icons.MALE if geschlecht.lower() == "männlich"
                        else ft.Icons.FEMALE if geschlecht.lower() == "weiblich"
                        else ft.Icons.QUESTION_MARK,
                        f"Geschlecht: {geschlecht}",
                    ),
                    meta_row(
                        ft.Icons.LABEL,
                        f"Rasse: {data['rasse']}" if data["rasse"] else "Rasse: Keine Angabe",
                    ),
                    meta_row(
                        ft.Icons.PALETTE,
                        f"Farbe: {data['farbe']}" if data["farbe"] else "Farbe: Keine Angabe",
                    ),
                    meta_row(
                        ft.Icons.LOCATION_ON,
                        f"Ort: {data['ort'] or DEFAULT_PLACEHOLDER}",
                        allow_wrap=is_mobile,
                        max_lines=2,
                    ),
                    meta_row(
                        ft.Icons.SCHEDULE,
                        f"{event_label}: {data['when']}" if data["when"] and data["when"] != "—" else DEFAULT_PLACEHOLDER,
                    ),
                    meta_row(ft.Icons.CALENDAR_TODAY, f"Erstellt am: {data['created_at']}"),
                ],
                spacing=6,
                tight=True,
            ),
        ],
        tight=True,
        spacing=8,
        width=None if is_mobile else 480,
        expand=True,
        scroll=ft.ScrollMode.AUTO if is_mobile else ft.ScrollMode.AUTO,
    )

    if supabase and post_id and profile_service is not None:
        comment_section = CommentSection(
            page, post_id, supabase,
            profile_service=profile_service,
            on_login_required=on_comment_login_required,
        )
        # CommentSection transparent - Dialog-Hintergrund scheint durch
        right_column = ft.Container(
            content=comment_section,
            width=None if is_mobile else 480,
            expand=True,
            padding=ft.padding.only(left=8) if not is_mobile else ft.padding.only(top=8),
        )
        if is_mobile:
            dialog_content = ft.Column(
                [details_column, right_column],
                spacing=12,
            )
        else:
            dialog_content = ft.Row(
                [details_column, right_column],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
    else:
        dialog_content = details_column

    if is_mobile:
        dialog_content = ft.Column(
            [dialog_content],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    dlg = ft.AlertDialog(
        title=title_row,
        title_padding=ft.padding.only(left=24, right=8, top=8, bottom=0),
        content=ft.Container(
            content=dialog_content,
            width=None if is_mobile else 1080,
            height=None if is_mobile else 600,
        ),
        content_padding=ft.padding.only(left=24, right=24, bottom=8),
    )
    close_btn.on_click = lambda _: page.close(dlg)
    page.open(dlg)
    # Kommentare nach Öffnen laden (Dialog muss bereits in der Page sein)
    if supabase and post_id and profile_service is not None:
        comment_section.load_comments()
        page.update()


def show_contact_form_dialog(
    page: ft.Page,
    item: Dict[str, Any],
    profile_service,
    on_submit_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> None:
    """Zeigt das Kontaktformular für eine Meldung als Dialog.

    Args:
        page: Flet Page-Instanz
        item: Post-Dictionary
        profile_service: ProfileService-Instanz (zum Laden von Nutzerdaten)
        on_submit_callback: Optionaler Callback nach dem Absenden (erhält contact_payload)
    """
    from utils.logging_config import get_logger
    _logger = get_logger(__name__)

    current_user = profile_service.get_current_user()
    email_value = (profile_service.get_email() or "").strip()
    user_meta = getattr(current_user, "user_metadata", {}) or {}
    first_name_value = user_meta.get("first_name") or user_meta.get("firstname") or ""
    last_name_value = user_meta.get("last_name") or user_meta.get("lastname") or ""

    email_field = ft.TextField(label="E-Mail", value=email_value, read_only=True, border_radius=10, expand=True)
    phone_field = ft.TextField(label="Telefon (optional)", hint_text="z. B. 0911/123456", border_radius=10, expand=True)
    first_name_field = ft.TextField(label="Vorname", value=str(first_name_value or ""), border_radius=10, expand=True)
    last_name_field = ft.TextField(label="Nachname", value=str(last_name_value or ""), border_radius=10, expand=True)
    subject_field = ft.TextField(label="Betreff", border_radius=10, max_length=120, counter_text="", expand=True)
    message_field = ft.TextField(
        label="Mitteilung",
        multiline=True,
        min_lines=6,
        max_lines=8,
        border_radius=10,
        max_length=2000,
        hint_text="Textlänge (maximal 2000)",
        expand=True,
    )

    post_title = str(item.get("headline") or item.get("title") or "Meldung")

    def close_dialog(_e=None) -> None:
        page.close(contact_dialog)

    def submit_contact(_e) -> None:
        subject = (subject_field.value or "").strip()
        message = (message_field.value or "").strip()

        if not subject:
            subject_field.error_text = "Bitte Betreff eingeben."
            page.update()
            return
        subject_field.error_text = None

        if not message:
            message_field.error_text = "Bitte Mitteilung eingeben."
            page.update()
            return
        message_field.error_text = None

        contact_payload = {
            "post_id": item.get("id"),
            "post_title": post_title,
            "email": email_field.value,
            "phone": (phone_field.value or "").strip() or None,
            "first_name": (first_name_field.value or "").strip() or None,
            "last_name": (last_name_field.value or "").strip() or None,
            "subject": subject,
            "message": message,
        }
        _logger.info("Kontaktanfrage erstellt für Post %s", contact_payload.get("post_id"))

        if on_submit_callback:
            try:
                on_submit_callback(contact_payload)
            except Exception as ex:
                _logger.warning(f"Kontakt-Callback fehlgeschlagen: {ex}")

        page.close(contact_dialog)
        page.snack_bar = ft.SnackBar(ft.Text("Kontaktanfrage vorbereitet."), bgcolor=PRIMARY_COLOR)
        page.snack_bar.open = True
        page.update()

    contact_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Kontaktformular", weight=ft.FontWeight.W_600),
        content=ft.Container(
            width=760,
            content=ft.Column(
                [
                    ft.Text(f"Ihre Nachricht zu: {post_title}", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.ResponsiveRow(
                        [ft.Container(first_name_field, col={"xs": 12, "md": 6}), ft.Container(last_name_field, col={"xs": 12, "md": 6})],
                        spacing=12, run_spacing=8,
                    ),
                    ft.ResponsiveRow(
                        [ft.Container(email_field, col={"xs": 12, "md": 6}), ft.Container(phone_field, col={"xs": 12, "md": 6})],
                        spacing=12, run_spacing=8,
                    ),
                    subject_field,
                    message_field,
                ],
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(top=4),
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=close_dialog),
            ft.ElevatedButton(
                "Senden",
                on_click=submit_contact,
                style=ft.ButtonStyle(bgcolor=PRIMARY_COLOR, color=ft.Colors.WHITE),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(contact_dialog)
