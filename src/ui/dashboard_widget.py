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
        
        # Sezione azioni rapide - Rimuovere o commentare
        # quick_actions = QHBoxLayout()
        # 
        # add_profile_btn = QPushButton("Nuovo Profilo")
        # add_profile_btn.clicked.connect(self.show_add_profile)
        # quick_actions.addWidget(add_profile_btn)
        # 
        # layout.addLayout(quick_actions)
        
        layout.addStretch() # Add stretch to push elements up
        
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
        # Use object name for QSS targeting
        desc_label.setObjectName("statDescLabel") 
        # desc_label.setStyleSheet("color: #aaaaaa;") # Removed, handled globally
        desc_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        
        # Set object name for the card itself for QSS
        card.setObjectName("statCard") 
        # card.setFrameShape(QFrame.StyledPanel) # Shape might conflict with QSS border-radius
        # card.setStyleSheet(""" # Removed, handled globally by #statCard or .glassPane
        #     QFrame {
        #         background-color: #2b2b2b;
        #         border-radius: 10px;
        #         padding: 15px;
        #     }
        # """)
        card.setProperty("class", "glassPane") # Apply the glassPane class
        
        return card
        
    def update_stats(self):
        """Aggiorna le statistiche mostrate usando i metodi pubblici dei manager."""
        print("[DashboardWidget] Updating stats...")
        
        # --- Profile Stats --- 
        try:
            # Use public getter for profiles
            all_profiles = self.profile_manager.get_all_profiles()
            total_profiles = len(all_profiles)
            if self.value_labels.get("Profili"):
                self.value_labels["Profili"].setText(str(total_profiles))
            else:
                 print("[DashboardWidget] Warning: Label for 'Profili' not found in value_labels.")
        except Exception as e:
            print(f"[DashboardWidget] Error updating profile stats: {e}")
            if self.value_labels.get("Profili"):
                self.value_labels["Profili"].setText("Errore")

        # --- Credential Stats --- 
        total_credentials = 0
        secure_count = 0
        compromised_count = 0
        weak_count = 0 # Defined as not compromised and not secure
        
        try:
            # --- CORREZIONE: Itera sui profili per ottenere le credenziali --- 
            all_profiles = self.profile_manager.get_all_profiles()
            all_credentials = []
            for profile in all_profiles:
                 # Assumiamo che Profile abbia un attributo 'id' valido
                 if profile.id is not None:
                      creds_for_profile = self.credential_manager.get_profile_credentials(profile.id)
                      all_credentials.extend(creds_for_profile)
                 else:
                      print(f"[DashboardWidget] Warning: Profile '{profile.name}' has no ID, skipping credentials.")
            # --- FINE CORREZIONE ---
            
            total_credentials = len(all_credentials)

            # Calculate password stats on the collected credentials
            for cred in all_credentials:
                # La password in 'cred.password' dovrebbe essere già decrittata
                if cred.password: # Check if password exists (non None or empty)
                    if self.credential_manager.is_password_compromised(cred.password):
                        compromised_count += 1
                    elif self.credential_manager.is_password_secure(cred.password):
                        secure_count += 1
                    else:
                         weak_count += 1 # Neither compromised nor secure = weak
                # else: Potremmo contare le password vuote o mancanti se necessario

            # Update Labels using the references stored in self.value_labels
            if self.value_labels.get("Credenziali"):
                self.value_labels["Credenziali"].setText(str(total_credentials))
            else:
                 print("[DashboardWidget] Warning: Label for 'Credenziali' not found in value_labels.")
                 
            if self.value_labels.get("Password Sicure"):
                 # Note: The card title is "Password Sicure" but logic calculates `secure_count`
                self.value_labels["Password Sicure"].setText(str(secure_count))
            else:
                 print("[DashboardWidget] Warning: Label for 'Password Sicure' not found in value_labels.")
                 
            if self.value_labels.get("Password Compromesse"):
                 # Note: The card title is "Password Compromesse", logic calculates `compromised_count`
                self.value_labels["Password Compromesse"].setText(str(compromised_count))
            else:
                 print("[DashboardWidget] Warning: Label for 'Password Compromesse' not found in value_labels.")
                 
            # Optional: Update a label for weak passwords if you add a card for it
            # if self.value_labels.get("Password Deboli"):
            #    self.value_labels["Password Deboli"].setText(str(weak_count))

        except Exception as e:
            print(f"[DashboardWidget] Error updating credential stats: {e}")
            # Set relevant labels to "Errore" on failure
            if self.value_labels.get("Credenziali"):
                self.value_labels["Credenziali"].setText("Errore")
            if self.value_labels.get("Password Sicure"):
                self.value_labels["Password Sicure"].setText("Errore")
            if self.value_labels.get("Password Compromesse"):
                self.value_labels["Password Compromesse"].setText("Errore")
        
        print("[DashboardWidget] Stats update complete.")

    # def show_add_profile(self):
    #     """Mostra la finestra per aggiungere un nuovo profilo."""
    #     # Implementa la logica per aggiungere un profilo
    #     pass 