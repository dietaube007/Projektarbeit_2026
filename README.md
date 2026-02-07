# PetBuddy

Eine moderne Web-Anwendung zur Vermittlung von vermissten und gefundenen Tieren.

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
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
FLET_SECRET_KEY=...
MAPBOX_TOKEN=...

# 3. Anwendung starten
python main.py
```

Die Anwendung öffnet sich automatisch im Browser unter `http://localhost:8550`

---

## Dokumentation

**Vollständige Dokumentation:** [https://dietaube007.github.io/Projektarbeit_2026/](https://dietaube007.github.io/Projektarbeit_2026/)

Lokal starten:

```bash
cd documentation
mkdocs serve
```

---

## Technologie-Stack

- **Flet** - Python UI-Framework
- **Supabase** - Backend (PostgreSQL, Auth, Storage)
- **Python 3.13+** - Programmiersprache
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

**Projektarbeit 2026**
