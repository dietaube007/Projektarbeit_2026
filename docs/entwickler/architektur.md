# Architektur

Überblick über die technische Architektur von PetBuddy.

## Technologie-Stack

| Schicht | Technologie |
|---------|-------------|
| Frontend | [Flet](https://flet.dev) (Python) |
| Backend | [Supabase](https://supabase.com) |
| Datenbank | PostgreSQL |
| Auth | Supabase Auth |
| Storage | Supabase Storage |

## Projektstruktur

```
Projektarbeit_2026/
├── main.py                 # Einstiegspunkt, PetBuddyApp-Klasse
├── pyproject.toml          # Projekt-Konfiguration
├── .env                    # Umgebungsvariablen (nicht in Git)
│
├── ui/                     # UI-Komponenten
│   ├── __init__.py
│   ├── auth.py             # AuthView - Login/Registrierung
│   ├── discover.py         # DiscoverView - Startseite
│   ├── post_form.py        # PostForm - Meldungsformular
│   ├── profile.py          # ProfileView - Profilbereich
│   └── theme.py            # ThemeManager, UI-Komponenten
│
├── services/               # Backend-Services
│   ├── __init__.py
│   ├── supabase_client.py  # Supabase-Client-Singleton
│   ├── posts.py            # PostService - CRUD für Meldungen
│   └── references.py       # ReferenceService - Stammdaten
│
├── docs/                   # MkDocs-Dokumentation
└── image_uploads/          # Temporäre Bild-Uploads
```

## Schichtenarchitektur

```
┌─────────────────────────────────────────┐
│              UI Layer (Flet)            │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐  │
│  │AuthView │ │Discover │ │ PostForm  │  │
│  └─────────┘ └─────────┘ └───────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            Service Layer                │
│  ┌─────────────┐ ┌──────────────────┐   │
│  │ PostService │ │ ReferenceService │   │
│  └─────────────┘ └──────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Supabase Client                 │
│  ┌──────┐ ┌─────────┐ ┌─────────────┐   │
│  │ Auth │ │Database │ │   Storage   │   │
│  └──────┘ └─────────┘ └─────────────┘   │
└─────────────────────────────────────────┘
```

## Hauptklassen

### PetBuddyApp (main.py)

Zentrale App-Klasse, verantwortlich für:

- Initialisierung von Page und Supabase-Client
- Navigation zwischen Tabs (Start, Melden, Profil)
- Login-Gating für geschützte Bereiche
- Theme-Management

```python
class PetBuddyApp:
    TAB_START = 0
    TAB_MELDEN = 1
    TAB_PROFIL = 2
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.is_logged_in = False
        # ...
```

### AuthView (ui/auth.py)

Authentifizierung mit:

- Login-Formular
- Registrierungs-Modal
- "Ohne Account fortsetzen"-Option
- Theme-Toggle

### DiscoverView (ui/discover.py)

Startseite mit:

- Suchleiste
- Filter (Kategorie, Tierart, Geschlecht, Farben)
- Meldungs-Karten

### PostForm (ui/post_form.py)

Formular für neue Meldungen:

- Foto-Upload mit Komprimierung
- Validierung
- Referenzdaten-Integration

### ProfileView (ui/profile.py)

Benutzer-Profilbereich:

- Profil anzeigen/bearbeiten
- Menü-Navigation
- Abmelden

## Services

### PostService

```python
class PostService:
    def create(self, payload: Dict) -> Dict
    def update(self, post_id: str, payload: Dict) -> Dict
    def delete(self, post_id: str) -> bool
    def get_by_id(self, post_id: str) -> Dict | None
    def get_all(self, limit: int = 200) -> List[Dict]
    def add_color(self, post_id: str, color_id: int)
    def add_photo(self, post_id: str, photo_url: str)
```

### ReferenceService

```python
class ReferenceService:
    def get_post_statuses() -> List[Dict]
    def get_species() -> List[Dict]
    def get_breeds_by_species() -> Dict[int, List[Dict]]
    def get_colors() -> List[Dict]
    def get_sex() -> List[Dict]
    def clear_cache()
```

## Authentifizierung

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│ AuthView │────▶│ Supabase │
│ (Login)  │     │          │     │   Auth   │
└──────────┘     └────┬─────┘     └──────────┘
                      │
                      ▼ on_auth_success()
               ┌──────────────┐
               │ PetBuddyApp  │
               │ is_logged_in │
               └──────────────┘
```

## Datenfluss: Meldung erstellen

```
1. User füllt PostForm aus
2. PostForm.save() validiert Eingaben
3. PostService.create() sendet an Supabase
4. Farben via PostService.add_color()
5. Foto via PostService.add_photo()
6. Callback: on_post_saved()
7. DiscoverView.load_posts() aktualisiert Liste
8. Navigation zu TAB_START
```
