"""
PetBuddy UI Module.

Dieses Modul enthält alle UI-Komponenten der PetBuddy-Anwendung.

Struktur:
├── auth.py          - Authentifizierung (Login/Registrierung)
├── theme.py         - Theme-Manager und UI-Hilfsfunktionen
├── post_form.py     - Formular für Tier-Meldungen
├── constants.py     - Zentrale Konstanten
├── helpers.py       - Hilfsfunktionen
├── components/      - Wiederverwendbare UI-Komponenten
├── discover/        - Startseite mit Meldungsübersicht
└── profile/         - Benutzer-Profil
"""

# Hauptkomponenten
from ui.auth import AuthView
from ui.theme import ThemeManager, soft_card, chip
from ui.post_form import PostForm
from ui.discover import DiscoverView
from ui.profile import ProfileView

# Konstanten
from ui.constants import (
    STATUS_COLORS,
    SPECIES_COLORS,
    MAX_POSTS_LIMIT,
    CARD_IMAGE_HEIGHT,
    LIST_IMAGE_HEIGHT,
    DIALOG_IMAGE_HEIGHT,
    DEFAULT_PLACEHOLDER,
)

# Komponenten
from ui.components import (
    show_login_required_dialog,
    show_confirm_dialog,
    show_success_dialog,
    show_error_dialog,
    show_validation_dialog,
    badge_for_typ,
    badge_for_species,
    image_placeholder,
    login_banner,
    empty_state,
    create_empty_state_card,
    create_no_results_card,
    loading_indicator,
    meta_row,
    filter_chip,
)

__all__ = [
    # Views
    "AuthView",
    "ThemeManager",
    "PostForm",
    "DiscoverView",
    "ProfileView",
    # Theme helpers
    "soft_card",
    "chip",
    # Konstanten
    "STATUS_COLORS",
    "SPECIES_COLORS",
    "MAX_POSTS_LIMIT",
    "CARD_IMAGE_HEIGHT",
    "LIST_IMAGE_HEIGHT",
    "DIALOG_IMAGE_HEIGHT",
    "DEFAULT_PLACEHOLDER",
    # Komponenten
    "show_login_required_dialog",
    "show_confirm_dialog",
    "show_success_dialog",
    "show_error_dialog",
    "show_validation_dialog",
    "badge_for_typ",
    "badge_for_species",
    "image_placeholder",
    "login_banner",
    "empty_state",
    "create_empty_state_card",
    "create_no_results_card",
    "loading_indicator",
    "meta_row",
    "filter_chip",
]
