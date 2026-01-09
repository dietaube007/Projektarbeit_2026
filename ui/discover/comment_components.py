"""
Kommentar-Komponenten für die Discover-View.

Enthält die CommentSection-Klasse für die Kommentar-Funktionalität in Posts.
"""

import flet as ft
from typing import Optional

from ui.helpers import format_time
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CommentSection(ft.Container):
    """
    Kommentar-Sektion für PetBuddy Posts mit Antwort-Funktion
    Funktioniert mit Supabase und der bestehenden comment-Tabelle
    """
    
    def __init__(self, page: ft.Page, post_id: str, supabase, profile_service=None):
        """Initialisiert die CommentSection.
        
        Args:
            page: Flet Page-Instanz
            post_id: UUID des Posts für den Kommentare angezeigt werden
            supabase: Supabase-Client für Datenbankzugriffe
            profile_service: Optional ProfileService für User-ID-Abfragen
        """
        self._page = page  # Verwende _page statt page um Konflikt zu vermeiden
        self.post_id = post_id  # UUID des Posts
        self.supabase = supabase
        self.profile_service = profile_service
        # Antwort-Funktion deaktiviert, da kein parent_comment_id im Schema
        self.replying_to = None
        
        # Kommentar-Liste (scrollbar)
        self.comments_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )
        
        # Lade-Indikator
        self.loading = ft.ProgressRing(visible=False)
        
        # Antwort-Info-Banner (zeigt an, auf welchen Kommentar geantwortet wird)
        self.reply_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.REPLY, size=16, color=ft.Colors.BLUE),
                ft.Text("Antwort auf ", size=12, color=ft.Colors.BLUE),
                ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    tooltip="Abbrechen",
                    on_click=self.cancel_reply
                )
            ], spacing=5),
            bgcolor=ft.Colors.BLUE_50,
            padding=8,
            border_radius=8,
            visible=False
        )
        
        # Kommentar-Eingabe
        self.comment_input = ft.TextField(
            hint_text="Schreibe einen Kommentar...",
            multiline=True,
            min_lines=1,
            max_lines=4,
            expand=True,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
            on_submit=self.post_comment
        )
        
        # Send-Button
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,  # FIX: Icons mit großem I
            tooltip="Kommentar senden",
            on_click=self.post_comment,
            icon_color=ft.Colors.BLUE,
            disabled=False
        )
        
        super().__init__(
            content=ft.Column([
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.COMMENT, size=24, color=ft.Colors.BLUE),
                        ft.Text(
                            "Kommentare",
                            size=18,
                            weight=ft.FontWeight.BOLD
                        ),
                        self.loading
                    ], spacing=10),
                    padding=ft.padding.only(top=20, bottom=10, left=10, right=10)
                ),
                
                # Kommentare Container
                ft.Container(
                    content=self.comments_list,
                    padding=10,
                    expand=True
                ),
                
                # Antwort-Banner
                ft.Container(
                    content=self.reply_banner,
                    padding=ft.padding.only(left=10, right=10, bottom=5)
                ),
                
                # Eingabe-Bereich
                ft.Container(
                    content=ft.Row([
                        self.comment_input,
                        self.send_button
                    ], spacing=10),
                    padding=10,
                    border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300)),
                    bgcolor=ft.Colors.WHITE
                )
            ], spacing=0),
            expand=True
        )
    
    
    def load_comments(self):
        """Lädt alle nicht gelöschten Kommentare für diesen Post.
        
        Zeigt einen Loading-Indikator während des Ladens und rendert die
        Kommentare in der Kommentar-Liste.
        """
        self.loading.visible = True
        self.comments_list.controls.clear()
        
        try:
            self._page.update()
        except Exception:
            pass
        
        try:
            # Kommentare mit User-Daten laden (nur nicht gelöschte)
            # Schema: comment referenziert user-Tabelle (nicht auth.users)
            response = self.supabase.table('comment') \
                .select('id, post_id, user_id, content, created_at, is_deleted, user:user_id(display_name, profile_image)') \
                .eq('post_id', self.post_id) \
                .eq('is_deleted', False) \
                .order('created_at', desc=False) \
                .execute()
            
            comments = response.data if response and hasattr(response, 'data') else []
            
            if not comments:
                # Keine Kommentare vorhanden
                self.comments_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(
                                ft.Icons.COMMENT_OUTLINED,
                                size=48,
                                color=ft.Colors.GREY_400
                            ),
                            ft.Text(
                                "Noch keine Kommentare",
                                size=16,
                                color=ft.Colors.GREY_600
                            ),
                            ft.Text(
                                "Sei der Erste, der kommentiert!",
                                size=12,
                                color=ft.Colors.GREY_500
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5),
                        padding=30,
                        alignment=ft.alignment.center
                    )
                )
            else:
                # Kommentare einfach auflisten (keine hierarchische Struktur, da kein parent_comment_id im Schema)
                for comment in comments:
                    self.comments_list.controls.append(
                        self.create_comment_card(comment, is_reply=False)
                    )
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Kommentare: {e}", exc_info=True)
            self.comments_list.controls.clear()
            self.comments_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"Fehler beim Laden: {str(e)}",
                        color=ft.Colors.RED_400,
                        size=14
                    ),
                    padding=20
                )
            )
        finally:
            # Stelle sicher, dass der Loading-Indikator IMMER ausgeblendet wird
            self.loading.visible = False
            try:
                self._page.update()
            except Exception:
                pass
    
    def create_comment_card(self, comment, is_reply=False):
        """Erstellt eine Kommentar-Karte.
        
        Args:
            comment: Dictionary mit Kommentar-Daten
            is_reply: Ob es sich um eine Antwort handelt (aktuell nicht verwendet)
        
        Returns:
            Container mit Kommentar-Karte
        """
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        is_author = (str(current_user_id) == str(comment.get('user_id')))
        
        # User-Daten extrahieren (Schema: user-Tabelle hat display_name, nicht username)
        user_data = comment.get('user', {})
        username = user_data.get('display_name', 'Unbekannt') if isinstance(user_data, dict) else 'Unbekannt'
        profile_image = user_data.get('profile_image') if isinstance(user_data, dict) else None
        
        # Antworten-Funktion entfernt, da kein parent_comment_id im Schema
        reply_button = ft.Container(width=0)
        
        card_content = ft.Row([
            # Profilbild
            ft.CircleAvatar(
                foreground_image_url=profile_image if profile_image else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE) if not profile_image else None,
                bgcolor=ft.Colors.BLUE_400,
                radius=20 if not is_reply else 16
            ),
            
            # Kommentar-Inhalt
            ft.Column([
                # Kopfzeile: Name + Zeit
                ft.Row([
                    ft.Text(
                        username,
                        weight=ft.FontWeight.BOLD,
                        size=14 if not is_reply else 13,
                        color=ft.Colors.BLACK87
                    ),
                    ft.Text(
                        format_time(comment.get('created_at')),
                        size=12 if not is_reply else 11,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=10),
                
                # Kommentar-Text
                ft.Text(
                    comment.get('content', ''),
                    size=14 if not is_reply else 13,
                    selectable=True,
                    color=ft.Colors.BLACK
                ),
                
                # Aktionen (Antworten, Löschen)
                ft.Row([
                    reply_button,
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=18,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Löschen",
                        visible=is_author,
                        on_click=lambda e, cid=comment.get('id'): self.delete_comment(cid)
                    ) if is_author else ft.Container(width=0)
                ], spacing=5)
                
            ], spacing=5, expand=True),
            
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
        
        # Container mit Einrückung für Antworten
        return ft.Container(
            content=card_content,
            padding=12,
            margin=ft.margin.only(left=50 if is_reply else 0),
            bgcolor=ft.Colors.GREY_50 if not is_reply else ft.Colors.BLUE_50,
            border_radius=10,
            border=ft.border.only(left=ft.BorderSide(3, ft.Colors.BLUE_300)) if is_reply else None,
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )
    
    def start_reply(self, comment):
        """Startet den Antwort-Modus für einen Kommentar"""
        self.replying_to = comment['id']
        
        # Username extrahieren (Schema: user-Tabelle hat display_name)
        user_data = comment.get('user', {})
        username = user_data.get('display_name', 'Unbekannt') if isinstance(user_data, dict) else 'Unbekannt'
        
        # Banner aktualisieren
        self.reply_banner.visible = True
        self.reply_banner.content.controls[2].value = username
        
        # Placeholder ändern
        self.comment_input.hint_text = f"Antworte auf {username}..."
        self.comment_input.focus()
        
        self._page.update()
    
    def cancel_reply(self, e=None):
        """Bricht den Antwort-Modus ab.
        
        Args:
            e: Optional ControlEvent vom Button-Klick
        """
        self.replying_to = None
        self.reply_banner.visible = False
        self.comment_input.hint_text = "Schreibe einen Kommentar..."
        self._page.update()
    
    def post_comment(self, e):
        """Speichert einen neuen Kommentar in Supabase.
        
        Args:
            e: ControlEvent vom Button-Klick
        """
        # Eingabe validieren
        if not self.comment_input.value or not self.comment_input.value.strip():
            return
        
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        
        # Login-Check
        if not current_user_id:
            self.show_snackbar("Sie müssen eingeloggt sein, um zu kommentieren!", ft.Colors.RED_400)
            return
        
        # Button während des Sendens deaktivieren
        self.send_button.disabled = True
        self._page.update()
        
        try:
            # Kommentar-Daten vorbereiten
            # Schema: id ist serial (auto-increment), kein parent_comment_id
            comment_data = {
                'post_id': self.post_id,
                'user_id': str(current_user_id),
                'content': self.comment_input.value.strip(),
                'is_deleted': False
            }
            
            # Kommentar in Supabase speichern
            self.supabase.table('comment').insert(comment_data).execute()
            
            # Eingabefeld leeren
            self.comment_input.value = ""
            
            # Antwort-Modus beenden
            if self.replying_to:
                self.cancel_reply()
            
            # Kommentare neu laden
            self.load_comments()
            
            # Success-Nachricht
            self.show_snackbar("Kommentar gepostet!", ft.Colors.GREEN_400)
            
        except Exception as e:
            logger.error(f"Fehler beim Posten des Kommentars: {e}", exc_info=True)
            self.show_snackbar(f"Fehler beim Senden: {str(e)}", ft.Colors.RED_400)
        
        finally:
            # Button wieder aktivieren
            self.send_button.disabled = False
            self._page.update()
    
    def delete_comment(self, comment_id):
        """Soft-Delete: Setzt is_deleted auf True.
        
        Args:
            comment_id: ID des zu löschenden Kommentars
        """
        try:
            # Soft Delete in Supabase
            self.supabase.table('comment') \
                .update({'is_deleted': True}) \
                .eq('id', comment_id) \
                .execute()
            
            # Kommentare neu laden
            self.load_comments()
            
            self.show_snackbar("Kommentar gelöscht", ft.Colors.ORANGE_400)
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Kommentars (ID: {comment_id}): {e}", exc_info=True)
            self.show_snackbar("Fehler beim Löschen", ft.Colors.RED_400)
    
    def show_snackbar(self, message: str, bgcolor: str):
        """Zeigt eine Snackbar-Nachricht.
        
        Args:
            message: Nachricht die angezeigt werden soll
            bgcolor: Hintergrundfarbe der Snackbar
        """
        self._page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=bgcolor,
            duration=3000
        )
        self._page.snack_bar.open = True
        self._page.update()