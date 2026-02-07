"""
Form Validation-Feature: Validierungslogik für das Meldungsformular.
"""

from __future__ import annotations

from typing import List, Tuple, Optional

from utils.validators import (
    validate_not_empty,
    validate_length,
    validate_list_not_empty,
    validate_date_not_future,
)
from ui.constants import DATE_FORMAT
from utils.constants import (
    MAX_HEADLINE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
)


def validate_form_fields(
    name_value: Optional[str],
    species_value: Optional[str],
    selected_farben: List[int],
    description_value: Optional[str],
    location_value: Optional[str],
    date_value: Optional[str],
    photo_url: Optional[str],
) -> Tuple[bool, List[str]]:
    """Validiert alle Formularfelder.
    
    Args:
        name_value: Wert des Name/Überschrift-Feldes
        species_value: Wert des Tierart-Dropdowns
        selected_farben: Liste der ausgewählten Farb-IDs
        description_value: Wert des Beschreibungsfeldes
        location_value: Wert des Orts-Feldes
        date_value: Wert des Datums-Feldes
        photo_url: URL des hochgeladenen Fotos
    
    Returns:
        Tuple mit (is_valid, errors_list)
    """
    errors = []
    
    # Name/Überschrift validieren
    name_valid, name_error = validate_not_empty(name_value, "Name/Überschrift")
    if not name_valid:
        errors.append(f"• {name_error}")
    else:
        name_length_valid, name_length_error = validate_length(
            name_value, max_length=MAX_HEADLINE_LENGTH, field_name="Name/Überschrift"
        )
        if not name_length_valid:
            errors.append(f"• {name_length_error}")
    
    # Tierart validieren
    if not species_value:
        errors.append("• Tierart ist erforderlich")
    
    # Farben validieren
    colors_valid, colors_error = validate_list_not_empty(
        selected_farben, "Farben", min_items=1
    )
    if not colors_valid:
        errors.append(f"• {colors_error}")
    
    # Beschreibung validieren
    desc_valid, desc_error = validate_not_empty(description_value, "Beschreibung")
    if not desc_valid:
        errors.append(f"• {desc_error}")
    else:
        desc_length_valid, desc_length_error = validate_length(
            description_value,
            min_length=MIN_DESCRIPTION_LENGTH,
            max_length=MAX_DESCRIPTION_LENGTH,
            field_name="Beschreibung"
        )
        if not desc_length_valid:
            errors.append(f"• {desc_length_error}")
    
    # Ort validieren
    location_valid, location_error = validate_not_empty(location_value, "Ort")
    if not location_valid:
        errors.append(f"• {location_error}")
    else:
        location_length_valid, location_length_error = validate_length(
            location_value, max_length=MAX_LOCATION_LENGTH, field_name="Ort"
        )
        if not location_length_valid:
            errors.append(f"• {location_length_error}")
    
    # Datum validieren (Format + nicht in Zukunft)
    date_valid, date_error = validate_date_not_future(date_value, DATE_FORMAT)
    if not date_valid:
        errors.append(f"• {date_error}")
    
    # Foto validieren
    if not photo_url:
        errors.append("• Foto ist erforderlich")
    
    return len(errors) == 0, errors


