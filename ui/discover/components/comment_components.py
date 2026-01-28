"""
Kommentar-Komponenten für die Discover-View.
"""

import flet as ft
from typing import Optional

from ui.helpers import format_time
from ui.theme import get_theme_color
from ui.constants import PRIMARY_COLOR
from services.posts import CommentService
from utils.logging_config import get_logger
from utils.constants import MAX_COMMENT_LENGTH
from ..handlers.comment_handler import (
    handle_load_comments,
    handle_post_comment,
    handle_delete_comment,
)

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
        self.profile_service = profile_service
        self.comment_service = CommentService(supabase, profile_service=profile_service)
        self.replying_to = None
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        
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
                ft.Icon(ft.Icons.REPLY, size=16, color=PRIMARY_COLOR),
                ft.Text("Antwort auf ", size=12, color=PRIMARY_COLOR),
                ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color=get_theme_color("text_secondary", self.is_dark),
                    tooltip="Abbrechen",
                    on_click=self.cancel_reply
                )
            ], spacing=5),
            bgcolor=get_theme_color("card", self.is_dark),
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
            border_color=get_theme_color("text_secondary", self.is_dark),
            focused_border_color=PRIMARY_COLOR,
            hint_style=ft.TextStyle(color=get_theme_color("text_secondary", self.is_dark)),
            color=get_theme_color("text_primary", self.is_dark),
            bgcolor=get_theme_color("card", self.is_dark),
            border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
            on_submit=self.post_comment,
            max_length=MAX_COMMENT_LENGTH,
        )
        
        # Send-Button
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,  # FIX: Icons mit großem I
            tooltip="Kommentar senden",
            on_click=self.post_comment,
            icon_color=PRIMARY_COLOR,
            disabled=False
        )
        
        super().__init__(
            bgcolor=get_theme_color("background", self.is_dark),
            content=ft.Column([
                ft.Divider(height=1, color=get_theme_color("text_secondary", self.is_dark)),
                
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.COMMENT, size=24, color=PRIMARY_COLOR),
                        ft.Text(
                            "Kommentare",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=get_theme_color("text_primary", self.is_dark)
                        ),
                        self.loading
                    ], spacing=10),
                    padding=ft.padding.only(top=20, bottom=10, left=10, right=10)
                ),
                
        # Kommentare Container
        ft.Container(
            content=self.comments_list,
            padding=10,
            expand=True,
            bgcolor=get_theme_color("background", self.is_dark)
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
                    border=ft.border.only(top=ft.BorderSide(1, get_theme_color("text_secondary", self.is_dark))),
                    bgcolor=get_theme_color("background", self.is_dark)
                )
            ], spacing=0),
            expand=True
        )
        self._apply_theme()
        if not hasattr(self._page, "_theme_listeners"):
            self._page._theme_listeners = []
        self._page._theme_listeners.append(self)
    
    def _apply_theme(self) -> None:
        """Aktualisiert alle Theme-abhängigen Farben (Hintergrund, Text, Rahmen).
        Wird beim Erstellen, bei load_comments() und beim Theme-Wechsel aufgerufen.
        """
        self.is_dark = self._page.theme_mode == ft.ThemeMode.DARK
        is_dark = self.is_dark
        
        # Haupt-Container Hintergrund
        self.bgcolor = get_theme_color("background", is_dark)
        
        # Column mit allen Controls
        col = self.content
        
        # Divider (Index 0)
        col.controls[0].color = get_theme_color("text_secondary", is_dark)
        
        # Header Container (Index 1) -> Row -> Text (Index 1)
        col.controls[1].content.controls[1].color = get_theme_color("text_primary", is_dark)
        
        # Kommentare Container (Index 2)
        col.controls[2].bgcolor = get_theme_color("background", is_dark)
        
        # Antwort-Banner Container (Index 3) -> reply_banner
        self.reply_banner.bgcolor = get_theme_color("card", is_dark)
        # Reply-Banner Row: IconButton Close (Index 4)
        self.reply_banner.content.controls[4].icon_color = get_theme_color("text_secondary", is_dark)
        
        # Eingabe-Bereich Container (Index 4)
        col.controls[4].bgcolor = get_theme_color("background", is_dark)
        col.controls[4].border = ft.border.only(top=ft.BorderSide(1, get_theme_color("text_secondary", is_dark)))
        
        # Kommentar-TextField
        self.comment_input.border_color = get_theme_color("text_secondary", is_dark)
        self.comment_input.hint_style = ft.TextStyle(color=get_theme_color("text_secondary", is_dark))
        self.comment_input.color = get_theme_color("text_primary", is_dark)
        self.comment_input.bgcolor = get_theme_color("card", is_dark)
        
        # Alle bereits gerenderten Kommentar-Karten aktualisieren
        self._update_comment_cards_theme()
    
    def _update_comment_cards_theme(self) -> None:
        """Aktualisiert die Theme-Farben aller bereits gerenderten Kommentar-Karten."""
        is_dark = self._page.theme_mode == ft.ThemeMode.DARK
        page = self._page
        
        def c(key: str):
            return get_theme_color(key, page=page)
        
        for card_control in self.comments_list.controls:
            if not isinstance(card_control, ft.Container):
                continue
            
            # Prüfe ob es ein Empty-State oder Error-State ist
            if hasattr(card_control, "content") and isinstance(card_control.content, ft.Column):
                # Empty-State: Column mit Icon, Text, Text
                col = card_control.content
                if len(col.controls) >= 2:
                    for control in col.controls:
                        if isinstance(control, ft.Icon):
                            control.color = c("text_secondary")
                        elif isinstance(control, ft.Text):
                            if "keine Kommentare" in control.value or "Erste" in control.value:
                                control.color = c("text_primary") if "keine Kommentare" in control.value else c("text_secondary")
                            elif "Fehler" in control.value:
                                control.color = ft.Colors.RED_400 if not is_dark else ft.Colors.RED_300
                continue
            
            # Kommentar-Karte Container: bgcolor = card
            card_control.bgcolor = c("card")
            
            # content ist ein Row mit [CircleAvatar, Column]
            if not hasattr(card_control, "content") or not isinstance(card_control.content, ft.Row):
                continue
            
            row = card_control.content
            if len(row.controls) < 2 or not isinstance(row.controls[1], ft.Column):
                continue
            
            # Column mit [Row(Name+Zeit), Text(Kommentar), Row(Aktionen)]
            col = row.controls[1]
            
            # Name + Zeit Row (Index 0)
            if len(col.controls) > 0 and isinstance(col.controls[0], ft.Row):
                name_time_row = col.controls[0]
                if len(name_time_row.controls) > 0 and isinstance(name_time_row.controls[0], ft.Text):
                    name_time_row.controls[0].color = c("text_primary")
                if len(name_time_row.controls) > 1 and isinstance(name_time_row.controls[1], ft.Text):
                    name_time_row.controls[1].color = c("text_secondary")
            
            # Kommentar-Text (Index 1)
            if len(col.controls) > 1 and isinstance(col.controls[1], ft.Text):
                col.controls[1].color = c("text_primary")
            
            # Aktionen Row (Index 2) - Delete-Button Icon-Farbe
            if len(col.controls) > 2 and isinstance(col.controls[2], ft.Row):
                actions_row = col.controls[2]
                for action_control in actions_row.controls:
                    if isinstance(action_control, ft.IconButton) and action_control.icon == ft.Icons.DELETE_OUTLINE:
                        action_control.icon_color = ft.Colors.RED_400 if not is_dark else ft.Colors.RED_300
    
    def load_comments(self):
        """Lädt alle nicht gelöschten Kommentare für diesen Post.
        
        Zeigt einen Loading-Indikator während des Ladens und rendert die
        Kommentare in der Kommentar-Liste.
        """
        self._apply_theme()
        handle_load_comments(
            comment_service=self.comment_service,
            post_id=self.post_id,
            comments_list=self.comments_list,
            loading_indicator=self.loading,
            page=self._page,
            create_empty_state=self._create_empty_state,
            create_comment_card=self.create_comment_card,
            create_error_state=self._create_error_state,
        )
    
    def _create_empty_state(self) -> ft.Control:
        """Erstellt den Empty-State-UI für keine Kommentare."""
        is_dark = self._page.theme_mode == ft.ThemeMode.DARK
        return ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.COMMENT_OUTLINED,
                    size=48,
                    color=get_theme_color("text_secondary", is_dark)
                ),
                ft.Text(
                    "Noch keine Kommentare",
                    size=16,
                    color=get_theme_color("text_primary", is_dark)
                ),
                ft.Text(
                    "Sei der Erste, der kommentiert!",
                    size=12,
                    color=get_theme_color("text_secondary", is_dark)
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5),
            padding=30,
            alignment=ft.alignment.center
        )
    
    def _create_error_state(self, error_message: str) -> ft.Control:
        """Erstellt den Error-State-UI für Fehler beim Laden."""
        is_dark = self._page.theme_mode == ft.ThemeMode.DARK
        error_color = ft.Colors.RED_400 if not is_dark else ft.Colors.RED_300
        return ft.Container(
            content=ft.Text(
                f"Fehler beim Laden: {error_message}",
                color=error_color,
                size=14
            ),
            padding=20
        )
    
    def create_comment_card(self, comment, is_reply=False):
        """Erstellt eine Kommentar-Karte.
        
        Args:
            comment: Dictionary mit Kommentar-Daten
            is_reply: Ob es sich um eine Antwort handelt (aktuell nicht verwendet)
        
        Returns:
            Container mit Kommentar-Karte
        """
        is_dark = self._page.theme_mode == ft.ThemeMode.DARK
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        is_author = (str(current_user_id) == str(comment.get('user_id')))
        
        # User-Daten extrahieren (Schema: user-Tabelle hat display_name, nicht username)
        user_data = comment.get('user', {})
        username = user_data.get('display_name', 'Unbekannt') if isinstance(user_data, dict) else 'Unbekannt'
        profile_image = user_data.get('profile_image') if isinstance(user_data, dict) else None
        
        # Antwort-Button
        reply_button = ft.IconButton(
            icon=ft.Icons.REPLY,
            icon_size=18,
            icon_color=PRIMARY_COLOR,
            tooltip="Antworten",
            on_click=lambda e, c=comment: self.start_reply(c)
        )
        
        card_content = ft.Row([
            # Profilbild
            ft.CircleAvatar(
                foreground_image_src=profile_image if profile_image else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE) if not profile_image else None,
                bgcolor=PRIMARY_COLOR,
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
                        color=get_theme_color("text_primary", is_dark)
                    ),
                    ft.Text(
                        format_time(comment.get('created_at')),
                        size=12 if not is_reply else 11,
                        color=get_theme_color("text_secondary", is_dark)
                    )
                ], spacing=10),
                
                # Kommentar-Text
                ft.Text(
                    comment.get('content', ''),
                    size=14 if not is_reply else 13,
                    selectable=True,
                    color=get_theme_color("text_primary", is_dark)
                ),
                
                # Aktionen (Antworten, Löschen)
                ft.Row([
                    reply_button,
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=18,
                        icon_color=ft.Colors.RED_400 if not is_dark else ft.Colors.RED_300,
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
            bgcolor=get_theme_color("card", is_dark),
            border_radius=10,
            border=ft.border.only(left=ft.BorderSide(3, PRIMARY_COLOR)) if is_reply else None,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
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
        """Speichert einen neuen Kommentar.
        
        Args:
            e: ControlEvent vom Button-Klick
        """
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        content = self.comment_input.value or ""
        
        def on_success_callback():
            """Callback nach erfolgreichem Speichern."""
            self.load_comments()
            # Antwort-Modus beenden (Handler setzt nur Banner, wir müssen auch replying_to zurücksetzen)
            if self.replying_to:
                self.replying_to = None
        
        handle_post_comment(
            comment_service=self.comment_service,
            post_id=self.post_id,
            user_id=current_user_id,
            content=content,
            comment_input=self.comment_input,
            send_button=self.send_button,
            reply_banner=self.reply_banner,
            replying_to=self.replying_to,
            page=self._page,
            on_success=on_success_callback,
            show_snackbar=self.show_snackbar,
        )
    
    def delete_comment(self, comment_id):
        """Soft-Delete: Setzt is_deleted auf True.
        
        Args:
            comment_id: ID des zu löschenden Kommentars
        """
        handle_delete_comment(
            comment_service=self.comment_service,
            comment_id=comment_id,
            page=self._page,
            on_success=self.load_comments,
            show_snackbar=self.show_snackbar,
        )
    
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