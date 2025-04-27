"""
Gestore dell'autenticazione per il Password Manager.
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from typing import Optional, Tuple
import logging

class AuthManager:
    def __init__(self):
        self._storage_path = Path("data/auth.json")
        self._storage_path.parent.mkdir(exist_ok=True)
        self._logger = logging.getLogger(__name__)
        
    def is_first_time(self) -> bool:
        """Verifica se è la prima volta che l'app viene eseguita."""
        try:
            if not self._storage_path.exists():
                return True
                
            if os.path.getsize(self._storage_path) == 0:
                return True
                
            with open(self._storage_path, 'r') as f:
                data = json.load(f)
                return not data.get('password_hash') or not data.get('salt')
        except Exception as e:
            self._logger.error(f"Errore durante la verifica dello stato iniziale: {e}")
            return True
        
    def register_password(self, password: str) -> Tuple[str, str]:
        """
        Registra una nuova password master.
        
        Args:
            password: La password da registrare
            
        Returns:
            Tuple[str, str]: La password generata e il suo hash
        """
        try:
            # Genera un salt casuale
            salt = os.urandom(32)
            
            # Crea l'hash della password
            password_hash = self._hash_password(password, salt)
            
            # Salva i dati
            auth_data = {
                "salt": base64.b64encode(salt).decode('utf-8'),
                "password_hash": password_hash,
                "created_at": str(os.path.getmtime(self._storage_path) if self._storage_path.exists() else None)
            }
            
            with open(self._storage_path, 'w') as f:
                json.dump(auth_data, f, indent=4)
                
            self._logger.info("Password master registrata con successo")
            return password, password_hash
        except Exception as e:
            self._logger.error(f"Errore durante la registrazione della password: {e}")
            raise
        
    def verify_password(self, password: str) -> bool:
        """
        Verifica se la password fornita è corretta.
        
        Args:
            password: La password da verificare
            
        Returns:
            bool: True se la password è corretta, False altrimenti
        """
        try:
            if not self._storage_path.exists():
                return False
                
            with open(self._storage_path, 'r') as f:
                auth_data = json.load(f)
                
            if not auth_data.get('salt') or not auth_data.get('password_hash'):
                return False
                
            salt = base64.b64decode(auth_data['salt'])
            stored_hash = auth_data['password_hash']
            
            return self._hash_password(password, salt) == stored_hash
        except Exception as e:
            self._logger.error(f"Errore durante la verifica della password: {e}")
            return False
        
    def _hash_password(self, password: str, salt: bytes) -> str:
        """
        Genera l'hash della password usando PBKDF2.
        
        Args:
            password: La password da hashare
            salt: Il salt da utilizzare
            
        Returns:
            str: L'hash della password
        """
        try:
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            return base64.b64encode(key).decode('utf-8')
        except Exception as e:
            self._logger.error(f"Errore durante l'hashing della password: {e}")
            raise 