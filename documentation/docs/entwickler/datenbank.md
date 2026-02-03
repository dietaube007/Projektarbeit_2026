# Datenbank

Übersicht über das Datenbankschema in Supabase/PostgreSQL.

## ER-Diagramm

```
┌──────────────┐       ┌──────────────┐
│     user     │       │  post_status │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│ email        │       │ name         │
│ display_name │       └──────┬───────┘
│ created_at   │              │
└──────┬───────┘              │
       │                      │
       │ 1:n                  │ 1:n
       │                      │
┌──────▼───────────────────────▼──────┐
│                post                  │
├─────────────────────────────────────┤
│ id (PK, UUID)                       │
│ user_id (FK → user)                 │
│ post_status_id (FK → post_status)   │
│ headline                            │
│ description                         │
│ species_id (FK → species)           │
│ breed_id (FK → breed)               │
│ sex_id (FK → sex)                   │
│ event_date                          │
│ location_text                       │
│ created_at                          │
└──────┬──────────────────────────────┘
       │
       │ 1:n              1:n
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│  post_image  │    │  post_color  │
├──────────────┤    ├──────────────┤
│ id (PK)      │    │ id (PK)      │
│ post_id (FK) │    │ post_id (FK) │
│ url          │    │ color_id(FK) │
└──────────────┘    └──────────────┘
```

## Tabellen

### user

Benutzer-Profildaten (ergänzt Supabase Auth).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key (= auth.users.id) |
| email | TEXT | E-Mail-Adresse |
| display_name | TEXT | Anzeigename |
| created_at | TIMESTAMP | Erstellungszeitpunkt |

### post_status

Meldungskategorien.

| id | name |
|----|------|
| 1 | Vermisst |
| 2 | Fundtier |
| 3 | Wiedervereint |

### species

Tierarten.

| id | name |
|----|------|
| 1 | Hund |
| 2 | Katze |
| 3 | Kleintier |

### breed

Rassen, gruppiert nach Tierart.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT | Primary Key |
| name | TEXT | Rassenname |
| species_id | INT | FK → species |

### sex

Geschlechts-Optionen.

| id | name |
|----|------|
| 1 | Männlich |
| 2 | Weiblich |
| 3 | Unbekannt |

### color

Verfügbare Farben.

| id | name |
|----|------|
| 1 | Schwarz |
| 2 | Weiß |
| 3 | Braun |
| ... | ... |

### post

Haupttabelle für Meldungen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| user_id | UUID | FK → user |
| post_status_id | INT | FK → post_status |
| headline | TEXT | Titel/Name |
| description | TEXT | Beschreibung |
| species_id | INT | FK → species |
| breed_id | INT | FK → breed (nullable) |
| sex_id | INT | FK → sex (nullable) |
| event_date | DATE | Datum des Ereignisses |
| location_text | TEXT | Standort-Beschreibung |
| created_at | TIMESTAMP | Erstellungszeitpunkt |

### post_image

Bilder zu Meldungen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| post_id | UUID | FK → post |
| url | TEXT | Storage-URL |

### post_color

Farben zu Meldungen (m:n).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INT | Primary Key |
| post_id | UUID | FK → post |
| color_id | INT | FK → color |

### profile

Erweiterte Benutzerprofile.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key (= auth.users.id) |
| display_name | TEXT | Anzeigename |
| profile_image | TEXT | URL zum Profilbild |
| created_at | TIMESTAMP | Erstellungszeitpunkt |
| updated_at | TIMESTAMP | Letzte Aktualisierung |

### favorite

Favorisierte Meldungen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| user_id | UUID | FK → auth.users |
| post_id | UUID | FK → post |
| created_at | TIMESTAMP | Erstellungszeitpunkt |

**Unique Constraint:** `(user_id, post_id)`

### saved_search

Gespeicherte Suchaufträge.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | SERIAL | Primary Key |
| user_id | UUID | FK → auth.users |
| name | TEXT | Name des Suchauftrags |
| filters | JSONB | Filter als JSON |
| created_at | TIMESTAMP | Erstellungszeitpunkt |

**Unique Constraint:** `(user_id, name)`

**Filters-JSON Struktur:**
```json
{
  "search_query": "suchbegriff",
  "status_id": 1,
  "species_id": 2,
  "breed_id": 5,
  "sex_id": 1,
  "colors": [1, 3, 5]
}
```

### comment

Kommentare zu Meldungen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | SERIAL | Primary Key |
| post_id | UUID | FK → post |
| user_id | UUID | FK → auth.users |
| content | TEXT | Kommentar-Text |
| parent_comment_id | INT | FK → comment (für Antworten) |
| is_deleted | BOOLEAN | Soft-Delete Flag |
| created_at | TIMESTAMP | Erstellungszeitpunkt |
| updated_at | TIMESTAMP | Letzte Aktualisierung |

### comment_reaction

Emoji-Reaktionen auf Kommentare.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| comment_id | INT | FK → comment |
| user_id | UUID | FK → auth.users |
| emoji | TEXT | Emoji-Zeichen |
| created_at | TIMESTAMP | Erstellungszeitpunkt |

**Unique Constraint:** `(comment_id, user_id, emoji)`

## SQL-Schema

```sql
-- Beispiel: Post mit Relationen laden
SELECT 
    p.*,
    ps.name as status_name,
    sp.name as species_name,
    br.name as breed_name,
    sx.name as sex_name
FROM post p
LEFT JOIN post_status ps ON p.post_status_id = ps.id
LEFT JOIN species sp ON p.species_id = sp.id
LEFT JOIN breed br ON p.breed_id = br.id
LEFT JOIN sex sx ON p.sex_id = sx.id
ORDER BY p.created_at DESC;
```

## Supabase Storage

Bilder werden im Bucket `pet-images` gespeichert.

```
pet-images/
├── {user_id}/
│   ├── {timestamp}_{filename}.jpg
│   └── ...
```

## Row Level Security (RLS)

Empfohlene Policies:

```sql
-- Posts: Jeder kann lesen
CREATE POLICY "Posts are viewable by everyone"
ON post FOR SELECT USING (true);

-- Posts: Nur eigene bearbeiten
CREATE POLICY "Users can update own posts"
ON post FOR UPDATE USING (auth.uid() = user_id);

-- Posts: Nur authentifizierte können erstellen
CREATE POLICY "Authenticated users can create posts"
ON post FOR INSERT WITH CHECK (auth.uid() = user_id);
```
