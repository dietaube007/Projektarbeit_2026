# API-Referenz

Dokumentation der Service-Klassen und ihrer Methoden.

## PostService

Service für CRUD-Operationen auf Meldungen.

```python
from services.posts import PostService

service = PostService(supabase_client)
```

### create()

Erstellt eine neue Meldung.

```python
def create(self, payload: Dict[str, Any]) -> Dict[str, Any]
```

**Parameter:**

| Name | Typ | Beschreibung |
|------|-----|--------------|
| payload | Dict | Meldungsdaten |

**Payload-Felder:**

```python
{
    "user_id": str,           # UUID des Benutzers
    "post_status_id": int,    # 1=Vermisst, 2=Fundtier
    "headline": str,          # Titel
    "description": str,       # Beschreibung
    "species_id": int,        # Tierart
    "breed_id": int | None,   # Rasse (optional)
    "sex_id": int | None,     # Geschlecht (optional)
    "event_date": str,        # ISO-Format (YYYY-MM-DD)
    "location_text": str,     # Standort
}
```

**Rückgabe:** Dict mit erstellter Meldung inkl. `id`.

**Beispiel:**

```python
post = service.create({
    "user_id": "abc-123",
    "post_status_id": 1,
    "headline": "Bello vermisst",
    "description": "Brauner Labrador...",
    "species_id": 1,
    "event_date": "2025-11-25",
    "location_text": "Berlin Mitte",
})
print(post["id"])  # UUID
```

---

### update()

Aktualisiert eine bestehende Meldung.

```python
def update(self, post_id: str, payload: Dict[str, Any]) -> Dict[str, Any]
```

---

### delete()

Löscht eine Meldung inkl. Bilder und Verknüpfungen.

```python
def delete(self, post_id: str) -> bool
```

**Rückgabe:** `True` bei Erfolg, `False` bei Fehler.

---

### get_by_id()

Holt eine Meldung anhand ihrer ID.

```python
def get_by_id(self, post_id: str) -> Dict[str, Any] | None
```

---

### get_all()

Holt alle Meldungen mit Relationen.

```python
def get_all(self, limit: int = 200) -> List[Dict[str, Any]]
```

**Rückgabe:** Liste von Meldungen mit verschachtelten Objekten:

```python
{
    "id": "...",
    "headline": "...",
    "post_status": {"id": 1, "name": "Vermisst"},
    "species": {"id": 1, "name": "Hund"},
    "breed": {"id": 5, "name": "Labrador"},
    "post_image": [{"url": "https://..."}],
    "post_color": [{"color": {"id": 3, "name": "Braun"}}],
    ...
}
```

---

### add_color()

Verknüpft eine Farbe mit einer Meldung.

```python
def add_color(self, post_id: str, color_id: int) -> None
```

---

### add_photo()

Speichert eine Foto-URL für eine Meldung.

```python
def add_photo(self, post_id: str, photo_url: str) -> None
```

---

## ReferenceService

Service für Stammdaten (Dropdowns, Filter).

```python
from services.references import ReferenceService

service = ReferenceService(supabase_client)
```

### get_post_statuses()

```python
def get_post_statuses(self, use_cache: bool = True) -> List[Dict[str, Any]]
```

**Rückgabe:**

```python
[
    {"id": 1, "name": "Vermisst"},
    {"id": 2, "name": "Fundtier"},
    {"id": 3, "name": "Wiedervereint"},
]
```

---

### get_species()

```python
def get_species(self, use_cache: bool = True) -> List[Dict[str, Any]]
```

---

### get_breeds_by_species()

Gruppiert Rassen nach Tierart-ID.

```python
def get_breeds_by_species(self, use_cache: bool = True) -> Dict[int, List[Dict[str, Any]]]
```

**Rückgabe:**

```python
{
    1: [  # Hund
        {"id": 1, "name": "Labrador", "species_id": 1},
        {"id": 2, "name": "Schäferhund", "species_id": 1},
    ],
    2: [  # Katze
        {"id": 10, "name": "Perser", "species_id": 2},
    ],
}
```

---

### get_colors()

```python
def get_colors(self, use_cache: bool = True) -> List[Dict[str, Any]]
```

---

### get_sex()

```python
def get_sex(self, use_cache: bool = True) -> List[Dict[str, Any]]
```

---

### clear_cache()

Löscht alle gecachten Referenzdaten.

```python
def clear_cache(self) -> None
```

---

## FavoritesService

Service für Favoriten-Verwaltung.

```python
from services.posts import FavoritesService

service = FavoritesService(supabase_client)
```

### get_favorites()

Lädt alle favorisierten Meldungen des aktuellen Benutzers.

```python
def get_favorites(self) -> List[Dict[str, Any]]
```

**Rückgabe:** Liste von Post-Dictionaries mit allen Relationen.

---

### add_favorite()

Fügt einen Post zu den Favoriten hinzu.

```python
def add_favorite(self, post_id: str) -> bool
```

**Rückgabe:** `True` bei Erfolg, `False` bei Fehler.

---

### remove_favorite()

Entfernt einen Post aus den Favoriten.

```python
def remove_favorite(self, post_id: str) -> bool
```

---

### is_favorite()

Prüft ob ein Post in den Favoriten ist.

