# Installation & Schnellstart

<a id="installation-schnellstart"></a>

Diese Anleitung ist auf den aktuellen Stand des Repositories abgestimmt und soll eine reproduzierbare Inbetriebnahme ohne Rückfragen ermöglichen.

Hinweis zum Kriterium: Ohne gültige Zugangsdaten (Supabase) ist die App nicht voll lauffähig. Damit ein technisch versierter Dritter trotzdem ohne Rückfragen starten kann, gibt es eine feste `.env.example`-Vorlage mit allen benötigten Schlüsseln.

## Voraussetzungen

- Git
- Python 3.13 oder höher (laut `pyproject.toml`)
- Ein Supabase-Projekt (URL + Anon Key)

## 1. Repository klonen

```bash
git clone https://github.com/dietaube007/Projektarbeit_2026.git
cd Projektarbeit_2026
```

## 2. Virtuelle Umgebung erstellen und aktivieren

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

## 4. Konfiguration (`.env`)

Erzeuge die `.env` direkt aus der Vorlage:

```bash
cp .env.example .env
```

Danach nur die Pflichtwerte in `.env` eintragen:

```env
# Pflicht
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
FLET_SECRET_KEY=CHANGE_ME_TO_A_LONG_RANDOM_VALUE

# Optional
MAPBOX_TOKEN=YOUR_MAPBOX_ACCESS_TOKEN
PORT=8080
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### Bedeutung der Variablen

- `SUPABASE_URL`: URL deines Supabase-Projekts
- `SUPABASE_ANON_KEY`: öffentlicher Anon Key (wird im Code zwingend erwartet)
- `FLET_SECRET_KEY`: Secret für Flet Uploads
- `MAPBOX_TOKEN` (optional): aktiviert Geocoding-Vorschläge; ohne Token läuft die App weiter, aber ohne Geocoding
- `PORT` (optional): Standard ist `8080`

Ohne `SUPABASE_URL` und `SUPABASE_ANON_KEY` bricht die App mit einer klaren Fehlermeldung ab. Das ist erwartetes Verhalten.

!!! warning "Sicherheit"
    `.env` niemals committen. Zugangsdaten und Secrets gehören nicht ins Repository.

## 5. Anwendung starten

```bash
python main.py
```

Erwartetes Verhalten:

- Die App startet über Uvicorn auf `http://localhost:8080` (oder deinem `PORT`)
- Lokal wird der Browser automatisch geöffnet (wenn `FLY_APP_NAME` nicht gesetzt ist)

## 6. Funktionscheck

1. Startseite öffnet sich im Browser
2. Anmeldung/Registrierung funktioniert (Supabase-Verbindung vorhanden)
3. Meldungen können geladen werden
4. Geocoding liefert Vorschläge nur dann, wenn `MAPBOX_TOKEN` gesetzt ist

## Häufige Fehlerbilder

- `Supabase-Konfiguration unvollständig`: `SUPABASE_URL` oder `SUPABASE_ANON_KEY` fehlt/falsch
- Kein Geocoding trotz laufender App: `MAPBOX_TOKEN` fehlt oder ist ungültig
- App startet nicht mit `python main.py`: Python-Version prüfen (`>=3.13`) und venv aktivieren
