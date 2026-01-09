# PetBuddy

Eine moderne Web-Anwendung zur Vermittlung von vermissten und gefundenen Tieren.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flet](https://img.shields.io/badge/Flet-0.28.3-green.svg)
![Supabase](https://img.shields.io/badge/Supabase-Backend-orange.svg)

---

## Schnellstart

```bash
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. .env Datei erstellen
SUPABASE_URL=...
SUPABASE_ANON_KEY=...

# 3. Anwendung starten
python main.py
```

Die Anwendung öffnet sich automatisch im Browser unter `http://localhost:8550`

---

## Dokumentation

**Vollständige Dokumentation:** Siehe [documentation/](documentation/) für die ausführliche MkDocs-Dokumentation.

### Dokumentation starten:

```bash
cd documentation
mkdocs serve
```

Dokumentation wird unter `http://localhost:8000` verfügbar sein.

---

## Technologie-Stack

- **Flet** - Python UI-Framework
- **Supabase** - Backend (PostgreSQL, Auth, Storage)
- **Python 3.11+** - Programmiersprache
- **Material Design 3** - Design-System

---

## Projektstruktur

```
├── app/              # Hauptanwendungslogik
├── services/         # Business Logic & Datenbankzugriff
├── ui/              # UI-Komponenten
├── utils/           # Utility-Module
├── documentation/   # MkDocs Dokumentation
└── main.py          # Einstiegspunkt
```

---

## Weitere Informationen

- **Installation & Setup**: Siehe [documentation/docs/entwickler/installation.md](documentation/docs/entwickler/installation.md)
- **Architektur**: Siehe [documentation/docs/entwickler/architektur.md](documentation/docs/entwickler/architektur.md)
- **API-Dokumentation**: Siehe [documentation/docs/entwickler/api.md](documentation/docs/entwickler/api.md)
- **Benutzer-Anleitung**: Siehe [documentation/docs/nutzer/](documentation/docs/nutzer/)

---

**Projektarbeit 2026**
