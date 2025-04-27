"""
Widget della dashboard che mostra statistiche e informazioni utili.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from ..core.profile_manager import ProfileManager
from ..core.credential_manager import CredentialManager

class DashboardWidget(QWidget):
    """
    Widget della dashboard che mostra statistiche e informazioni utili.
    """
    
    def __init__(self, profile_manager: ProfileManager, credential_manager: CredentialManager):
        """Inizializza il widget della dashboard."""
        super().__init__()
        self.profile_manager = profile_manager
        self.credential_manager = credential_manager
        
        # Riferimenti ai label dei valori
        self.value_labels = {
            "Profili": None,
            "Credenziali": None,
            "Password Sicure": None,
            "Password Compromesse": None
        }
        
        self.setup_ui()
        self.update_stats()
        
    def setup_ui(self):
        """Configura l'interfaccia della dashboard."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Titolo
        title = QLabel("Dashboard")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Griglia delle statistiche
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        
        # Statistiche profili
        self.profiles_count = self.create_stat_card(
            "Profili",
            "0",
            "Numero totale di profili salvati"
        )
        stats_grid.addWidget(self.profiles_count, 0, 0)
        
        # Statistiche credenziali
        self.credentials_count = self.create_stat_card(
            "Credenziali",
            "0",
            "Numero totale di credenziali salvate"
        )
        stats_grid.addWidget(self.credentials_count, 0, 1)
        
        # Statistiche password sicure
        self.secure_passwords = self.create_stat_card(
            "Password Sicure",
            "0",
            "Password che soddisfano i criteri di sicurezza"
        )
        stats_grid.addWidget(self.secure_passwords, 1, 0)
        
        # Statistiche password compromesse
        self.compromised_passwords = self.create_stat_card(
            "Password Compromesse",
            "0",
            "Password trovate in violazioni di dati note"
        )
        stats_grid.addWidget(self.compromised_passwords, 1, 1)
        
        layout.addLayout(stats_grid)
        
        # Sezione azioni rapide
        quick_actions = QHBoxLayout()
        
        add_profile_btn = QPushButton("Nuovo Profilo")
        add_profile_btn.clicked.connect(self.show_add_profile)
        quick_actions.addWidget(add_profile_btn)
        
        layout.addLayout(quick_actions)
        
    def create_stat_card(self, title: str, value: str, description: str) -> QFrame:
        """
        Crea una card per mostrare una statistica.
        
        Args:
            title: Titolo della statistica
            value: Valore della statistica
            description: Descrizione della statistica
            
        Returns:
            QFrame: Card della statistica
        """
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        value_label.setStyleSheet("color: #4CAF50;")
        
        # Salva il riferimento al label del valore
        self.value_labels[title] = value_label
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #aaaaaa;")
        desc_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        
        return card
        
    def update_stats(self):
        """Aggiorna le statistiche mostrate."""
        # Aggiorna il conteggio dei profili
        if self.value_labels["Profili"]:
            self.value_labels["Profili"].setText(
                str(len(self.profile_manager.profiles))
            )
        
        # Aggiorna il conteggio delle credenziali
        if self.value_labels["Credenziali"]:
            self.value_labels["Credenziali"].setText(
                str(len(self.credential_manager.credentials))
            )
        
        # Aggiorna il conteggio delle password sicure
        if self.value_labels["Password Sicure"]:
            secure_count = sum(
                1 for cred in self.credential_manager.credentials
                if self.credential_manager.is_password_secure(cred.password)
            )
            self.value_labels["Password Sicure"].setText(
                str(secure_count)
            )
        
        # Aggiorna il conteggio delle password compromesse
        if self.value_labels["Password Compromesse"]:
            compromised_count = sum(
                1 for cred in self.credential_manager.credentials
                if self.credential_manager.is_password_compromised(cred.password)
            )
            self.value_labels["Password Compromesse"].setText(
                str(compromised_count)
            )
        
    def show_add_profile(self):
        """Mostra la finestra per aggiungere un nuovo profilo."""
        # Implementa la logica per aggiungere un profilo
        pass 