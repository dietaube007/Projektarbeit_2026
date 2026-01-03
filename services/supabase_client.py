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

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Lade Umgebungsvariablen aus .env-Datei beim Modul-Import
load_dotenv()


def get_client() -> Client:
    """Erstellt und gibt einen Supabase Client zurück.
            
    Note:
        Diese Funktion sollte am Anfang der Anwendung aufgerufen werden.
        Der Client wird normalerweise in main.py initialisiert und an
        alle anderen Module weitergegeben.
    """
    # Lese Konfiguration aus Umgebungsvariablen
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    # Validiere dass beide Konfigurationswerte vorhanden sind
    if not url or not key:
        # Hilfreiche Fehlermeldung mit Status-Indikatoren
        raise RuntimeError(
            "Supabase-Konfiguration unvollständig!\n\n"
            "Bitte .env-Datei mit folgenden Variablen erstellen:\n"
            "  - SUPABASE_URL: {} {}\n"
            "  - SUPABASE_ANON_KEY: {} {}\n\n"
            "Beispiel .env:\n"
            "  SUPABASE_URL=https://yourproject.supabase.co\n"
            "  SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...".format(
                "(vorhanden)" if url else "(FEHLT)",
                "(vorhanden)" if key else "(FEHLT)")
        )

    # Versuche Client zu initialisieren
    try:
        client = create_client(url, key)
        return client
    except Exception as ex:
        raise RuntimeError(
            f"Fehler beim Erstellen des Supabase Clients:\n"
            f"{str(ex)}\n\n"
            f"Überprüfe:\n"
            f"1. SUPABASE_URL ist gültig und erreichbar\n"
            f"2. SUPABASE_ANON_KEY ist korrekt\n"
            f"3. Netzwerkverbindung ist aktiv"
        )