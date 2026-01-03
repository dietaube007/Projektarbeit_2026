# Installation

Anleitung zur lokalen Einrichtung der PetBuddy-Entwicklungsumgebung.

## Voraussetzungen

- Python 3.11 oder höher
- Git
- Supabase-Projekt (für Backend)

## Repository klonen

```bash
git clone https://github.com/dietaube007/Projektarbeit_2026.git
cd Projektarbeit_2026
```

## Virtuelle Umgebung

```bash
# Erstellen
python -m venv .venv

# Aktivieren (macOS/Linux)
source .venv/bin/activate

# Aktivieren (Windows)
.venv\Scripts\activate
```

## Abhängigkeiten installieren

```bash
pip install -e .
```

Oder manuell:

```bash
pip install flet supabase python-dotenv pillow
```

## Umgebungsvariablen

Erstelle eine `.env`-Datei im Projektverzeichnis:

```env
SUPABASE_URL=https://dein-projekt.supabase.co
SUPABASE_KEY=dein-anon-key
FLET_SECRET_KEY=ein-geheimer-schluessel
```

!!! warning "Sicherheit"
    Die `.env`-Datei niemals committen! Sie ist bereits in `.gitignore`.

## Supabase einrichten

1. Erstelle ein Projekt auf [supabase.com](https://supabase.com)
2. Kopiere URL und Anon-Key aus den Projekteinstellungen
3. Führe das Datenbankschema aus (siehe [Datenbank](datenbank.md))

## App starten

```bash
python main.py
```

Die App öffnet sich im Browser unter `http://localhost:8550`.

## Entwicklungsmodus

Für Hot-Reload während der Entwicklung:

```bash
flet run main.py -d
```

## Nächste Schritte

- [Architektur](architektur.md)
- [Datenbank](datenbank.md)
- [API-Referenz](api.md)
