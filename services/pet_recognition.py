"""
Pet Recognition Service - KI-gestützte Tier- und Rassenerkennung.

Verwendet ein vortrainiertes Modell zur Erkennung von Hunde- und Katzenrassen
aus Bildern. Das Modell wird beim ersten Start heruntergeladen.
"""

import io
from typing import Optional, Dict, Tuple
from PIL import Image
import numpy as np


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
            from transformers import AutoImageProcessor, AutoModelForImageClassification
            
            # Verwende ein stabiles, bewährtes Modell für Bildklassifikation
            # Dieses Modell ist nicht speziell für Haustiere, aber funktioniert zuverlässig
            model_name = "google/vit-base-patch16-224"
            
            print("🔄 Lade KI-Modell für Bilderkennung...")
            print(f"   Modell: {model_name}")
            print("   Dies kann beim ersten Start einige Minuten dauern...")
            print("   Hinweis: Dies ist ein allgemeines Bilderkennungsmodell (ImageNet-basiert)")
            
            self.processor = AutoImageProcessor.from_pretrained(model_name)
            self.model = AutoModelForImageClassification.from_pretrained(model_name)
            
            self.labels = self.model.config.id2label
            self._model_loaded = True
            print("✅ Modell erfolgreich geladen!")
            
        except Exception as ex:
            print(f"❌ Fehler beim Laden des Modells: {ex}")
            # Setze Flag, dass Modell nicht verfügbar ist
            self._model_loaded = False
            raise RuntimeError(
                "KI-Modell konnte nicht geladen werden.\n\n"
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
        except Exception as ex:
            raise ValueError(f"Bild konnte nicht geladen werden: {ex}")
    
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
                breed_name = label_norm.title()
                # Wenn es eine Wildkatze ist, gib generischen Namen
                if any(wild in label_lower for wild in ['cougar', 'lynx', 'leopard', 'lion', 'tiger', 'cheetah', 'jaguar', 'wildcat']):
                    return ("Katze", "Hauskatze (ähnlich zu " + breed_name + ")")
                return ("Katze", breed_name.replace("Cat", "Katze"))
        
        # Prüfe auf Hund
        for dog_indicator in dog_indicators:
            if dog_indicator in label_lower:
                breed_name = label_norm.title()
                return ("Hund", breed_name)
        
        # Fallback: Wenn nicht eindeutig, gib zurück was erkannt wurde
        # mit Hinweis auf Unsicherheit
        breed_name = label_norm.title()
        return (None, breed_name)
    
    def recognize_pet(
        self,
        image_data: bytes,
        species_filter: Optional[str] = None
    ) -> Dict[str, any]:
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
            # Lade Modell falls noch nicht geschehen
            if not self._model_loaded:
                self._load_model()
            
            # Bild vorbereiten
            img = self._preprocess_image(image_data)
            
            # Inference
            inputs = self.processor(images=img, return_tensors="pt")
            outputs = self.model(**inputs)
            
            # Hole Vorhersage
            import torch
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            top_prob, top_class = probs[0].topk(1)
            
            confidence = top_prob.item()
            predicted_label = self.labels[top_class.item()]
            
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
            
        except Exception as ex:
            return {
                "success": False,
                "error": f"Fehler bei der Erkennung: {str(ex)}",
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
