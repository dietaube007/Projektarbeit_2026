# KI-Rassenerkennung

## Überblick

Die KI-Rassenerkennung hilft dir beim Erstellen einer Fundtier-Meldung, wenn du die Rasse des gefundenen Tieres nicht kennst. Die KI analysiert das hochgeladene Foto und schlägt eine mögliche Tierart und Rasse vor.

## Wann ist die Funktion verfügbar?

Die KI-Rassenerkennung ist **nur für Fundtiere** verfügbar, da Besitzer vermisster Tiere in der Regel die Rasse ihres Haustieres bereits kennen.

Die Funktion wird nur angezeigt, wenn du:
- Eine Meldung für ein **Fundtier** erstellst
- Ein **Foto hochgeladen** hast

## So funktioniert's

### 1. Foto hochladen
Lade zuerst ein Foto des gefundenen Tieres hoch.

### 2. KI-Erkennung starten
Klicke auf den Button **"🤖 KI-Rassenerkennung starten"**.

### 3. Einverständnis geben
Ein Dialog erscheint mit folgenden Informationen:
- Das Bild wird lokal durch eine KI analysiert
- Das Bild wird nicht an externe Dienste gesendet
- Die Erkennung ist nur ein Vorschlag ohne Garantie
- Du kannst den Vorschlag ablehnen

Klicke auf **"Akzeptieren & Starten"**, um fortzufahren.

### 4. Ergebnis prüfen
Die KI analysiert das Bild und zeigt dir:
- **Tierart** (z.B. Hund oder Katze)
- **Rasse** (z.B. Golden Retriever, Britisch Kurzhaar)
- **Konfidenz** (wie sicher sich die KI ist)

Ein **Hinweis** erinnert dich daran, dass dies nur ein Vorschlag ist.

### 5. Entscheiden
Du hast zwei Möglichkeiten:

#### ✅ Übernehmen
- Die erkannte Tierart wird automatisch ausgewählt
- Die erkannte Rasse wird im Rassen-Dropdown ausgewählt
- Ein Hinweis mit den KI-Erkennungsdaten wird in die "Beschreibung & Merkmale" eingefügt

#### ❌ Ablehnen
- Der Vorschlag wird verworfen
- Du kannst die Daten manuell eingeben

## Unterstützte Tiere

Die KI-Erkennung funktioniert derzeit für:
- **Hunde** (verschiedene Rassen)
- **Katzen** (verschiedene Rassen)

Kleintiere werden derzeit nicht unterstützt.

## Wichtige Hinweise

### ⚠️ Keine Garantie
Die KI-Erkennung ist **nicht fehlerfrei**. Die vorgeschlagene Rasse kann falsch sein. Nutze sie als Hilfsmittel, nicht als absolute Wahrheit.

### 📸 Tipps für bessere Ergebnisse
- Verwende ein **klares, gut beleuchtetes** Foto
- Das Tier sollte **vollständig sichtbar** sein
- **Frontal- oder Seitenansicht** funktioniert am besten
- Vermeide **unscharfe oder zu dunkle** Bilder

### 🔒 Datenschutz
- Die Analyse erfolgt **lokal** auf dem Server
- Das Bild wird **nicht an externe KI-Dienste** gesendet
- Deine Privatsphäre ist geschützt

### ❓ Bei Unsicherheit
Wenn die KI das Tier nicht sicher erkennen kann oder du dir unsicher bist:
- Versuche ein **anderes Foto**
- Trage die Daten **manuell** ein
- Kontaktiere ein **Tierheim** und beschreibe das Tier

## Fehlerbehandlung

### "Kein Foto"
Du musst zuerst ein Foto hochladen, bevor du die KI-Erkennung starten kannst.

### "Nur für Fundtiere"
Die Funktion ist nur für gefundene Tiere verfügbar. Bei vermissten Tieren wird angenommen, dass du die Rasse bereits kennst.

### "Erkennung fehlgeschlagen"
Die KI konnte das Tier nicht sicher erkennen. Mögliche Gründe:
- Das Foto ist zu unscharf
- Das Tier ist nicht vollständig sichtbar
- Die Beleuchtung ist zu schlecht
- Es handelt sich um eine sehr seltene Rasse

**Lösung**: Versuche ein anderes Foto oder trage die Daten manuell ein.

## Modell-Information

Die KI verwendet ein vortrainiertes Machine-Learning-Modell, das auf tausenden von Tier-Bildern trainiert wurde. Beim ersten Start der Anwendung wird das Modell automatisch heruntergeladen (~100 MB).
