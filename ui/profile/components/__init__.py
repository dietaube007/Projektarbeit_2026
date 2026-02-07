"""
Profile Components - UI-Komponenten für ProfileView.
"""

from .edit_profile_components import (
    # Sections
    create_profile_image_section,
    create_display_name_section,
    create_password_section,
    create_delete_account_section,
    # Dialogs
    create_change_password_dialog,
    create_delete_account_dialog,
    create_delete_profile_image_dialog,
    # View
    create_edit_profile_view,
)
from .my_posts_components import (
    build_my_post_card,
    create_my_posts_view,
)
from .my_favorites_components import (
    build_favorite_card,
    create_favorites_view,
)
from .edit_post_components import EditPostDialog
from .my_saved_search_components import (
    build_search_card,
    build_saved_searches_list,
    create_delete_search_dialog,
)
from .settings_components import (
    create_settings_view,
)

__all__ = [
    # Edit Profile Components
    "create_profile_image_section",
    "create_display_name_section",
    "create_password_section",
    "create_delete_account_section",
    "create_change_password_dialog",
    "create_delete_account_dialog",
    "create_delete_profile_image_dialog",
    # My Posts Components
    "build_my_post_card",
    "create_my_posts_view",
    "EditPostDialog",
    # My Favorites Components
    "build_favorite_card",
    "create_favorites_view",
    # Edit Profile Components
    "create_edit_profile_view",
    # My Saved Search Components
    "build_search_card",
    "build_saved_searches_list",
    "create_delete_search_dialog",
    # Settings Components
    "create_settings_view",
]
