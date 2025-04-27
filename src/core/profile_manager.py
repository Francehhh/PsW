"""
Modulo per la gestione dei profili utente.
"""

import json
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Profile:
    """
    Rappresenta un profilo utente.
    
    Attributes:
        id: Identificatore univoco del profilo
        name: Nome dell'utente
        email: Email dell'utente
        username: Username dell'utente
        phone: Numero di telefono (opzionale)
        address: Indirizzo (opzionale)
        notes: Note aggiuntive (opzionale)
        created_at: Data di creazione
        updated_at: Data di ultimo aggiornamento
    """
    id: str
    name: str
    email: str
    username: str
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        """Inizializza le date se non specificate."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

class ProfileManager:
    """
    Gestisce le operazioni CRUD sui profili utente.
    
    Utilizza un file JSON per la persistenza dei dati.
    """
    
    def __init__(self, storage_path: str = "data/profiles.json"):
        """
        Inizializza il gestore dei profili.
        
        Args:
            storage_path: Percorso del file di storage
        """
        self.storage_path = storage_path
        self.profiles: List[Profile] = []
        self.load_profiles()
        self.profile_changed = None
        
    def load_profiles(self):
        """Carica i profili dal file di storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.profiles = [Profile(**profile) for profile in data]
        except FileNotFoundError:
            self.profiles = []
            
    def save_profiles(self):
        """Salva i profili nel file di storage."""
        with open(self.storage_path, 'w') as f:
            json.dump([profile.__dict__ for profile in self.profiles], f, indent=4)
            
    def add_profile(self, profile: Profile) -> bool:
        """
        Aggiunge un nuovo profilo.
        
        Args:
            profile: Il profilo da aggiungere
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not self.validate_profile(profile):
            return False
        self.profiles.append(profile)
        self.save_profiles()
        if self.profile_changed:
            self.profile_changed()
        return True
        
    def update_profile(self, profile_id: str, updated_profile: Profile) -> bool:
        """
        Aggiorna un profilo esistente.
        
        Args:
            profile_id: ID del profilo da aggiornare
            updated_profile: Il profilo aggiornato
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not self.validate_profile(updated_profile):
            return False
        for i, profile in enumerate(self.profiles):
            if profile.id == profile_id:
                updated_profile.updated_at = datetime.now().isoformat()
                self.profiles[i] = updated_profile
                self.save_profiles()
                if self.profile_changed:
                    self.profile_changed()
                return True
        return False
        
    def delete_profile(self, profile_id: str) -> bool:
        """
        Elimina un profilo.
        
        Args:
            profile_id: ID del profilo da eliminare
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        for i, profile in enumerate(self.profiles):
            if profile.id == profile_id:
                del self.profiles[i]
                self.save_profiles()
                if self.profile_changed:
                    self.profile_changed()
                return True
        return False
        
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """
        Ottiene un profilo specifico.
        
        Args:
            profile_id: ID del profilo da ottenere
            
        Returns:
            Il profilo richiesto o None se non trovato
        """
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None
        
    def search_profiles(self, query: str) -> List[Profile]:
        """
        Cerca profili che corrispondono alla query.
        
        Args:
            query: Stringa di ricerca
            
        Returns:
            Lista di profili che corrispondono alla query
        """
        query = query.lower()
        return [
            profile for profile in self.profiles
            if query in profile.name.lower() or
               query in profile.email.lower() or
               query in profile.username.lower()
        ]
        
    @staticmethod
    def validate_profile(profile: Profile) -> bool:
        """
        Valida i dati del profilo.
        
        Args:
            profile: Il profilo da validare
            
        Returns:
            True se il profilo è valido, False altrimenti
        """
        if not profile.id or not profile.name or not profile.email or not profile.username:
            return False
        return True 