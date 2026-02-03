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
├── main.py                     # Einstiegspunkt
├── pyproject.toml              # Projekt-Konfiguration
├── .env                        # Umgebungsvariablen (nicht in Git)
│
├── ui/                         # UI-Layer
│   ├── constants.py            # Konstanten (Farben, Größen)
│   ├── helpers.py              # Hilfsfunktionen
│   ├── shared_components.py    # Gemeinsame Komponenten
│   ├── theme.py                # ThemeManager, UI-Komponenten
│   │
│   ├── auth/                   # Authentifizierung
│   │   ├── view.py             # AuthView - Login/Registrierung
│   │   ├── components/         # Login, Register, Password Reset
│   │   └── handlers/           # Auth-Handler
│   │
│   ├── discover/               # Startseite
│   │   ├── view.py             # DiscoverView - Meldungsliste
│   │   ├── components/         # Post-Cards, Filter, Kommentare
│   │   └── handlers/           # Search, Filter, Favorites, Comments
│   │
│   ├── post_form/              # Meldungsformular
│   │   ├── view.py             # PostForm - Neue Meldung
│   │   ├── components/         # Formular, Foto, KI-Erkennung
│   │   └── handlers/           # Validation, Upload, AI
│   │
│   └── profile/                # Profilbereich
│       ├── view.py             # ProfileView - Profil, Einstellungen
│       ├── components/         # Menu, Edit, Favorites, Posts
│       └── handlers/           # Profile, Settings, Posts
│
├── services/                   # Backend-Services
│   ├── supabase_client.py      # Supabase-Client-Singleton
│   │
│   ├── account/                # Benutzer-Services
│   │   ├── auth.py             # AuthService - Login/Logout
│   │   ├── profile.py          # ProfileService - Profildaten
│   │   ├── profile_image.py    # ProfileImageService
│   │   └── account_deletion.py # Kontolöschung
│   │
│   ├── posts/                  # Meldungs-Services
│   │   ├── post.py             # PostService - CRUD
│   │   ├── search.py           # SearchService - Suche
│   │   ├── filters.py          # FilterService
│   │   ├── references.py       # ReferenceService - Stammdaten
│   │   ├── favorites.py        # FavoritesService
│   │   ├── saved_search.py     # SavedSearchService
│   │   ├── comment.py          # CommentService
│   │   └── queries.py          # SQL-Queries
│   │
│   └── ai/                     # KI-Services
│       └── pet_recognition.py  # PetRecognitionService
│
├── i18n/                       # Internationalisierung
│   ├── translator.py           # Übersetzungs-Engine
│   ├── de.json                 # Deutsche Texte
│   └── en.json                 # Englische Texte
│
├── utils/                      # Utilities
│   ├── logging_config.py       # Logging
│   ├── validators.py           # Eingabevalidierung
│   └── constants.py            # Globale Konstanten
│
└── documentation/              # MkDocs-Dokumentation
```

## Schichtenarchitektur

```
┌─────────────────────────────────────────────────────────┐
│                   UI Layer (Flet)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │
│  │ AuthView │ │ Discover │ │ PostForm │ │ProfileView│   │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘   │
│        │            │            │            │         │
│        └────────────┴────────────┴────────────┘         │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐    │
│  │              UI Handlers                        │    │
│  │  (Search, Filter, Favorite, Comment, ...)       │    │
│  └──────────────────────┬──────────────────────────┘    │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    Service Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Account         │  │ Posts           │               │
│  │ ├─ AuthService  │  │ ├─ PostService  │               │
│  │ ├─ Profile      │  │ ├─ SearchService│               │
│  │ └─ ProfileImage │  │ ├─ Favorites    │               │
│  └─────────────────┘  │ ├─ SavedSearch  │               │
│                       │ ├─ Comments     │               │
│  ┌─────────────────┐  │ └─ References   │               │
│  │ AI              │  └─────────────────┘               │
│  │ └─ PetRecognit. │                                    │
│  └─────────────────┘                                    │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                  Supabase Client                        │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │   Auth   │  │  Database  │  │      Storage        │  │
│  │          │  │ (Postgres) │  │   (pet-images,      │  │
│  │          │  │            │  │    profile-images)  │  │
│  └──────────┘  └────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
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

### Account-Services

#### AuthService
Authentifizierung und Session-Management.

```python
class AuthService:
    def login(email, password) -> AuthResult
    def register(email, password, display_name) -> AuthResult
    def logout() -> AuthResult
    def reset_password(email) -> AuthResult
    def change_password(new_password) -> AuthResult
```

#### ProfileService
Benutzerprofil-Verwaltung.

```python
class ProfileService:
    def get_current_user() -> User | None
    def get_user_id() -> str | None
    def get_display_name() -> str
    def get_email() -> str | None
    def get_profile_image_url() -> str | None
    def update_display_name(name) -> bool
    def get_user_profiles(user_ids) -> Dict[str, Dict]
```

### Post-Services

#### PostService
CRUD-Operationen für Meldungen.

```python
class PostService:
    def create(payload: Dict) -> Dict
    def update(post_id: str, payload: Dict) -> Dict
    def delete(post_id: str) -> bool
    def get_by_id(post_id: str) -> Dict | None
```

#### SearchService
Suche und Filterung von Meldungen.

```python
class SearchService:
    def search(filters: Dict, limit: int = 200) -> List[Dict]
```

#### FavoritesService
Favoriten-Verwaltung.

```python
class FavoritesService:
    def get_favorites() -> List[Dict]
    def add_favorite(post_id: str) -> bool
    def remove_favorite(post_id: str) -> bool
    def is_favorite(post_id: str) -> bool
    def get_favorite_ids(user_id: str) -> Set[str]
```

#### SavedSearchService
Gespeicherte Suchaufträge.

```python
class SavedSearchService:
    def get_saved_searches() -> List[Dict]
    def save_search(name, filters...) -> Tuple[bool, str]
    def delete_search(search_id: int) -> Tuple[bool, str]
```

#### CommentService
Kommentar-Verwaltung.

```python
class CommentService:
    def get_comments(post_id: str) -> List[Dict]
    def create_comment(post_id, user_id, content, parent_id) -> bool
    def delete_comment(comment_id: int) -> bool
```

#### ReferenceService
Stammdaten (gecacht).

```python
class ReferenceService:
    def get_post_statuses() -> List[Dict]
    def get_species() -> List[Dict]
    def get_breeds_by_species() -> Dict[int, List[Dict]]
    def get_colors() -> List[Dict]
    def get_sex() -> List[Dict]
    def clear_cache()
```

### AI-Services

#### PetRecognitionService
KI-gestützte Tierart-/Rassenerkennung.

```python
class PetRecognitionService:
    def recognize_pet(image_data: bytes) -> Dict
    # Returns: {success, species, breed, confidence, error}
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
