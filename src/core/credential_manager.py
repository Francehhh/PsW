"""
Modulo per la gestione delle credenziali.
"""

import json
import re
import hashlib
from typing import List, Optional
from datetime import datetime
from ..core.profile_manager import Profile
from ..core.credential import Credential
import os
import uuid
from PySide6.QtCore import QObject, Signal
from ..utils.sync_manager import SyncManager
from ..core.database_manager import get_db_manager, DatabaseManager

class CredentialManager(QObject):
    """
    Gestisce le operazioni CRUD sulle credenziali, interagendo con SyncManager
    per ottenere password/salt e con DatabaseManager per lo storage.
    """
    
    credential_changed = Signal()

    def __init__(self, sync_manager: SyncManager):
        """
        Inizializza il gestore delle credenziali.
        
        Args:
            sync_manager: Istanza del gestore di sincronizzazione (per password/salt).
        """
        super().__init__()
        self.sync_manager = sync_manager
        self.db_manager: DatabaseManager = get_db_manager()
        print("[CredentialManager] Initialized.")
        
    def get_profile_credentials(self, profile_id: int) -> List[Credential]:
        """Restituisce le credenziali per un ID profilo specifico leggendo dal DB."""
        print(f"[CredentialManager] Getting credentials for profile_id: {profile_id}")
        credentials_list = []
        verified_password = self.sync_manager._get_verified_password_for_session()
        salt_bytes = self.sync_manager.get_master_password_salt()
            
        if not verified_password or not salt_bytes:
            # Considera se la password è necessaria o meno (potrebbe non essere impostata)
            if self.sync_manager.is_master_password_set():
                 print(f"[CredentialManager] Cannot get credentials for profile {profile_id}: Master password set but not verified or salt missing.")
                 return [] # Non possiamo decriptare se la password è impostata ma non verificata
            # else: password non impostata, procedi senza password/salt
            # print(f"[CredentialManager] Master password not set, loading credentials without decryption attempt.")
            pass # Proceed with verified_password = None, salt_bytes = None

        try:
            # DatabaseManager ora usa sempre app_name internamente
            creds_data = self.db_manager.get_credentials_for_profile(profile_id, verified_password, salt_bytes)
            for cred_dict in creds_data:
                try:
                    # Assicurati che il dizionario abbia 'app_name' e non 'credential_name'
                    # Rimuovi la chiave errata se presente per errore
                    if 'credential_name' in cred_dict:
                        cred_dict.pop('credential_name') 
                        
                    # Aggiungi la chiave attesa 'app_name' se manca (improbabile dopo fix DB)
                    # if 'app_name' not in cred_dict:
                    #     cred_dict['app_name'] = 'Unknown' # O gestisci l'errore

                    # Rimuovi flag non più esistente
                    # cred_dict['is_encrypted_in_memory'] = False 
                    
                    # Assumi che DBManager restituisca 'password' decriptata
                    # E ora anche i nuovi campi (first_name, last_name, email)
                    credentials_list.append(Credential(**cred_dict))
                except TypeError as te:
                    # Log più specifico per l'errore di keyword
                    print(f"[CredentialManager] TypeError converting DB data to Credential object: {te} - Data: {cred_dict}")
                except Exception as e:
                    print(f"[CredentialManager] Error converting DB data to Credential object for profile {profile_id}: {e} - Data: {cred_dict}")
            print(f"[CredentialManager] Found {len(credentials_list)} credentials for profile {profile_id}.")
            return credentials_list
        except Exception as e:
             print(f"[CredentialManager] Error fetching credentials from DB for profile {profile_id}: {e}")
             return []
        
    def add_credential(self, credential: Credential) -> bool:
        """Adds a new credential using DatabaseManager."""
        if not self.validate_credential(credential):
            print(f"[CredentialManager] Validation failed for new credential.")
            return False
            
        verified_password = self.sync_manager._get_verified_password_for_session()
        salt_bytes = self.sync_manager.get_master_password_salt()

        if not verified_password or not salt_bytes:
            print(f"[CredentialManager] Cannot add credential: Master password not verified or salt missing.")
            return False

        cred_data_dict = {
            'profile_id': credential.profile_id,
            'app_name': credential.app_name,
            'first_name': credential.first_name,
            'last_name': credential.last_name,
            'email': credential.email,
            'username': credential.username,
            'password': credential.password,
            'notes': credential.notes
        }
        
        try:
            new_id = self.db_manager.add_credential(cred_data_dict, verified_password, salt_bytes)
            if new_id is not None:
                print(f"[CredentialManager] Credential '{credential.app_name}' added successfully to DB with ID {new_id}.")
                self.credential_changed.emit()
                return True # Return True only if ID is received
            else:
                # db_manager.add_credential returned None, indicating a failure (e.g., encryption failed)
                print(f"[CredentialManager] Failed to add credential '{credential.app_name}' to DB (DB method returned None).")
                return False # Return False if ID is None
        except Exception as e:
            print(f"[CredentialManager] Error calling db_manager.add_credential: {e}")
            return False # Return False on exception

    def update_credential(self, updated_credential: Credential) -> bool:
        """Updates an existing credential using DatabaseManager."""
        if not self.validate_credential(updated_credential):
            print(f"[CredentialManager] Validation failed for updated credential.")
            return False

        credential_id = updated_credential.id 
        if not credential_id:
            print("[CredentialManager] Cannot update credential without an ID.")
            return False

        verified_password = self.sync_manager._get_verified_password_for_session()
        salt_bytes = self.sync_manager.get_master_password_salt()
        
        if not verified_password or not salt_bytes:
            print(f"[CredentialManager] Cannot update credential {credential_id}: Master password not verified or salt missing.")
            return False

        cred_data_dict = {
            'app_name': updated_credential.app_name,
            'first_name': updated_credential.first_name,
            'last_name': updated_credential.last_name,
            'email': updated_credential.email,
            'username': updated_credential.username,
            'password': updated_credential.password,
            'notes': updated_credential.notes
        }
        
        try:
            success = self.db_manager.update_credential(credential_id, cred_data_dict, verified_password, salt_bytes)
            if success:
                print(f"[CredentialManager] Credential ID {credential_id} ('{updated_credential.app_name}') updated successfully in DB.")
                self.credential_changed.emit()
                return True # Return True on success
            else:
                # db_manager.update_credential returned False (e.g., not found or encryption failed)
                print(f"[CredentialManager] Failed to update credential ID {credential_id} in DB (DB method returned False).")
                return False # Return False on failure reported by DB manager
        except Exception as e:
            print(f"[CredentialManager] Error calling db_manager.update_credential for ID {credential_id}: {e}")
            return False # Return False on exception
            
    def delete_credential(self, credential_to_delete: Credential) -> bool:
        """Deletes a credential using DatabaseManager."""
        credential_id = credential_to_delete.id
        if not credential_id:
            print("[CredentialManager] Cannot delete credential without an ID.")
            return False
            
        try:
            success = self.db_manager.delete_credential(credential_id)
            if success:
                print(f"[CredentialManager] Credential ID {credential_id} deleted successfully from DB.")
                self.credential_changed.emit()
                return True # Return True on success
            else:
                # db_manager.delete_credential returned False (e.g., not found)
                print(f"[CredentialManager] Failed to delete credential ID {credential_id} from DB (DB method returned False).")
                return False # Return False on failure reported by DB manager
        except Exception as e:
            print(f"[CredentialManager] Error calling db_manager.delete_credential for ID {credential_id}: {e}")
            return False # Return False on exception

    def get_credential(self, credential_id: int) -> Optional[Credential]: # Assume ID is int
        """Retrieves a single credential by its ID from the DB."""
        # Note: This might be less efficient than getting all for a profile if called repeatedly.
        # Consider if get_profile_credentials covers most use cases.
        print(f"[CredentialManager] Getting single credential with ID: {credential_id}")
        verified_password = self.sync_manager._get_verified_password_for_session()
        salt_bytes = self.sync_manager.get_master_password_salt()

        if not verified_password or not salt_bytes:
            print(f"[CredentialManager] Cannot get credential {credential_id}: Master password not verified or salt missing.")
            return None

        # We need a new method in DatabaseManager: get_credential_by_id
        # Placeholder - assuming DatabaseManager will have this method:
        # try:
        #     cred_dict = self.db_manager.get_credential_by_id(credential_id, verified_password, salt_bytes)
        #     if cred_dict:
        #         try:
        #             cred_dict['is_encrypted_in_memory'] = False
        #             return Credential(**cred_dict)
        #         except Exception as e:
        #             print(f"[CredentialManager] Error converting DB data to Credential object for ID {credential_id}: {e}")
        #             return None
        #     else:
        #         return None # Not found
        # except AttributeError:
        #      print("[CredentialManager] ERROR: db_manager.get_credential_by_id method not implemented yet.")
        #      return None
        # except Exception as e:
        #      print(f"[CredentialManager] Error fetching credential {credential_id} from DB: {e}")
        #      return None
        print("[CredentialManager] WARNING: get_credential(id) not fully implemented pending DB method.")
        # Temporary fallback: Get all for profile and filter (inefficient)
        # This requires knowing the profile_id from the credential_id... difficult.
        # Best to implement the DB method.
        return None
        
    def search_credentials(self, query: str) -> List[Credential]:
        """Searches credentials across all profiles based on query."""
        # This requires significant refactoring for DB search.
        # Needs to potentially join profiles and credentials tables,
        # and handle decryption for searching sensitive fields if password is known.
        print("[CredentialManager] WARNING: search_credentials() needs refactoring for DB access.")
        return []
        # Simple search on non-encrypted fields for now
        # query = query.lower()
        # results = []
        # for cred in self.get_all_credentials(): # Inefficient
        #     if query in cred.app_name.lower():
        #         results.append(cred)
        # return results

    @staticmethod
    def validate_credential(credential: Credential) -> bool:
        # Basic validation, can be expanded
        if not credential.profile_id or not credential.app_name:
            return False
        # Add more checks if needed (e.g., username format?)
        return True
    
    def is_password_compromised(self, password: str) -> bool:
        """Checks if a password has been compromised using HaveIBeenPwned API."""
        if not password: return False
        sha1pwd = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        head, tail = sha1pwd[:5], sha1pwd[5:]
        api_url = f'https://api.pwnedpasswords.com/range/{head}'
        try:
            # Use requests library for HTTP request (need to add dependency)
            import requests 
            response = requests.get(api_url, timeout=5) # Add timeout
            response.raise_for_status() # Raise exception for bad status codes
            
            # Efficiently check if the tail exists in the response
            return tail in response.text
            
        except ImportError:
             print("[CredentialManager] 'requests' library not installed. Cannot check pwned passwords.")
             return False # Indicate compromise cannot be checked
        except requests.exceptions.RequestException as e:
            print(f"[CredentialManager] Error querying HaveIBeenPwned API: {e}")
            return False # Assume not compromised if API check fails
        except Exception as e:
             print(f"[CredentialManager] Unexpected error checking pwned password: {e}")
        return False
        
    def is_password_secure(self, password: str) -> bool:
        """Checks if a password meets basic security criteria (length, complexity)."""
        if not password or len(password) < 10: # Example: Minimum length
            return False
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_symbol = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        return has_upper and has_lower and has_digit and has_symbol
        
    def generate_password(self, length: int = 16, use_special_chars: bool = True) -> str:
        """Generates a secure random password."""
        import string
        import secrets
        
        chars = string.ascii_letters + string.digits
        if use_special_chars:
            # Define allowed special characters explicitly
            allowed_special = "!@#$%^&*()" 
            chars += allowed_special
            
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))
            # Ensure the generated password meets complexity requirements if needed
            # (e.g., must contain at least one of each type)
            # For simplicity now, we just generate and return.
            # Add checks here if stricter generation is required.
            if self.is_password_secure(password): # Check if generated meets criteria
                 return password
            # else: print("DEBUG: Regenerating password...") # Optional debug
        
    def attempt_decryption(self):
        """
        Placeholder method to trigger credential loading/decryption.
        Might be called after master password verification.
        In the DB approach, this might not be needed if reads are on-demand.
        """
        print("[CredentialManager] attempt_decryption called - In DB mode, data is loaded on demand.")
        # Triggering a refresh might involve emitting the signal
        self.credential_changed.emit()
        pass 