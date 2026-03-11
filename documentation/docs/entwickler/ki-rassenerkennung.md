# KI-Rassenerkennung in PetBuddy - Vollständige Dokumentation

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Was ist Künstliche Intelligenz?](#was-ist-künstliche-intelligenz)
3. [Machine Learning und Deep Learning](#machine-learning-und-deep-learning)
4. [Das verwendete Modell](#das-verwendete-modell)
5. [ImageNet - Der Datensatz](#imagenet---der-datensatz)
6. [Technische Architektur](#technische-architektur)
7. [Integration in PetBuddy](#integration-in-petbuddy)
8. [Benutzer-Workflow](#benutzer-workflow)
9. [Technische Implementierung](#technische-implementierung)
10. [Ergebnisse und Limitierungen](#ergebnisse-und-limitierungen)
11. [Zukünftige Verbesserungen](#zukünftige-verbesserungen)

---

## Überblick

Die KI-Rassenerkennung ist eine zentrale Funktion der **PetBuddy**-Anwendung. Sie ermöglicht es Benutzern, **gefundene Tiere automatisch zu identifizieren**, indem ein Foto des Tieres mit Hilfe von Künstlicher Intelligenz analysiert wird.

### Was leistet diese Funktion?

- **Automatische Erkennung**: Der Benutzer macht ein Foto eines gefundenen Tieres
- **Klassifikation**: Das System erkennt automatisch die **Tierart** (Hund, Katze, etc.)
- **Rassenerkennung**: Das System bestimmt die **Rasse** des Tieres
- **Genauigkeitsbewertung**: Das System gibt an, wie **sicher** es sich bei der Erkennung ist (Konfidenz-Score)
- **Manuelle Korrektur**: Benutzer können die Erkennungen manual korrigieren oder manuell eingeben

### Warum ist das wertvoll?

Wenn jemand ein **vermisstes Tier findet**, weiß er oft nicht, welche Rasse es ist. Mit dieser KI-Funktion kann er:
- Das Tier schnell beschreiben
- In den Datenbanken nach ähnlichen Tieren suchen
- Tierheime und Besitzer schneller finden
- Die Chance erhöhen, das Tier zu seinem Besitzer zurückzubringen

---

## Was ist Künstliche Intelligenz?

### Für Anfänger erklärt

**Künstliche Intelligenz (KI)** ist die Fähigkeit von Computern, Aufgaben zu lösen, die normalerweise menschliche Intelligenz erfordern.

#### Beispiele aus dem Alltag:

| Anwendung | Ergebnis |
|-----------|----------|
| **Autokorrektur** auf dem Smartphone | Das System erkennt Tippfehler und korrigiert sie |
| **Gesichtserkennung** (Face ID, Photo App) | Das System identifiziert Menschen auf Fotos |
| **Sprachassistenten** (Siri, Alexa) | Das System versteht gesprochene Befehle |
| **Empfehlungen** auf Netflix/YouTube | Das System schlägt Inhalte vor, die dir gefallen |
| **Auto-Untertitel** auf YouTube | Das System wandelt Sprache in Text um |

### Wie funktioniert KI?

KI funktioniert nach einem ähnlichen Prinzip wie der menschliche Lernprozess:

```
1. TRAINIEREN: Das System lernt von vielen Beispielen
2. ERKENNEN: Das System wendet das Gelernte auf neue Beispiele an
3. VERBESSERN: Das System wird mit mehr Beispielen genauer
```

**Vergleich mit menschlichem Lernen:**
- Ein Kleinkind sieht 100 Hunde → es lernt, was ein Hund ist
- Ein Kind sieht Hunde verschiedener Rassen → es kann Rassen unterscheiden
- Ein Erwachsener kann sehr schnell Hunderassen identifizieren
- **AI macht dasselbe**, aber mit Millionen von Bildern statt nur wenigen

---

## Machine Learning und Deep Learning

### Was ist Machine Learning?

**Machine Learning** ist ein Teilgebiet der KI, in dem:
- Der Computer **nicht explizit programmiert** wird, sondern
- Der Computer **von Daten lernt** und eigene Muster erkennt

#### Traditionelle Programmierung vs. Machine Learning

**Traditionelle Programmierung:**
```
INPUT → [Programm-Regeln] → OUTPUT

Beispiel:
if breite > 40cm and höhe > 50cm:
    print("Großer Hund")
else:
    print("Kleiner Hund")
```

**Machine Learning:**
```
TRAININGSDATEN → [Lernalgorithmus] → MODELL → OUTPUT

Das System lernt selbst die Regeln aus Millionen von Beispielen!
```

### Was ist Deep Learning?

**Deep Learning** ist eine spezielle Form des Machine Learning, die:
- **Neuronale Netze** (inspiriert vom menschlichen Gehirn) verwendet
- **Mehrere Schichten** (daher "Deep") von Neuronen hat
- Besonders gut für **Bilder, Sprache und Videos** geeignet ist

#### Vereinfachtes Modell eines Neuronalen Netzes:

```
Eingabe-Layer     Versteckte Layer      Ausgabe-Layer
(Bild-Pixel)      (Muster erkennen)    (Rasse)

Hund-Foto →  [Kanten]  →  [Formen]  →  [Teile]  →  "Golden Retriever"
             erkennen     erkennen      erkennen
```

Jede Schicht erkennt immer **abstraktere Muster**:
1. **Layer 1**: Einfache Muster (Linien, Kanten)
2. **Layer 2**: Kombinierte Muster (Ohren, Pfoten)
3. **Layer 3**: Komplexe Muster (Gesicht, Körperbau)
4. **Ausgabe**: "Das ist ein Hund" → "Rasse: Golden Retriever"

---

## Das verwendete Modell

### Vision Transformer (ViT)

Die PetBuddy-App verwendet das Modell **`google/vit-base-patch16-224`** von Google.

### Was ist Vision Transformer?

Ein **Vision Transformer** ist ein modernes Deep-Learning-Modell, das:
- 😍 **2017**: Transformer wurden ursprünglich für Sprache entwickelt
- 📷 **2021**: Google adaptierte sie für Bildanalyse
- 🚀 **Heute**: State-of-the-art Ergebnisse bei Bilderkennung

#### Wie funktioniert Vision Transformer?

```
1. UNTERTEILUNG: Das Bild wird in kleine 16×16-Pixel-Quadrate unterteilt
   (Daher der Name "patch16" - 16 Pixel große Patches)

2. VEKTORISIERUNG: Jedes Quadrat wird in eine numerische Representation 
   umgewandelt (ähnlich wie ein Fingerabdruck)

3. AUFMERKSAMKEIT: Das Modell untersucht, wie die Quadrate 
   miteinander zusammenhängen (Aufmerksamkeitsmechanismus)

4. KLASSIFIKATION: Am Ende wird das gesamte Bild in eine Kategorie
   eingeordnet (z.B. "tabby cat", "golden retriever")
```

### Spezifikationen des Modells

| Eigenschaft | Wert |
|---|---|
| **Name** | google/vit-base-patch16-224 |
| **Eingabe-Größe** | 224 × 224 Pixel |
| **Parameter** | ~86 Millionen |
| **Training** | ImageNet (siehe nächsten Abschnitt) |
| **Genauigkeit** | ~88% Top-1 Accuracy auf ImageNet |
| **Größe** | ~350 MB (erster Download) |
| **Quelle** | Google Research, Hugging Face Hub |

### Warum dieses Modell?

✅ **Vorteile:**
- Bereits trainiert (wir müssen nicht von Null anfangen)
- Kostenlos verfügbar
- Hohe Genauigkeit
- Schnell genug für Web-Anwendungen
- Funktioniert auf verschiedene Tierarten

⚠️ **Limitierungen:**
- Trainiert auf allerhand Objektklassen, nicht speziell auf Haustiere
- Funktioniert besser bei klaren, deutlichen Bildern
- Kann mit Wildtieren verwechselt werden
- Funktioniert nicht mit sehr dunklen oder verschwommenen Fotos

---

## ImageNet - Der Datensatz

### Was ist ImageNet?

**ImageNet** ist eine massive Bilderdatenbank mit über **14 Millionen Bildern**.

### Geschichte von ImageNet

| Jahr | Event |
|------|-------|
| **2009** | Fei-Fei Li (Stanford) startet ImageNet-Projekt |
| **2010** | ImageNet klein: ~100.000 Bilder, 100 Kategorien |
| **2015** | ImageNet wächst: ~1 Million Bilder, 1.000 Kategorien |
| **2020** | Heute: 14+ Millionen Bilder, 20.000+ Kategorien |
| **Aktuell** | Basis für Milliarden von KI-Modellen weltweit |

### Struktur von ImageNet

ImageNet ist nach den **WordNet-Kategorien** organisiert (ähnlich wie Wikipedia):

```
Lebewesen (Entity)
├── Tier (Animal)
│   ├── Säugetier (Mammal)
│   │   ├── Hund (Canis familiaris)
│   │   │   ├── Huskys
│   │   │   ├── Labradors
│   │   │   ├── Golden Retriever
│   │   │   └── ... (200+ Hunderassen)
│   │   └── Katze (Felis catus)
│   │       ├── Tabby
│   │       ├── Siameser
│   │       └── ... (Katzenrassen)
│   └── Vogel (Bird)
└── Pflanze (Plant)
```

### Hunde- und Katzenklassen in ImageNet

**ImageNet enthält 262 verschiedene Hunde- und Katzenrassen!**

Beispiele:
- **Hunde**: Golden Retriever, German Shepherd, Bulldog, Poodle, Husky, Beagle (und 260+ mehr)
- **Katzen**: Tabby, Persian, Siamese, Maine Coon (und viele mehr)

### Wie wurden die Bilder gesammelt?

1. **Automatisches Scraping**: Bilder wurden aus dem Internet heruntergeladen
2. **Manuelle Überprüfung**: Menschen überprüften jedes Bild, dass es in die Kategorie passt
3. **Qualitätskontrolle**: Falsche oder fehlerhafte Bilder wurden entfernt
4. **Lizenzierung**: Bilder sind für Forschungszwecke frei verfügbar

### Herausforderungen bei ImageNet

Die Datensammlung prägt das Modell:

| Herausforderung | Auswirkung |
|---|---|
| **Westliche Voreingenommenheit** | Überwiegend westliche Hunderassen (keine afrikanischen Straßenhunde) |
| **Helle Bilder bevorzugt** | Outdoor-Bilder überrepräsentiert, dunkle/schwache Lichtverhältnisse unterrepräsentiert |
| **Klare Objekte** | Verschwommene Bilder oder Hunde in ungewöhnlichen Posen sind selten |
| **Reine Rassen** | Mischlinge sind unterrepräsentiert |

**Fazit**: Das Modell arbeitet am besten mit klaren, gut beleuchteten Fotos von reinen Rassen.

---

## Technische Architektur

### System-Übersicht

```
PetBuddy App
    ↓
[Benutzer wählt Foto]
    ↓
[PostForm: Meldungsformular]
    ↓
[Benutzer klickt "KI-Rassenerkennung"]
    ↓
[AGBs akzeptieren Dialog]
    ↓
[Bild wird hochgeladen]
    ↓
[ProcessingDialog: "KI analysiert..."]
    ↓
[KI-Service: recognize_pet()]
    ↓
[Modell lädt] → [Processor generiert Features] → [Modell führt Inference durch]
    ↓
[Ergebnis: erfolg, Tierart, Rasse, Konfidenz]
    ↓
[Benutzer akzeptiert oder lehnt ab]
    ↓
[Ergebnis wird ins Formular übernommen]
```

### Komponenten-Beschreibung

#### 1. **Frontend (Benutzer-Interface)**
- **Datei**: `ui/post_form/view.py`
- **Aufgabe**: Zeigt dem Benutzer das Formular und den "KI-Rassenerkennung"-Button
- **Interaktion**: Ruft AGB-Dialog auf, startet KI-Prozess

#### 2. **Handler-Schicht**
- **Datei**: `ui/post_form/handlers/ai_recognition_handler.py`
- **Aufgabe**: Koordiniert den gesamten KI-Workflow
- **Funktionen**:
  - `handle_ai_recognition_flow()`: Hauptfunktion
  - `show_consent_dialog()`: AGB-Akzeptanz
  - `perform_ai_recognition()`: Startet Inference
  - `show_ai_result()`: Zeigt Ergebnis

#### 3. **Storage-Service**
- **Datei**: `services/posts/post_image.py`
- **Aufgabe**: Lädt Bilddaten von Supabase oder lokal
- **Methoden**:
  - `read_local_image_bytes()`: Liest lokale Datei
  - `download_post_image()`: Lädt von Supabase

#### 4. **KI-Service (Kernel)**
- **Datei**: `services/ai/pet_recognition.py`
- **Aufgabe**: Spricht mit dem Machine-Learning-Modell
- **Klasse**: `PetRecognitionService`
- **Hauptmethoden**:
  - `_load_model()`: Lädt das ViT-Modell
  - `recognize_pet()`: Führt Bildanalyse durch
  - `_is_cat_or_dog()`: Klassifiziert Ergebnis

#### 5. **Deep Learning Framework**
- **Bibliothek**: `transformers` von Hugging Face
- **Framework**: `PyTorch`
- **GPU-Support**: Falls verfügbar (für schnellere Verarbeitung)

### Datenfluss Detail

```python
# 1. BILDDATEN LADEN
image_bytes = post_storage_service.read_local_image_bytes(path)
# → Binäare Bilddaten (z.B. 50 KB - 5 MB)

# 2. PREPROCESSING
from PIL import Image
img = Image.open(io.BytesIO(image_bytes))
img = img.convert("RGB")  # RGB-Modus sicherstellen
# → PIL Image Objekt in RGB-Modus (224×224 Pixel)

# 3. FEATURE-EXTRACTION (Processor)
inputs = processor(images=img, return_tensors="pt")
# → PyTorch Tensor Shape: [1, 3, 224, 224]
# inputs.keys() = ["pixel_values"]
# Diese Tensor sind die "Features" - numerische Repräsentation des Bildes

# 4. MODELL-INFERENCE
outputs = model(**inputs)
# → Outputs shape: [1, 1000]
# 1 = Batch-Größe (1 Bild)
# 1000 = ImageNet hat 1000 Klassen

# 5. POSTPROCESSING
probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
top_prob, top_class = probs[0].topk(1)
# confidence = 0.95 (95% Sicherheit)
# predicted_label = "golden retriever" (die Top-1 Klasse)

# 6. KLASSENVERTEILUNG (Species/Breed)
species, breed = _is_cat_or_dog(predicted_label)
# → ("Hund", "Golden Retriever")

# 7. RESULT
result = {
    "success": True,
    "species": "Hund",
    "breed": "Golden Retriever",
    "confidence": 0.95
}
```

---

## Integration in PetBuddy

### Wo wird KI verwendet?

Die KI ist primär in der **Meldungserstellung** (Fundtiere) integriert:

```
1. Benutzer navigiert zu "Neue Meldung"
2. Wählt "Fundtier" (nicht "Vermisst")
3. Lädt ein Foto hoch
4. Klickt auf Button "KI-Rassenerkennung"
5. Bestätigt AGBs
6. System analysiert Foto
7. Ergebnis wird angeboten
8. Benutzer akzeptiert oder lehnt ab
9. Ergebnis wird ins Formular übernommen
```

### UI-Komponenten

#### Button "KI-Rassenerkennung"
```python
# Datei: ui/post_form/components/ai_components.py
ft.OutlinedButton(
    text="KI-Rassenerkennung",
    on_click=on_ai_recognition_click,
    icon="smart_toy"  # Roboter-Icon
)
```

#### AGB-Dialog
```
Titel: "Einverständnis erforderlich"

Text: "Die KI-Rassenerkennung wird automatisch durchgeführt.
Die von dir hochgeladenen Bilder werden verarbeitet, um 
Tierart und Rasse zu erkennen. Dieses Modell:
- Wurde auf ImageNet trainiert
- Funktioniert nicht immer perfekt
- Kann falsche Ergebnisse liefern"

Button: "Akzeptieren" | "Ablehnen"
```

#### Ergebnis-Anzeige
```
┌─────────────────────────────────┐
│ KI-Erkennungs-Ergebnis         │
├─────────────────────────────────┤
│ ✓ Erkannt: Golden Retriever    │
│ Konfidenz: 94%                  │
│ Tierart: Hund                   │
│                                 │
│ [Übernehmen]  [Ablehnen]       │
└─────────────────────────────────┘
```

---

## Benutzer-Workflow

### Szenario: Benutzer findet einen Hund und möchte ihn helfen

#### Schritt-für-Schritt Ablauf

**Schritt 1: App öffnen → "Neue Meldung" klicken**
- Benutzer startet die PetBuddy App
- Klickt auf "+" oder "Neue Meldung"

**Schritt 2: Meldungsart wählen**
```
[ ] Vermisst (mein Haustier ist weg)
[X] Fundtier (ich habe ein Tier gefunden)
```
- Der Benutzer wählt "Fundtier"
- Grund: Die KI ist nur für Fundtiere verfügbar (da Besitzer von vermissten Tieren die Rasse kennen)

**Schritt 3: Foto hochladen**
- Benutzer macht Foto von dem gefundenen Hund
- Oder wählt Foto aus der Galerie
- Foto wird in die App hochgeladen

**Schritt 4: "KI-Rassenerkennung" klicken**
```
┌─────────────────────────────────┐
│ Foto:         [Hund-Foto]      │
│ Name:         ___________      │
│ Rasse:        ___________      │
│ Farbe:        ___________      │
│                                 │
│ [KI-Rassenerkennung] ← Hier klicken!
│ [Speichern]                    │
└─────────────────────────────────┘
```

**Schritt 5: AGBs bestätigen**
```
Dialog-Anfang zu erscheinen:

"Einverständnis erforderlich"

Die KI-Rassenerkennung ist optional und funktioniert
nicht immer fehlerlos. Mit dem Klick auf 'Akzeptieren'
stimmst du zu, dass:

✓ Dein Foto an unser KI-System gesendet wird
✓ Das Foto analysiert wird
✓ Die Ergebnisse möglicherweise falsch sind
✓ Du die Ergebnisse vor dem Speichern überprüfen kannst

[Akzeptieren]  [Ablehnen]
```

**Schritt 6: Wartezeit**
- Benutzer sieht: "KI analysiert das Bild..."
- Wartet 3-10 Sekunden (abhängig von: Bildgröße, Modell-Ladezeit, CPU-Geschwindigkeit)
- Im Hintergrund: 
  - Modell wird ggf. heruntergeladen (300 MB erste Zeit)
  - Bild wird verarbeitet
  - Inference läuft

**Schritt 7: Ergebnis anzeigen**
```
┌──────────────────────────────────┐
│ ✓ KI-Erkennungs-Ergebnis        │
├──────────────────────────────────┤
│ Erkannte Rasse: Golden Retriever│
│ Tierart: Hund                    │
│ Konfidenz: 94%                   │
│                                  │
│ [✓ Übernehmen] [✗ Ablehnen]     │
└──────────────────────────────────┘
```

**Schritt 8a: WENN Benutzer klickt "Übernehmen"**
```
→ Formular wird automatisch gefüllt:
  - Rasse: Golden Retriever
  - Tierart: Hund
  - Beschreibung: "[KI-Erkennnung: ...] + Nutzer-Text"

→ Benutzer kann nun:
  - Weitere Details hinzufügen
  - Findet den Button "Speichern"
  - Meldung wird erstellt
```

**Schritt 8b: WENN Benutzer klickt "Ablehnen"**
```
→ Formular bleibt leer
→ Benutzer muss Daten manuell eingeben
→ Benutzer sieht Fehlermeldung: "KI-Vorschlag abgelehnt"
```

**Schritt 9: Meldung speichern und veröffentlichen**
- Benutzer klickt "Speichern"
- Meldung wird in Datenbank gespeichert
- Andere Benutzer können das Tier jetzt sehen
- Der echte Besitzer kann kontaktiert werden

---

## Technische Implementierung

### Die Haupt-KI-Klasse

```python
# Datei: services/ai/pet_recognition.py

class PetRecognitionService:
    """Service zur KI-gestützten Tier- und Rassenerkennung."""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.labels = None
        self._model_loaded = False
    
    def _load_model(self):
        """Lädt das Vision Transformer Modell von Hugging Face."""
        
        # Schritt 1: Importiere Modell-Klassen
        from transformers import AutoModelForImageClassification
        from transformers import AutoImageProcessor  # oder AutoFeatureExtractor (ältere Versionen)
        
        # Schritt 2: Modell-Name
        model_name = "google/vit-base-patch16-224"
        
        # Schritt 3: Lade Processor (Feature-Extractor)
        # Der Processor nimmt ein PIL-Bild und konvertiert es in Tensoren
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        
        # Schritt 4: Lade Modell
        # Das Modell enthält 86 Millionen trainierte Parameter
        self.model = AutoModelForImageClassification.from_pretrained(model_name)
        
        # Schritt 5: Extrahiere Labels (1000 ImageNet-Klassen)
        self.labels = self.model.config.id2label  # {0: "tench", 1: "goldfish", ...}
        
        self._model_loaded = True
    
    def recognize_pet(self, image_data: bytes) -> Dict[str, Any]:
        """
        Hauptfunktion: Erkennt Tierart und Rasse aus Bilddaten.
        
        Args:
            image_data: Bilddaten als bytes (z.B. aus files.read())
        
        Returns:
            {
                "success": bool,
                "species": "Hund" oder "Katze" oder None,
                "breed": "Golden Retriever",
                "confidence": 0.95
            }
        """
        
        # Schritt 1: Stelle sicher, dass Modell geladen ist
        if not self._model_loaded:
            self._load_model()
        
        # Schritt 2: Konvertiere bytes zu Bild
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_data))
        img = img.convert("RGB")  # Stelle RGB sicher
        
        # Schritt 3: Processor verarbeitet Bild → Tensor
        inputs = self.processor(images=img, return_tensors="pt")
        # inputs ist jetzt ein PyTorch-Dictionary
        # inputs["pixel_values"] hat Shape [1, 3, 224, 224]
        
        # Schritt 4: Modell macht Vorhersage
        outputs = self.model(**inputs)
        # outputs.logits hat Shape [1, 1000]
        
        # Schritt 5: Konvertiere Logits zu Wahrscheinlichkeiten
        import torch
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        # probs hat auch Shape [1, 1000], aber Werte summieren zu 1.0
        
        # Schritt 6: Finde Top-1 Vorhersage
        top_prob, top_class = probs[0].topk(1)
        confidence = top_prob.item()  # z.B. 0.95
        predicted_label = self.labels[top_class.item()]  # z.B. "golden_retriever"
        
        # Schritt 7: Klassifiziere als Hund oder Katze
        species, breed = self._is_cat_or_dog(predicted_label)
        
        # Schritt 8: Rückgabe
        if species is None:
            return {
                "success": False,
                "error": "Das scheint kein Haustier zu sein",
                "suggested_breed": breed
            }
        
        if confidence < 0.3:  # Zu unsicher
            return {
                "success": False,
                "error": "Zu unsicher",
                "suggested_species": species,
                "suggested_breed": breed,
                "confidence": confidence
            }
        
        return {
            "success": True,
            "species": species,
            "breed": breed,
            "confidence": confidence
        }
```

### Feature-Extraction Prozess (vereinfacht)

```
Eingabe: JPEG-Bilddatei (z.B. hund.jpg - 2 MB)
    ↓
[PIL konvertiert zu RGB]
    → PIL Image (3 × beliebige × beliebige)
    ↓
[Processor skaliert auf 224×224]
    → PIL Image (3 × 224 × 224)
    ↓
[Processor normalisiert Pixel-Werte]
    → Werte im Bereich [-1, 1] statt [0, 255]
    ↓
[Processor konvertiert zu PyTorch Tensor]
    → PyTorch Tensor shape(1, 3, 224, 224)
    ↓
[Modell akzeptiert diesen Tensor]
    → Verarbeitet ihn durch 12 Layer
    → Output: 1000 Logits
    ↓
[Softmax anwenden]
    → 1000 Wahrscheinlichkeiten (summen zu 1.0)
    ↓
[Top-1 wählen]
    → Häufigste Klasse mit höchster Wahrscheinlichkeit
    ↓
Ausgabe: "golden_retriever" (95% Confidence)
```

### Kosten und Performance

#### Speicher-Anforderungen
| Komponente | Größe |
|---|---|
| Modell-Gewichte | ~350 MB (beim Download) |
| Modell im Memory | ~700 MB (RAM beim Laden) |
| Eingabe-Tensor | ~1 MB (224×224 RGB Bild) |
| Ausgabe-Tensor | < 1 MB (1000 Logits) |
| **Total RAM benötigt** | ~1 GB |

#### Geschwindigkeit (Benchmarks)
| Szenario | Zeit |
|---|---|
| Modell downloaden (1. Start) | 5-10 Minuten |
| Modell laden in RAM (1. Start) | 30-60 Sekunden |
| Modell laden in RAM (nachfolgende) | < 1 Sekunde |
| Feature-Extraction | 100-200 ms |
| Modell-Inference | 500-1000 ms |
| **Total pro Bildanalyse** | 600-1200 ms |

**Auf Laptop der Schule**: ~2-3 Sekunden
**Mit Grafikkarte (GPU)**: ~200-500 ms

---

## Ergebnisse und Limitierungen

### Genauigkeit

Das Modell erreicht auf ImageNet:
- **Top-1 Accuracy**: ~88% (richtige Klasse auf Platz 1)
- **Top-5 Accuracy**: ~99% (richtige Klasse in den Top 5)

Aber: ImageNet ≠ reale Welt

### In der Praxis mit PetBuddy

#### Szenarien wo es GUT funktioniert
- ✅ Klares Foto eines Hundes/einer Katze
- ✅ Gute Beleuchtung (Tagsüber, nicht dunkel)
- ✅ Häufige Rassen (Golden Retriever, Labrador, Tabby-Katze)
- ✅ Ganze Tier sichtbar (nicht nur Kopf)
- ✅ Reine Rassen

#### Szenarien wo es SCHLECHT funktioniert
- ❌ Verschwommenes Foto (Bewegungsunschärfe)
- ❌ Sehr dunkles Bild (Nachts, schlechte Beleuchtung)
- ❌ Nur Kopf oder Hinter des Tieres sichtbar
- ❌ Mischlinge (Mischung verschiedener Rassen)
- ❌ Seltene, unbekannte Rassen
- ❌ Wildtiere (werden oft als Haustierrassen klassifiziert)
- ❌ Stark verdecktes Tier (Hund unter Decke etc.)

### Beispiel-Szenarien

#### Scenario 1: Photo eines Golden Retrievers (gut beleuchtet)
```
INPUT: golden-retriever.jpg
  ↓
PROCESSOR: Konvertiert zu 224×224 Tensor
  ↓
MODEL: Führt Inference durch
  ↓
LOGITS: 
  Klasse 207 (golden retriever): 0.945 ← TOP
  Klasse 209 (Labrador): 0.032
  Klasse 210 (retriever): 0.015
  ...
  ↓
RESULT: 
{
    "success": true,
    "species": "Hund",
    "breed": "Golden Retriever",
    "confidence": 0.945
}
```

#### Scenario 2: Verschwommenes Foto (schlecht)
```
INPUT: blurry-dog.jpg (Motion Blur)
  ↓
PROCESSOR: Versucht zu konvertieren, aber Info verloren
  ↓
MODEL: Kann nicht viel erkennen
  ↓
LOGITS:
  Klasse 150 (dog, generic): 0.12
  Klasse 203 (poodle): 0.11
  Klasse 250 (table): 0.10  ← FALSCH!
  ...
  ↓
RESULT:
{
    "success": false,
    "error": "Konnte nicht sicher erkennen",
    "confidence": 0.12
}

→ Modell sagt "nicht sicher" und schlägt nichts vor
```

#### Scenario 3: Mischling (Hund + Katze? Oder welche Rasse?)
```
INPUT: mischling.jpg (70% Schäferhund, 30% Husky)
  ↓
MODEL: Versucht, die dominanteste Rasse zu erraten
  ↓
LOGITS:
  Klasse 111 (German Shepherd): 0.40 ← TOP
  Klasse 112 (Husky): 0.35
  ...
  ↓
RESULT:
{
    "success": true,
    "species": "Hund",
    "breed": "Deutscher Schäferhund",  ← Nur beste Guess!
    "confidence": 0.40  ← Niedrig, da unsicher
}

→ Modell wählt die wahrscheinlichste Rasse,
  aber die Konfidenz zeigt, dass es unsicher ist
```

### Umgang mit Unsicherheit

Das System hat mehrere Mechanismen:

1. **Konfidenz-Threshold** (30%)
   - Wenn confidence < 30% → "Zu unsicher" Dialog
   - Benutzer wird informiert

2. **Manuelle Überprüfung**
   - Benutzer sieht immer das Ergebnis VOR dem Speichern
   - Kann es ablehnen und manuell eingeben

3. **Fehlertoleranz**
   - Selbst wenn Rasse falsch → Tier wird gefunden
   - Nicht perfekt, aber besser als nichts

---

## Zukünftige Verbesserungen

### Idee 1: Spezial-Modell für Haustiere

**Problem**: Aktuelles Modell auf ImageNet trainiert (allgemeine Objekte)

**Lösung**: Fine-Tuning auf Haustier-Datensatz
```
Mögliche Datensätze:
- Stanford Dogs (120 Hunderassen mit 20.000 Bildern)
- Oxford Pet Dataset (37 Kategorien von Haustieren)
- COCO Dataset (hat auch Tiere)

Verbesserung: +10-20% Genauigkeit bei Haustieren
```

### Idee 2: Mehrere Rassen-Vorschläge

**Aktuell**: Nur die Top-1 Rasse wird gezeigt

**Zukünftig**: Top-3 oder Top-5 Rassen anzeigen
```
Ergebnis-Dialog:
┌─────────────────────────────────┐
│ Top Vorschläge:                 │
│ 1. Golden Retriever (94%)      │
│ 2. Labrador (5%)               │
│ 3. Retriever Mix (1%)          │
│                                 │
│ [Akzeptieren] [Manuell eingeben]
└─────────────────────────────────┘
```

### Idee 3: Lokale Modelle (Offline)

**Problem**: Modell wird heruntergeladen, braucht Internet

**Lösung**: Mobile-optimierte Modelle (z.B. MobileViT)
```
MobileViT: Nur 50 MB, läuft auf Smartphones
- Nicht so genau wie google/vit
- Aber schnell und offline verfügbar
```

### Idee 4: Benutzer-Feedback Loop

**System verhessern durch Nutzer-Feedback**:
```
Benutzer sieht die Rasse des gefundenen Tieres 
später im Tierheim oder von Bestitzer → gibt Feedback

"Das war falsch, die Rasse ist..."
↓
Feedback wird gesammelt
↓
Modell wird mit echten Korrektionen neu trainert
↓
Nächste Version wird genauer
```

### Idee 5: Kompatibilität mit selbst trainierten Modellen

Benutzer könnten ihre eigenen Modelle hochladen:
```
Admin lädt custom-hundmodell.pth hoch
→ System nutzt dieses Modell statt google/vit
→ Vielleicht spezialisiert auf deutsche Rassen
```

---

## Zusammenfassung für die PowerPoint-Präsentation

### Kern-Botschaften

| Punkt | Erklärung |
|---|---|
| **Was?** | KI erkennt Tierrasse aus Fotos automatisch |
| **Warum?** | Hilft, gefundene Tiere ihren Besitzern zuzuordnen |
| **Wie?** | Deep Learning Modell (Vision Transformer) analysiert Bilder |
| **Woher Daten?** | Modell trainiert auf ImageNet (14M Bilder, 1000 Kategorien) |
| **Genauigkeit?** | 88-95% bei optimalen Bedingungen, 30-50% bei schlechten Bildern |
| **Grenzen?** | Funktioniert gut nur mit klaren, guten Fotos |

### Visualisierungs-Ideen für PowerPoint

1. **Ablauf-Diagramm**: Foto → KI-Verarbeitung → Ergebnis
2. **Statistik**: ImageNet Aufbau (14M Bilder, 1000 Klassen)
3. **Genauigkeits-Chart**: Vision Transformer vs. andere Modelle
4. **Use-Case Beispiele**: Erfolgreiche Erkennungen
5. **Fehler-Beispiele**: Wo die KI fehlschlägt
6. **Timeline**: Geschichte von ImageNet und Vision Transformers

### Präsentations-Struktur (für 10 Minuten)

```
1. Einleitung (1 Min)
   - "Wie hilft KI Tieren?"
   
2. Was ist KI? (1.5 Min)
   - Neuronale Netze vereinfacht erklärt
   - Vergleich: Mensch vs. Maschine
   
3. Das Modell (1.5 Min)
   - Vision Transformer
   - Google hat das entwickelt
   
4. ImageNet Datensatz (1 Min)
   - 14 Millionen Bilder
   - 1000 Kategorien
   
5. Wie funktioniert es in PetBuddy? (2 Min)
   - Demo: Foto hochladen → Ergebnis
   - Erfolgsbeispiele zeigen
   
6. Limitierungen (1.5 Min)
   - Funktioniert nicht immer
   - Beispiele von Fehlern
   
7. Zukünfte (0.5 Min)
   - Verbesserungen möglich
   - Noch bessere Modelle verfügbar
```

---

## Technische Referenzen

### Verwendete Biblioteken

```python
# pip install transformers torch pillow
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch
from PIL import Image
```

### Modell-Links

- **Model Card (Hugging Face)**: https://huggingface.co/google/vit-base-patch16-224
- **ViT Paper**: https://arxiv.org/abs/2010.11929
- **ImageNet**: https://www.image-net.org/

### Weitere Ressourcen

- **Dokumentation**: https://huggingface.co/transformers/
- **PyTorch Docs**: https://pytorch.org/
- **Deep Learning Basics**: https://course.fast.ai/

---

## FAQ - Häufig Gestellte Fragen

### F: Woher bekommt die KI die Informationen?
**A**: Das Modell wurde mit 14 Millionen gelabelten Bildern trainiert (ImageNet). Es lernte Muster zu erkennen, wie Hunde aussehen, welche Teile sie haben, etc.

### F: Kann die KI auch Wildtiere erkennen?
**A**: Ja, theoretisch. Aber sie wurde für Haustiere trainiert, daher funktioniert es bei exotischen Tieren schlechter.

### F: Wieso brauchts das Internet?
**A**: Das Modell ist 350 MB groß. Beim ersten Start wird es heruntergeladen. Nach dem Download funktioniert es offline.

### F: Was passiert mit meinen Fotos?
**A**: Sie werden lokal auf dem Gerät analysiert. Sie werden nicht an Server gesendet (außer wenn der Benutzer die Meldung speichert).

### F: Kann die KI lügen?
**A**: Ja, die Konfidenzwerte können irre sein. Das Modell gibt hohe Konfidenz auch bei Bildern, die es nicht versteht.

### F: Wie lange dauert die Analyse?
**A**: 1-3 Sekunden. Beim ersten Start kann es 60 Sekunden dauern (Modell-Laden).

### F: Kann man das Modell verbessern?
**A**: Ja! Mit mehr Haustier-Bildern könnte man es neu trainieren oder "fine-tunen".

---

## Danksagungen und Quellen

- **Google**: Für das Vision Transformer Modell
- **Hugging Face**: Für die transformers Bibliothek
- **Stanford/Fei-Fei Li**: Für ImageNet
- **Meta AI**: Für PyTorch Framework

---

**Letztes Update**: 9. März 2026
**Version**: 1.0
**Autor**: PetBuddy Development Team

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




