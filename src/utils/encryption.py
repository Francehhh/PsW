"""
Utility functions for encrypting and decrypting data using AES-GCM.
Uses PBKDF2HMAC for key derivation from a user password.
"""

import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import base64

# Constants
SALT_SIZE = 16        # Size of the salt (bytes)
NONCE_SIZE = 12       # Size of the nonce for AES-GCM (bytes)
KEY_LENGTH = 32       # Key length for AES-256 (bytes)
PBKDF2_ITERATIONS = 390000 # Number of iterations for PBKDF2 (adjust as needed)

# --- Key Derivation ---
def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a cryptographic key from a password and salt using PBKDF2HMAC."""
    if not isinstance(password, bytes):
        password = password.encode('utf-8')
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS
    )
    key = kdf.derive(password)
    return key

# --- Encryption ---
def encrypt(plaintext: str, password: str) -> str:
    """
    Encrypts plaintext using AES-GCM with a key derived from the password.

    Args:
        plaintext: The string data to encrypt.
        password: The user's password for key derivation.

    Returns:
        A base64 encoded string containing salt, nonce, and ciphertext.
        Returns an empty string if plaintext is empty or encryption fails.
    """
    if not plaintext:
        return "" # Don't encrypt empty strings

    if not isinstance(plaintext, bytes):
        plaintext_bytes = plaintext.encode('utf-8')
    else:
        plaintext_bytes = plaintext

    try:
        # 1. Generate a random salt
        salt = os.urandom(SALT_SIZE)
        
        # 2. Derive the key
        key = derive_key(password, salt)
        
        # 3. Generate a random nonce
        nonce = os.urandom(NONCE_SIZE)
        
        # 4. Encrypt using AES-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None) # No associated data
        
        # 5. Combine salt, nonce, and ciphertext
        # Prepending salt and nonce makes decryption easier
        encrypted_blob = salt + nonce + ciphertext
        
        # 6. Encode the result in base64 for easier storage/transfer
        return base64.b64encode(encrypted_blob).decode('utf-8')
        
    except Exception as e:
        print(f"[Encryption] Error during encryption: {e}")
        # In a real app, handle this more gracefully (e.g., specific exceptions)
        return "" # Indicate failure

# --- Decryption ---
def decrypt(encrypted_base64: str, password: str) -> str:
    """
    Decrypts data previously encrypted with the encrypt function.

    Args:
        encrypted_base64: The base64 encoded string containing salt, nonce, and ciphertext.
        password: The user's password for key derivation.

    Returns:
        The original plaintext string, or an empty string if decryption fails 
        (e.g., wrong password, corrupted data).
    """
    if not encrypted_base64:
        return ""

    try:
        # 1. Decode from base64
        encrypted_blob = base64.b64decode(encrypted_base64.encode('utf-8'))
        
        # 2. Extract salt, nonce, and ciphertext
        if len(encrypted_blob) < (SALT_SIZE + NONCE_SIZE):
            print("[Encryption] Error: Encrypted data is too short.")
            return "" # Data is definitely corrupted or invalid
            
        salt = encrypted_blob[:SALT_SIZE]
        nonce = encrypted_blob[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
        ciphertext = encrypted_blob[SALT_SIZE + NONCE_SIZE:]
        
        # 3. Derive the key using the extracted salt
        key = derive_key(password, salt)
        
        # 4. Decrypt using AES-GCM
        aesgcm = AESGCM(key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None) # No associated data
        
        # 5. Decode the plaintext back to a string
        return plaintext_bytes.decode('utf-8')
        
    except InvalidTag:
        # This exception specifically indicates the password was wrong or data corrupted
        print("[Encryption] Decryption failed: Invalid password or corrupted data (InvalidTag).")
        return "" 
    except Exception as e:
        print(f"[Encryption] Error during decryption: {e}")
        # Handle other potential errors (e.g., base64 decoding)
        return ""

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    pwd = "mysecretpassword"
    original_data = "This is some very secret information!"
    
    print(f"Original: {original_data}")
    
    encrypted = encrypt(original_data, pwd)
    print(f"Encrypted (base64): {encrypted}")
    
    if encrypted:
        decrypted = decrypt(encrypted, pwd)
        print(f"Decrypted (correct password): {decrypted}")
        
        # Test with wrong password
        wrong_pwd = "wrongpassword"
        decrypted_wrong = decrypt(encrypted, wrong_pwd)
        print(f"Decrypted (wrong password): '{decrypted_wrong}' (Should be empty)")

        # Test with corrupted data
        corrupted_encrypted = encrypted[:-5] + "XXXXX"
        decrypted_corrupt = decrypt(corrupted_encrypted, pwd)
        print(f"Decrypted (corrupted data): '{decrypted_corrupt}' (Should be empty)")
    else:
        print("Encryption failed.") 