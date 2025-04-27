"""
Modulo per la gestione delle credenziali.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Credential:
    """
    Rappresenta una credenziale utente.
    
    Attributes:
        id: Identificatore univoco della credenziale
        profile_id: ID del profilo associato
        app_name: Nome dell'applicazione
        username: Username
        password: Password (crittografata)
        url: URL dell'applicazione (opzionale)
        notes: Note aggiuntive (opzionale)
        created_at: Data di creazione
        updated_at: Data di ultimo aggiornamento
    """
    id: str
    profile_id: str
    app_name: str
    username: str
    password: str
    url: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        """Inizializza le date se non specificate."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
            
    def to_dict(self) -> dict:
        """
        Converte la credenziale in un dizionario.
        
        Returns:
            Dizionario con i dati della credenziale
        """
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "app_name": self.app_name,
            "username": self.username,
            "password": self.password,
            "url": self.url,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        } 