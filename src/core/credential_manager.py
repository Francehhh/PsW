"""
Modulo per la gestione delle credenziali.
"""

import json
import re
import hashlib
from typing import List, Optional
from datetime import datetime
from .crypto_manager import CryptoManager
from ..core.profile_manager import Profile
from ..core.credential import Credential
import os

class CredentialManager:
    """
    Gestisce le operazioni CRUD sulle credenziali.
    
    Utilizza un file JSON per la persistenza dei dati e il CryptoManager
    per la crittografia.
    """
    
    def __init__(self, storage_path: str = "data/credentials.json", master_password: str = None):
        """
        Inizializza il gestore delle credenziali.
        
        Args:
            storage_path: Percorso del file di storage
            master_password: Password master per la crittografia
        """
        self.storage_path = storage_path
        self.credentials: List[Credential] = []
        self.crypto = CryptoManager()
        self.master_password = master_password
        self.load_credentials()
        self.credential_changed = None
        
    def is_password_compromised(self, password: str) -> bool:
        """
        Verifica se una password è stata compromessa.
        Per semplicità, controlla solo se la password:
        - È troppo corta (< 8 caratteri)
        - È una password comune
        - Contiene solo numeri
        - Contiene solo lettere
        
        Args:
            password: La password da verificare
            
        Returns:
            True se la password è compromessa, False altrimenti
        """
        # Lista di password comuni da evitare
        common_passwords = {
            'password', '123456', '12345678', '1234', 'qwerty',
            '12345', 'dragon', 'baseball', 'football', 'letmein',
            'monkey', 'abc123', 'mustang', 'michael', 'shadow',
            'master', 'jennifer', '111111', '2000', 'jordan',
            'superman', 'harley', '1234567', 'fuckme', 'hunter',
            'fuckyou', 'trustno1', 'ranger', 'buster', 'thomas',
            'tigger', 'robert', 'soccer', 'batman', 'test',
            'pass', 'killer', 'hockey', 'george', 'charlie',
            'andrew', 'michelle', 'love', 'sunshine', 'jessica',
            'pepper', 'daniel', 'access', '123456789', '654321',
            'joshua', 'maggie', 'starwars', 'silver', 'william',
            'dallas', 'yankees', '123123', 'ashley', '666666',
            'hello', 'amanda', 'orange', 'biteme', 'freedom',
            'computer', 'sexy', 'thunder', 'nicole', 'ginger',
            'heather', 'hammer', 'summer', 'corvette', 'taylor',
            'fucker', 'austin', '1111', 'merlin', 'matthew',
            '121212', 'golfer', 'cheese', 'princess', 'martin',
            'chelsea', 'patrick', 'richard', 'diamond', 'yellow',
            'bigdog', 'secret', 'asdfgh', 'sparky', 'cowboy'
        }
        
        # Verifica lunghezza minima
        if len(password) < 8:
            return True
            
        # Verifica se è una password comune
        if password.lower() in common_passwords:
            return True
            
        # Verifica se contiene solo numeri
        if password.isdigit():
            return True
            
        # Verifica se contiene solo lettere
        if password.isalpha():
            return True
            
        return False
        
    def is_password_secure(self, password: str) -> bool:
        """
        Verifica se una password è sicura secondo i criteri:
        - Almeno 12 caratteri
        - Almeno una lettera maiuscola
        - Almeno una lettera minuscola
        - Almeno un numero
        - Almeno un carattere speciale
        
        Args:
            password: La password da verificare
            
        Returns:
            True se la password è sicura, False altrimenti
        """
        if len(password) < 12:
            return False
            
        # Verifica presenza di lettere maiuscole
        if not re.search(r'[A-Z]', password):
            return False
            
        # Verifica presenza di lettere minuscole
        if not re.search(r'[a-z]', password):
            return False
            
        # Verifica presenza di numeri
        if not re.search(r'[0-9]', password):
            return False
            
        # Verifica presenza di caratteri speciali
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
            
        return True
        
    def load_credentials(self):
        """Carica le credenziali dal file di storage."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.credentials = [Credential(**credential) for credential in data]
        else:
            self.credentials = []
            
    def save_credentials(self):
        """Salva le credenziali nel file di storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump([credential.__dict__ for credential in self.credentials], f, indent=4)
            
    def add_credential(self, credential: Credential) -> bool:
        """
        Aggiunge una nuova credenziale.
        
        Args:
            credential: La credenziale da aggiungere
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not self.validate_credential(credential):
            return False
        self.credentials.append(credential)
        self.save_credentials()
        if self.credential_changed:
            self.credential_changed()
        return True
        
    def update_credential(self, credential_id: str, updated_credential: Credential) -> bool:
        """
        Aggiorna una credenziale esistente.
        
        Args:
            credential_id: ID della credenziale da aggiornare
            updated_credential: La credenziale aggiornata
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not self.validate_credential(updated_credential):
            return False
        for i, credential in enumerate(self.credentials):
            if credential.id == credential_id:
                updated_credential.updated_at = datetime.now().isoformat()
                self.credentials[i] = updated_credential
                self.save_credentials()
                if self.credential_changed:
                    self.credential_changed()
                return True
        return False
        
    def delete_credential(self, credential: Credential) -> bool:
        """
        Elimina una credenziale.
        
        Args:
            credential: La credenziale da eliminare
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        for i, c in enumerate(self.credentials):
            if c.id == credential.id:
                del self.credentials[i]
                self.save_credentials()
                if self.credential_changed:
                    self.credential_changed()
                return True
        return False
        
    def get_credential(self, credential_id: str) -> Optional[Credential]:
        """
        Ottiene una credenziale specifica.
        
        Args:
            credential_id: ID della credenziale da ottenere
            
        Returns:
            La credenziale richiesta o None se non trovata
        """
        for credential in self.credentials:
            if credential.id == credential_id:
                return credential
        return None
        
    def search_credentials(self, query: str) -> List[Credential]:
        """
        Cerca credenziali che corrispondono alla query.
        
        Args:
            query: Stringa di ricerca
            
        Returns:
            Lista di credenziali che corrispondono alla query
        """
        query = query.lower()
        return [
            credential for credential in self.credentials
            if query in credential.app_name.lower() or
               query in credential.username.lower()
        ]
        
    def generate_password(self, length: int = 16, use_special_chars: bool = True) -> str:
        """
        Genera una password sicura.
        
        Args:
            length: Lunghezza della password
            use_special_chars: Se includere caratteri speciali
            
        Returns:
            La password generata
        """
        import string
        import random
        
        chars = string.ascii_letters + string.digits
        if use_special_chars:
            chars += string.punctuation
            
        return ''.join(random.choice(chars) for _ in range(length))
        
    @staticmethod
    def validate_credential(credential: Credential) -> bool:
        """
        Valida i dati della credenziale.
        
        Args:
            credential: La credenziale da validare
            
        Returns:
            True se la credenziale è valida, False altrimenti
        """
        if not credential.id or not credential.profile_id or not credential.app_name or not credential.username or not credential.password:
            return False
        return True

    def get_profile_credentials(self, profile: Profile) -> List[Credential]:
        """
        Restituisce tutte le credenziali associate a un profilo.
        
        Args:
            profile: Il profilo di cui ottenere le credenziali
            
        Returns:
            Lista delle credenziali associate al profilo
        """
        return [cred for cred in self.credentials if cred.profile_id == profile.id] 