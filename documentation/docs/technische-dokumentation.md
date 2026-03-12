# Technische Dokumentation

<a id="technische-dokumentation"></a>

Diese Seite beschreibt die technische Konzeption von PetBuddy – Architektur, Datenmodell und die wichtigsten Module. Sie richtet sich an Entwickler und technisch Interessierte.

---

## Architekturdiagramm

PetBuddy folgt einer **Schichtenarchitektur** mit klarer Trennung von UI, Geschäftslogik und Datenzugriff.

```mermaid
graph TD
    subgraph Client
        A[Flet Web/Desktop UI]
    end

    subgraph "UI-Schicht · ui/"
        B1[auth/]
        B2[discover/]
        B3[post_form/]
        B4[profile/]
    end

    subgraph "App-Steuerung · app/"
        C1[PetBuddyApp]
        C2[Navigation & Routing]
        C3[AuthFlow]
    end

    subgraph "Service-Schicht · services/"
        D1[account/ – Auth, Profil]
        D2[posts/ – CRUD, Suche, Kommentare]
        D3[geocoding/ – Mapbox]
        D4[ai/ – Tiererkennung]
    end

    subgraph "Externe Dienste"
        E1[(Supabase PostgreSQL)]
        E2[(Supabase Storage)]
        E3[Mapbox API]
        E4[Hugging Face ViT]
    end

    A --> B1 & B2 & B3 & B4
    B1 & B2 & B3 & B4 --> C1
    C1 --> C2 & C3
    C1 --> D1 & D2 & D3 & D4
    D1 & D2 --> E1
    D2 --> E2
    D3 --> E3
    D4 --> E4
```

### Schichten im Überblick

| Schicht | Verzeichnis | Aufgabe |
|---------|-------------|---------|
| **Einstiegspunkt** | `main.py` → `app/app.py` | Flet-App starten, Routing, Theme |
| **UI** | `ui/` | Views, Components, Handler (je Feature) |
| **App-Steuerung** | `app/` | Navigation, Drawer, Auth-Flow, Dialoge |
| **Services** | `services/` | Geschäftslogik, Supabase-Zugriff |
| **Utils** | `utils/` | Logging, PDF-Export, Validierung, Karten |
| **Externe Dienste** | — | Supabase (DB + Storage), Mapbox, Hugging Face |

---

## Datenbankmodell

Die Daten liegen in **Supabase (PostgreSQL)**. Nachfolgend das logische Datenmodell:

```mermaid
erDiagram
    user {
        UUID id PK
        text display_name
        text profile_image
    }

    post {
        UUID id PK
        UUID user_id FK
        text headline
        text description
        text location_text
        float location_lat
        float location_lon
        date event_date
        timestamp created_at
        bool is_active
        int post_status_id FK
        int species_id FK
        int breed_id FK
        int sex_id FK
    }

    post_status {
        int id PK
        text name
    }

    species {
        int id PK
        text name
    }

    breed {
        int id PK
        text name
        int species_id FK
    }

    color {
        int id PK
        text name
    }

    sex {
        int id PK
        text name
    }

    post_image {
        UUID id PK
        UUID post_id FK
        text url
    }

    post_color {
        UUID id PK
        UUID post_id FK
        int color_id FK
    }

    comment {
        UUID id PK
        UUID post_id FK
        UUID user_id FK
        text content
        UUID parent_comment_id FK
        timestamp created_at
        bool is_deleted
    }

    comment_reaction {
        UUID id PK
        UUID comment_id FK
        UUID user_id FK
        text emoji
    }

    favorite {
        UUID id PK
        UUID user_id FK
        UUID post_id FK
    }

    saved_search {
        UUID id PK
        UUID user_id FK
        text name
        json filters
        timestamp created_at
    }

    user ||--o{ post : "erstellt"
    user ||--o{ comment : "schreibt"
    user ||--o{ favorite : "favorisiert"
    user ||--o{ saved_search : "speichert"
    user ||--o{ comment_reaction : "reagiert"

    post }o--|| post_status : "hat Status"
    post }o--|| species : "ist Tierart"
    post }o--|| breed : "ist Rasse"
    post }o--|| sex : "hat Geschlecht"
    post ||--o{ post_image : "hat Bilder"
    post ||--o{ post_color : "hat Farben"
    post ||--o{ comment : "hat Kommentare"
    post ||--o{ favorite : "wird favorisiert"

    post_color }o--|| color : "referenziert"
    comment ||--o{ comment_reaction : "hat Reaktionen"
    comment ||--o{ comment : "hat Antworten"
    species ||--o{ breed : "hat Rassen"
```

### Lookup-Tabellen

| Tabelle | Inhalt |
|---------|--------|
| `post_status` | „Vermisst", „Gefunden" |
| `species` | „Hund", „Katze", „Vogel", … |
| `breed` | Rassen je Tierart |
| `color` | Fellfarben |
| `sex` | „Männlich", „Weiblich", „Unbekannt" |

### Storage Buckets (Supabase)

| Bucket | Zweck | Limits |
|--------|-------|--------|
| `pet-images` | Meldungsfotos | max. 10 MB, komprimiert auf 1920×1920 px |
| `profile-pictures` | Profilbilder | — |

---

## API-Referenz / Modulbeschreibung

