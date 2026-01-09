"""
translator.py - Übersetzungs-Engine für PetBuddy.
"""

from typing import Dict, Any, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Translator:
    """Klasse für die Verwaltung von Übersetzungen."""
    
    # Singleton-Instanz
    _instance: Optional["Translator"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialisiert den Translator."""
        if not hasattr(self, "_initialized"):
            self._current_language: str = "de"
            self._translations: Dict[str, Dict[str, Any]] = {}
            self._load_translations()
            self._initialized = True
    
    def _load_translations(self) -> None:
        """Lädt alle Übersetzungsdateien."""
        i18n_dir = Path(__file__).parent
        
        for lang in ["de", "en"]:
            lang_file = i18n_dir / f"{lang}.json"
            if lang_file.exists():
                try:
                    with open(lang_file, "r", encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
                    logger.info(f"Übersetzungen für '{lang}' geladen")
                except Exception as e:
                    logger.error(f"Fehler beim Laden von {lang}.json: {e}")
                    self._translations[lang] = {}
            else:
                logger.warning(f"Übersetzungsdatei {lang_file} nicht gefunden")
                self._translations[lang] = {}
    
    def set_language(self, language: str) -> None:
        """
        Setzt die aktuelle Sprache.
        
        Args:
            language: Sprachcode ("de" oder "en")
        """
        if language in self._translations:
            self._current_language = language
            logger.info(f"Sprache auf '{language}' gesetzt")
        else:
            logger.warning(f"Sprache '{language}' nicht verfügbar")
    
    def get_language(self) -> str:
        """Gibt die aktuelle Sprache zurück."""
        return self._current_language
    
    def t(self, key: str, **kwargs) -> str:
        """
        Übersetzt einen Schlüssel in die aktuelle Sprache.
        
        Args:
            key: Übersetzungsschlüssel (z.B. "auth.login" oder "auth.email")
            **kwargs: Variablen für String-Formatierung
        
        Returns:
            Übersetzter Text oder Schlüssel falls nicht gefunden
        """
        # Verschachtelte Keys unterstützen (z.B. "auth.login")
        keys = key.split(".")
        value = self._translations.get(self._current_language, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        if value is None:
            logger.warning(f"Übersetzung nicht gefunden: {key} ({self._current_language})")
            return key
        
        # String-Formatierung mit kwargs
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.error(f"Formatierungsfehler für '{key}': {e}")
                return value
        
        return value
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Gibt verfügbare Sprachen zurück.
        
        Returns:
            Dictionary mit Sprachcode -> Sprachname
        """
        return {
            "de": "Deutsch",
            "en": "English"
        }


# Globale Instanz
_translator_instance: Optional[Translator] = None


def get_translator() -> Translator:
    """
    Gibt die Singleton-Instanz des Translators zurück.
    
    Returns:
        Translator-Instanz
    """
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = Translator()
    return _translator_instance
