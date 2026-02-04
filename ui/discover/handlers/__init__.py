"""
Discover Handlers - UI-Handler für Discover-View.
"""

from .comment_handler import (
    handle_load_comments,
    handle_post_comment,
    handle_delete_comment,
)
from .favorite_handler import (
    handle_toggle_favorite,
    handle_view_toggle_favorite,
)
from .filter_handler import (
    reset_filters,
    apply_saved_search_filters,
    collect_current_filters,
    handle_view_reset_filters,
    handle_view_apply_saved_search,
    handle_view_show_save_search_dialog,
    handle_view_filter_change,
    handle_view_get_filter_value,
    handle_view_toggle_farben_panel,
)
from .reference_handler import (
    load_and_populate_references,
    update_breeds_dropdown,
    handle_view_load_references,
    handle_view_tierart_change,
    handle_view_update_rassen_dropdown,
)
from .saved_search_handler import show_save_search_dialog
from .search_handler import (
    handle_render_items,
    handle_view_load_posts,
    handle_view_render_items,
    handle_view_show_detail_dialog,
    handle_view_view_change,
)

__all__ = [
    # Comment handlers
    "handle_load_comments",
    "handle_post_comment",
    "handle_delete_comment",
    # Favorite handlers
    "handle_toggle_favorite",
    "handle_view_toggle_favorite",
    # Filter handlers
    "reset_filters",
    "apply_saved_search_filters",
    "collect_current_filters",
    "handle_view_reset_filters",
    "handle_view_apply_saved_search",
    "handle_view_show_save_search_dialog",
    "handle_view_filter_change",
    "handle_view_get_filter_value",
    "handle_view_toggle_farben_panel",
    # Reference handlers
    "load_and_populate_references",
    "update_breeds_dropdown",
    "handle_view_load_references",
    "handle_view_tierart_change",
    "handle_view_update_rassen_dropdown",
    # Saved search handlers
    "show_save_search_dialog",
    # Search handlers
    "handle_render_items",
    "handle_view_load_posts",
    "handle_view_render_items",
    "handle_view_show_detail_dialog",
    "handle_view_view_change",
]
