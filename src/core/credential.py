"""
Modulo per la gestione delle credenziali.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import uuid

@dataclass
class Credential:
    """
    Rappresenta una credenziale salvata.
    """
    # --- Fields WITHOUT default values FIRST ---
    profile_id: str 
    app_name: str
    username: str # Will be encrypted
    password: str # Will be encrypted
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    
    # --- Fields WITH default values or factories SECOND ---
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: Optional[str] = None # Will be encrypted
    notes: Optional[str] = None # Will be encrypted
    created_at: str = None
    updated_at: str = None
    is_encrypted_in_memory: bool = False

    def __post_init__(self):
        """Inizializza le date se non specificate."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
            
    def to_dict(self) -> dict:
        """
        Converte la credenziale in un dizionario.
        (Potrebbe essere sostituito da dataclasses.asdict se appropriato)
        
        Returns:
            Dizionario con i dati della credenziale
        """
        return {
            # Ensure correct order for reconstruction if needed
            "profile_id": self.profile_id,
            "app_name": self.app_name,
            "username": self.username,
            "password": self.password,
            "id": self.id,
            "url": self.url,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
            # is_encrypted_in_memory is transient, not included in dict for saving
        } 