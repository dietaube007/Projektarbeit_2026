"""Supabase Client Initialisierung und Verwaltung.

Dieses Modul ist verantwortlich für die Verbindung zur Supabase-Datenbank.
Es lädt die Konfiguration aus der .env-Datei und stellt einen initialisierten
Supabase Client für die gesamte Anwendung zur Verfügung.

Konfiguration:
    Benötigte Umgebungsvariablen (in .env-Datei):
    - SUPABASE_URL: Die URL des Supabase-Projekts
      Format: https://[PROJECT-ID].supabase.co
    - SUPABASE_ANON_KEY: Der anonyme API-Schlüssel für public Operationen
      Format: eyJ... (JWT Token)
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from supabase import create_client, Client

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Lade Umgebungsvariablen aus .env-Datei beim Modul-Import
load_dotenv()


def get_client() -> Client:
    """Erstellt und gibt einen Supabase Client zurück.
    
    Returns:
        Initialisierter Supabase Client
        
    Raises:
        RuntimeError: Wenn Konfiguration fehlt oder Client nicht erstellt werden kann
    """
    # Lese Konfiguration aus Umgebungsvariablen
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    # Validiere dass beide Konfigurationswerte vorhanden sind
    if not url or not key:
        url_status = "(vorhanden)" if url else "(FEHLT)"
        key_status = "(vorhanden)" if key else "(FEHLT)"
        
        error_msg = (
            "Supabase-Konfiguration unvollständig!\n\n"
            "Bitte .env-Datei mit folgenden Variablen erstellen:\n"
            f"  - SUPABASE_URL: {url_status}\n"
            f"  - SUPABASE_ANON_KEY: {key_status}\n\n"
            "Beispiel .env:\n"
            "  SUPABASE_URL=https://yourproject.supabase.co\n"
            "  SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
        logger.error("Supabase-Konfiguration fehlt")
        raise RuntimeError(error_msg)

    # Versuche Client zu initialisieren
    try:
        logger.debug("Initialisiere Supabase Client...")
        client = create_client(url, key)
        logger.info("Supabase Client erfolgreich initialisiert")
        return client
    except Exception as e:  # noqa: BLE001
        error_msg = (
            f"Fehler beim Erstellen des Supabase Clients:\n"
            f"{str(e)}\n\n"
            f"Überprüfe:\n"
            f"1. SUPABASE_URL ist gültig und erreichbar\n"
            f"2. SUPABASE_ANON_KEY ist korrekt\n"
            f"3. Netzwerkverbindung ist aktiv"
        )
        logger.error(f"Fehler beim Erstellen des Supabase Clients: {e}", exc_info=True)
        raise RuntimeError(error_msg) from e
