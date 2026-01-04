"""
Logging-Konfiguration für PetBuddy.

Dieses Modul stellt eine zentrale Logging-Konfiguration bereit.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: str = None,
    log_to_file: bool = True,
    log_file_path: str = "logs/petbuddy.log"
) -> None:
    """
    Konfiguriert das Logging-System für die Anwendung.
    
    Args:
        log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Falls None, wird aus Umgebungsvariable LOG_LEVEL gelesen
        log_to_file: Ob Logs in Datei geschrieben werden sollen
        log_file_path: Pfad zur Log-Datei
    """
    # Log-Level bestimmen
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Log-Level zu uppercase konvertieren (für Konsistenz)
    if isinstance(log_level, str):
        log_level = log_level.upper()
    
    # Log-Level validieren
    numeric_level = getattr(logging, log_level, logging.INFO)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Bestehende Handler entfernen (falls bereits konfiguriert)
    root_logger.handlers.clear()
    
    # Log-Format definieren
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler (immer aktiv)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_to_file:
        # Log-Verzeichnis erstellen falls nicht vorhanden
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating File Handler (max. 10MB pro Datei, 5 Backup-Dateien)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    
    # Externe Logger auf WARNING setzen (um Spam zu reduzieren)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Gibt einen Logger für das angegebene Modul zurück.
    
    Args:
        name: Name des Moduls (normalerweise __name__)
    
    Returns:
        Konfigurierter Logger
    """
    return logging.getLogger(name)


if os.getenv("AUTO_SETUP_LOGGING", "false").lower() == "true":
    setup_logging()

