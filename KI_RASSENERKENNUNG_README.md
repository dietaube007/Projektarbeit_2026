# 🤖 KI-Rassenerkennung - Quick Start

## Was ist das?

Eine KI-gestützte Funktion, die automatisch die Tierart und Rasse aus Fotos von gefundenen Tieren erkennt.

## ✨ Features

- 🐕 **Hunde-Erkennung**: Erkennt verschiedene Hunderassen
- 🐈 **Katzen-Erkennung**: Erkennt verschiedene Katzenrassen  
- 🔒 **Datenschutz**: Analyse erfolgt lokal, keine externen APIs
- ✅ **Opt-In**: Nutzer müssen explizit zustimmen
- ⚠️ **Disclaimer**: Klarer Hinweis, dass es nur ein Vorschlag ist
- 🎯 **Confidence Score**: Zeigt an, wie sicher die KI ist

## 🚀 Installation

Dependencies installieren:
```bash
pip install -r requirements.txt
```

Beim ersten Start wird das ML-Modell automatisch heruntergeladen (~100 MB).

## 📖 Verwendung

### Für Nutzer

1. Wähle "**Fundtier**" beim Erstellen einer Meldung
2. Lade ein **Foto** hoch
3. Klicke auf "**🤖 KI-Rassenerkennung starten**"
4. Akzeptiere die Einverständniserklärung
5. Warte auf das Ergebnis
6. **Übernehmen** oder **Ablehnen**

### Für Entwickler

```python
from services.pet_recognition import get_recognition_service

# Service holen (Singleton)
service = get_recognition_service()

# Bild analysieren
with open("dog.jpg", "rb") as f:
    image_data = f.read()

result = service.recognize_pet(image_data)

if result["success"]:
    print(f"Tierart: {result['species']}")
    print(f"Rasse: {result['breed']}")
    print(f"Confidence: {result['confidence']:.2%}")
else:
    print(f"Fehler: {result['error']}")
```

## 🎯 Nur für Fundtiere

Die Funktion ist **nur** für gefundene Tiere verfügbar, da Besitzer vermisster Tiere die Rasse normalerweise bereits kennen.

## ⚙️ Technische Details

- **Modell**: `dima806/dog_breed_image_detection`
- **Framework**: Hugging Face Transformers
- **Backend**: PyTorch
- **Größe**: ~1.2 GB (inkl. Dependencies)
- **Inference-Zeit**: ~2-5 Sekunden

## 📚 Dokumentation

- **Nutzer**: [ki-rassenerkennung.md](documentation/docs/nutzer/ki-rassenerkennung.md)
- **Entwickler**: [ki-rassenerkennung.md](documentation/docs/entwickler/ki-rassenerkennung.md)

## ⚠️ Wichtige Hinweise

1. **Keine Garantie**: Die KI kann Fehler machen
2. **Nur Vorschlag**: Nutzer können ablehnen und manuell eingeben
3. **Beste Ergebnisse**: Klare, gut beleuchtete Fotos verwenden
4. **Nur Hunde/Katzen**: Kleintiere werden nicht unterstützt

## 🔧 Konfiguration

### Confidence-Schwelle anpassen

In `services/pet_recognition.py`:
```python
if confidence < 0.2:  # Erhöhe/Senke diesen Wert
```

### Katzenrassen erweitern

In `services/pet_recognition.py`, Methode `_is_cat_or_dog()`:
```python
cat_breeds = [
    'abyssinian', 'bengal', 'birman',
    # Weitere Rassen hier...
]
```

## 🐛 Troubleshooting

### "Modell konnte nicht geladen werden"
- ✅ Internetverbindung prüfen
- ✅ Speicherplatz prüfen (~1.5 GB frei)
- ✅ Dependencies installiert?

### "Erkennung ist unsicher"
- 📸 Besseres Foto verwenden
- 💡 Mehr Licht
- 🎯 Tier vollständig sichtbar
- ✍️ Manuell eingeben als Alternative

## 🚀 Performance

| Aktion | Zeit |
|--------|------|
| Modell-Download (erste Ausführung) | ~30-60s |
| Modell-Load (erste Ausführung) | ~5-10s |
| Inference (pro Bild) | ~2-5s |
| Folge-Ausführungen | ~2-5s |

## 📦 Dateien

```
services/
  └── pet_recognition.py          # Service-Layer
ui/
  └── post_form/
      ├── view.py                  # UI-Integration
      └── form_fields.py           # UI-Komponenten
documentation/
  └── docs/
      ├── nutzer/
      │   └── ki-rassenerkennung.md
      └── entwickler/
          └── ki-rassenerkennung.md
```

## 🎉 Fertig!

Die KI-Rassenerkennung ist jetzt einsatzbereit. Viel Erfolg! 🐾
