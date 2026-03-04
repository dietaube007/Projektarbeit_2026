"""
My Posts Handler: Logik für Verwaltung eigener Meldungen im Profilbereich.
Enthält: Laden, Rendern, Löschen, Bearbeiten.
"""

from __future__ import annotations

from typing import Callable, List, Optional
from pathlib import Path
from urllib.parse import urlparse
import time
import uuid
import flet as ft

from ui.shared_components import loading_indicator, show_success_dialog, show_error_dialog
from services.posts import PostService, PostStorageService
from services.posts.references import ReferenceService
from utils.logging_config import get_logger
from utils.validators import validate_email
from utils.pdf_generator import create_post_pdf, create_post_pdf_bytes
from ..components.my_posts_components import build_my_post_card
from ui.discover.components.post_card_components import show_detail_dialog
from ..components.edit_post_components import EditPostDialog

logger = get_logger(__name__)


def show_post_details(page: ft.Page, post: dict) -> None:
    """Zeigt die Details einer Meldung in einem Dialog an (Handler).
    
    Args:
        page: Flet Page-Instanz
        post: Post-Dictionary
    """
    show_detail_dialog(page=page, item=post)


# build_my_post_card wird aus components.post_components importiert


def delete_post(sb, post_id: int) -> bool:
    """Löscht einen Post und alle verknüpften Daten inkl. Storage-Bilder.
    
    Diese Funktion verwendet PostService.delete() für konsistente Löschlogik.
    
    Args:
        sb: Supabase Client-Instanz
        post_id: ID des zu löschenden Posts (int wird zu str konvertiert)
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # PostService verwendet str für post_id, daher konvertieren
        post_service = PostService(sb)
        return post_service.delete(str(post_id))
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Posts {post_id}: {e}", exc_info=True)
        return False


def handle_mark_reunited(
    post: dict,
    page: ft.Page,
    sb,
    on_posts_changed: Optional[Callable] = None,
) -> None:
    """Setzt eine Meldung auf 'Wiedervereint'."""
    try:
        ref_service = ReferenceService(sb)
        statuses = ref_service.get_post_statuses() or []
        reunited = next(
            (s for s in statuses if str(s.get("name", "")).lower() == "wiedervereint"),
            None,
        )
        if not reunited:
            show_error_dialog(page, "Fehler", "Status 'Wiedervereint' nicht gefunden.")
            return

        post_service = PostService(sb)
        post_service.update(str(post.get("id")), {"post_status_id": reunited["id"]})
        show_success_dialog(page, "Aktualisiert", "Meldung wurde auf 'Wiedervereint' gesetzt.")
        if on_posts_changed:
            on_posts_changed()
    except Exception as e:
        logger.error(f"Fehler beim Setzen auf Wiedervereint: {e}", exc_info=True)
        show_error_dialog(page, "Fehler", "Die Meldung konnte nicht aktualisiert werden.")


def render_my_posts_list(
    posts_list: ft.ResponsiveRow,
    posts_items: List[dict],
    page: ft.Page,
    on_edit: Optional[Callable[[dict], None]] = None,
    on_delete: Optional[Callable[[int], None]] = None,
    on_mark_reunited: Optional[Callable[[dict], None]] = None,
    on_export_pdf: Optional[Callable[[dict], None]] = None,
    not_logged_in: bool = False,
    supabase=None,
    profile_service=None,
):
    """Rendert die Liste der eigenen Meldungen.
    
    Args:
        posts_list: ResponsiveRow-Container für die Liste
        posts_items: Liste der Post-Dictionaries
        page: Flet Page-Instanz
        on_edit: Optionaler Callback zum Bearbeiten
        on_delete: Optionaler Callback zum Löschen
        on_mark_reunited: Optionaler Callback zum Als-wiedervereint-markieren
        not_logged_in: Ob der Benutzer nicht eingeloggt ist
        supabase: Supabase-Client (für Kommentare im Detail-Dialog)
        profile_service: ProfileService (für Kommentare im Detail-Dialog)
    """
    posts_list.controls.clear()
    
    if not_logged_in:
        posts_list.controls.append(
            ft.Container(
                content=ft.Text("Bitte einloggen um Ihre Meldungen zu sehen.", color=ft.Colors.GREY_600),
                col=12,
            )
        )
    elif not posts_items:
        posts_list.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ARTICLE_OUTLINED, size=48, color=ft.Colors.GREY_400),
                        ft.Text("Sie haben noch keine Meldungen erstellt.", color=ft.Colors.GREY_600),
                        ft.Text(
                            "Erstellen Sie eine Meldung über den 'Melden'-Tab.",
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                col=12,
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=32),
            )
        )
    else:
        for post in posts_items:
            posts_list.controls.append(
                build_my_post_card(
                    post,
                    page=page,
                    on_edit=on_edit,
                    on_delete=on_delete,
                    on_mark_reunited=on_mark_reunited,
                    on_export_pdf=on_export_pdf,
                    supabase=supabase,
                    profile_service=profile_service,
                )
            )


async def load_my_posts(
    my_posts_list: ft.ResponsiveRow,
    my_posts_items: List[dict],
    page: ft.Page,
    sb,
    on_posts_changed: Optional[Callable] = None,
    on_edit: Optional[Callable[[dict], None]] = None,
    on_delete: Optional[Callable[[int], None]] = None,
    on_mark_reunited: Optional[Callable[[dict], None]] = None,
    on_export_pdf: Optional[Callable[[dict], None]] = None,
) -> List[dict]:
    """Lädt alle eigenen Meldungen des aktuellen Benutzers.
    
    Args:
        my_posts_list: ResponsiveRow-Container für die Liste
        my_posts_items: Liste der Posts (wird aktualisiert)
        page: Flet Page-Instanz
        sb: Supabase Client
        on_posts_changed: Optionaler Callback wenn Posts geändert wurden
        on_edit: Optionaler Callback zum Bearbeiten
        on_delete: Optionaler Callback zum Löschen
    
    Returns:
        Liste der geladenen Posts
    """
    try:
        my_posts_list.controls = [ft.Container(content=loading_indicator("Meldungen werden geladen..."), col=12)]
        page.update()

        from services.account import ProfileService
        profile_service = ProfileService(sb)
        user_id = profile_service.get_user_id()
        
        if not user_id:
            my_posts_items.clear()
            render_my_posts_list(
                my_posts_list,
                my_posts_items,
                page=page,
                on_edit=on_edit,
                on_delete=on_delete,
                on_mark_reunited=on_mark_reunited,
                not_logged_in=True,
            )
            page.update()
            return my_posts_items

        # PostService nutzen
        post_service = PostService(sb)
        my_posts_items.clear()
        posts = post_service.get_my_posts(user_id)

        # Eigene Profildaten an Posts anhängen (für Detail-Dialog)
        display_name = profile_service.get_display_name()
        profile_image_url = profile_service.get_profile_image_url()
        for p in posts:
            p["user_display_name"] = display_name
            p["user_profile_image"] = profile_image_url

        my_posts_items.extend(posts)
        render_my_posts_list(
            my_posts_list,
            my_posts_items,
            page=page,
            on_edit=on_edit,
            on_delete=on_delete,
            on_mark_reunited=on_mark_reunited,
            on_export_pdf=on_export_pdf,
            supabase=sb,
            profile_service=profile_service,
        )
        page.update()
        return my_posts_items

    except Exception as e:
        logger.error(f"Fehler beim Laden der eigenen Meldungen: {e}", exc_info=True)
        my_posts_items.clear()
        render_my_posts_list(
            my_posts_list,
            my_posts_items,
            page=page,
            on_edit=on_edit,
            on_delete=on_delete,
            on_mark_reunited=on_mark_reunited,
            on_export_pdf=on_export_pdf,
        )
        page.update()
        return my_posts_items


def _normalize_contact(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _get_post_contact(post: dict) -> tuple[Optional[str], Optional[str]]:
    email = _normalize_contact(post.get("contact_email"))
    phone = _normalize_contact(post.get("contact_phone"))
    return email, phone


def handle_export_pdf_request(
    page: ft.Page,
    post: dict,
    profile_service,
    on_confirm: Callable[[dict, Optional[str], Optional[str], Optional[str]], None],
) -> None:
    """Startet den PDF-Export und fragt Kontaktmethode nur bei Bedarf ab."""
    post_email, post_phone = _get_post_contact(post)
    email = post_email or _normalize_contact(profile_service.get_email())
    phone = post_phone

    email_tf = ft.TextField(
        label="E-Mail",
        keyboard_type=ft.KeyboardType.EMAIL,
        value=email or "",
    )
    phone_tf = ft.TextField(
        label="Telefonnummer",
        keyboard_type=ft.KeyboardType.PHONE,
        input_filter=ft.NumbersOnlyInputFilter(),
        helper_text="Nur Zahlen eingeben",
        value=phone or "",
    )
    additions_tf = ft.TextField(
        label="Ergänzungen",
        hint_text="Weitere Hinweise oder Zusatzinfos",
        multiline=True,
        min_lines=2,
        max_lines=4,
    )
    error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

    def on_cancel(_):
        page.close(dialog)

    def on_continue(_):
        entered_email = _normalize_contact(email_tf.value)
        entered_phone = _normalize_contact(phone_tf.value)
        additions = _normalize_contact(additions_tf.value)

        if not entered_email and not entered_phone:
            error_text.value = "Bitte E-Mail oder Telefonnummer angeben."
            page.update()
            return

        if entered_email:
            valid, msg = validate_email(entered_email)
            if not valid:
                error_text.value = msg or "Ungültige E-Mail-Adresse."
                page.update()
                return

        page.close(dialog)
        on_confirm(post, entered_email, entered_phone, additions)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Kontakt angeben"),
        content=ft.Column(
            [
                ft.Text(
                    "Bitte gib mindestens eine Kontaktmethode an, "
                    "die in der PDF erscheinen soll."
                ),
                email_tf,
                phone_tf,
                additions_tf,
                error_text,
            ],
            tight=True,
            spacing=8,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton("Weiter", on_click=on_continue),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dialog)


def generate_post_pdf(
    page: ft.Page,
    sb,
    post: dict,
    output_path: Optional[str],
    contact_email: Optional[str],
    contact_phone: Optional[str],
    additions: Optional[str],
) -> None:
    """Erstellt die PDF-Datei fuer eine Meldung und speichert sie lokal."""
    try:
        image_bytes = None
        post_images = post.get("post_image") or []
        image_url = post_images[0].get("url") if post_images else None
        if isinstance(image_url, str) and image_url.strip():
            storage_service = PostStorageService(sb)
            storage_path = storage_service.extract_storage_path_from_url(image_url)
            if storage_path:
                image_bytes = storage_service.download_post_image(storage_path)

        if page.web:
            pdf_bytes = create_post_pdf_bytes(
                post=post,
                image_bytes=image_bytes,
                contact_email=contact_email,
                contact_phone=contact_phone,
                additions=additions,
            )
            root_dir = Path(__file__).resolve().parents[3]
            export_dir = root_dir / "assets" / "pdf_exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            post_id = post.get("id") or "meldung"
            safe_id = str(post_id).replace(" ", "_")
            filename = f"{safe_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.pdf"
            export_path = export_dir / filename
            export_path.write_bytes(pdf_bytes)
            download_path = f"/download/{filename}"
            raw_url = (page.url or "").strip()
            base_url = ""
            if raw_url:
                parsed = urlparse(raw_url)
                scheme = parsed.scheme
                if scheme == "ws":
                    scheme = "http"
                elif scheme == "wss":
                    scheme = "https"
                if parsed.netloc:
                    base_url = f"{scheme}://{parsed.netloc}"
            full_url = f"{base_url}{download_path}" if base_url else download_path

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("PDF bereit"),
                content=ft.Text("Die PDF wird heruntergeladen."),
                actions=[
                    ft.TextButton("Abbrechen", on_click=lambda e: page.close(dialog)),
                    ft.ElevatedButton(
                        "Download starten",
                        url=full_url,
                        url_target=ft.UrlTarget.BLANK,
                        on_click=lambda e: page.close(dialog),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.open(dialog)
            return

        if not output_path:
            show_error_dialog(page, "Fehler", "Kein Speicherpfad ausgewaehlt.")
            return

        create_post_pdf(
            post=post,
            output_path=output_path,
            image_bytes=image_bytes,
            contact_email=contact_email,
            contact_phone=contact_phone,
            additions=additions,
        )
        show_success_dialog(page, "PDF erstellt", "Die PDF wurde erfolgreich gespeichert.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Fehler beim PDF-Export: {e}", exc_info=True)
        show_error_dialog(page, "Fehler", "Die PDF konnte nicht erstellt werden.")


def edit_post(
    post: dict,
    page: ft.Page,
    sb,
    on_save_callback: Optional[Callable] = None,
) -> None:
    """Öffnet den Bearbeitungsdialog für einen Post.
    
    Args:
        post: Post-Dictionary
        page: Flet Page-Instanz
        sb: Supabase Client
        on_save_callback: Optionaler Callback nach dem Speichern
    """
    dialog = EditPostDialog(
        page=page,
        sb=sb,
        post=post,
        on_save_callback=on_save_callback,
    )
    dialog.show()


def confirm_delete_post(
    post_id: int,
    page: ft.Page,
    on_confirm: Callable[[int], None],
) -> None:
    """Zeigt Bestätigungsdialog zum Löschen eines Posts.
    
    Args:
        post_id: ID des Posts
        page: Flet Page-Instanz
        on_confirm: Callback der beim Bestätigen aufgerufen wird
    """
    def on_confirm_click(e):
        page.close(dialog)
        on_confirm(post_id)

    def on_cancel(e):
        page.close(dialog)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Meldung löschen?"),
        content=ft.Text(
            "Möchten Sie diese Meldung wirklich löschen?\nDiese Aktion kann nicht rückgängig gemacht werden."
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_cancel),
            ft.ElevatedButton(
                "Löschen",
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                on_click=on_confirm_click,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dialog)


def handle_delete_post(
    post_id: int,
    my_posts_items: List[dict],
    my_posts_list: ft.ResponsiveRow,
    page: ft.Page,
    sb,
    on_posts_changed: Optional[Callable] = None,
    on_edit: Optional[Callable[[dict], None]] = None,
    on_delete: Optional[Callable[[int], None]] = None,
    on_mark_reunited: Optional[Callable[[dict], None]] = None,
    profile_service=None,
) -> None:
    """Löscht einen Post und aktualisiert die UI.
    
    Args:
        post_id: ID des Posts
        my_posts_items: Liste der Posts (wird aktualisiert)
        my_posts_list: ResponsiveRow-Container für die Liste
        page: Flet Page-Instanz
        sb: Supabase Client
        on_posts_changed: Optionaler Callback wenn Posts geändert wurden
        on_edit: Optionaler Callback zum Bearbeiten
        on_delete: Optionaler Callback zum Löschen
        profile_service: ProfileService (für Kommentare im Detail-Dialog)
    """
    try:
        if delete_post(sb, post_id):
            # Lokal entfernen
            my_posts_items[:] = [
                p for p in my_posts_items if p.get("id") != post_id
            ]
            render_my_posts_list(
                my_posts_list,
                my_posts_items,
                page=page,
                on_edit=on_edit,
                on_delete=on_delete,
                on_mark_reunited=on_mark_reunited,
                supabase=sb,
                profile_service=profile_service,
            )
            show_success_dialog(page, "Meldung gelöscht", "Die Meldung wurde erfolgreich gelöscht.")
            page.update()

            # Startseite aktualisieren
            if on_posts_changed:
                on_posts_changed()
        else:
            show_error_dialog(page, "Löschen fehlgeschlagen", "Die Meldung konnte nicht gelöscht werden.")
            page.update()

    except Exception as e:
        logger.error(f"Fehler beim Löschen des Posts {post_id}: {e}", exc_info=True)
