"""
Utility per la crittografia/decrittografia dei dati sensibili.
Utilizza Fernet (crittografia simmetrica autenticata) derivando la chiave
dalla master password dell'utente.
"""

import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Optional

# Costanti allineate con SyncManager (sebbene il salt qui sia usato solo per KDF)
PBKDF2_ITERATIONS = 600000 # Numero di iterazioni per PBKDF2
# NOTA: Il SALT per Fernet è incorporato nel token Fernet stesso.
#       Tuttavia, per derivare la chiave Fernet dalla password utente,
#       abbiamo bisogno di un salt *per il KDF (PBKDF2)*. Questo salt
#       dovrebbe essere lo stesso usato per l'hash di verifica della password.
#       Quindi, le funzioni qui richiederanno il salt (in bytes) come argomento.

def _derive_fernet_key(password: str, salt: bytes) -> Optional[bytes]:
    """Deriva una chiave Fernet (URL-safe base64 encoded) dalla password e dal salt usando PBKDF2."""
    if not password or not salt:
        print("[_derive_fernet_key] Errore: Password o salt mancanti.")
        return None
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32, # Fernet usa chiavi a 32 byte
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        # La chiave per Fernet deve essere URL-safe base64 encoded
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        # print(f"DEBUG: Derived Fernet key: {key[:5]}...{key[-5:]}") # Debugging Key Derivation
        return key
    except Exception as e:
        print(f"[_derive_fernet_key] Errore durante la derivazione della chiave: {e}")
        return None

def encrypt_data(plain_text: str, password: str, salt: bytes) -> Optional[str]:
    """
    Crittografa una stringa di testo usando Fernet.

    Args:
        plain_text: Il testo in chiaro da crittografare.
        password: La master password dell'utente.
        salt: Il salt (in bytes) associato alla master password (usato per derivare la chiave).

    Returns:
        La stringa crittografata (URL-safe base64 encoded), o None se fallisce.
    """
    if not plain_text:
        # print("[encrypt_data] Input text is empty, returning empty string.") # Allow encrypting empty
        return '' # Ritorna stringa vuota se l'input è vuoto
        
    key = _derive_fernet_key(password, salt)
    if not key:
        print("[encrypt_data] Fallimento derivazione chiave, impossibile crittografare.")
        return None
    try:
        f = Fernet(key)
        encrypted_bytes = f.encrypt(plain_text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8') # Il token Fernet è già URL-safe base64
    except Exception as e:
        print(f"[encrypt_data] Errore durante la crittografia: {e}")
        return None

def decrypt_data(encrypted_text: str, password: str, salt: bytes) -> Optional[str]:
    """
    Decrittografa una stringa crittografata con Fernet.

    Args:
        encrypted_text: La stringa crittografata (URL-safe base64 encoded).
        password: La master password dell'utente.
        salt: Il salt (in bytes) associato alla master password (usato per derivare la chiave).

    Returns:
        La stringa decrittografata, o None se fallisce (es. password errata, dati corrotti).
    """
    if not encrypted_text:
        # print("[decrypt_data] Input text is empty, returning empty string.")
        return '' # Ritorna stringa vuota se l'input è vuoto
        
    key = _derive_fernet_key(password, salt)
    if not key:
        print("[decrypt_data] Fallimento derivazione chiave, impossibile decrittografare.")
        return None
    try:
        f = Fernet(key)
        decrypted_bytes = f.decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except InvalidToken:
         print("[decrypt_data] Errore: Token invalido. Password errata o dati corrotti.")
         return None # Specifico per password errata o dati manomessi
    except Exception as e:
        print(f"[decrypt_data] Errore generico durante la decrittografia: {e}")
        return None 