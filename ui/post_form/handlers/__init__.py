"""
Post Form Handlers - UI-Handler für das Meldungsformular.

Enthält Logik für:
- AI Recognition: KI-Rassenerkennung
- Photo Upload: Foto-Upload und -Verwaltung
- Post Upload: Meldung-Erstellung und Speicherung
- Form Validation: Formularvalidierung
- References: Referenzdaten laden und verwalten
"""

from .ai_recognition_handler import (
    handle_start_ai_recognition,
    show_consent_dialog,
    perform_ai_recognition,
    show_ai_result,
    show_ai_suggestion_dialog,
    handle_view_start_ai_recognition,
    handle_view_show_consent_dialog,
    handle_view_perform_ai_recognition,
    handle_view_show_ai_result,
    handle_view_accept_ai_result,
    handle_view_reject_ai_result,
    handle_view_show_ai_suggestion_wrapper,
    handle_ai_recognition_flow,
)
from .photo_upload_handler import (
    handle_pick_photo,
    handle_remove_photo,
    handle_view_pick_photo,
    handle_view_remove_photo,
)
from .post_upload_handler import (
    handle_save_post,
    reset_form_fields,
    handle_view_save_post,
)
from .form_validation_handler import validate_form_fields
from .references_handler import (
    load_and_populate_references,
    update_breeds_dropdown,
    handle_view_load_references,
    handle_view_update_breeds,
)

__all__ = [
    # AI Recognition
    "handle_start_ai_recognition",
    "show_consent_dialog",
    "perform_ai_recognition",
    "show_ai_result",
    "show_ai_suggestion_dialog",
    "handle_view_start_ai_recognition",
    "handle_view_show_consent_dialog",
    "handle_view_perform_ai_recognition",
    "handle_view_show_ai_result",
    "handle_view_accept_ai_result",
    "handle_view_reject_ai_result",
    "handle_view_show_ai_suggestion_wrapper",
    "handle_ai_recognition_flow",
    # Photo Upload
    "handle_pick_photo",
    "handle_remove_photo",
    "handle_view_pick_photo",
    "handle_view_remove_photo",
    # Post Upload
    "handle_save_post",
    "reset_form_fields",
    "handle_view_save_post",
    # Form Validation
    "validate_form_fields",
    # References
    "load_and_populate_references",
    "update_breeds_dropdown",
    "handle_view_load_references",
    "handle_view_update_breeds",
]
