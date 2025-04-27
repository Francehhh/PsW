"""
Widget per la visualizzazione e gestione delle credenziali di un profilo.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ..core.profile_manager import Profile
from ..core.credential import Credential
from datetime import datetime
from .credential_list import CredentialList

class CredentialsView(QFrame):
    """Widget per visualizzare e gestire le credenziali di un profilo."""
    
    add_credential = Signal(Profile)
    delete_credential = Signal(Credential)
    
    def __init__(self, profile: Profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                margin: 4px;
                padding: 16px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QListWidget {
                background-color: #333333;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QListWidget::item {
                color: white;
                padding: 8px;
                border-bottom: 1px solid #444444;
            }
            QListWidget::item:selected {
                background-color: #4b4b4b;
            }
            QPushButton {
                background-color: #4b4b4b;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5b5b5b;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Titolo
        title = QLabel(f"Credenziali di {self.profile.name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Lista credenziali (solo CredentialList)
        self.credential_list = CredentialList()
        self.credential_list.credential_selected.connect(self.on_credential_selected)
        layout.addWidget(self.credential_list)
        
        # Pulsanti azioni
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        add_btn = QPushButton("Nuova Credenziale")
        add_btn.clicked.connect(lambda: self.add_credential.emit(self.profile))
        actions_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Elimina Credenziale")
        delete_btn.clicked.connect(self.on_delete_credential)
        actions_layout.addWidget(delete_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        self.populate_credentials()
        
    def populate_credentials(self):
        self.credential_list.clear()
        # Aggiungi tutte le credenziali del profilo
        for cred in getattr(self.profile, 'credentials', []):
            self.credential_list.add_credential(cred)
        
    def on_credential_selected(self, credential):
        # Aggiorna la visualizzazione del dettaglio credenziale
        # (implementa qui la logica per mostrare i dettagli della credenziale selezionata)
        pass
        
    def on_delete_credential(self):
        """Gestisce l'eliminazione della credenziale selezionata."""
        current_item = self.credential_list.currentItem()
        if current_item:
            self.delete_credential.emit(current_item.credential)
            self.credential_list.takeItem(self.credential_list.row(current_item)) 