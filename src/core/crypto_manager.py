"""
Modulo per la gestione della crittografia e della sicurezza dei dati.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from argon2 import PasswordHasher

class CryptoManager:
    """
    Gestisce tutte le operazioni di crittografia e sicurezza.
    
    Utilizza:
    - Fernet per la crittografia simmetrica
    - PBKDF2 per la derivazione delle chiavi
    - Argon2 per l'hashing delle password
    """
    
    def __init__(self):
        """Inizializza il gestore della crittografia."""
        self.ph = PasswordHasher()
        
    def generate_key(self, password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """
        Genera una chiave di crittografia dalla password.
        
        Args:
            password: La password da cui derivare la chiave
            salt: Il salt da utilizzare (opzionale)
            
        Returns:
            Una tupla contenente (chiave, salt)
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
        
    def encrypt_data(self, data: str, key: bytes) -> bytes:
        """
        Crittografa i dati.
        
        Args:
            data: I dati da crittografare
            key: La chiave di crittografia
            
        Returns:
            I dati crittografati
        """
        f = Fernet(key)
        return f.encrypt(data.encode())
        
    def decrypt_data(self, encrypted_data: bytes, key: bytes) -> str:
        """
        Decrittografa i dati.
        
        Args:
            encrypted_data: I dati crittografati
            key: La chiave di crittografia
            
        Returns:
            I dati decrittografati
        """
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
        
    def hash_password(self, password: str) -> str:
        """
        Genera un hash della password.
        
        Args:
            password: La password da hashing
            
        Returns:
            L'hash della password
        """
        return self.ph.hash(password)
        
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verifica se la password corrisponde all'hash.
        
        Args:
            password: La password da verificare
            hashed_password: L'hash da confrontare
            
        Returns:
            True se la password corrisponde, False altrimenti
        """
        try:
            self.ph.verify(hashed_password, password)
            return True
        except:
            return False 