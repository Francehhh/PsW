"""
Dialog per la registrazione della password master.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QClipboard, QFont

class RegistrationDialog(QDialog):
    """Dialog per la registrazione della password master."""
    
    registered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrazione - Imposta Master Password")
        self.setModal(True)
        self.setObjectName("RegistrationDialog")
        self.setProperty("class", "glassPane")
        self.setFixedSize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia utente."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Messaggio di avviso
        warning_label = QLabel(
            "⚠️ ATTENZIONE: Questa è la tua password master.\n\n"
            "È fondamentale che la salvi in un luogo sicuro (ad esempio un gestore di password o un foglio cartaceo).\n\n"
            "Se la perdi, non potrai più accedere ai tuoi dati.\n\n"
            "La password verrà copiata automaticamente negli appunti."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # Campo password
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Inserisci la password master")
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)
        
        # Campo conferma password
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("Conferma la password master")
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_edit)
        
        # Pulsanti
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.register_button = QPushButton("Registra")
        self.register_button.setStyleSheet("""
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
        self.register_button.clicked.connect(self.on_register)
        buttons_layout.addWidget(self.register_button)
        
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
        
    def on_register(self):
        """Gestisce il click sul pulsante di registrazione."""
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        
        if not password or not confirm:
            QMessageBox.warning(
                self,
                "Errore",
                "Inserisci una password valida."
            )
            return
            
        if password != confirm:
            QMessageBox.warning(
                self,
                "Errore",
                "Le password non coincidono."
            )
            return
            
        # Copia la password negli appunti
        clipboard = QApplication.clipboard()
        clipboard.setText(password)
        
        # Mostra un messaggio di conferma
        QMessageBox.information(
            self,
            "Password Copiata",
            "La password è stata copiata negli appunti.\n"
            "Assicurati di salvarla in un luogo sicuro."
        )
        
        # Emetti il segnale con la password
        self.registered.emit(password)
        self.accept() 