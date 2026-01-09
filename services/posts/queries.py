"""Zentrale Query-Definitionen für Post-Services.

Enthält wiederverwendbare Select-Statements und Query-Bausteine
für konsistente Datenbankabfragen.
"""

# Vollständiges Post-Select mit allen Relationen
POST_SELECT_FULL = """
    id, headline, description, location_text, event_date, created_at, is_active, user_id,
    post_status(id, name),
    species(id, name),
    breed(id, name),
    sex(id, name),
    post_image(url),
    post_color(color(id, name))
"""

# Post-Select für Listen-Ansicht (ohne description)
POST_SELECT_LIST = """
    id,
    headline,
    location_text,
    event_date,
    created_at,
    is_active,
    post_status(id, name),
    species(id, name),
    breed(id, name),
    post_image(url),
    post_color(color(id, name))
"""

# Post-Select für Favoriten-Ansicht
POST_SELECT_FAVORITES = """
    id,
    headline,
    location_text,
    event_date,
    created_at,
    is_active,
    post_status(id, name),
    species(id, name),
    breed(id, name),
    post_image(url),
    post_color(color(id, name))
"""

# Post-Select für "Meine Meldungen"
POST_SELECT_MY_POSTS = """
    id,
    headline,
    description,
    location_text,
    event_date,
    created_at,
    is_active,
    post_status(id, name),
    species(id, name),
    breed(id, name),
    sex(id, name),
    post_image(url),
    post_color(color(id, name))
"""

# Minimales Post-Select (nur ID und Bilder)
POST_SELECT_MINIMAL = """
    id,
    post_image(url)
"""
