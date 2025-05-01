from dataclasses import dataclass, field # Import field if using default_factory
from typing import List, Optional

# Assicurati che anche ProfileManager importi Profile
# e viceversa, se necessario (anche se meno comune)

@dataclass
class Profile:
    """
    Rappresenta un profilo utente (struttura dati in memoria).
    La crittografia avviene a livello DB.
    """
    id: Optional[int] = None # Allow None initially, DB will assign
    name: str = '' # Profile Name or First Name?
    last_name: Optional[str] = None # New field for last name
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None # Plaintext in memory after decryption
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None # Loaded from DB
    updated_at: Optional[str] = None # Loaded from DB

# Puoi spostare Credential qui se ha senso o tenerla separata
# Dipende dalle dipendenze tra Profile e Credential

# @dataclass
# class Credential:
#     ... 