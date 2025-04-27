"""
Finestra di impostazioni per la gestione della sincronizzazione con Google Drive.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFormLayout, QLineEdit,
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ..utils.sync_manager import SyncManager
import os

class SettingsDialog(QDialog):
    """
    Dialog per le impostazioni dell'applicazione.
    """
    
    def __init__(self, parent=None):
        """Inizializza il dialog delle impostazioni."""
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setMinimumWidth(400)
        
        self.sync_manager = SyncManager()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog."""
        layout = QVBoxLayout(self)
        
        # Titolo
        title = QLabel("Impostazioni")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Form impostazioni
        form_layout = QFormLayout()
        
        # Sincronizzazione
        self.sync_enabled = QCheckBox("Abilita sincronizzazione con Google Drive")
        self.sync_enabled.setChecked(self.sync_manager.sync_enabled)
        self.sync_enabled.stateChanged.connect(self.on_sync_toggled)
        form_layout.addRow(self.sync_enabled)
        
        # Credenziali Google Drive
        self.client_id = QLineEdit()
        self.client_id.setText(self.sync_manager.client_id)
        form_layout.addRow("Client ID:", self.client_id)
        
        self.client_secret = QLineEdit()
        self.client_secret.setText(self.sync_manager.client_secret)
        form_layout.addRow("Client Secret:", self.client_secret)
        
        layout.addLayout(form_layout)
        
        # Pulsanti
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def save_settings(self):
        """Salva le impostazioni."""
        self.sync_manager.sync_enabled = self.sync_enabled.isChecked()
        self.sync_manager.client_id = self.client_id.text()
        self.sync_manager.client_secret = self.client_secret.text()
        
        try:
            self.sync_manager.save_settings()
            self.sync_manager.save_credentials()
            QMessageBox.information(self, "Successo", "Impostazioni salvate con successo")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio: {str(e)}")

    def on_sync_toggled(self, state):
        """
        Gestisce il cambio di stato della checkbox di sincronizzazione.
        
        Args:
            state: Stato della checkbox
        """
        if state == Qt.Checked:
            if not os.path.exists(self.sync_manager.CREDENTIALS_FILE):
                QMessageBox.warning(
                    self,
                    "Credenziali mancanti",
                    "Configura prima le credenziali di Google Drive."
                )
                self.sync_enabled.setChecked(False)
                
    def browse_credentials(self):
        """Apre il dialogo per selezionare il file delle credenziali."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file delle credenziali",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # Copia il file nella directory config
                import shutil
                os.makedirs(os.path.dirname(self.sync_manager.CREDENTIALS_FILE), exist_ok=True)
                shutil.copy2(file_path, self.sync_manager.CREDENTIALS_FILE)
                self.credentials_path.setText(self.sync_manager.CREDENTIALS_FILE)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Impossibile copiare il file delle credenziali: {e}"
                ) 