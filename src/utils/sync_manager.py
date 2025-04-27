"""
Modulo per la gestione della sincronizzazione con Google Drive.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import pickle
import json
import io
from typing import Optional, Dict, Any

class SyncManager:
    """
    Gestisce la sincronizzazione dei dati con Google Drive.
    
    Utilizza l'API di Google Drive per il backup e la sincronizzazione
    dei file di configurazione e dei dati.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    TOKEN_FILE = 'config/token.pickle'
    CREDENTIALS_FILE = 'config/credentials.json'
    SETTINGS_FILE = 'config/sync_settings.json'
    DRIVE_FOLDER_NAME = 'PsW Backup'
    
    def __init__(self):
        """Inizializza il gestore della sincronizzazione."""
        self.creds = None
        self.service = None
        self.sync_enabled = False
        self.drive_folder_id = None
        self.client_id = ""
        self.client_secret = ""
        self.load_settings()
        self.load_credentials()
        
    def load_settings(self):
        """Carica le impostazioni di sincronizzazione."""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.sync_enabled = settings.get('sync_enabled', False)
                    self.drive_folder_id = settings.get('drive_folder_id')
            except Exception as e:
                print(f"Errore nel caricamento delle impostazioni: {e}")
                self.sync_enabled = False
                self.drive_folder_id = None
                
    def load_credentials(self):
        """Carica le credenziali di Google Drive."""
        if os.path.exists(self.CREDENTIALS_FILE):
            try:
                with open(self.CREDENTIALS_FILE, 'r') as f:
                    creds = json.load(f)
                    self.client_id = creds.get('client_id', '')
                    self.client_secret = creds.get('client_secret', '')
            except Exception as e:
                print(f"Errore nel caricamento delle credenziali: {e}")
                self.client_id = ""
                self.client_secret = ""
                
    def save_settings(self):
        """Salva le impostazioni di sincronizzazione."""
        settings = {
            'sync_enabled': self.sync_enabled,
            'drive_folder_id': self.drive_folder_id
        }
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Errore nel salvataggio delle impostazioni: {e}")
            
    def save_credentials(self):
        """Salva le credenziali di Google Drive."""
        creds = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            os.makedirs('config', exist_ok=True)
            with open(self.CREDENTIALS_FILE, 'w') as f:
                json.dump(creds, f)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio delle credenziali: {e}")
            return False
            
    def enable_sync(self) -> bool:
        """
        Attiva la sincronizzazione con Google Drive.
        
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not os.path.exists(self.CREDENTIALS_FILE):
            print("File delle credenziali non trovato. Configura prima le credenziali di Google Drive.")
            return False
            
        try:
            self.initialize_service()
            if not self.service:
                return False
                
            # Crea la cartella su Google Drive se non esiste
            if not self.drive_folder_id:
                self.drive_folder_id = self.create_drive_folder()
                if not self.drive_folder_id:
                    return False
                    
            self.sync_enabled = True
            self.save_settings()
            return True
        except Exception as e:
            print(f"Errore nell'attivazione della sincronizzazione: {e}")
            return False
            
    def disable_sync(self):
        """Disattiva la sincronizzazione con Google Drive."""
        self.sync_enabled = False
        self.save_settings()
        
    def create_drive_folder(self) -> Optional[str]:
        """
        Crea una cartella dedicata su Google Drive.
        
        Returns:
            ID della cartella creata o None in caso di errore
        """
        try:
            file_metadata = {
                'name': self.DRIVE_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            print(f"Errore nella creazione della cartella: {e}")
            return None
            
    def initialize_service(self):
        """Inizializza il servizio Google Drive."""
        if not os.path.exists(self.CREDENTIALS_FILE):
            return
            
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
                
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)
                
        self.service = build('drive', 'v3', credentials=self.creds)
        
    def upload_file(self, file_path: str, mime_type: str = 'application/json') -> Optional[str]:
        """
        Carica un file su Google Drive.
        
        Args:
            file_path: Percorso del file da caricare
            mime_type: Tipo MIME del file
            
        Returns:
            ID del file caricato o None in caso di errore
        """
        if not self.sync_enabled or not self.service:
            return None
            
        try:
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [self.drive_folder_id]
            }
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            print(f"Errore durante il caricamento del file: {e}")
            return None
            
    def download_file(self, file_id: str, save_path: str) -> bool:
        """
        Scarica un file da Google Drive.
        
        Args:
            file_id: ID del file da scaricare
            save_path: Percorso dove salvare il file
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not self.sync_enabled or not self.service:
            return False
            
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            with open(save_path, 'wb') as f:
                f.write(fh.getvalue())
            return True
        except Exception as e:
            print(f"Errore durante il download del file: {e}")
            return False
            
    def list_files(self) -> list:
        """
        Lista i file nella cartella dedicata su Google Drive.
        
        Returns:
            Lista dei file disponibili
        """
        if not self.sync_enabled or not self.service:
            return []
            
        try:
            results = self.service.files().list(
                q=f"'{self.drive_folder_id}' in parents",
                pageSize=10,
                fields="nextPageToken, files(id, name)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Errore durante il recupero dei file: {e}")
            return []
            
    def delete_file(self, file_id: str) -> bool:
        """
        Elimina un file da Google Drive.
        
        Args:
            file_id: ID del file da eliminare
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        if not self.sync_enabled or not self.service:
            return False
            
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Errore durante l'eliminazione del file: {e}")
            return False 