"""
Gestore della sincronizzazione con Google Drive.
"""

import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from cryptography.fernet import InvalidToken
from typing import Optional

class SyncManager:
    """Gestisce la sincronizzazione dei dati con Google Drive."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    TOKEN_FILE = 'config/token.json'
    CREDENTIALS_FILE = 'config/credentials.json'
    
    def __init__(self):
        """Inizializza il gestore di sincronizzazione."""
        self.credentials = None
        self.service = None
        self.client_id = ""
        self.client_secret = ""
        self.load_credentials()
        
    def load_credentials(self):
        """Carica le credenziali dal file di configurazione."""
        try:
            if os.path.exists(self.CREDENTIALS_FILE):
                with open(self.CREDENTIALS_FILE, 'r') as f:
                    creds = json.load(f)
                    self.client_id = creds.get('client_id', '')
                    self.client_secret = creds.get('client_secret', '')
        except Exception as e:
            print(f"Errore nel caricamento delle credenziali: {e}")
            
    def save_credentials(self, client_id: str, client_secret: str):
        """Salva le credenziali nel file di configurazione."""
        try:
            os.makedirs('config', exist_ok=True)
            with open(self.CREDENTIALS_FILE, 'w') as f:
                json.dump({
                    'client_id': client_id,
                    'client_secret': client_secret
                }, f)
            self.client_id = client_id
            self.client_secret = client_secret
            return True
        except Exception as e:
            print(f"Errore nel salvataggio delle credenziali: {e}")
            return False
            
    def authenticate(self):
        """Autentica l'utente con Google Drive."""
        if self.credentials and self.credentials.valid:
            self.service = build('drive', 'v3', credentials=self.credentials)
            return True

        # If no valid token, start the OAuth flow
        print("[SyncManager.authenticate] No valid token found. Starting OAuth flow...") # LOG
        try:
            # Client config using loaded (and potentially decrypted) secret
            # Ensure client_secret is available (must have been decrypted if needed)
            if not self.client_secret:
                 print("[SyncManager.authenticate] ERROR: Client Secret is not available (missing or failed decryption?). Cannot proceed with authentication.")
                 # Maybe prompt user again for password?
                 verified_pwd = self._get_verified_password_for_session("Master Password necessaria per autenticare Google Drive:")
                 if not verified_pwd:
                      return False # Still cannot proceed if password not provided
                 # If password provided, reload settings to trigger decryption again?
                 self.load_settings() # Attempt reload to get decrypted secret
                 if not self.client_secret: # Check again
                     print("[SyncManager.authenticate] ERROR: Client Secret still not available after password verification and reload.")
                     return False
                     
            client_config = {
                 'installed': {
                     'client_id': self.client_id,
                     'client_secret': self.client_secret, # Use the in-memory decrypted secret
                     'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                     'token_uri': 'https://oauth2.googleapis.com/token',
                     'redirect_uris': ["http://localhost"]
                 }
            }
            print("[SyncManager.authenticate] Using client_config dictionary for InstalledAppFlow (not reading secrets file).") # LOG
            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            # Run local server, this will block until user grants permission in browser
            creds = flow.run_local_server(port=0)
            print("[SyncManager] Google Drive authentication successful.")
            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Errore nell'autenticazione: {e}")
            return False
            
    def sync_data(self, data: dict):
        """Sincronizza i dati con Google Drive."""
        if not self.service:
            if not self.authenticate():
                return False
                
        try:
            file_metadata = {
                'name': 'password_manager_data.json',
                'mimeType': 'application/json'
            }
            
            media = MediaFileUpload(
                'data/password_manager_data.json',
                mimetype='application/json',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return True
        except Exception as e:
            print(f"Errore nella sincronizzazione: {e}")
            return False

    def _reset_to_defaults(self):
        """Resets all current settings to their default values."""
        print("[SyncManager._reset_to_defaults] Internal settings state reset to defaults.")

    def save_settings(self, verified_password_override: Optional[str] = None):
        """Saves all current settings (including potentially encrypted secret) to the JSON file.
        
        Args:
            verified_password_override: If provided, use this password for encryption 
                                        instead of relying on the current session verification state.
                                        Useful when called immediately after password set/change.
        """
        print(f"[SyncManager.save_settings] Saving settings to {self.settings_file}...")
        settings_data = {
            'sync_enabled': self.sync_enabled,
            'sync_interval': self.sync_interval,
            'hotkey_config': self.hotkey_config,
            'client_id': self.client_id,
            # Master password hash/salt are saved directly as they are
            'master_password_hash_b64': self.master_password_hash_b64,
            'master_password_salt_b64': self.master_password_salt_b64,
            # Handle client secret encryption
            'client_secret': None, # Placeholder
            'client_secret_encrypted': False # Default to false
        }

        # Determine which password to use for potential encryption
        master_pwd_is_set = self.is_master_password_set()
        password_to_use = None
        if verified_password_override:
             password_to_use = verified_password_override
             print("[SyncManager.save_settings] Using provided password override for encryption check.")
        else:
             # Check session verification status only if override not provided
             session_verified_pwd = self._get_verified_password_for_session(None) # Don't prompt here
             if session_verified_pwd:
                 password_to_use = session_verified_pwd
                 print("[SyncManager.save_settings] Using session-verified password for encryption check.")
             else:
                 print("[SyncManager.save_settings] No session-verified password available and no override provided.")
                 
        salt = self._get_master_password_salt() # Get salt bytes

        # Encrypt client secret if master password is set AND we have a password to use
        if master_pwd_is_set and password_to_use and salt and self.client_secret:
            print("[SyncManager.save_settings] Master password set and password available. Encrypting client secret...")
            encrypted_secret = _encrypt_setting(self.client_secret, password_to_use, salt)
            if encrypted_secret:
                settings_data['client_secret'] = encrypted_secret
                settings_data['client_secret_encrypted'] = True
                print("[SyncManager.save_settings] Client secret encrypted successfully.")
            else:
                 print("[SyncManager.save_settings] WARNING: Failed to encrypt client secret. Saving as plaintext (if available). Check logs.")
                 # Fallback to plaintext if encryption fails unexpectedly
                 settings_data['client_secret'] = self.client_secret
                 settings_data['client_secret_encrypted'] = False
        elif self.client_secret:
             # Save as plaintext if no master pwd or no password available for encryption
             print("[SyncManager.save_settings] Saving client secret as plaintext (master pwd not set or no verified password available).")
             settings_data['client_secret'] = self.client_secret
             settings_data['client_secret_encrypted'] = False
        else:
             print("[SyncManager.save_settings] No client secret to save.")
             settings_data['client_secret'] = None
             settings_data['client_secret_encrypted'] = False

        try:
            # Ensure directory exists
            os.makedirs('config', exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio delle impostazioni: {e}")
            return False 