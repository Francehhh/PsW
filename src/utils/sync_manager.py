"""
Gestore della sincronizzazione con Google Drive e delle impostazioni generali.
"""

import os
import json # Import json
import base64
import hashlib
import threading
import time # For sync loop
import hmac
from pathlib import Path
from typing import Optional

# Google API Client Libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io # For MediaIoBaseDownload

# Re-add Cryptography imports needed for password verification KDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Import DatabaseManager
from ..core.database_manager import get_db_manager, DatabaseManager

# --- Constants ---
# Rimuovi riferimenti a file JSON specifici
# SETTINGS_FILE = "data/settings.json"
# GOOGLE_TOKEN_FILE = "data/google_token.json" # Store token separately
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DRIVE_FOLDER_NAME = 'PsWCursor Backup'
DATABASE_FILENAME = "pswcursor_data.db" # Nome del file DB da sincronizzare
DATABASE_FILE_PATH = f"data/{DATABASE_FILENAME}" # Percorso completo del DB

# --- Rimuovi Encryption parameters e Utility Functions --- 
# SALT_SIZE = 16 # Gestito centralmente se necessario, ma Fernet lo include
# PBKDF2_ITERATIONS = 600000 # Ora in crypto.py e database_manager
# Rimuovi _derive_key, _encrypt_setting, _decrypt_setting
# def _derive_key(...)
# def _encrypt_setting(...)
# def _decrypt_setting(...)

