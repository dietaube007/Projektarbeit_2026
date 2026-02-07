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
    on_comments_loaded: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
    show_loading: bool = True,
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
        on_comments_loaded: Optionaler Callback mit der geladenen Kommentar-Liste (für Inline-Refresh)
    """
    if show_loading:
        loading_indicator.visible = True
    comments_list.controls.clear()
    
    if show_loading:
        try:
            page.update()
        except Exception:
            pass
    
    try:
        # Kommentare über Service laden
        comments = comment_service.get_comments(post_id)
        if on_comments_loaded is not None:
            on_comments_loaded(comments or [])
        
        if not comments:
            # Keine Kommentare vorhanden
            comments_list.controls.append(create_empty_state())
        else:
            # Kommentare hierarchisch rendern
            def render_comment_with_replies(comment, is_reply=False):
                """Rendert einen Kommentar mit allen seinen Antworten."""
                comments_list.controls.append(create_comment_card(comment, is_reply=is_reply))
                # Antworten rekursiv rendern
                replies = comment.get("replies", [])
                for reply in replies:
                    render_comment_with_replies(reply, is_reply=True)
            
            for comment in comments:
                render_comment_with_replies(comment, is_reply=False)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Kommentare: {e}", exc_info=True)
        comments_list.controls.clear()
        comments_list.controls.append(create_error_state(str(e)))
    finally:
        # Stelle sicher, dass der Loading-Indikator IMMER ausgeblendet wird
        if show_loading:
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
    
    Returns:
        True bei Erfolg, False bei Fehler oder ungültiger Eingabe
    """
    # Eingabe validieren
    if not content or not content.strip():
        return False
    
    # Login-Check
    if not user_id:
        return False
    
    # Button während des Sendens deaktivieren
    send_button.disabled = True
    page.update()
    
    try:
        # Kommentar über Service speichern
        parent_id = None
        if replying_to:
            try:
                parent_id = int(replying_to) if isinstance(replying_to, str) else replying_to
            except (ValueError, TypeError):
                logger.warning(f"Ungültige parent_comment_id: {replying_to}")
        
        success = comment_service.create_comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            parent_comment_id=parent_id,
        )
        
        if success:
            # Eingabefeld leeren
            comment_input.value = ""
            
            # Antwort-Modus beenden
            if replying_to:
                reply_banner.visible = False
                comment_input.hint_text = "Schreibe einen Kommentar..."
            
            # Kommentare neu laden
            on_success()
            
            return True
        else:
            return False
        
    except Exception as e:
        logger.error(f"Fehler beim Posten des Kommentars: {e}", exc_info=True)
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
) -> bool:
    """Löscht einen Kommentar (Soft-Delete).
    
    Args:
        comment_service: CommentService-Instanz
        comment_id: ID des Kommentars (serial integer oder String)
        page: Flet Page-Instanz
        on_success: Callback nach erfolgreichem Löschen (z.B. Kommentare neu laden)
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Kommentar über Service löschen
        success = comment_service.delete_comment(comment_id)
        
        if success:
            # Kommentare neu laden
            on_success()
            return True
        else:
            return False
        
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Kommentars (ID: {comment_id}): {e}", exc_info=True)
        return False
