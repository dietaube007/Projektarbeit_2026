"""Service für KI-gestützte Tier- und Rassenerkennung aus Bildern."""

from __future__ import annotations

import io
from typing import Optional, Dict, Tuple, Any
from PIL import Image

from utils.logging_config import get_logger

logger = get_logger(__name__)


class PetRecognitionService:
    """Service zur Erkennung von Tierarten und -rassen aus Bildern."""
    
    def __init__(self):
        """Initialisiert den Service und lädt das Modell."""
        self.model = None
        self.processor = None
        self.labels = None
        self._model_loaded = False
    
    def _load_model(self):
        """Lädt das Modell beim ersten Aufruf."""
        if self._model_loaded:
            return
        
        try:
            logger.info("=" * 60)
            logger.info("STARTE MODELL-LADEN")
            logger.info("=" * 60)
            
            from transformers import AutoModelForImageClassification
            logger.info("AutoModelForImageClassification importiert")

            try:
                # Neuere transformers-Versionen
                from transformers import AutoImageProcessor as ProcessorClass
                logger.info("AutoImageProcessor (neuere Version) importiert")
            except Exception as import_ex:
                logger.warning(f"AutoImageProcessor konnte nicht importiert werden: {import_ex}")
                # Fallback für ältere transformers-Versionen
                from transformers import AutoFeatureExtractor as ProcessorClass
                logger.info("AutoFeatureExtractor (Fallback) importiert")
            
            # Verwende ein stabiles, bewährtes Modell für Bildklassifikation
            # Dieses Modell ist nicht speziell für Haustiere, aber funktioniert zuverlässig
            model_name = "google/vit-base-patch16-224"
            
            logger.info("Lade KI-Modell für Bilderkennung...")
            logger.info(f"Modell: {model_name}")
            logger.info("Dies kann beim ersten Start einige Minuten dauern...")
            logger.info("Hinweis: Dies ist ein allgemeines Bilderkennungsmodell (ImageNet-basiert)")
            
            logger.info(f"Lade Processor ({ProcessorClass.__name__})...")
            self.processor = ProcessorClass.from_pretrained(model_name)
            logger.info(f"Processor geladen: {type(self.processor).__name__}")
            
            logger.info("Lade Modell...")
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            logger.info(f"Modell geladen: {type(self.model).__name__}")
            
            self.labels = self.model.config.id2label
            self._model_loaded = True
            logger.info(f"Labels geladen: {len(self.labels)} Klassen")
            logger.info("=" * 60)
            logger.info("MODELL-LADEN ERFOLGREICH")
            logger.info("=" * 60)
            
        except Exception as e:  # noqa: BLE001
            logger.error("=" * 60)
            logger.error("FEHLER BEIM MODELL-LADEN")
            logger.error("=" * 60)
            logger.error(f"Exception: {type(e).__name__}")
            logger.error(f"Nachricht: {str(e)}")
            logger.error("Details: ", exc_info=True)
            logger.error("=" * 60)
            # Setze Flag, dass Modell nicht verfügbar ist
            self._model_loaded = False
            raise RuntimeError(
                f"KI-Modell konnte nicht geladen werden.\n\n"
                f"Fehler: {type(e).__name__}: {str(e)}\n\n"
                "Mögliche Ursachen:\n"
                "- Keine Internetverbindung beim ersten Start\n"
                "- Hugging Face ist nicht erreichbar\n"
                "- Fehlende Abhängigkeiten (transformers, torch)\n\n"
                "Bitte trage die Rasse manuell ein."
            )
    
    def _preprocess_image(self, image_data: bytes) -> Image.Image:
        """Bereitet das Bild für die Verarbeitung vor."""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Konvertiere zu RGB falls notwendig
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            return img
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"Bild konnte nicht geladen werden: {e}")
    
    def _is_cat_or_dog(self, predicted_label: str) -> Tuple[Optional[str], str]:
        """
        Prüft, ob die erkannte Klasse ein Hund oder eine Katze ist.
        
        Funktioniert mit ImageNet-Labels (z.B. "tabby", "golden_retriever").
        
        Returns:
            Tuple[species, breed]: (Tierart, Rasse)
        """
        # Normalisiere Label für robustere Erkennung
        label_norm = predicted_label.replace('-', ' ').replace('_', ' ')
        label_lower = label_norm.lower()

        translations = {
            "french bulldog": "Französische Bulldogge",
            "german shepherd": "Deutscher Schäferhund",
            "german shepherd dog": "Deutscher Schäferhund",
            "golden retriever": "Golden Retriever",
            "labrador retriever": "Labrador Retriever",
            "beagle": "Beagle",
            "boxer": "Boxer",
            "rottweiler": "Rottweiler",
            "poodle": "Pudel",
            "standard poodle": "Pudel",
            "miniature poodle": "Zwergpudel",
            "toy poodle": "Toypudel",
            "dachshund": "Dackel",
            "chihuahua": "Chihuahua",
            "pomeranian": "Zwergspitz",
            "pug": "Mops",
            "bulldog": "Englische Bulldogge",
            "english bulldog": "Englische Bulldogge",
            "boston bull": "Boston Terrier",
            "saint bernard": "Bernhardiner",
            "basset": "Basset",
            "great dane": "Deutsche Dogge",
            "doberman": "Dobermann",
            "siberian husky": "Sibirischer Husky",
            "samoyed": "Samojede",
            "collie": "Collie",
            "border collie": "Border Collie",
            "sheltie": "Shetland Sheepdog",
            "papillon": "Papillon",
            "maltese dog": "Malteser",
            "yorkshire terrier": "Yorkshire Terrier",
            "west highland white terrier": "West Highland Terrier",
            "scottish terrier": "Schottischer Terrier",
            "irish setter": "Irischer Setter",
            "weimaraner": "Weimaraner",
            "cocker spaniel": "Cocker Spaniel",
            "english cocker spaniel": "Cocker Spaniel",
            "tabby": "Getigerte Katze",
            "tiger cat": "Tigerkatze",
            "persian cat": "Perser",
            "siamese cat": "Siamkatze",
            "egyptian cat": "Ägyptische Mau",
        }

        def translate(label: str) -> str:
            key = label.lower().strip()
            return translations.get(key, label)
        
        # ImageNet Katzen-Labels
        cat_labels = [
            'tabby', 'tiger cat', 'persian cat', 'siamese cat',
            'egyptian cat', 'cougar', 'lynx', 'leopard', 'snow leopard',
            'jaguar', 'lion', 'tiger', 'cheetah', 'wildcat'
        ]
        
        # ImageNet Hunde-Labels (häufige Rassen)
        dog_indicators = [
            'dog', 'puppy', 'hound', 'terrier', 'retriever', 'shepherd',
            'spaniel', 'poodle', 'bulldog', 'beagle', 'collie', 'corgi',
            'dachshund', 'husky', 'pomeranian', 'chihuahua', 'rottweiler',
            'boxer', 'labrador', 'golden', 'german_shepherd', 'mastiff'
        ]
        
        # Prüfe auf Katze
        for cat_label in cat_labels:
            if cat_label in label_lower or ' cat' in label_lower or label_lower.startswith('cat'):
                breed_name = translate(label_norm).title()
                # Wenn es eine Wildkatze ist, gib generischen Namen
                if any(wild in label_lower for wild in ['cougar', 'lynx', 'leopard', 'lion', 'tiger', 'cheetah', 'jaguar', 'wildcat']):
                    return ("Katze", "Hauskatze (ähnlich zu " + breed_name + ")")
                return ("Katze", breed_name.replace("Cat", "Katze"))
        
        # Prüfe auf Hund
        for dog_indicator in dog_indicators:
            if dog_indicator in label_lower:
                breed_name = translate(label_norm).title()
                return ("Hund", breed_name)
        
        # Fallback: Wenn nicht eindeutig, gib zurück was erkannt wurde
        # mit Hinweis auf Unsicherheit
        breed_name = translate(label_norm).title()
        return (None, breed_name)
    
    def recognize_pet(
        self,
        image_data: bytes,
        species_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Erkennt die Tierart und Rasse aus einem Bild.
        
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
        try:
            logger.info("=" * 60)
            logger.info("STARTE RASSENERKENNUNG")
            logger.info(f"Bilddaten: {len(image_data)} bytes")
            logger.info(f"Modell geladen: {self._model_loaded}")
            logger.info("=" * 60)
            
            # Lade Modell falls noch nicht geschehen
            if not self._model_loaded:
                logger.info("Modell ist noch nicht geladen, lade es jetzt...")
                self._load_model()
                logger.info("Modell erfolgreich geladen")
            
            # Bild vorbereiten
            logger.info("Bereite Bild vor...")
            img = self._preprocess_image(image_data)
            logger.info(f"Bild vorbereitet: {img.size}, Mode: {img.mode}")
            
            # Inference
            logger.info("Starte Inference...")
            inputs = self.processor(images=img, return_tensors="pt")
            logger.info("Inputs vorbereitet")
            outputs = self.model(**inputs)
            logger.info("Modell-Ausgabe erhalten")
            
            # Hole Vorhersage
            import torch
            logger.info("Berechne Wahrscheinlichkeiten...")
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            top_prob, top_class = probs[0].topk(1)
            
            confidence = top_prob.item()
            predicted_label = self.labels[top_class.item()]
            logger.info(f"Erkannte Klasse: '{predicted_label}' mit {confidence:.2%} Konfidenz")
            
            # Bestimme Tierart und formatiere Rasse
            species, breed = self._is_cat_or_dog(predicted_label)
            
            # Prüfe ob es ein Haustier ist (unbekannt -> Vorschlag anbieten)
            if species is None:
                return {
                    "success": False,
                    "error": f"Das Bild zeigt vermutlich kein Haustier (erkannt: {breed}). Bitte trage die Rasse manuell ein.",
                    "species": None,
                    "breed": None,
                    "confidence": confidence,
                    "suggested_species": None,
                    "suggested_breed": breed
                }
            
            # Prüfe Filter
            if species_filter and species != species_filter:
                return {
                    "success": False,
                    "error": f"Das Bild zeigt vermutlich {species.lower()}, aber {species_filter} wurde erwartet.",
                    "species": None,
                    "breed": None,
                    "confidence": 0.0
                }
            
            # Minimale Konfidenz prüfen
            if confidence < 0.3:
                return {
                    "success": False,
                    "error": "Die Erkennung ist unsicher. Bitte versuche ein anderes Bild oder gib die Rasse manuell ein.",
                    "species": None,
                    "breed": None,
                    "confidence": confidence,
                    "suggested_species": species,
                    "suggested_breed": breed
                }
            
            return {
                "success": True,
                "species": species,
                "breed": breed,
                "confidence": confidence,
                "error": None
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error("=" * 60)
            logger.error("FEHLER BEI DER RASSENERKENNUNG")
            logger.error("=" * 60)
            logger.error(f"Exception: {type(e).__name__}")
            logger.error(f"Nachricht: {str(e)}")
            logger.error("Details: ", exc_info=True)
            logger.error("=" * 60)
            return {
                "success": False,
                "error": f"Fehler bei der Erkennung: {str(e)}",
                "species": None,
                "breed": None,
                "confidence": 0.0
            }


# Globale Instanz (Singleton)
_recognition_service = None


def get_recognition_service() -> PetRecognitionService:
    """Gibt die globale Instanz des Recognition Service zurück."""
    global _recognition_service
    if _recognition_service is None:
        _recognition_service = PetRecognitionService()
    return _recognition_service
