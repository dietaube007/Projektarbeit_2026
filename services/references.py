"""Referenzdaten-Management.

Dieses Modul verwaltet alle statischen Referenzdaten aus der Datenbank, die für Dropdowns, Filter und die Formularvalidierung benötigt werden

"""

from supabase import Client
from typing import List, Dict, Any

class ReferenceService:
    # Service-Klasse für das Laden von Referenzdaten aus der Datenbank.
    
    def __init__(self, sb: Client):
        # Initialisiert den Service mit dem Supabase-Client.
        self.sb = sb
        
        # Cache für Referenzdaten
        self._post_statuses = None
        self._species = None
        self._breeds_by_species = None
        self._colors = None
        self._sex = None
    
    def get_post_statuses(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        # Lädt alle verfügbaren Post-Statuses/Kategorien.
        if use_cache and self._post_statuses is not None:
            return self._post_statuses
        
        try:
            res = self.sb.table("post_status").select("*").execute()
            self._post_statuses = res.data or []
            return self._post_statuses
        except Exception as ex:
            print(f"Fehler beim Laden von Meldungstypen: {ex}")
            return []
    
    def get_species(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        # Lädt alle verfügbaren Tierarten.
        if use_cache and self._species is not None:
            return self._species
        
        try:
            res = self.sb.table("species").select("*").execute()
            self._species = res.data or []
            return self._species
        except Exception as ex:
            print(f"Fehler beim Laden von Tierarten: {ex}")
            return []
    
    def get_breeds_by_species(self, use_cache: bool = True) -> Dict[int, List[Dict[str, Any]]]:
        # Lädt alle Rassen und gruppiert sie nach Tierart.
        if use_cache and self._breeds_by_species is not None:
            return self._breeds_by_species
        
        try:
            res = self.sb.table("breed").select("*").execute()
            grouped = {}
            for breed in res.data or []:
                sid = breed.get("species_id")
                if sid is not None:
                    if sid not in grouped:
                        grouped[sid] = []
                    grouped[sid].append(breed)
            self._breeds_by_species = grouped
            return self._breeds_by_species
        except Exception as ex:
            print(f"Fehler beim Laden von Rassen: {ex}")
            return {}
    
    def get_colors(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        # Lädt alle verfügbaren Farb-Beschreibungen.
        if use_cache and self._colors is not None:
            return self._colors
        
        try:
            res = self.sb.table("color").select("*").execute()
            self._colors = res.data or []
            return self._colors
        except Exception as ex:
            print(f"Fehler beim Laden von Farben: {ex}")
            return []
    
    def get_sex(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        # Lädt alle verfügbaren Geschlechts-Optionen.
        if use_cache and self._sex is not None:
            return self._sex
        
        try:
            res = self.sb.table("sex").select("*").execute()
            self._sex = res.data or []
            return self._sex
        except Exception as ex:
            print(f"Fehler beim Laden von Geschlechtern: {ex}")
            return []
    
    def clear_cache(self):
        # Löscht alle gecachten Daten.
        self._post_statuses = None
        self._species = None
        self._breeds_by_species = None
        self._colors = None
        self._sex = None
