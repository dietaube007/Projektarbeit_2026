"""Service für Kommentar-Verwaltung."""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING

from supabase import Client

from utils.logging_config import get_logger
from utils.constants import MAX_COMMENT_LENGTH
from utils.validators import validate_length
from .queries import COMMENT_SELECT_FULL

if TYPE_CHECKING:
    from services.account.profile import ProfileService

logger = get_logger(__name__)


class CommentService:
    """Service-Klasse für das Verwalten von Kommentaren."""

    def __init__(
        self,
        sb: Client,
        profile_service: Optional["ProfileService"] = None,
    ) -> None:
        """Initialisiert den CommentService.
        
        Args:
            sb: Supabase Client-Instanz
            profile_service: Optional ProfileService 
        """
        self.sb = sb
        if profile_service is None:
            from services.account.profile import ProfileService
            self._profile_service = ProfileService(sb)
        else:
            self._profile_service = profile_service

    def get_comments(self, post_id: str) -> List[Dict[str, Any]]:
        """Lädt alle nicht gelöschten Kommentare für einen Post.
        
        Args:
            post_id: UUID des Posts
        
        Returns:
            Liste von Kommentar-Dictionaries mit User-Daten (display_name, profile_image).
            Kommentare sind hierarchisch strukturiert mit 'replies' Liste für Antworten.
            Leere Liste bei Fehler oder wenn keine Kommentare vorhanden.
        """
        try:
            # Kommentare laden 
            response = (
                self.sb.table("comment")
                .select(COMMENT_SELECT_FULL)
                .eq("post_id", post_id)
                .eq("is_deleted", False)
                .order("created_at", desc=True)
                .execute()
            )
            
            comments = response.data if response and hasattr(response, "data") else []
            
            # User-Daten über ProfileService anreichern (konsistent mit SearchService)
            if comments:
                user_ids = {c.get("user_id") for c in comments if c.get("user_id")}
                user_profiles = self._profile_service.get_user_profiles(user_ids)
                
                # User-Daten zu Kommentaren hinzufügen (konsistent mit comment_components Erwartung)
                for comment in comments:
                    user_id = comment.get("user_id")
                    profile = user_profiles.get(user_id, {})
                    comment["user"] = {
                        "display_name": profile.get("display_name", "Unbekannt"),
                        "profile_image": profile.get("profile_image"),
                    }
                    comment["replies"] = []  # Initialisiere replies-Liste

                # Emoji-Reaktionen laden
                current_user_id = self._profile_service.get_user_id()
                comment_ids = [c.get("id") for c in comments if c.get("id") is not None]
                reactions_map = self.get_comment_reactions(comment_ids, current_user_id)
                for comment in comments:
                    r = reactions_map.get(comment.get("id"), {"counts": {}, "user_emojis": set()})
                    comment["reactions"] = r.get("counts", {})
                    comment["user_reactions"] = list(r.get("user_emojis", set()))
            
            # Hierarchische Struktur aufbauen
            top_level = []
            replies_map = {}
            
            for comment in comments:
                parent_id = comment.get("parent_comment_id")
                if parent_id is None:
                    # Top-Level Kommentar
                    top_level.append(comment)
                else:
                    # Antwort - zu replies_map hinzufügen
                    parent_id_str = str(parent_id)
                    if parent_id_str not in replies_map:
                        replies_map[parent_id_str] = []
                    replies_map[parent_id_str].append(comment)
            
            # Antworten zu ihren Eltern zuordnen
            def attach_replies(comment_list):
                for comment in comment_list:
                    comment_id_str = str(comment.get("id"))
                    if comment_id_str in replies_map:
                        comment["replies"] = sorted(
                            replies_map[comment_id_str],
                            key=lambda x: x.get("created_at", "")
                        )
                        attach_replies(comment["replies"])  # Rekursiv für verschachtelte Antworten
            
            attach_replies(top_level)
            
            return top_level
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Kommentare für Post {post_id}: {e}", exc_info=True)
            return []

    def get_comment_reactions(
        self,
        comment_ids: List[int],
        user_id: Optional[str] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """Lädt Emoji-Reaktionen für mehrere Kommentare.

        Returns:
            Dict[comment_id] = {"counts": {emoji: count}, "user_emojis": set()}
        """
        if not comment_ids:
            return {}
        try:
            response = (
                self.sb.table("comment_reaction")
                .select("comment_id, emoji, user_id")
                .in_("comment_id", comment_ids)
                .execute()
            )
            rows = response.data if response and hasattr(response, "data") else []
            result: Dict[int, Dict[str, Any]] = {}
            for row in rows:
                cid = row.get("comment_id")
                if cid is None:
                    continue
                if cid not in result:
                    result[cid] = {"counts": {}, "user_emojis": set()}
                emoji = row.get("emoji")
                if emoji:
                    result[cid]["counts"][emoji] = result[cid]["counts"].get(emoji, 0) + 1
                    if user_id and row.get("user_id") == str(user_id):
                        result[cid]["user_emojis"].add(emoji)
            return result
        except Exception as e:
            logger.error(f"Fehler beim Laden der Reaktionen: {e}", exc_info=True)
            return {}

    def toggle_reaction(self, comment_id: Union[int, str], user_id: str, emoji: str) -> bool:
        """Toggle einer Emoji-Reaktion für einen Kommentar.

        Returns:
            True wenn hinzugefügt, False wenn entfernt oder Fehler.
        """
        try:
            comment_id_int = int(comment_id) if isinstance(comment_id, str) else comment_id
            existing = (
                self.sb.table("comment_reaction")
                .select("id")
                .eq("comment_id", comment_id_int)
                .eq("user_id", str(user_id))
                .eq("emoji", emoji)
                .execute()
            )
            if existing and getattr(existing, "data", None):
                reaction_id = existing.data[0].get("id")
                self.sb.table("comment_reaction").delete().eq("id", reaction_id).execute()
                return False

            self.sb.table("comment_reaction").insert({
                "comment_id": comment_id_int,
                "user_id": str(user_id),
                "emoji": emoji,
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Fehler beim Toggle der Reaktion: {e}", exc_info=True)
            return False

    def create_comment(
        self,
        post_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[Union[int, str]] = None,
    ) -> bool:
        """Erstellt einen neuen Kommentar.
        
        Args:
            post_id: UUID des Posts
            user_id: UUID des Benutzers
            content: Kommentar-Text (max. MAX_COMMENT_LENGTH Zeichen)
            parent_comment_id: Optional ID des übergeordneten Kommentars (für Antworten)
        
        Returns:
            True bei Erfolg, False bei Fehler oder ungültiger Eingabe
        """
        # Validierung: Leerer Kommentar
        if not content or not content.strip():
            logger.warning("Versuch, leeren Kommentar zu erstellen")
            return False
        
        # Validierung: Maximale Länge (1000 Zeichen)
        length_valid, length_error = validate_length(
            content.strip(),
            max_length=MAX_COMMENT_LENGTH
        )
        if not length_valid:
            logger.warning(f"Kommentar zu lang: {length_error}")
            return False
        
        try:
            # Kommentar-Daten vorbereiten
            # Schema: id ist serial (auto-increment integer)
            comment_data = {
                "post_id": post_id,
                "user_id": str(user_id),
                "content": content.strip(),
                "is_deleted": False,
            }
            if parent_comment_id is not None:
                comment_data["parent_comment_id"] = int(parent_comment_id) if isinstance(parent_comment_id, str) else parent_comment_id
            
            # Kommentar in Supabase speichern
            self.sb.table("comment").insert(comment_data).execute()
            
            logger.info(f"Kommentar erstellt für Post {post_id} von User {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Kommentars: {e}", exc_info=True)
            return False

    def delete_comment(self, comment_id: Union[int, str]) -> bool:
        """Soft-Delete: Setzt is_deleted auf True und updated_at.
        
        Args:
            comment_id: ID des Kommentars (serial integer)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Konvertiere comment_id zu int (falls als str übergeben)
            comment_id_int = int(comment_id) if isinstance(comment_id, str) else comment_id
            
            # Soft Delete in Supabase (updated_at wird automatisch von DB-Trigger gesetzt)
            self.sb.table("comment").update({
                "is_deleted": True,
                # updated_at sollte von DB-Trigger automatisch gesetzt werden
            }).eq("id", comment_id_int).execute()
            
            logger.info(f"Kommentar {comment_id_int} als gelöscht markiert")
            return True
            
        except (ValueError, TypeError) as e:
            logger.error(f"Ungültige comment_id: {comment_id} ({type(comment_id)}): {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Kommentars (ID: {comment_id}): {e}", exc_info=True)
            return False
