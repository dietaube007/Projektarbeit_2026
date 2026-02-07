"""
My Posts Handler: Logik für Verwaltung eigener Meldungen im Profilbereich.
Enthält: Laden, Rendern, Löschen, Bearbeiten.
"""

from __future__ import annotations

from typing import Callable, List, Optional
import flet as ft

from ui.shared_components import loading_indicator, show_success_dialog, show_error_dialog
from services.posts import PostService
from services.posts.references import ReferenceService
from utils.logging_config import get_logger
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
        )
        page.update()
        return my_posts_items


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
