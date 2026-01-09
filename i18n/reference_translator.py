"""
Hilfsfunktionen für die Übersetzung von Referenzdaten.
"""

from i18n import get_translator


def translate_reference_name(name: str, category: str = None) -> str:
    """
    Übersetzt Referenzdaten-Namen basierend auf vordefinierten Mappings.
    
    Args:
        name: Der zu übersetzende Name
        category: Optionale Kategorie (status, species, sex, colors)
    
    Returns:
        Übersetzter Name oder Original, wenn keine Übersetzung gefunden wurde
    """
    if not name:
        return name
    
    t = get_translator()
    name_lower = name.lower()
    
    # Mapping von Datenbank-Namen zu i18n-Keys
    mappings = {
        # Status/Kategorien
        "vermisst": "status.lost",
        "gefunden": "status.found",
        "lost": "status.lost",
        "found": "status.found",
        
        # Tierarten
        "hund": "species.dog",
        "katze": "species.cat",
        "vogel": "species.bird",
        "sonstiges": "species.other",
        "dog": "species.dog",
        "cat": "species.cat",
        "bird": "species.bird",
        "other": "species.other",
        
        # Geschlecht
        "männlich": "sex.male",
        "weiblich": "sex.female",
        "unbekannt": "sex.unknown",
        "keine angabe": "sex.unknown",
        "male": "sex.male",
        "female": "sex.female",
        "unknown": "sex.unknown",
        
        # Farben
        "schwarz": "colors.black",
        "weiß": "colors.white",
        "weiss": "colors.white",
        "braun": "colors.brown",
        "grau": "colors.gray",
        "orange": "colors.orange",
        "gefleckt": "colors.spotted",
        "gestreift": "colors.striped",
        "black": "colors.black",
        "white": "colors.white",
        "brown": "colors.brown",
        "gray": "colors.gray",
        "grey": "colors.gray",
        "spotted": "colors.spotted",
        "striped": "colors.striped",
        "rot": "colors.orange",
        "red": "colors.orange",
        "gelb": "colors.orange",
        "yellow": "colors.orange",
        "beige": "colors.brown",
        "hellbraun": "colors.brown",
        "dunkelbraun": "colors.brown",
    }
    
    # Versuche direkte Übersetzung
    key = mappings.get(name_lower)
    if key:
        return t.t(key)
    
    # Fallback auf Originalnamen
    return name


def translate_reference_list(items: list, name_key: str = "name") -> list:
    """
    Übersetzt eine Liste von Referenzdaten-Objekten.
    
    Args:
        items: Liste von Dictionaries mit Referenzdaten
        name_key: Schlüssel für den Namen im Dictionary
    
    Returns:
        Liste mit übersetzten Namen
    """
    if not items:
        return items
    
    result = []
    for item in items:
        translated_item = item.copy()
        if name_key in translated_item:
            translated_item[name_key] = translate_reference_name(translated_item[name_key])
        result.append(translated_item)
    
    return result
