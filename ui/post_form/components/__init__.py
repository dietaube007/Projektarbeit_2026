"""
Post Form Components - UI-Komponenten für das Meldungsformular.
"""

from .form_components import (
    create_meldungsart_button,
    create_name_field,
    create_title_label,
    create_species_dropdown,
    create_breed_dropdown,
    create_sex_dropdown,
    create_description_field,
    create_location_field,
    create_date_field,
    create_status_text,
    create_farben_panel,
    create_farben_header_and_panel,
    create_save_button,
    create_form_header,
    create_form_photo_section,
    create_form_basic_info_section,
    create_form_colors_section,
    create_form_details_section,
    create_form_action_section,
    create_form_layout,
)
from .photo_components import (
    create_photo_preview,
    create_photo_upload_area,
)
from .ai_components import (
    create_ai_recognition_button,
    create_ai_result_container,
    create_consent_dialog,
    create_ai_result_content,
    create_ai_suggestion_dialog,
)

__all__ = [
    # Form Fields
    "create_meldungsart_button",
    "create_name_field",
    "create_title_label",
    "create_species_dropdown",
    "create_breed_dropdown",
    "create_sex_dropdown",
    "create_description_field",
    "create_location_field",
    "create_date_field",
    "create_status_text",
    "create_farben_panel",
    "create_farben_header_and_panel",
    "create_save_button",
    # Form Layout Sections
    "create_form_header",
    "create_form_photo_section",
    "create_form_basic_info_section",
    "create_form_colors_section",
    "create_form_details_section",
    "create_form_action_section",
    "create_form_layout",
    # Photo Components
    "create_photo_preview",
    "create_photo_upload_area",
    # AI Components
    "create_ai_recognition_button",
    "create_ai_result_container",
    "create_consent_dialog",
    "create_ai_result_content",
    "create_ai_suggestion_dialog",
]
