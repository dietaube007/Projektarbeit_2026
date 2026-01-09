# KI-Rassenerkennung - Entwickler-Dokumentation

## Architektur

Die KI-Rassenerkennung besteht aus drei Hauptkomponenten:

### 1. Service-Layer (`services/pet_recognition.py`)
Enthält die Hauptlogik für die Bilderkennung.

### 2. UI-Layer (`ui/post_form/`)
Integration in das Post-Formular mit Dialogen und Ergebnis-Anzeige.

### 3. ML-Modell
Verwendet ein vortrainiertes Hugging Face Transformers-Modell.

## Service: `PetRecognitionService`

### Initialisierung

```python
from services.pet_recognition import get_recognition_service

service = get_recognition_service()  # Singleton-Instanz
```

Das Modell wird **lazy loaded** beim ersten Aufruf von `recognize_pet()`.

### Hauptmethode: `recognize_pet()`

```python
def recognize_pet(
    image_data: bytes,
    species_filter: Optional[str] = None
) -> Dict[str, any]:
    """
    Erkennt Tierart und Rasse aus einem Bild.
    
    Args:
        image_data: Bilddaten als Bytes
        species_filter: Optional - Filter auf "Hund" oder "Katze"
    
    Returns:
        Dict mit:
            - success: bool - Ob die Erkennung erfolgreich war
            - species: str - Erkannte Tierart (Hund/Katze)
            - breed: str - Erkannte Rasse
            - confidence: float - Konfidenz-Score (0-1)
            - error: str - Fehlermeldung falls success=False
    """
```

### Verwendetes Modell

**Modell**: `dima806/dog_breed_image_detection`
- Vortrainiert auf Hunde- und Katzenrassen
- Basiert auf ViT (Vision Transformer)
- ~100 MB Download-Größe

### Interne Methoden

#### `_load_model()`
Lädt das Modell beim ersten Aufruf. Wird automatisch von `recognize_pet()` aufgerufen.

#### `_preprocess_image(image_data: bytes) -> Image.Image`
Konvertiert Bytes zu PIL Image und stellt RGB-Format sicher.

#### `_is_cat_or_dog(predicted_label: str) -> Tuple[Optional[str], str]`
Klassifiziert die erkannte Rasse als Hund oder Katze basierend auf bekannten Katzrassen.

**Bekannte Katzenrassen**:
- Abyssinian, Bengal, Birman, Bombay
- British Shorthair, Egyptian Mau, Maine Coon
- Persian, Ragdoll, Russian Blue, Siamese, Sphynx

Alle anderen Rassen werden als Hunde klassifiziert.

## UI-Integration

### Neue UI-Komponenten

#### `create_ai_recognition_button(on_click)`
Erstellt den Button zum Starten der KI-Erkennung.

#### `create_ai_result_container()`
Container für die Anzeige der Erkennungsergebnisse.

### PostForm-Erweiterungen

#### Neue State-Variablen
```python
self.recognition_service = get_recognition_service()
self.ai_result = None
self.ai_consent_given = False
```

#### Neue Methoden

**`_start_ai_recognition()`**
- Prüft Voraussetzungen (Foto vorhanden, Fundtier)
- Zeigt Einverständnisdialog

**`_show_consent_dialog()`**
- Zeigt Einverständniserklärung und Hinweise
- Bei Akzeptanz: Start der Erkennung

**`_perform_ai_recognition()`**
- Lädt Bild von Supabase Storage
- Ruft `recognition_service.recognize_pet()` auf
- Zeigt Ergebnis oder Fehler

**`_show_ai_result(result)`**
- Zeigt Erkennungsergebnis mit Confidence
- Buttons für Übernehmen/Ablehnen

**`_accept_ai_result()`**
- Übernimmt Tierart in Dropdown
- Übernimmt Rasse in Dropdown
- Fügt KI-Info zur Beschreibung hinzu

**`_reject_ai_result()`**
- Verwirft Ergebnis
- Blendet Container aus

#### Anpassungen

**`_update_title_label()`**
- Zeigt KI-Button nur bei Fundtieren
- Versteckt Button bei vermissten Tieren

## Workflow

```
1. User wählt "Fundtier"
   ↓
2. User lädt Foto hoch
   ↓
3. KI-Button wird sichtbar
   ↓
4. User klickt auf KI-Button
   ↓
5. _start_ai_recognition() prüft Voraussetzungen
   ↓
6. _show_consent_dialog() zeigt Einverständnis
   ↓
7. User akzeptiert
   ↓
8. _perform_ai_recognition() lädt Bild
   ↓
9. recognition_service.recognize_pet() analysiert
   ↓
10. _show_ai_result() zeigt Ergebnis
   ↓
11a. User übernimmt → _accept_ai_result()
11b. User lehnt ab → _reject_ai_result()
```

## Dependencies

### Neue Packages
```
transformers>=4.30.0
torch>=2.0.0
numpy>=1.24.0
```

### Größe
- `transformers`: ~400 MB
- `torch`: ~700 MB (CPU-Version)
- `numpy`: ~15 MB
- **Modell**: ~100 MB (wird beim ersten Start geladen)

