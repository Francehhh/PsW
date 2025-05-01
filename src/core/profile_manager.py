"""
Modulo per la gestione dei profili utente.
Ora interagisce con DatabaseManager per lo storage e la crittografia.
"""

import base64
import hashlib
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..utils.sync_manager import SyncManager
from ..core.database_manager import get_db_manager, DatabaseManager

from PySide6.QtCore import QObject, Signal

@dataclass
class Profile:
    """
    Rappresenta un profilo utente (struttura dati in memoria).
    La crittografia avviene a livello DB.
    """
    id: int # ID dal DB sarà intero
    name: str
    last_name: Optional[str] = None
    url: Optional[str] = None # Aggiunto url mancante
    username: Optional[str] = None
    password: Optional[str] = None # Password in chiaro in memoria dopo decrittografia
    email: Optional[str] = None # Aggiunto email mancante
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None # Caricato da DB
    updated_at: Optional[str] = None # Caricato da DB
    
class ProfileManager(QObject):
    """
    Gestisce i profili utente, caricandoli/salvandoli tramite DatabaseManager.
    Mantiene una cache in memoria dei profili caricati.
    """
    profile_changed = Signal()
    
    def __init__(self):
        """
        Inizializza il gestore dei profili.
        """
        super().__init__()
        self.profiles: List[Profile] = [] # Cache in memoria
        self.sync_manager = SyncManager() 
        self.db_manager: DatabaseManager = get_db_manager() # Ottieni istanza DB
        
        print("[ProfileManager] Initialized.")
        
    # --- Master Password Management (rimane invariato, delega a SyncManager) ---
    def is_master_password_set(self) -> bool:
        """Checks SyncManager to see if a master password is configured."""
        return self.sync_manager.is_master_password_set()
        
    def set_master_password(self, password: str) -> bool:
        """
        Imposta/modifica/rimuove la master password.
        La logica di crittografia/decrittografia dei profili E' STATA RIMOSSA.
        Ora si occupa solo di aggiornare hash/salt in SyncManager/DB
        e chiamare save_settings.
        La (de)crittografia dei profili avviene on-demand tramite DatabaseManager.
        """
        if not password:
            # Rimozione password
            if self.is_master_password_set():
                print("[ProfileManager] Attempting to remove master password...")
                # Richiede comunque la vecchia password per la rimozione
                if not self._prompt_and_verify_password("Verifica la vecchia password per rimuoverla:"):
                    return False
                
                # Non serve più decrittografare i profili qui
                # if not self._decrypt_all_profiles(...): return False
                
                # Pulisce hash/salt in SyncManager (memoria)
                self.sync_manager.clear_master_password()
                try:
                    # Salva le impostazioni (che ora includono hash/salt vuoti) nel DB
                    # Passa None come override per assicurarsi che il client_secret venga salvato in chiaro.
                    print(f"[ProfileManager] Calling SyncManager.save_settings to persist password removal...")
                    self.sync_manager.save_settings(verified_password_override=None) 
                    print("[ProfileManager] Master password hash/salt removed from DB via save_settings.")
                except Exception as e:
                    print(f"[ProfileManager] CRITICAL ERROR saving settings after clearing hash/salt: {e}. State may be inconsistent.")
                    # Ricarica le impostazioni per riflettere lo stato reale del DB?
                    try: self.sync_manager.load_settings() 
                    except: pass # Ignora errori nel recupero
                    return False 
                    
                # Non serve più salvare i profili qui (erano salvati dopo decrittografia)
                # self.save_profiles() 
                print("[ProfileManager] Master password removed.")
                # Ricarica i profili per riflettere il nuovo stato (non criptato)
                self.load_profiles() 
                return True
            else:
                return True # Già non impostata
        
        # --- Impostazione/Modifica Password --- 
        new_salt = os.urandom(16)
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), new_salt, 600000)
        
        # Non serve più decrittografare profili esistenti con vecchia password qui
        # if self.is_master_password_set():
            # ... logica vecchia di decrittografia rimossa ...
            # if not self._decrypt_all_profiles(...): return False

        # Non serve più crittografare i profili con la nuova password qui
        # if not self._encrypt_all_profiles(...): return False
        
        # Imposta hash/salt in SyncManager (memoria)
        self.sync_manager.set_master_password_hash_salt(new_hash, new_salt)
        try:
            # Salva le impostazioni (nuovo hash/salt) nel DB
            # Passa la nuova password per crittografare client_secret/token se presenti
            print(f"[ProfileManager] Calling SyncManager.save_settings to persist new hash/salt...")
            self.sync_manager.save_settings(verified_password_override=password) 
            print("[ProfileManager] New master password hash/salt saved to DB via save_settings.")
        except Exception as e:
             print(f"[ProfileManager] CRITICAL ERROR saving settings after setting hash/salt: {e}. State may be inconsistent.")
             # Rimuove hash/salt dalla memoria se il salvataggio fallisce
             self.sync_manager.clear_master_password() 
             return False
             
        # Assicura che la sessione sia marcata come verificata con la nuova password
        # Questo avviene già dentro set_master_password_hash_salt?
        # Chiamiamolo esplicitamente per sicurezza.
        if not self.sync_manager._verify_session_master_password(password):
             # Questo non dovrebbe accadere se abbiamo appena impostato hash/salt
             print("[ProfileManager] CRITICAL WARNING: Failed to verify password immediately after setting hash/salt!")
             # Cosa fare? Forse ritornare False?
        
        # Non serve più salvare esplicitamente i profili qui
        # self.save_profiles() 
        print(f"[ProfileManager] Master password set/changed.")
        # Ricarica i profili per riflettere il nuovo stato (criptato)
        self.load_profiles()
        return True

    # verify_master_password rimane invariato (delega a SyncManager)
    def verify_master_password(self, password: str) -> bool:
        print("[ProfileManager] Delegating password verification to SyncManager...")
        return self.sync_manager._verify_session_master_password(password)

    # --- Core Profile Operations (Refactored for DB) ---
    def load_profiles(self):
        """Loads profiles from DatabaseManager and populates the in-memory cache.
           Relies on SyncManager session state for password verification.
        """
        print("[ProfileManager.load_profiles] Starting profile load from DB...") 
        self.profiles = [] # Clear cache
        
        # Inizializza esplicitamente le variabili
        verified_password = None
        salt_bytes = None
        
        password_needed = self.is_master_password_set()
        
        if password_needed:
            # Password è necessaria, proviamo a prenderla dalla sessione
            verified_password = self.sync_manager._get_verified_password_for_session()
            salt_bytes = self.sync_manager.get_master_password_salt()
            print(f"[ProfileManager.load_profiles] Password needed. Verified Pwd available: {bool(verified_password)}, Salt available: {bool(salt_bytes)}")

            if not verified_password or not salt_bytes:
                # Password necessaria ma non verificata/salt mancante -> non caricare
                print("[ProfileManager.load_profiles] Master password is set but not verified in session (or salt missing). Cannot load profiles.")
                # Emetti segnale con lista vuota e ritorna
                if self.profile_changed:
                     print("[ProfileManager.load_profiles] Emitting profile_changed (empty list).")
                     self.profile_changed.emit()
                return # Esce dalla funzione, non carica nulla
            # Se siamo qui, password necessaria e verificata, procedi con password/salt
            print("[ProfileManager.load_profiles] Proceeding with verified password and salt.")
        else:
            # Password non necessaria (non impostata)
            print("[ProfileManager.load_profiles] Master password not set. Loading without password.")
            # verified_password e salt_bytes rimangono None
        
        # --- Chiamata a DB Manager --- 
        # Ora verified_password/salt_bytes sono corretti (o None se non servono)
        try:
            print(f"[ProfileManager.load_profiles] Calling db_manager.get_all_profiles (pwd provided: {bool(verified_password)})..." ) # Log DB call
            profiles_data = self.db_manager.get_all_profiles(verified_password, salt_bytes)
            print(f"[ProfileManager.load_profiles] db_manager.get_all_profiles returned: {len(profiles_data)} items.") # Log result count
            # print(f"DEBUG: Profiles data from DB: {profiles_data}") # Optional detailed log
            
            temp_profiles = []
            for profile_dict in profiles_data:
                print(f"[ProfileManager.load_profiles] Processing profile data: {profile_dict.get('id')}, {profile_dict.get('name')}") # Log processing
                try:
                    # Ensure all expected keys for Profile dataclass exist, providing None if missing
                    profile_args = {
                        'id': profile_dict.get('id'),
                        'name': profile_dict.get('name'),
                        'last_name': profile_dict.get('last_name'),
                        'url': profile_dict.get('url'),
                        'username': profile_dict.get('username'),
                        'password': profile_dict.get('password'), # Already decrypted by DBManager
                        'email': profile_dict.get('email'),
                        'phone': profile_dict.get('phone'),
                        'address': profile_dict.get('address'),
                        'notes': profile_dict.get('notes'),
                        'created_at': profile_dict.get('created_at'),
                        'updated_at': profile_dict.get('updated_at')
                    }
                    # Filter out None values if the dataclass definition doesn't handle them directly
                    # Although the current definition seems okay with Optional[str]=None
                    # filtered_args = {k: v for k, v in profile_args.items() if v is not None}
                    
                    temp_profiles.append(Profile(**profile_args))
                    print(f"    -> Successfully converted profile ID {profile_args['id']} to object.") # Log success
                except Exception as e:
                    print(f"[ProfileManager] Error converting DB data to Profile object: {e} - Data: {profile_dict}")
            
            self.profiles = temp_profiles
            print(f"[ProfileManager.load_profiles] Updated cache with {len(self.profiles)} profiles.")
            
            if self.profile_changed:
                 print("[ProfileManager.load_profiles] Emitting profile_changed signal.") # Log emit
                 self.profile_changed.emit()
                 
        except Exception as e:
            print(f"[ProfileManager] UNEXPECTED ERROR loading profiles from DB: {e}")
            self.profiles = []
            if self.profile_changed:
                 print("[ProfileManager.load_profiles] Emitting profile_changed (error state).") # Log emit
                 self.profile_changed.emit()
            
    # Rimuovi save_profiles - le modifiche sono salvate al momento (add/update/delete)
    # def save_profiles(self):
    #    ...
            
    def add_profile(self, profile: Profile) -> bool:
        """Adds a new profile via DatabaseManager and reloads the local cache."""
        print(f"[ProfileManager] Attempting to add profile: {profile.name}")
        
        # ID is assigned by DB, ensure it's None or handled appropriately before add
        if hasattr(profile, 'id') and profile.id is not None:
             print(f"[ProfileManager] Warning: Profile object already has an ID ({profile.id}) before adding. DB will assign a new one.")

        verified_password = self.sync_manager._get_verified_password_for_session()
        salt_bytes = self.sync_manager.get_master_password_salt()

        if self.is_master_password_set() and (not verified_password or not salt_bytes):
            print("[ProfileManager] Cannot add profile: Master password set but not verified or salt missing.")
            return False
        
        # Convert Profile object to dict for DBManager (excluding id)
        # Include the plaintext password if present in the Profile object
        profile_data = {
            'name': profile.name,
            'last_name': profile.last_name,
            'url': profile.url,
            'username': profile.username,
            'password': profile.password, # Pass plaintext password from Profile object
            'email': profile.email,
            'phone': profile.phone,
            'address': profile.address,
            'notes': profile.notes
        }
        
        try:
            new_id = self.db_manager.add_profile(profile_data, verified_password, salt_bytes)
            if new_id is not None:
                print(f"[ProfileManager] Profile '{profile.name}' added to DB with ID {new_id}. Reloading profiles...")
                # Reload all profiles from DB to refresh cache and ensure consistency
                self.load_profiles() 
                # The load_profiles method now emits the signal
            return True
            # Se new_id è None (fallimento DB), esce dall'if e arriva qui
            print(f"[ProfileManager] Failed to add profile '{profile.name}' to DB (DB method returned None).")
            return False
        except Exception as e: 
            print(f"[ProfileManager] Error adding profile '{profile.name}': {e}")
            return False
        
    def update_profile(self, profile_id: int, updated_profile: Profile) -> bool:
        """Updates an existing profile via DatabaseManager and reloads the local cache."""
        print(f"[ProfileManager] Attempting to update profile ID: {profile_id}")

        verified_password = self.sync_manager._get_verified_password_for_session()
        salt_bytes = self.sync_manager.get_master_password_salt()

        if self.is_master_password_set() and (not verified_password or not salt_bytes):
            print(f"[ProfileManager] Cannot update profile {profile_id}: Master password set but not verified or salt missing.")
            return False

        # Convert Profile object to dict for DBManager (excluding id, created_at, updated_at)
        profile_data = {
            'name': updated_profile.name,
            'last_name': updated_profile.last_name,
            'url': updated_profile.url,
            'username': updated_profile.username,
            'password': updated_profile.password, # Pass plaintext password
            'email': updated_profile.email,
            'phone': updated_profile.phone,
            'address': updated_profile.address,
            'notes': updated_profile.notes
        }
        
        try:
            success = self.db_manager.update_profile(profile_id, profile_data, verified_password, salt_bytes)
            if success:
                print(f"[ProfileManager] Profile ID {profile_id} updated in DB. Reloading profiles...")
                self.load_profiles()
                return True
            else:
                print(f"[ProfileManager] Failed to update profile ID {profile_id} in DB (not found or DB error).")
                return False
        except Exception as e:
            print(f"[ProfileManager] Error updating profile ID {profile_id}: {e}")
            return False

    def delete_profile(self, profile_id: int) -> bool:
        """Deletes a profile via DatabaseManager and reloads the local cache."""
        print(f"[ProfileManager] Attempting to delete profile ID: {profile_id}")
        try:
            success = self.db_manager.delete_profile(profile_id)
            if success:
                print(f"[ProfileManager] Profile ID {profile_id} deleted from DB. Reloading profiles...")
                # Reload to update cache and signal UI
                self.load_profiles()
                return True
            else:
                print(f"[ProfileManager] Failed to delete profile ID {profile_id} from DB (not found or DB error).")
                return False
        except Exception as e:
            print(f"[ProfileManager] Error deleting profile ID {profile_id}: {e}")
        return False
        
    def get_profile(self, profile_id: int) -> Optional[Profile]:
        """Gets a specific profile from the in-memory cache."""
        # Assumes load_profiles() has populated the cache correctly
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        print(f"[ProfileManager] Profile ID {profile_id} not found in cache.") # Log if not found
        return None
        
    def get_all_profiles(self) -> List[Profile]:
        """Returns the current in-memory list of profiles."""
        # The list is populated/updated by load_profiles()
        print(f"[ProfileManager] Returning {len(self.profiles)} profiles from cache.")
        return self.profiles
        
    def search_profiles(self, query: str) -> List[Profile]:
        """Searches profiles in the in-memory cache across multiple fields."""
        if not query: return self.profiles # Return all if query is empty
        
        # Search should work fine as profiles in cache are decrypted by load_profiles
        print(f"[ProfileManager] Searching profiles in cache for query: '{query}'")
        query = query.lower()
        results = []
        for profile in self.profiles:
            if (profile.name and query in profile.name.lower()) or \
               (profile.url and query in profile.url.lower()) or \
               (profile.username and query in profile.username.lower()) or \
               (profile.email and query in profile.email.lower()) or \
               (profile.notes and query in profile.notes.lower()): 
                results.append(profile)
                   
        print(f"[ProfileManager] Search found {len(results)} results.")
        return results
        
    @staticmethod
    def validate_profile(profile: Profile) -> bool:
        """Validates basic profile data (non-empty name)."""
        # Simpler validation now, DB handles constraints
        if not profile.name: # Basic check
            print("[ProfileManager] Validation failed: Profile name cannot be empty.")
            return False
        return True 