# --- SyncManager Class (Singleton) ---
class SyncManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SyncManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        print("[SyncManager.__init__] Initializing SyncManager instance...")
        # Rimuovi riferimenti a settings_file, token_file
        # self.settings_file = settings_file
        # self.token_file = token_file
        self.db_manager: DatabaseManager = get_db_manager() # Ottieni istanza DB Manager

        # --- Internal State (inizializzati a default sicuri) --- 
        self.sync_enabled: bool = False
        self.sync_interval: int = 300
        self.drive_folder_id: Optional[str] = None
        self.client_id: Optional[str] = None
        # self.client_secret viene caricato on-demand da load_settings, non tenuto qui costantemente
        self._client_secret_internal: Optional[str] = None # Cache interna temporanea se necessario
        self.google_credentials = None
        self.drive_service = None
        self.master_password_hash_b64: Optional[str] = None # Letto da DB
        self.master_password_salt_b64: Optional[str] = None # Letto da DB
        # Rimuovi: self.client_secret_encrypted_in_file (ora è nel DB)
        # Hotkey config: Manteniamo come dict in memoria, letto/scritto da DB
        self.hotkey_config: dict = {'config_str': 'Nessuno', 'modifiers': 0, 'vk_code': 0}
        # Session password state
        self._session_master_password: Optional[str] = None
        self._session_password_verified: bool = False
        # Sync Loop control
        self.last_sync_time = None
        self.sync_in_progress = False
        self.sync_thread = None
        self.stop_event = threading.Event()

        # self.load_settings() # Defer loading until password is verified
        self._initialized = True
        print("[SyncManager.__init__] SyncManager initialization complete.")

    # --- Settings Load/Save --- 
    def load_settings(self):
        """Loads all settings from the DatabaseManager."""
        print(f"[SyncManager.load_settings] Loading settings from Database...")
        self._reset_to_defaults() # Resetta stato interno prima di caricare
        
        # --- Leggi valori base dal DB --- 
        try:
            self.sync_enabled = self.db_manager.get_setting('sync_enabled', 'false').lower() == 'true'
            try:
                self.sync_interval = int(self.db_manager.get_setting('sync_interval', '300'))
            except (ValueError, TypeError):
                self.sync_interval = 300 # Default se conversione fallisce
                print("[SyncManager.load_settings] WARNING: Invalid sync_interval in DB, using default 300.")
                
            self.drive_folder_id = self.db_manager.get_setting('drive_folder_id', '')
            # Hotkey config
            self.hotkey_config = {
                 'config_str': self.db_manager.get_setting('hotkey_config_str', 'Nessuno'),
                 'modifiers': int(self.db_manager.get_setting('hotkey_modifiers', '0') or 0),
                 'vk_code': int(self.db_manager.get_setting('hotkey_vk_code', '0') or 0)
            }
            
            # --- Master Password Hash/Salt --- 
            self.master_password_hash_b64 = self.db_manager.get_setting('master_password_hash_b64', '')
            self.master_password_salt_b64 = self.db_manager.get_setting('master_password_salt_b64', '')
            master_pwd_is_set = bool(self.master_password_hash_b64 and self.master_password_salt_b64)
            print(f"[SyncManager.load_settings] Master Pwd Hash/Salt loaded from DB. Is Set: {master_pwd_is_set}")

            # --- Google Client Credentials --- 
            self.client_id = self.db_manager.get_setting('client_id', '')
            client_secret_is_encrypted = self.db_manager.get_setting('client_secret_encrypted', 'false').lower() == 'true'
            print(f"[SyncManager.load_settings] Client ID loaded. Client Secret Encrypted Flag in DB: {client_secret_is_encrypted}")
            
            # Tentativo di decrittografare client_secret SOLO se necessario e possibile
            self._client_secret_internal = None # Resetta cache interna
            if client_secret_is_encrypted and master_pwd_is_set:
                print("[SyncManager.load_settings] Client secret is marked as encrypted. Attempting decryption...")
                verified_pwd = self._get_verified_password_for_session() # Non chiedere qui, usa solo se già verificato
                salt_bytes = self.get_master_password_salt()
                if verified_pwd and salt_bytes:
                    # Passa password e salt a get_setting per la decrittografia interna al DB manager
                    decrypted_secret = self.db_manager.get_setting('encrypted_client_secret', '', master_password=verified_pwd, salt=salt_bytes)
                    if decrypted_secret is not None:
                        self._client_secret_internal = decrypted_secret
                        print("[SyncManager.load_settings] Client secret decrypted successfully using session password.")
                    else:
                        print("[SyncManager.load_settings] WARNING: Failed to decrypt client secret with session password. Check password or data integrity.")
                else:
                    print("[SyncManager.load_settings] Cannot decrypt client secret: Master password not verified this session or salt missing.")
            elif not client_secret_is_encrypted:
                # Leggi come plaintext (ma non decrittografare)
                self._client_secret_internal = self.db_manager.get_setting('encrypted_client_secret', '')
                if self._client_secret_internal:
                    print("[SyncManager.load_settings] Client secret loaded as plaintext (not marked as encrypted).")
                else:
                    print("[SyncManager.load_settings] No client secret value found in DB.")
            else: # client_secret_is_encrypted è True ma master_pwd_is_set è False
                print("[SyncManager.load_settings] Client secret marked encrypted, but no master password set. Cannot load.")

            # --- Google API Token --- 
            # load_google_token sarà chiamato separatamente o quando necessario,
            # leggerà 'google_token_json' dal DB usando password/salt.
            # self.load_google_token() # Non caricarlo automaticamente qui? Forse meglio on-demand.
            self.google_credentials = None # Assicurati che sia resettato
            self.drive_service = None

        except Exception as e:
            print(f"[SyncManager.load_settings] UNEXPECTED ERROR loading settings from DB: {e}")
            # Non resettare a default qui? Potrebbe nascondere problemi
            # self._reset_to_defaults()
            # Potrebbe essere meglio sollevare l'eccezione? O loggare e continuare con valori default?
            # Per ora, logga e usa i default impostati da _reset_to_defaults() chiamato all'inizio.
            pass
            
        # Reset session verification state AFTER loading attempt is complete
        # self._session_password_verified = False # Non resettare qui, la verifica avviene in main.py
        # self._session_master_password = None
        print(f"[SyncManager.load_settings] Finished loading from DB. Sync Enabled: {self.sync_enabled}, Master Pwd Set: {self.is_master_password_set()}, Client Secret Loaded: {bool(self._client_secret_internal)}")

    def _reset_to_defaults(self):
         """Resets internal state variables to default values,
            PRESERVING session verification state.
         """
         print("[SyncManager._reset_to_defaults] Resetting internal state (preserving session verification)...)")
         self.sync_enabled = False
         self.sync_interval = 300
         self.drive_folder_id = None
         self.client_id = None
         self.google_credentials = None
         self.drive_service = None
         self.last_sync_time = None
         self.hotkey_config = {'config_str': 'Nessuno', 'modifiers': 0, 'vk_code': 0}
         self.master_password_hash_b64 = None
         self.master_password_salt_b64 = None
         self._client_secret_internal = None
         # --- DO NOT RESET THESE --- 
         # self._session_master_password = None
         # self._session_password_verified = False

    def save_settings(self, verified_password_override: Optional[str] = None):
        """Saves all current settings to the DatabaseManager.
        Handles encryption of client_secret based on password availability.

        Args:
            verified_password_override: If provided, use this password for encryption
                                        instead of relying on the current session verification state.
        """
        print(f"[SyncManager.save_settings] Saving settings to Database...")
        
        # Determine which password and salt to use for potential encryption
        master_pwd_is_set = self.is_master_password_set()
        password_to_use = None
        salt_bytes = None

        if verified_password_override is not None:
             password_to_use = verified_password_override if verified_password_override else None
             print(f"[SyncManager.save_settings] Using provided password override for encryption check (Provided: {bool(password_to_use)}).")
             if password_to_use: # Only get salt if we have a password
                 salt_bytes = self.get_master_password_salt() 
        else:
             session_verified_pwd = self._get_verified_password_for_session(None) # Don't prompt
             if session_verified_pwd:
                 password_to_use = session_verified_pwd
                 salt_bytes = self.get_master_password_salt() # Get salt associated with session pwd
                 print("[SyncManager.save_settings] Using session-verified password for encryption check.")
             else:
                 print("[SyncManager.save_settings] No session-verified password or override available for potential encryption.")
        
        # Determine if client_secret should be saved as encrypted
        # It should be encrypted if a master password IS set AND we have a password/salt to use for encryption NOW
        client_secret_to_be_encrypted = master_pwd_is_set and bool(password_to_use and salt_bytes)
        current_client_secret_value = self._client_secret_internal

        try:
            # Save non-encrypted settings first
            self.db_manager.set_setting('sync_enabled', str(self.sync_enabled).lower())
            self.db_manager.set_setting('sync_interval', str(self.sync_interval))
            self.db_manager.set_setting('drive_folder_id', self.drive_folder_id or '')
            self.db_manager.set_setting('hotkey_config_str', self.hotkey_config.get('config_str', 'Nessuno'))
            self.db_manager.set_setting('hotkey_modifiers', str(self.hotkey_config.get('modifiers', 0)))
            self.db_manager.set_setting('hotkey_vk_code', str(self.hotkey_config.get('vk_code', 0)))
            self.db_manager.set_setting('master_password_hash_b64', self.master_password_hash_b64 or '')
            self.db_manager.set_setting('master_password_salt_b64', self.master_password_salt_b64 or '')
            self.db_manager.set_setting('client_id', self.client_id or '')
            
            self.db_manager.set_setting('client_secret_encrypted', str(client_secret_to_be_encrypted).lower())
            
            # Save the client secret itself
            if client_secret_to_be_encrypted:
                print("[SyncManager.save_settings] Encrypting and saving client secret...")
                self.db_manager.set_setting('encrypted_client_secret', 
                                            current_client_secret_value or '', 
                                            master_password=password_to_use, 
                                            salt=salt_bytes)
            elif current_client_secret_value:
                print("[SyncManager.save_settings] Saving client secret as plaintext...")
                self.db_manager.set_setting('encrypted_client_secret', current_client_secret_value)
            else:
                print("[SyncManager.save_settings] No client secret to save. Saving empty.")
                self.db_manager.set_setting('encrypted_client_secret', '')
                 
            # Handle Google Token JSON
            google_token_json = self.google_credentials.to_json() if self.google_credentials else ''
            if google_token_json and master_pwd_is_set and password_to_use and salt_bytes:
                print("[SyncManager.save_settings] Encrypting and saving Google token JSON...")
                self.db_manager.set_setting('google_token_json', 
                                            google_token_json, 
                                            master_password=password_to_use, 
                                            salt=salt_bytes)
            elif google_token_json:
                print("[SyncManager.save_settings] Saving Google token JSON as plaintext...")
                self.db_manager.set_setting('google_token_json', google_token_json)
            else:
                print("[SyncManager.save_settings] No Google token JSON to save. Saving empty.")
                self.db_manager.set_setting('google_token_json', '')
                 
            print(f"[SyncManager.save_settings] Settings saved successfully to Database.")
            return True
        except Exception as e:
            print(f"[SyncManager.save_settings] CRITICAL ERROR saving settings to Database: {e}")
            return False

    # --- Google Drive Specific Methods --- 
    def load_google_token(self):
         """Loads and decrypts the Google API token from the database."""
         print("[SyncManager.load_google_token] Attempting to load token from DB...")
         self.google_credentials = None # Reset state
         self.drive_service = None
         
         master_pwd_is_set = self.is_master_password_set()
         token_json = None
         
         if master_pwd_is_set:
             verified_pwd = self._get_verified_password_for_session() # Use session password if verified
             salt_bytes = self.get_master_password_salt()
             if verified_pwd and salt_bytes:
                 print("[SyncManager.load_google_token] Decrypting token using session password...")
                 token_json = self.db_manager.get_setting('google_token_json', '', 
                                                        master_password=verified_pwd, 
                                                        salt=salt_bytes)
                 if token_json is None: # Decryption failed
                      print("[SyncManager.load_google_token] WARNING: Failed to decrypt token JSON.")
                      token_json = '' # Treat as empty if decryption fails
             else:
                 print("[SyncManager.load_google_token] Cannot decrypt token: Master password not verified or salt missing.")
                 # Try reading as plaintext? Only if not explicitly marked as encrypted?
                 # For simplicity, assume if master pwd is set, token *should* be encrypted.
                 token_json = '' # Treat as unavailable if pwd not verified
         else: # No master password set, read as plaintext
              print("[SyncManager.load_google_token] Reading token as plaintext (no master pwd set)...")
              token_json = self.db_manager.get_setting('google_token_json', '')

         if not token_json:
              print("[SyncManager.load_google_token] No token JSON found in DB.")
              return # Nothing to load
              
         # Load credentials from the retrieved JSON
         creds = None
         try:
             creds_info = json.loads(token_json)
             # Ensure required keys are present for Credentials object
             if all(k in creds_info for k in ('token', 'refresh_token', 'client_id', 'client_secret', 'scopes')):
                  creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
                  print(f"[SyncManager] Loaded Google credentials object from DB JSON.")
             else:
                  print("[SyncManager.load_google_token] ERROR: Token JSON from DB is missing required keys.")
         except json.JSONDecodeError:
             print(f"[SyncManager.load_google_token] ERROR: Could not decode token JSON from DB.")
         except Exception as e:
             print(f"[SyncManager] Error creating Credentials object from DB JSON: {e}")
             creds = None # Assicura che creds sia None in caso di errore

         # Refresh token if needed (logic remains similar)
         refreshed = False
         if creds and creds.expired and creds.refresh_token:
             try:
                 print("[SyncManager] Google token expired. Refreshing...")
                 creds.refresh(Request())
                 print("[SyncManager] Google token refreshed successfully.")
                 refreshed = True
             except Exception as e:
                 print(f"[SyncManager] Error refreshing Google token: {e}. Need re-authentication.")
                 # Consider clearing the token in DB? Risky.
                 # For now, just nullify creds in memory
                 creds = None

         self.google_credentials = creds

         # Save refreshed token immediately back to DB (encrypted if possible)
         if refreshed and self.google_credentials:
              print("[SyncManager.load_google_token] Saving refreshed token back to DB...")
              self.save_google_token(self.google_credentials) # save_google_token handles encryption

         # Build service if credentials are valid
         if self.google_credentials and self.google_credentials.valid:
             try:
                 self.drive_service = build('drive', 'v3', credentials=self.google_credentials)
                 print("[SyncManager] Google Drive service built successfully after loading token.")
             except Exception as e:
                 print(f"[SyncManager] Error building Google Drive service after loading token: {e}")
                 self.drive_service = None
         else:
              self.drive_service = None
              print("[SyncManager] Cannot build Google Drive service: Invalid or missing credentials after load attempt.")

    def save_google_token(self, creds):
         """Saves the Google API token JSON to the database, encrypting if possible."""
         if not creds:
             print("[SyncManager.save_google_token] No credentials provided to save.")
             token_json_to_save = ''
         else:
             try:
                 token_json_to_save = creds.to_json()
             except Exception as e:
                 print(f"[SyncManager.save_google_token] Error converting credentials to JSON: {e}")
                 token_json_to_save = ''
                 
         # Use save_settings logic to handle encryption based on current state
         # Get current verified password and salt
         password_to_use = self._get_verified_password_for_session()
         salt_bytes = self.get_master_password_salt()
         master_pwd_is_set = self.is_master_password_set()
         
         should_encrypt = master_pwd_is_set and bool(password_to_use and salt_bytes)
         
         try:
            if should_encrypt and token_json_to_save:
                 print("[SyncManager.save_google_token] Saving encrypted token to DB...")
                 self.db_manager.set_setting('google_token_json', 
                                             token_json_to_save, 
                                             master_password=password_to_use, 
                                             salt=salt_bytes)
            else:
                 print("[SyncManager.save_google_token] Saving token as plaintext to DB...")
                 self.db_manager.set_setting('google_token_json', token_json_to_save)
                 
            # Update internal state as well
            self.google_credentials = creds 
            # Rebuild service if creds are valid
            if self.google_credentials and self.google_credentials.valid:
                 try:
                      self.drive_service = build('drive', 'v3', credentials=self.google_credentials)
                 except Exception:
                      self.drive_service = None # Silently fail build here?
            else:
                 self.drive_service = None
                 
            print(f"[SyncManager.save_google_token] Google token saved to Database.")
         except Exception as e:
             print(f"[SyncManager.save_google_token] Error saving Google token to Database: {e}")

    def authenticate_google_drive(self):
        """Initiates the Google Drive OAuth flow if needed, using settings from DB."""
        # Load settings if not already loaded (ensure client_id/secret are available)
        # This might be redundant if load_settings is called reliably elsewhere
        if self.client_id is None or self._client_secret_internal is None:
             print("[SyncManager.authenticate] Settings not fully loaded. Loading now...")
             self.load_settings()
             
        # Retrieve client ID and secret from internal state (populated by load_settings)
        current_client_id = self.client_id
        current_client_secret = self._client_secret_internal
        
        if not current_client_id:
            print("[SyncManager.authenticate] Cannot authenticate: Client ID missing from settings.")
            # Maybe prompt user via SettingsDialog?
            return False
            
        if not current_client_secret:
             print("[SyncManager.authenticate] Client Secret missing or not decrypted.")
             if self.db_manager.get_setting('client_secret_encrypted', 'false').lower() == 'true':
                  print("[SyncManager.authenticate] Client secret is encrypted. Attempting check for session password...")
                  # Try getting verified password WITHOUT prompting
                  verified_pwd = self._get_verified_password_for_session()
                  salt_bytes = self.get_master_password_salt()
                  if verified_pwd and salt_bytes:
                       # Try decrypting again now
                       current_client_secret = self.db_manager.get_setting('encrypted_client_secret', '', master_password=verified_pwd, salt=salt_bytes)
                       if not current_client_secret:
                            print("[SyncManager.authenticate] ERROR: Failed to decrypt client secret with session password.")
                            return False
                       else:
                            print("[SyncManager.authenticate] Client secret decrypted using session password.")
                            self._client_secret_internal = current_client_secret 
                  else: # Password not verified in session
                       print("[SyncManager.authenticate] Cannot decrypt client secret: Password not verified in session. Aborting authentication.")
                       return False
             else: # Secret wasn't encrypted, but still missing
                  print("[SyncManager.authenticate] Client secret is missing but was not marked as encrypted.")
                  return False

        # Check if already authenticated (valid token loaded/refreshed)
        self.load_google_token() # Ensure latest token state is loaded from DB
        if self.google_credentials and self.google_credentials.valid:
             print("[SyncManager.authenticate] Already authenticated with Google Drive.")
             # Ensure drive service is built
             if not self.drive_service:
                  try:
                       self.drive_service = build('drive', 'v3', credentials=self.google_credentials)
                  except Exception as e:
                       print(f"[SyncManager.authenticate] Error rebuilding drive service: {e}")
                       self.drive_service = None
                       return False # Fail if service cannot be built
             return True

        # Start the OAuth flow
        print("[SyncManager.authenticate] Starting OAuth flow...")
        try:
            client_config = {
                 'installed': {
                     'client_id': current_client_id,
                     'client_secret': current_client_secret, # Use the retrieved secret
                     'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                     'token_uri': 'https://oauth2.googleapis.com/token',
                     'redirect_uris': ["http://localhost"] # Or use oob?
                 }
            }
            print("[SyncManager.authenticate] Using client_config dictionary.")
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            print("[SyncManager] Google Drive authentication successful via OAuth flow.")
            self.save_google_token(creds) # Save the new token to DB (encrypted if possible)
            # self.load_google_token() # save_google_token should update internal state now
            return True
        except Exception as e:
            print(f"[SyncManager] Google Drive authentication flow failed: {e}")
            self.google_credentials = None
            self.drive_service = None
            return False
            
    def _find_drive_folder(self) -> Optional[str]:
        """Finds the dedicated backup folder ID on Google Drive."""
        if not self.drive_service:
             print("[_find_drive_folder] Drive service not available.")
             return None
        try:
             response = self.drive_service.files().list(
                 q=f"mimeType='application/vnd.google-apps.folder' and name='{DRIVE_FOLDER_NAME}' and trashed=false",
                 spaces='drive',
                 fields='files(id, name)'
             ).execute()
             folders = response.get('files', [])
             if folders:
                 folder_id = folders[0].get('id')
                 print(f"[_find_drive_folder] Found existing folder '{DRIVE_FOLDER_NAME}' with ID: {folder_id}")
                 return folder_id
             else:
                 print(f"[_find_drive_folder] Folder '{DRIVE_FOLDER_NAME}' not found.")
                 return None
        except Exception as e:
             print(f"[_find_drive_folder] Error searching for folder: {e}")
             return None

    def _create_drive_folder(self) -> Optional[str]:
        """Creates the dedicated backup folder on Google Drive."""
        if not self.drive_service:
             print("[_create_drive_folder] Drive service not available.")
             return None
        print(f"[_create_drive_folder] Creating folder '{DRIVE_FOLDER_NAME}'...")
        try:
            file_metadata = {
                'name': DRIVE_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            folder_id = file.get('id')
            print(f"[_create_drive_folder] Folder created successfully with ID: {folder_id}")
            return folder_id
        except Exception as e:
            print(f"[_create_drive_folder] Error creating folder: {e}")
            return None
            
    def ensure_drive_folder_exists(self) -> bool:
         """Checks if the Drive folder exists, creates it if not, and stores the ID."""
         if self.drive_folder_id: # Already have it
              # Optional: Verify it still exists? Could be slow.
              return True
         if not self.drive_service:
              print("[ensure_drive_folder_exists] Cannot ensure folder: Drive service not initialized.")
              # Try to authenticate/initialize service first?
              if not self.authenticate_google_drive(): return False # Authenticate if service missing
              if not self.drive_service: return False # Still failed?

         folder_id = self._find_drive_folder()
         if not folder_id:
              folder_id = self._create_drive_folder()

         if folder_id:
              self.drive_folder_id = folder_id
              # Save the folder ID immediately to settings for persistence
              print("[ensure_drive_folder_exists] Saving newly found/created folder ID to settings...")
              self.save_settings(verified_password_override=self._session_master_password)
              return True
         else:
              print("[ensure_drive_folder_exists] Failed to find or create the Drive folder.")
              return False

    # --- Sync Loop Methods --- 
    def start_sync_loop(self):
        if not self.sync_enabled:
            print("[SyncManager.start_sync_loop] Sync is disabled in settings.")
            return
        if self.sync_thread and self.sync_thread.is_alive():
            print("[SyncManager.start_sync_loop] Sync loop already running.")
            return

        # Ensure authentication before starting loop
        if not self.drive_service:
             print("[SyncManager.start_sync_loop] Authenticating before starting loop...")
             if not self.authenticate_google_drive():
                  print("[SyncManager.start_sync_loop] Authentication failed. Cannot start sync loop.")
                  return

        # Ensure folder exists
        if not self.ensure_drive_folder_exists():
            print("[SyncManager.start_sync_loop] Failed to ensure Drive folder exists. Cannot start sync loop.")
            return
            
        print("[SyncManager.start_sync_loop] Starting sync loop...")
        self.stop_event.clear()
        self.sync_thread = threading.Thread(target=self._sync_cycle, daemon=True)
        self.sync_thread.start()

    def stop_sync_loop(self):
        """Stops the background sync loop."""
        if self.sync_thread and self.sync_thread.is_alive():
            print("[SyncManager] Stopping sync loop...")
            self.stop_event.set() # Signal the thread to stop
            self.sync_thread.join() # Wait for the thread to finish
            print("[SyncManager] Sync loop stopped.")
        self.sync_thread = None

    def _sync_cycle(self):
        """The function executed periodically by the sync thread."""
        while not self.stop_event.is_set():
            try:
                # Check if sync is enabled and enough time has passed
                do_sync = False
                if self.sync_enabled:
                    current_time = time.monotonic()
                    if self.last_sync_time is None or (current_time - self.last_sync_time >= self.sync_interval):
                        do_sync = True
                    # else: # Debugging interval
                        # print(f"DEBUG Sync Interval: {(current_time - self.last_sync_time):.1f} < {self.sync_interval}")
                
                if do_sync and not self.sync_in_progress:
                    print("[SyncManager._sync_cycle] Starting scheduled sync...")
                    self.sync_now()
                
                # Wait for the next check or until stopped
                # Wait in smaller intervals to be more responsive to stop_event
                self.stop_event.wait(timeout=min(self.sync_interval / 10, 10)) # Wait 1/10th interval or 10s max
            except Exception as e:
                 print(f"[SyncManager._sync_cycle] Error in sync cycle: {e}")
                 # Avoid busy-waiting on error
                 time.sleep(60)
        print("[SyncManager._sync_cycle] Exiting sync loop function.")

    def sync_now(self):
        """Performs an immediate synchronization (placeholder)."""
        if not self.sync_enabled:
            print("[SyncManager.sync_now] Sync is disabled.")
            return
        if self.sync_in_progress:
            print("[SyncManager.sync_now] Sync already in progress.")
            return
        if not self.drive_service:
            print("[SyncManager.sync_now] Drive service not available. Attempting authentication...")
            if not self.authenticate_google_drive():
                print("[SyncManager.sync_now] Authentication failed. Sync aborted.")
                return
        if not self.drive_folder_id:
            print("[SyncManager.sync_now] Drive folder ID not set. Ensuring folder exists...")
            if not self.ensure_drive_folder_exists():
                print("[SyncManager.sync_now] Could not ensure Drive folder. Sync aborted.")
                return

        self.sync_in_progress = True
        print("[SyncManager.sync_now] Starting immediate sync...")
        try:
            # --- Sync Logic --- 
            # TODO: Implement robust 2-way sync logic
            # 1. Get remote file list (settings.json, profiles.json) with modified times.
            # 2. Compare with local file modified times.
            # 3. Download remote changes if newer.
            # 4. Upload local changes if newer.
            # 5. Handle potential conflicts (e.g., both modified since last sync).

            # --- Placeholder Implementation: Upload settings.json & profiles.json --- 
            print(f"[SyncManager.sync_now] Placeholder: Uploading local files...")
            # Note: We should only upload if local is newer than remote.
            # Also, profile saving should likely trigger an upload.
            settings_upload_ok = self._upload_single_file(self.settings_file, self.drive_folder_id)
            # Assuming ProfileManager uses "data/profiles.json"
            profiles_file = os.path.join(os.path.dirname(self.settings_file), "profiles.json")
            profiles_upload_ok = self._upload_single_file(profiles_file, self.drive_folder_id)

            if settings_upload_ok and profiles_upload_ok:
                print(f"[SyncManager.sync_now] Placeholder: Upload successful.")
            else:
                print(f"[SyncManager.sync_now] Placeholder: Upload failed for one or more files.")
            # --- End Placeholder --- 

            self.last_sync_time = time.monotonic() # Use monotonic time
            print("[SyncManager.sync_now] Sync operation complete.")

        except Exception as e:
            print(f"[SyncManager.sync_now] Error during sync operation: {e}")
        finally:
            self.sync_in_progress = False

    def _upload_single_file(self, local_file_path: str, drive_folder_id: str) -> bool:
        """Helper to upload or update a single file on Drive."""
        if not os.path.exists(local_file_path):
            print(f"[_upload_single_file] Local file not found: {local_file_path}")
            return False
        if not self.drive_service:
            print(f"[_upload_single_file] Drive service not initialized.")
            return False
            
        file_name = os.path.basename(local_file_path)
        mime_type = 'application/json' if file_name.endswith('.json') else 'application/octet-stream'

        try:
            # Check if file already exists in the specific folder
            response = self.drive_service.files().list(
                 q=f"name='{file_name}' and '{drive_folder_id}' in parents and trashed=false",
                 spaces='drive',
                 fields='files(id, name)'
             ).execute()
            existing_files = response.get('files', [])

            file_metadata = {'name': file_name}
            media = MediaFileUpload(local_file_path, mimetype=mime_type, resumable=True)

            if existing_files:
                file_id = existing_files[0]['id']
                print(f"[_upload_single_file] Updating existing file '{file_name}' (ID: {file_id})...")
                updated_file = self.drive_service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields='id').execute()
                return bool(updated_file)
            else:
                print(f"[_upload_single_file] Creating new file '{file_name}'...")
                file_metadata['parents'] = [drive_folder_id]
                new_file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id').execute()
                return bool(new_file)

        except Exception as e:
            print(f"[_upload_single_file] Error uploading file '{file_name}': {e}")
            return False
            
    # --- Hotkey Methods --- 
    def get_hotkey_config(self) -> dict:
        return self.hotkey_config

    def set_hotkey_config(self, config_str: str, modifiers: int, vk_code: int):
        self.hotkey_config = {
            'config_str': config_str,
            'modifiers': modifiers,
            'vk_code': vk_code
        }
        # Save settings immediately when hotkey changes? Probably not.
        # Let SettingsDialog handle saving all settings together.
        # self.save_settings()

    # --- Master Password Methods --- 
    def is_master_password_set(self) -> bool:
        """Checks DIRECTLY in the database if master password hash and salt are set."""
        # Reads directly from DB, does not rely on loaded memory state.
        try:
            hash_val = self.db_manager.get_setting('master_password_hash_b64', '')
            salt_val = self.db_manager.get_setting('master_password_salt_b64', '')
            is_set = bool(hash_val and salt_val)
            # print(f"[SyncManager.is_master_password_set] DB Check -> Hash: '{hash_val[:5]}...', Salt: '{salt_val[:5]}...', IsSet: {is_set}") # Debug
            return is_set
        except Exception as e:
             print(f"[SyncManager.is_master_password_set] Error checking DB for hash/salt: {e}")
             return False # Assume not set if DB check fails

    def get_master_password_salt(self) -> Optional[bytes]:
         """Returns the raw bytes of the master password salt (loaded from DB)."""
         # Assumes load_settings() has been called
         if not self.master_password_salt_b64: return None
         try:
             # Use standard b64decode as stored in DB via DatabaseManager
             return base64.b64decode(self.master_password_salt_b64.encode('utf-8'))
         except Exception as e:
              print(f"[SyncManager] Error decoding master password salt from memory: {e}")
              return None

    def get_master_password_hash(self) -> Optional[bytes]:
        """Returns the raw bytes of the master password hash (loaded from DB)."""
        # Assumes load_settings() has been called
        if not self.master_password_hash_b64: return None
        try:
            # Use standard b64decode as stored in DB via DatabaseManager
            return base64.b64decode(self.master_password_hash_b64.encode('utf-8'))
        except Exception as e:
             print(f"[SyncManager] Error decoding master password hash from memory: {e}")
             return None

    def set_master_password_hash_salt(self, hash_bytes: bytes, salt_bytes: bytes):
        """Sets the hash and salt (in memory) from raw bytes, converting to b64 string.
           Persistence requires calling save_settings() afterwards.
        """
        if not hash_bytes or not salt_bytes:
            print("[SyncManager] Error: Attempted to set empty hash or salt.")
            return
        try:
            # Encode to standard Base64 for consistency
            self.master_password_hash_b64 = base64.b64encode(hash_bytes).decode('utf-8')
            self.master_password_salt_b64 = base64.b64encode(salt_bytes).decode('utf-8')
            print("[SyncManager] Master password hash and salt updated in memory.")
            # Also reset session verification as the password has changed
            self._session_password_verified = False
            self._session_master_password = None
            # Reset potentially decrypted client secret cache
            self._client_secret_internal = None 
        except Exception as e:
             print(f"[SyncManager] Error encoding hash/salt to Base64: {e}")
        # Note: save_settings() must be called by caller (like ProfileManager)

    def clear_master_password(self):
        """Clears the master password hash and salt (in memory).
           Persistence requires calling save_settings() afterwards.
        """
        print("[SyncManager] Clearing master password hash and salt in memory.")
        self.master_password_hash_b64 = None
        self.master_password_salt_b64 = None
        self._session_password_verified = False
        self._session_master_password = None
        # Reset potentially decrypted client secret cache
        self._client_secret_internal = None 
        # Note: save_settings() must be called by caller (like ProfileManager)

    # --- Password Verification Helper for SyncManager Session ---
    def _verify_session_master_password(self, password_attempt: str) -> bool:
        """Verifies the provided password against the hash/salt stored in the database."""
        # Read hash and salt DIRECTLY from DB for verification
        print("[SyncManager._verify_session_master_password] Reading hash/salt from DB for verification...")
        try:
            stored_hash_b64 = self.db_manager.get_setting('master_password_hash_b64')
            stored_salt_b64 = self.db_manager.get_setting('master_password_salt_b64')
        except Exception as e:
            print(f"[SyncManager._verify_session_master_password] Error reading hash/salt from DB: {e}")
            return False

        if not stored_hash_b64 or not stored_salt_b64:
            print("[SyncManager._verify_session_master_password] No master password hash/salt found in DB.")
            return False
        
        print("[SyncManager._verify_session_master_password] Attempting verification...")
        try:
            # Use standard b64decode 
            salt_bytes = base64.b64decode(stored_salt_b64.encode('utf-8'))
            
            # Derive key from user attempt using the retrieved salt
            kdf_verify = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32, # Length of the stored hash
                salt=salt_bytes,
                iterations=600000, # Must match iterations used when setting password
                backend=default_backend()
            )
            key_attempt_bytes = kdf_verify.derive(password_attempt.encode('utf-8'))
            
            # Decode the hash retrieved from DB
            stored_hash_bytes = base64.b64decode(stored_hash_b64.encode('utf-8'))
            
            # Compare using hmac.compare_digest
            is_valid = hmac.compare_digest(stored_hash_bytes, key_attempt_bytes)
            
            if is_valid:
                print("[SyncManager._verify_session_master_password] Verification successful.")
                # Set session state ONLY on successful verification
                self._session_master_password = password_attempt 
                self._session_password_verified = True
                 # Pre-populate in-memory hash/salt after successful verification
                 # This avoids reading from DB again if load_settings hasn't run yet
                self.master_password_hash_b64 = stored_hash_b64 
                self.master_password_salt_b64 = stored_salt_b64
            else:
                print("[SyncManager._verify_session_master_password] Verification failed: Password mismatch.")
                # Clear potentially outdated session state on failure
                self._session_master_password = None 
                self._session_password_verified = False
            return is_valid
        except (TypeError, ValueError, base64.binascii.Error) as e:
            print(f"[SyncManager._verify_session_master_password] Error decoding hash/salt from DB: {e}")
            # Clear session state on decoding error
            self._session_master_password = None 
            self._session_password_verified = False
            return False
        except Exception as e:
            print(f"[SyncManager._verify_session_master_password] Error during hash comparison: {e}")
            # Clear session state on other errors
            self._session_master_password = None 
            self._session_password_verified = False
            return False

    def _get_verified_password_for_session(self, prompt_message: Optional[str] = None) -> Optional[str]:
         """Gets the verified master password for the current session.
            If already verified, returns it.
            If not verified and prompt_message is provided, prompts the user.
            Returns None if not verified and no prompt, or if verification fails.
         """
         if self._session_password_verified and self._session_master_password is not None:
             return self._session_master_password
         elif prompt_message and self.is_master_password_set(): 
             print(f"[SyncManager._get_verified_password_for_session] Password not verified in session. Prompting user: '{prompt_message}'")
             try:
                 # Import locally to avoid potential circular dependencies
                 from ..ui.master_password_dialog import MasterPasswordDialog
                 password = MasterPasswordDialog.get_password(None, prompt_message)
                 if password is not None:
                     if self._verify_session_master_password(password):
                         print("[SyncManager._get_verified_password_for_session] Password verified via prompt.")
                         return password
                     else:
                          print("[SyncManager._get_verified_password_for_session] Verification failed via prompt.")
                          return None
                 else:
                      print("[SyncManager._get_verified_password_for_session] User cancelled password prompt.")
                      return None
             except ImportError:
                  print("[SyncManager._get_verified_password_for_session] ERROR: Could not import MasterPasswordDialog. Cannot prompt.")
                  return None
         else:
             return None

    # --- Client Secret Accessor --- 
    def get_client_secret(self) -> Optional[str]:
        """Returns the decrypted client secret, prompting for password if needed and possible."""
        # 1. Check if already decrypted and cached in memory
        if self._client_secret_internal:
            # print("[SyncManager.get_client_secret] Returning cached decrypted secret.") # Debug
            return self._client_secret_internal
            
        # 2. Check if it *should* be encrypted based on DB flag
        client_secret_is_encrypted = False
        try: # Defend against DB errors
            client_secret_is_encrypted = self.db_manager.get_setting('client_secret_encrypted', 'false').lower() == 'true'
        except Exception as e:
             print(f"[SyncManager.get_client_secret] Error checking encryption flag in DB: {e}")
             return None # Cannot proceed without flag
             
        if not client_secret_is_encrypted:
             # Read and return plaintext value directly from DB
             print("[SyncManager.get_client_secret] Secret not marked as encrypted, returning value from DB.")
             try:
                  return self.db_manager.get_setting('encrypted_client_secret', '')
             except Exception as e:
                  print(f"[SyncManager.get_client_secret] Error reading plaintext secret from DB: {e}")
                  return None
        
        # 3. If encrypted, try decrypting using session password or prompting
        print("[SyncManager.get_client_secret] Secret is encrypted, attempting decryption...")
        master_pwd_is_set = self.is_master_password_set()
        if not master_pwd_is_set:
            print("[SyncManager.get_client_secret] Cannot decrypt: Master password is not set.")
            return None 

        # Try getting verified password WITHOUT prompting
        verified_pwd = self._get_verified_password_for_session() 
        salt_bytes = self.get_master_password_salt()
        
        if verified_pwd and salt_bytes:
            # Attempt decryption using the verified password
            decrypted_secret = self.db_manager.get_setting('encrypted_client_secret', '', 
                                                         master_password=verified_pwd, 
                                                         salt=salt_bytes)
            if decrypted_secret is not None:
                print("[SyncManager.get_client_secret] Decryption successful.")
                self._client_secret_internal = decrypted_secret # Cache it
                return decrypted_secret
            else:
                print("[SyncManager.get_client_secret] Decryption failed (wrong password or corrupt data?).")
                return None # Decryption failed
        else:
            print("[SyncManager.get_client_secret] Cannot decrypt: Password not verified in session or salt missing.")
            return None # Could not get password/salt
            
# Optional: Provide a way to get the instance easily
# def get_sync_manager():
#     return SyncManager()