**Gesamt**: ~1.2 GB

## Performance

### Erste Ausführung
- Modell-Download: ~30-60 Sekunden (je nach Internet)
- Modell-Load: ~5-10 Sekunden

### Folgende Ausführungen
- Modell bereits gecached
- Inference: ~2-5 Sekunden pro Bild

## Konfiguration

### Anpassen der Katzenrassen-Liste

In `services/pet_recognition.py`, Methode `_is_cat_or_dog()`:

```python
cat_breeds = [
    'abyssinian', 'bengal', 'birman', 'bombay', 'british_shorthair',
    # Weitere Rassen hinzufügen...
]
```

### Anpassen der Confidence-Schwelle

In `services/pet_recognition.py`, Methode `recognize_pet()`:

```python
if confidence < 0.2:  # Erhöhe oder senke den Wert
    return {
        "success": False,
        # ...
    }
```

**Empfehlung**: 0.2 (20%) ist ein guter Startwert.

### Verwenden eines anderen Modells

In `services/pet_recognition.py`, Methode `_load_model()`:

```python
model_name = "dima806/dog_breed_image_detection"  # Anderes Modell hier
```

**Hinweis**: Stelle sicher, dass das neue Modell:
- Ein Image Classification Modell ist
- `AutoImageProcessor` und `AutoModelForImageClassification` unterstützt
- Tier-/Rassenklassen im `id2label` hat

## Testing

### Manueller Test

1. Starte die Anwendung
2. Melde dich an
3. Gehe zu "Tier melden"
4. Wähle "Fundtier"
5. Lade ein Hunde- oder Katzenbild hoch
6. Klicke "KI-Rassenerkennung starten"
7. Akzeptiere Einverständnis
8. Prüfe Ergebnis

### Test-Bilder

Verwende klare, gut beleuchtete Bilder von:
- Golden Retriever
- Deutscher Schäferhund
- Britisch Kurzhaar
- Siamkatze

## Fehlerbehandlung

### Modell kann nicht geladen werden
**Fehler**: `RuntimeError: Modell konnte nicht geladen werden`

**Ursachen**:
- Keine Internetverbindung beim ersten Start
- Nicht genug Speicherplatz
- Hugging Face Hub nicht erreichbar

**Lösung**: 
- Internetverbindung prüfen
- Speicherplatz freigeben
- Später erneut versuchen

### Bild kann nicht verarbeitet werden
**Fehler**: `ValueError: Bild konnte nicht geladen werden`

**Ursachen**:
- Korruptes Bild
- Nicht unterstütztes Format
- Zu großes Bild

**Lösung**:
- Anderes Bild verwenden
- Bild neu hochladen
- Bildgröße reduzieren

### Niedrige Confidence
**Verhalten**: `success=False` mit Meldung "Erkennung ist unsicher"

**Ursachen**:
- Schlechte Bildqualität
- Ungewöhnliche Pose
- Seltene Rasse
- Mehrere Tiere im Bild

**Lösung**:
- Besseres Bild verwenden
- Manuell eingeben

## Erweiterungsmöglichkeiten

### Weitere Tierarten
1. Modell trainieren oder finden, das Kleintiere unterstützt
2. `_is_cat_or_dog()` erweitern zu `_classify_species()`
3. Neue Spezies-Kategorien hinzufügen

### Multi-Language-Support
1. Rassen-Namen in `i18n/` übersetzen
2. `_is_cat_or_dog()` anpassen für andere Sprachen

### Confidence-Visualization
1. Zeige Confidence als Fortschrittsbalken
2. Verschiedene Farben je nach Confidence-Level

### Batch-Processing
1. Mehrere Bilder gleichzeitig analysieren
2. Bestes Ergebnis auswählen

## Sicherheit

### Datenschutz
- ✅ Analyse erfolgt lokal
- ✅ Kein Senden an externe APIs
- ✅ Einverständniserklärung eingeholt

### Eingabevalidierung
- ✅ Bildgröße wird begrenzt
- ✅ Nur erlaubte Formate
- ✅ Fehlerbehandlung bei korrupten Daten

## Deployment

### Production Checklist
- [ ] Modell vorab herunterladen (nicht zur Laufzeit)
- [ ] Cache-Verzeichnis konfigurieren
- [ ] Timeout für Inference setzen
- [ ] Logging aktivieren
- [ ] Memory-Limits prüfen

### Docker
Füge zum Dockerfile hinzu:
```dockerfile
# KI-Dependencies installieren
RUN pip install transformers torch numpy

# Modell vorab herunterladen (optional)
RUN python -c "from transformers import AutoImageProcessor, AutoModelForImageClassification; \
    AutoImageProcessor.from_pretrained('dima806/dog_breed_image_detection'); \
    AutoModelForImageClassification.from_pretrained('dima806/dog_breed_image_detection')"
```

### Umgebungsvariablen
```bash
# Optional: Cache-Verzeichnis für Modelle
export TRANSFORMERS_CACHE=/path/to/cache

# Optional: Offline-Modus (Modelle müssen vorher geladen sein)
export TRANSFORMERS_OFFLINE=1
```
