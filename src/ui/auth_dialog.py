"""
Dialog per l'autenticazione dell'utente.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from typing import Optional

from ..utils.sync_manager import SyncManager

class AuthDialog(QDialog):
    """Dialog per l'autenticazione dell'utente."""
    
    authenticated = Signal(str)
    
    def __init__(self, sync_manager: SyncManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autenticazione Richiesta")
        self.setModal(True)
        self.sync_manager = sync_manager
        self.password: Optional[str] = None
        self.setObjectName("AuthDialog")
        self.setProperty("class", "glassPane")
        self.setFixedSize(400, 200)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia utente."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Messaggio di benvenuto
        welcome_label = QLabel(
            "🔐 Benvenuto in PsW\n\n"
            "Inserisci la tua master password per accedere alle tue credenziali."
        )
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(welcome_label)
        
        # Campo password
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password master")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.password_edit)
        
        # Pulsanti
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.login_button = QPushButton("Accedi")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_button.clicked.connect(self.on_login)
        buttons_layout.addWidget(self.login_button)
        
        self.cancel_button = QPushButton("Annulla")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
    def on_login(self):
        """Gestisce il click sul pulsante di login."""
        password = self.password_edit.text()
        
        if not password:
            QMessageBox.warning(
                self,
                "Errore",
                "Inserisci una password valida."
            )
            return
            
        is_correct = self.sync_manager._verify_session_master_password(password)
            
        if is_correct:
            self.password = password
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Errore",
                "Password non valida. Riprova."
            )
            self.password_edit.clear()
            self.password_edit.setFocus() 