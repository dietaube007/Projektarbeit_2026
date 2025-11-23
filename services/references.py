"""Referenzdaten-Management.

Dieses Modul verwaltet alle statischen Referenzdaten aus der Datenbank, die
für Dropdowns, Filter und die Formularvalidierung benötigt werden:

- Meldung-Statuses: Kategorien wie "Vermisst" oder "Gefunden"
- Tierarten
- Rassen: Gruppiert nach Tierart (z.B. Labrador unter Hund)
- Farben: 
- Geschlechter:

"""

from supabase import Client
from typing import List, Dict, Any


def get_post_statuses(sb: Client) -> List[Dict[str, Any]]:
    
    # Lädt alle verfügbaren Post-Statuses/Kategorien.

    try:
        res = sb.table("post_status").select("*").execute()
        return res.data or []
    except Exception as ex:
        print(f"Fehler beim Laden von Post-Statuses: {ex}")
        return []


def get_species(sb: Client) -> List[Dict[str, Any]]:
    
    #Lädt alle verfügbaren Tierarten.
    
    try:
        res = sb.table("species").select("*").execute()
        return res.data or []
    except Exception as ex:
        print(f"Fehler beim Laden von Tierarten: {ex}")
        return []


def get_breeds_by_species(sb: Client) -> Dict[int, List[Dict[str, Any]]]:
    
    # Lädt alle Rassen und gruppiert sie nach Tierart.
    
    try:
        res = sb.table("breed").select("*").execute()
        grouped = {}
        for breed in res.data or []:
            # Sichere Dictionay-Access mit .get() um KeyError zu vermeiden
            sid = breed.get("species_id")
            if sid is not None:
                # Initialisiere die Liste für diese Tierart falls noch nicht vorhanden
                if sid not in grouped:
                    grouped[sid] = []
                # Füge die Rasse zur entsprechenden Tierart hinzu
                grouped[sid].append(breed)
        return grouped
    except Exception as ex:
        print(f"Fehler beim Laden von Rassen: {ex}")
        return {}


def get_colors(sb: Client) -> List[Dict[str, Any]]:
    
    # Lädt alle verfügbaren Farb-Beschreibungen.
    
    try:
        res = sb.table("color").select("*").execute()
        return res.data or []
    except Exception as ex:
        print(f"Fehler beim Laden von Farben: {ex}")
        return []


def get_sex(sb: Client) -> List[Dict[str, Any]]:
    
    # Lädt alle verfügbaren Geschlechts-Optionen.
    
    try:
        res = sb.table("sex").select("*").execute()
        return res.data or []
    except Exception as ex:
        print(f"Fehler beim Laden von Geschlechtern: {ex}")
        return []