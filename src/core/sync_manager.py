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
        try:
            if os.path.exists(self.TOKEN_FILE):
                self.credentials = Credentials.from_authorized_user_file(
                    self.TOKEN_FILE, self.SCOPES)
                    
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CREDENTIALS_FILE, self.SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                    
                with open(self.TOKEN_FILE, 'w') as token:
                    token.write(self.credentials.to_json())
                    
            self.service = build('drive', 'v3', credentials=self.credentials)
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