```python
def is_favorite(self, post_id: str) -> bool
```

---

### get_favorite_ids()

Holt alle Favoriten-IDs eines Benutzers (optimiert für Batch-Abfragen).

```python
def get_favorite_ids(self, user_id: str) -> Set[str]
```

---

## SavedSearchService

Service für gespeicherte Suchaufträge.

```python
from services.posts import SavedSearchService

service = SavedSearchService(supabase_client)
```

### get_saved_searches()

Lädt alle gespeicherten Suchaufträge des aktuellen Benutzers.

```python
def get_saved_searches(self) -> List[Dict[str, Any]]
```

**Rückgabe:**

```python
[
    {
        "id": 1,
        "name": "Vermisste Katzen Berlin",
        "filters": {
            "status_id": 1,
            "species_id": 2,
            "colors": [1, 5]
        },
        "created_at": "2025-01-20T..."
    }
]
```

---

### save_search()

Speichert einen neuen Suchauftrag.

```python
def save_search(
    self,
    name: str,
    search_query: Optional[str] = None,
    status_id: Optional[int] = None,
    species_id: Optional[int] = None,
    breed_id: Optional[int] = None,
    sex_id: Optional[int] = None,
    colors: Optional[List[int]] = None,
) -> Tuple[bool, str]
```

**Rückgabe:** `(True, "")` bei Erfolg, `(False, "Fehlermeldung")` bei Fehler.

**Limits:**
- Max. 20 Suchaufträge pro Benutzer
- Max. 100 Zeichen für Namen

---

### delete_search()

Löscht einen gespeicherten Suchauftrag.

```python
def delete_search(self, search_id: int) -> Tuple[bool, str]
```

---

## CommentService

Service für Kommentar-Verwaltung.

```python
from services.posts import CommentService

service = CommentService(supabase_client)
```

### get_comments()

Lädt alle Kommentare für einen Post (hierarchisch strukturiert).

```python
def get_comments(self, post_id: str) -> List[Dict[str, Any]]
```

**Rückgabe:**

```python
[
    {
        "id": 1,
        "content": "Kommentar-Text",
        "user": {
            "display_name": "Max",
            "profile_image": "https://..."
        },
        "created_at": "2025-01-20T...",
        "replies": [
            {
                "id": 2,
                "content": "Antwort",
                "parent_comment_id": 1,
                ...
            }
        ]
    }
]
```

---

### create_comment()

Erstellt einen neuen Kommentar.

```python
def create_comment(
    self,
    post_id: str,
    user_id: str,
    content: str,
    parent_comment_id: Optional[int] = None,
) -> bool
```

**Parameter:**

| Name | Typ | Beschreibung |
|------|-----|--------------|
| post_id | str | UUID des Posts |
| user_id | str | UUID des Benutzers |
| content | str | Kommentar-Text (max. 1000 Zeichen) |
| parent_comment_id | int | Optional: ID des Eltern-Kommentars für Antworten |

---

### delete_comment()

Soft-Delete: Markiert einen Kommentar als gelöscht.

```python
def delete_comment(self, comment_id: int) -> bool
```

---

## AuthService

Service für Authentifizierung.

```python
from services.account import AuthService

service = AuthService(supabase_client)
```

### login()

Meldet einen Benutzer an.

```python
def login(self, email: str, password: str) -> AuthResult
```

**Rückgabe:** `AuthResult(success=True/False, message="...")`

---

### register()

Registriert einen neuen Benutzer.

```python
def register(
    self,
    email: str,
    password: str,
    display_name: str
) -> AuthResult
```

---

### logout()

Meldet den aktuellen Benutzer ab.

```python
def logout(self) -> AuthResult
```

---

### reset_password()

Sendet eine Passwort-Reset-E-Mail.

```python
def reset_password(self, email: str) -> AuthResult
```

---

## ProfileService

Service für Benutzerprofil-Verwaltung.

```python
from services.account import ProfileService

service = ProfileService(supabase_client)
```

### get_current_user()

Holt den aktuell eingeloggten Benutzer.

```python
def get_current_user(self) -> User | None
```

---

### get_display_name()

Holt den Anzeigenamen des aktuellen Benutzers.

```python
def get_display_name(self) -> str
```

---

### update_display_name()

Aktualisiert den Anzeigenamen.

```python
def update_display_name(self, name: str) -> bool
```

---

### get_profile_image_url()

Holt die Profilbild-URL.

```python
def get_profile_image_url(self) -> str | None
```

---

## ThemeManager

Verwaltet das App-Theme.

```python
from ui.theme import ThemeManager

manager = ThemeManager(page)
manager.apply_theme("light")  # oder "dark"
```

### Methoden

| Methode | Beschreibung |
|---------|--------------|
| `apply_theme(mode)` | Wendet Theme an ("light" oder "dark") |
| `create_toggle_button()` | Erstellt IconButton zum Wechseln |

---

## UI-Komponenten

### chip()

Erstellt einen Badge-Chip.

```python
from ui.theme import chip

badge = chip("Vermisst", ft.Colors.RED_200)
```

### soft_card()

Erstellt eine Card mit sanfter Elevation.

```python
from ui.theme import soft_card

card = soft_card(
    content=ft.Text("Inhalt"),
    pad=16,
    elev=2
)
```
