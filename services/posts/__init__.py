"""Post Services - Alles rund um Meldungen.

Enthält:
- post: Post CRUD (create, read, update, delete)
- post_relations: Post-Verknüpfungen (Farben, Fotos)
- post_image: Post Image Storage (upload, download, remove)
- search: Post-Suche & Filter
- favorites: Favoriten-Verwaltung
- saved_search: Gespeicherte Suchen
- comment: Kommentar-Verwaltung
- queries: Zentrale Query-Definitionen
- references: Post-Stammdaten (Tierarten, Rassen, Farben, etc.)
"""

from .post import PostService
from .post_relations import PostRelationsService
from .post_image import PostStorageService
from .search import SearchService
from .favorites import FavoritesService
from .saved_search import SavedSearchService
from .comment import CommentService
from .references import ReferenceService

__all__ = [
    "PostService",
    "PostRelationsService",
    "PostStorageService",
    "SearchService",
    "FavoritesService",
    "SavedSearchService",
    "CommentService",
    "ReferenceService",
]