Da PetBuddy eine **Flet-Anwendung** ist (kein REST-Backend), liegt die Geschäftslogik in der Service-Schicht. Nachfolgend die wichtigsten Module und ihre Funktionen.

### `services/account/` – Benutzerverwaltung

| Modul | Klasse | Wichtige Methoden |
|-------|--------|-------------------|
| `auth.py` | `AuthService` | `login()`, `register()`, `password_reset()` |
| `profile.py` | `ProfileService` | `get_current_user()`, `update_display_name()`, `get_user_profiles()` |
| `profile_image.py` | `ProfileImageService` | `upload_profile_image()`, `delete_profile_image()` |
| `account_deletion.py` | `AccountDeletionService` | `delete_account()` – kaskadiert Posts, Bilder, Kommentare |

### `services/posts/` – Meldungsverwaltung

| Modul | Klasse / Funktion | Wichtige Methoden |
|-------|-------------------|-------------------|
| `post.py` | `PostService` | `create()`, `update()`, `delete()`, `get_post_by_id()`, `get_posts()` |
| `search.py` | `SearchService` | `search()` – kombiniert Filter, Sortierung, Standort |
| `filters.py` | Hilfsfunktionen | `filter_by_search()`, `filter_by_colors()`, `filter_by_location()`, `sort_by_event_date()`, `enrich_with_distance()` |
| `comment.py` | `CommentService` | `get_comments()`, `add_comment()`, `add_reaction()`, `remove_reaction()` |
| `favorites.py` | `FavoritesService` | `get_favorites()`, `add_favorite()`, `remove_favorite()` |
| `saved_search.py` | `SavedSearchService` | `get_saved_searches()`, `create_saved_search()`, `delete_saved_search()` |
| `references.py` | `ReferenceService` | `get_post_statuses()`, `get_species()`, `get_breeds_by_species()`, `get_colors()` |
| `post_image.py` | `PostStorageService` | `upload_post_image()`, `remove_post_image()` – JPEG-Komprimierung |
| `post_relations.py` | `PostRelationsService` | `add_color()`, `update_colors()`, `add_photo()` |

### `services/geocoding/` – Standortdienste

| Modul | Funktion | Beschreibung |
|-------|----------|--------------|
| `mapbox_geocoding.py` | `geocode_suggestions()` | Mapbox-Autocomplete → `{text, lat, lon}` |

### `services/ai/` – Künstliche Intelligenz

| Modul | Klasse | Beschreibung |
|-------|--------|--------------|
| `pet_recognition.py` | `PetRecognitionService` | `recognize_pet()` – Bilderkennung via Hugging Face ViT (google/vit-base-patch16-224) |

### `utils/` – Hilfsfunktionen

| Modul | Zweck |
|-------|-------|
| `logging_config.py` | Zentrales Logging (Konsole + Datei) |
| `pdf_generator.py` | PDF-Export von Meldungen (ReportLab) |
| `map_generator.py` | Kartenansicht (Folium/Leaflet) |
| `validators.py` | Eingabevalidierung |
| `constants.py` | App-weite Konstanten |

---

## Dateistruktur

```
Projektarbeit_2026/
├── main.py                  # Einstiegspunkt
├── app/
│   ├── app.py               # PetBuddyApp – Hauptklasse
│   ├── navigation.py        # Drawer, AppBar, Routing
│   ├── auth_flow.py         # Login/Logout-Workflow
│   └── dialogs.py           # Wiederverwendbare Dialoge
├── ui/                      # Feature-basierte UI-Module
│   ├── auth/                # Anmeldung / Registrierung
│   ├── discover/            # Entdecken, Suche, Karte
│   ├── post_form/           # Meldung erstellen / bearbeiten
│   ├── profile/             # Profil, Favoriten, Einstellungen
│   ├── theme.py             # ThemeManager (Hell/Dunkel)
│   └── shared_components.py # Gemeinsame UI-Elemente
├── services/                # Geschäftslogik & Datenzugriff
│   ├── supabase_client.py   # Singleton Supabase-Client
│   ├── account/             # Auth, Profil, Löschung
│   ├── posts/               # CRUD, Suche, Kommentare
│   ├── geocoding/           # Mapbox-Integration
│   └── ai/                  # Tiererkennung (ViT)
├── utils/                   # Logging, PDF, Karten, Validierung
├── deploy/
│   ├── Dockerfile           # Multi-Stage Docker Build
│   └── fly.toml             # Fly.io Konfiguration
└── documentation/           # MkDocs-Dokumentation
```

---

## Tech-Stack

| Kategorie | Technologie |
|-----------|-------------|
| **Sprache** | Python 3.13+ |
| **UI-Framework** | Flet 0.28.3 (Web + Desktop) |
| **Datenbank** | Supabase (PostgreSQL + Auth + Storage) |
| **Geocoding** | Mapbox API |
| **KI-Modell** | Hugging Face ViT (google/vit-base-patch16-224) |
| **Bildverarbeitung** | Pillow (Komprimierung, Resize) |
| **PDF** | ReportLab |
| **Karten** | Folium / Leaflet |
| **Deployment** | Fly.io (Docker, Frankfurt, 2 GB RAM) |
| **Dokumentation** | MkDocs Material |
