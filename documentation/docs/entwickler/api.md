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
