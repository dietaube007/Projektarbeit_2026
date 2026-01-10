"""
Discover Components - UI-Komponenten für Discover-View.
"""

from .search_filter_components import (
    create_search_field,
    create_dropdown,
    create_farben_header,
    create_reset_button,
    create_view_toggle,
    create_sort_dropdown,
    populate_dropdown,
)
from .post_card_components import (
    build_small_card,
    build_big_card,
    show_detail_dialog,
)
from .comment_components import CommentSection

__all__ = [
    # Search & Filter
    "create_search_field",
    "create_dropdown",
    "create_farben_header",
    "create_reset_button",
    "create_view_toggle",
    "create_sort_dropdown",
    "populate_dropdown",
    # Post Cards
    "build_small_card",
    "build_big_card",
    "show_detail_dialog",
    # Comments
    "CommentSection",
]
