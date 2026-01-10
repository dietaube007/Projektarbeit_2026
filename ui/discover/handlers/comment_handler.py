"""
Comment-Handler: UI-Handler für Kommentar-Verwaltung.
"""

from __future__ import annotations

from typing import List, Dict, Any, Callable, Optional, Union

import flet as ft

from utils.logging_config import get_logger
from services.posts import CommentService

logger = get_logger(__name__)


def handle_load_comments(
    comment_service: CommentService,
    post_id: str,
    comments_list: ft.Column,
    loading_indicator: ft.ProgressRing,
    page: ft.Page,
    create_empty_state: Callable[[], ft.Control],
    create_comment_card: Callable[[Dict[str, Any], bool], ft.Control],
    create_error_state: Callable[[str], ft.Control],
) -> None:
    """Lädt alle nicht gelöschten Kommentare für einen Post.
    
    Args:
        comment_service: CommentService-Instanz
        post_id: UUID des Posts
        comments_list: Column-Container für die Kommentar-Liste
        loading_indicator: ProgressRing für Lade-Indikator
        page: Flet Page-Instanz
        create_empty_state: Funktion zum Erstellen des Empty-State-UI
        create_comment_card: Funktion zum Erstellen einer Kommentar-Karte
        create_error_state: Funktion zum Erstellen des Error-State-UI
    """
    loading_indicator.visible = True
    comments_list.controls.clear()
    
    try:
        page.update()
    except Exception:
        pass
    
    try:
        # Kommentare über Service laden
        comments = comment_service.get_comments(post_id)
        
        if not comments:
            # Keine Kommentare vorhanden
            comments_list.controls.append(create_empty_state())
        else:
            # Kommentare einfach auflisten (keine hierarchische Struktur, da kein parent_comment_id im Schema)
            for comment in comments:
                comments_list.controls.append(create_comment_card(comment, is_reply=False))
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Kommentare: {e}", exc_info=True)
        comments_list.controls.clear()
        comments_list.controls.append(create_error_state(str(e)))
    finally:
        # Stelle sicher, dass der Loading-Indikator IMMER ausgeblendet wird
        loading_indicator.visible = False
        try:
            page.update()
        except Exception:
            pass


def handle_post_comment(
    comment_service: CommentService,
    post_id: str,
    user_id: Optional[str],
    content: str,
    comment_input: ft.TextField,
    send_button: ft.IconButton,
    reply_banner: ft.Container,
    replying_to: Optional[str],
    page: ft.Page,
    on_success: Callable[[], None],
    show_snackbar: Callable[[str, str], None],
) -> bool:
    """Speichert einen neuen Kommentar.
    
    Args:
        comment_service: CommentService-Instanz
        post_id: UUID des Posts
        user_id: UUID des Benutzers (None wenn nicht eingeloggt)
        content: Kommentar-Text
        comment_input: TextField für Kommentar-Eingabe
        send_button: IconButton zum Senden
        reply_banner: Container für Antwort-Banner
        replying_to: Optional UUID des Kommentars auf den geantwortet wird
        page: Flet Page-Instanz
        on_success: Callback nach erfolgreichem Speichern (z.B. Kommentare neu laden)
        show_snackbar: Funktion zum Anzeigen von Snackbar-Nachrichten
    
    Returns:
        True bei Erfolg, False bei Fehler oder ungültiger Eingabe
    """
    # Eingabe validieren
    if not content or not content.strip():
        return False
    
    # Login-Check
    if not user_id:
        show_snackbar("Sie müssen eingeloggt sein, um zu kommentieren!", ft.Colors.RED_400)
        return False
    
    # Button während des Sendens deaktivieren
    send_button.disabled = True
    page.update()
    
    try:
        # Kommentar über Service speichern
        success = comment_service.create_comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
        )
        
        if success:
            # Eingabefeld leeren
            comment_input.value = ""
            
            # Antwort-Modus beenden
            if replying_to:
                reply_banner.visible = False
                comment_input.hint_text = "Schreibe einen Kommentar..."
            
            # Success-Nachricht
            show_snackbar("Kommentar gepostet!", ft.Colors.GREEN_400)
            
            # Kommentare neu laden
            on_success()
            
            return True
        else:
            show_snackbar("Fehler beim Senden des Kommentars.", ft.Colors.RED_400)
            return False
        
    except Exception as e:
        logger.error(f"Fehler beim Posten des Kommentars: {e}", exc_info=True)
        show_snackbar(f"Fehler beim Senden: {str(e)}", ft.Colors.RED_400)
        return False
    
    finally:
        # Button wieder aktivieren
        send_button.disabled = False
        page.update()


def handle_delete_comment(
    comment_service: CommentService,
    comment_id: Union[int, str],
    page: ft.Page,
    on_success: Callable[[], None],
    show_snackbar: Callable[[str, str], None],
) -> bool:
    """Löscht einen Kommentar (Soft-Delete).
    
    Args:
        comment_service: CommentService-Instanz
        comment_id: ID des Kommentars (serial integer oder String)
        page: Flet Page-Instanz
        on_success: Callback nach erfolgreichem Löschen (z.B. Kommentare neu laden)
        show_snackbar: Funktion zum Anzeigen von Snackbar-Nachrichten
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Kommentar über Service löschen
        success = comment_service.delete_comment(comment_id)
        
        if success:
            show_snackbar("Kommentar gelöscht", ft.Colors.ORANGE_400)
            # Kommentare neu laden
            on_success()
            return True
        else:
            show_snackbar("Fehler beim Löschen", ft.Colors.RED_400)
            return False
        
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Kommentars (ID: {comment_id}): {e}", exc_info=True)
        show_snackbar("Fehler beim Löschen", ft.Colors.RED_400)
        return False
