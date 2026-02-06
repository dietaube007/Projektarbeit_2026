"""
Kommentar-Komponenten für die Discover-View.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dialogs import create_reaction_login_dialog
from services.posts import CommentService
from ui.constants import PRIMARY_COLOR
from ui.helpers import format_time
from ui.theme import get_theme_color
from utils.constants import MAX_COMMENT_LENGTH
from utils.logging_config import get_logger

from ..handlers.comment_handler import (
    handle_delete_comment,
    handle_load_comments,
    handle_post_comment,
)

logger = get_logger(__name__)


class CommentSection(ft.Container):
    """
    Kommentar-Sektion für PetBuddy Posts mit Antwort-Funktion
    Funktioniert mit Supabase und der bestehenden comment-Tabelle
    """
    
    def __init__(
        self,
        page: ft.Page,
        post_id: str,
        supabase,
        profile_service=None,
        on_login_required: Optional[Callable[[], None]] = None,
    ):
        """Initialisiert die CommentSection.
        
        Args:
            page: Flet Page-Instanz
            post_id: UUID des Posts für den Kommentare angezeigt werden
            supabase: Supabase-Client für Datenbankzugriffe
            profile_service: Optional ProfileService für User-ID-Abfragen
            on_login_required: Optional Callback wenn Gast kommentieren möchte (Login-Dialog)
        """
        self._page = page  # Verwende _page statt page um Konflikt zu vermeiden
        self.post_id = post_id  # UUID des Posts
        self.profile_service = profile_service
        self.on_login_required = on_login_required
        self.comment_service = CommentService(supabase, profile_service=profile_service)
        self.replying_to = None
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self._current_comments = []
        self._delete_confirming_id = None
        self.is_logged_in = bool(profile_service and profile_service.get_user_id())
        self.reaction_emojis = ["👍", "❤️", "😂", "😮", "😢"]

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
            bgcolor=None,  # Transparent
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
            bgcolor=None,  # Transparent
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
            bgcolor=None,  # Transparent 
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
                    bgcolor=None  # Transparent
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
                    bgcolor=None  # Transparent
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
        
        self.bgcolor = None
        
        # Column mit allen Controls
        col = self.content
        
        # Divider (Index 0)
        col.controls[0].color = get_theme_color("text_secondary", is_dark)
        
        # Header Container (Index 1) -> Row -> Text (Index 1)
        col.controls[1].content.controls[1].color = get_theme_color("text_primary", is_dark)
        
        # Kommentare Container (Index 2) - transparent
        col.controls[2].bgcolor = None
        
        # Antwort-Banner Container (Index 3) -> reply_banner - transparent
        self.reply_banner.bgcolor = None
        # Reply-Banner Row: IconButton Close (Index 4)
        self.reply_banner.content.controls[4].icon_color = get_theme_color("text_secondary", is_dark)
        
        # Eingabe-Bereich Container (Index 4) - transparent
        col.controls[4].bgcolor = None
        col.controls[4].border = ft.border.only(top=ft.BorderSide(1, get_theme_color("text_secondary", is_dark)))
        
        # Kommentar-TextField - transparent
        self.comment_input.border_color = get_theme_color("text_secondary", is_dark)
        self.comment_input.hint_style = ft.TextStyle(color=get_theme_color("text_secondary", is_dark))
        self.comment_input.color = get_theme_color("text_primary", is_dark)
        self.comment_input.bgcolor = None
        
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
            
            # Kommentar-Karte Container: heller als Umgebung
            if is_dark:
                card_control.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
            else:
                card_control.bgcolor = ft.Colors.with_opacity(0.35, ft.Colors.WHITE)
            
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
    
    def load_comments(self) -> None:
        """Lädt alle nicht gelöschten Kommentare für diesen Post.
        
        Zeigt einen Loading-Indikator während des Ladens und rendert die
        Kommentare in der Kommentar-Liste.
        """
        self._delete_confirming_id = None
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
            on_comments_loaded=lambda cs: setattr(self, "_current_comments", cs or []),
        )

    def _refresh_comments_ui(self) -> None:
        """Baut die Kommentar-Liste aus _current_comments neu (ohne erneutes Laden)."""
        self.comments_list.controls.clear()
        if not self._current_comments:
            self.comments_list.controls.append(self._create_empty_state())
        else:
            def render(c, is_reply=False):
                self.comments_list.controls.append(self.create_comment_card(c, is_reply=is_reply))
                for r in c.get("replies", []):
                    render(r, is_reply=True)
            for c in self._current_comments:
                render(c, is_reply=False)
        self._page.update()
    
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
    
    def _build_comment_actions_row(
        self, comment, is_reply: bool, is_author: bool, is_dark: bool, reply_button: ft.IconButton
    ) -> ft.Row:
        """Baut die Aktionen-Zeile: Antworten + Löschen-Icon oder Inline-Bestätigung."""
        cid = comment.get("id")
        is_confirming = is_author and (self._delete_confirming_id == cid)
        if is_confirming:
            return ft.Row(
                [
                    reply_button,
                    ft.Text(
                        "Wirklich löschen?",
                        size=12,
                        color=get_theme_color("text_secondary", is_dark),
                    ),
                    ft.TextButton(
                        "Abbrechen",
                        on_click=lambda e: self._cancel_delete_confirm(),
                    ),
                    ft.FilledButton(
                        "Löschen",
                        on_click=lambda e, cid=cid: self._do_delete_comment(cid),
                    ),
                ],
                spacing=8,
            )
        if is_author:
            return ft.Row(
                [
                    reply_button,
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=16,
                        icon_color=ft.Colors.RED_400 if not is_dark else ft.Colors.RED_300,
                        tooltip="Löschen",
                        on_click=lambda e, cid=cid: self._request_delete_comment(cid),
                    ),
                ],
                spacing=0,
            )
        return ft.Row([reply_button], spacing=0)

    def _build_reactions_row(self, comment: dict) -> ft.Row:
        counts = comment.get("reactions", {}) or {}
        user_reactions = set(comment.get("user_reactions", []) or [])

        def reaction_chip(emoji: str, count: int) -> ft.Control:
            is_active = emoji in user_reactions
            label = f"{emoji} {count}"
            return ft.OutlinedButton(
                label,
                on_click=lambda e, em=emoji, c=comment: self._toggle_reaction(c, em),
                height=28,
                style=ft.ButtonStyle(
                    bgcolor=(ft.Colors.BLUE_50 if (is_active and not self.is_dark) else (ft.Colors.BLUE_GREY_800 if (is_active and self.is_dark) else None)),
                    color=(ft.Colors.BLUE_700 if (is_active and not self.is_dark) else None),
                ),
            )

        chips = [reaction_chip(e, c) for e, c in counts.items() if c]

        emoji_menu = ft.PopupMenuButton(
            icon=ft.Icons.ADD_REACTION,
            tooltip="Reagieren",
            items=[
                ft.PopupMenuItem(
                    text=e,
                    on_click=lambda _, em=e, c=comment: self._toggle_reaction(c, em),
                )
                for e in self.reaction_emojis
            ],
        )

        return ft.Row(chips + [emoji_menu], spacing=6, wrap=True)

    def _toggle_reaction(self, comment: dict, emoji: str) -> None:
        if not self.is_logged_in:
            self._show_reaction_login_dialog()
            return
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        if not current_user_id:
            return
        self.comment_service.toggle_reaction(comment.get("id"), current_user_id, emoji)
        self.load_comments()

    def _show_reaction_login_dialog(self) -> None:
        """Zeigt einen Login-Dialog wenn ein Gast auf eine Reaktion klickt."""
        def on_login_click(e: ft.ControlEvent) -> None:
            self._page.close(dialog)
            self._page.route = "/login"
            self._page.update()

        def on_cancel_click(e: ft.ControlEvent) -> None:
            self._page.close(dialog)

        dialog = create_reaction_login_dialog(
            self._page, on_login_click, on_cancel_click
        )
        self._page.open(dialog)

    def create_comment_card(self, comment: dict, is_reply: bool = False) -> ft.Container:
        """Erstellt eine Kommentar-Karte.
        
        Args:
            comment: Dictionary mit Kommentar-Daten
            is_reply: Ob es sich um eine Antwort handelt (aktuell nicht verwendet)
        
        Returns:
            Container mit Kommentar-Karte
        """
        is_dark = self._page.theme_mode == ft.ThemeMode.DARK
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        comment_user_id = comment.get("user_id")
        is_author = bool(
            current_user_id and comment_user_id
            and str(current_user_id).strip().lower() == str(comment_user_id).strip().lower()
        )
        
        # User-Daten extrahieren (Schema: user-Tabelle hat display_name, nicht username)
        user_data = comment.get('user', {})
        username = user_data.get('display_name', 'Unbekannt') if isinstance(user_data, dict) else 'Unbekannt'
        profile_image = user_data.get('profile_image') if isinstance(user_data, dict) else None
        
        # Antwort-Button 
        reply_button = ft.IconButton(
            icon=ft.Icons.REPLY,
            icon_size=16,
            icon_color=PRIMARY_COLOR,
            tooltip="Antworten",
            on_click=lambda e, c=comment: self.start_reply(c),
        )
        
        card_content = ft.Row([
            # Profilbild
            ft.CircleAvatar(
                foreground_image_src=profile_image if profile_image else None,
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=14) if not profile_image else None,
                bgcolor=PRIMARY_COLOR,
                radius=16 if not is_reply else 14
            ),
            
            # Kommentar-Inhalt
            ft.Column([
                # Kopfzeile: Name + Zeit + Reaktionen
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    username,
                                    weight=ft.FontWeight.BOLD,
                                    size=13 if not is_reply else 12,
                                    color=get_theme_color("text_primary", is_dark),
                                ),
                                ft.Text(
                                    format_time(comment.get('created_at')),
                                    size=11 if not is_reply else 10,
                                    color=get_theme_color("text_secondary", is_dark),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(expand=True),
                        self._build_reactions_row(comment),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                
                # Kommentar-Text
                ft.Text(
                    comment.get('content', ''),
                    size=13 if not is_reply else 12,
                    selectable=True,
                    color=get_theme_color("text_primary", is_dark)
                ),

                # Aktionen (Antworten, Löschen oder Inline-Bestätigung)
                self._build_comment_actions_row(
                    comment=comment,
                    is_reply=is_reply,
                    is_author=is_author,
                    is_dark=is_dark,
                    reply_button=reply_button,
                )
                
            ], spacing=2, expand=True),
            
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START)
        
        # Container mit Einrückung für Antworten
        # Hintergrundfarbe: heller als Umgebung (beide Modi)
        if is_dark:
            card_bg = ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
        else:
            card_bg = ft.Colors.with_opacity(0.35, ft.Colors.WHITE)
        
        return ft.Container(
            content=card_content,
            padding=8,
            margin=ft.margin.only(left=40 if is_reply else 0),
            bgcolor=card_bg,
            border_radius=8,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        )
    
    def start_reply(self, comment: dict) -> None:
        """Startet den Antwort-Modus für einen Kommentar."""
        if not self.is_logged_in:
            if self.on_login_required:
                self.on_login_required()
            return
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
    
    def cancel_reply(self, e: Optional[ft.ControlEvent] = None) -> None:
        """Bricht den Antwort-Modus ab.
        
        Args:
            e: Optional ControlEvent vom Button-Klick
        """
        self.replying_to = None
        self.reply_banner.visible = False
        self.comment_input.hint_text = "Schreibe einen Kommentar..."
        self._page.update()
    
    def post_comment(self, e: ft.ControlEvent) -> None:
        """Speichert einen neuen Kommentar (oder zeigt Login-Dialog im Gastmodus).
        
        Args:
            e: ControlEvent vom Button-Klick
        """
        current_user_id = self.profile_service.get_user_id() if self.profile_service else None
        if not current_user_id and self.on_login_required:
            self.on_login_required()
            return
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
    
    def _request_delete_comment(self, comment_id) -> None:
        """Zeigt Inline-Bestätigung (Detail-Dialog bleibt offen)."""
        self._delete_confirming_id = comment_id
        self._refresh_comments_ui()

    def _cancel_delete_confirm(self) -> None:
        """Bricht die Inline-Löschbestätigung ab."""
        self._delete_confirming_id = None
        self._refresh_comments_ui()

    def _do_delete_comment(self, comment_id) -> None:
        """Führt den Soft-Delete aus (nach Bestätigung)."""
        handle_delete_comment(
            comment_service=self.comment_service,
            comment_id=comment_id,
            page=self._page,
            on_success=self.load_comments,
            show_snackbar=self.show_snackbar,
        )
    
    def show_snackbar(self, message: str, bgcolor: str) -> None:
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
