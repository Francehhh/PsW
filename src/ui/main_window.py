"""
Finestra principale dell'applicazione PsW.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QListWidget, QListWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QMenuBar, QMenu, QToolBar
)
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtCore import Qt
from ..core.profile_manager import ProfileManager
from ..core.credential_manager import CredentialManager
from ..utils.sync_manager import SyncManager
from .settings_dialog import SettingsDialog
from .dashboard_widget import DashboardWidget
from .profile_widget import ProfileWidget
from .. import __version__, __author__

class MainWindow(QMainWindow):
    """
    Finestra principale dell'applicazione PsW.
    """
    
    def __init__(self, master_password, parent=None):
        """Inizializza la finestra principale."""
        super().__init__(parent)
        self.master_password = master_password
        self.setWindowTitle("PsW")
        self.setMinimumSize(800, 600)
        
        # Inizializzazione dei manager
        self.profile_manager = ProfileManager()
        self.credential_manager = CredentialManager()
        self.sync_manager = SyncManager()
        
        # Setup dell'interfaccia
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        
    def setup_ui(self):
        """Configura l'interfaccia principale."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QFrame {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:checked {
                background-color: #0d6efd;
            }
        """)
        
        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principale
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar per la navigazione
        top_bar = QFrame()
        top_bar.setFrameShape(QFrame.StyledPanel)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Pulsanti di navigazione
        self.dashboard_btn = QPushButton("Dashboard")
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(True)
        self.dashboard_btn.clicked.connect(lambda: self.show_section("dashboard"))
        
        self.profiles_btn = QPushButton("Profili")
        self.profiles_btn.setCheckable(True)
        self.profiles_btn.clicked.connect(lambda: self.show_section("profiles"))
        
        self.settings_btn = QPushButton("Impostazioni")
        self.settings_btn.setCheckable(True)
        self.settings_btn.clicked.connect(lambda: self.show_section("settings"))
        
        top_bar_layout.addWidget(self.dashboard_btn)
        top_bar_layout.addWidget(self.profiles_btn)
        top_bar_layout.addWidget(self.settings_btn)
        top_bar_layout.addStretch()
        
        main_layout.addWidget(top_bar)
        
        # Widget stack per le diverse sezioni
        self.stack = QStackedWidget()
        
        # Dashboard
        self.dashboard = DashboardWidget(self.profile_manager, self.credential_manager)
        self.stack.addWidget(self.dashboard)
        
        # Profili
        self.profiles = ProfileWidget(self.profile_manager, self.credential_manager)
        self.stack.addWidget(self.profiles)
        
        # Impostazioni
        self.settings = SettingsDialog(self)
        self.stack.addWidget(self.settings)
        
        main_layout.addWidget(self.stack)
        
        # Collego segnali custom per aggiornare la dashboard
        self.profiles.profile_manager.profile_changed = self.update_dashboard
        self.profiles.credential_manager.credential_changed = self.update_dashboard
        
    def setup_menu(self):
        """Configura la barra dei menu."""
        menubar = self.menuBar()
        
        # Menu File
        file_menu = menubar.addMenu("File")
        
        sync_action = QAction("Sincronizza", self)
        sync_action.triggered.connect(self.sync_data)
        file_menu.addAction(sync_action)
        
        # Menu Aiuto
        help_menu = menubar.addMenu("Aiuto")
        
        about_action = QAction("Informazioni", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Configura la barra degli strumenti."""
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2b2b2b;
                border: none;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 6px;
            }
            QToolButton:hover {
                background-color: #3c3c3c;
            }
        """)
        self.addToolBar(toolbar)
        
        # Pulsante Sincronizza
        sync_action = QAction(QIcon("icons/sync.png"), "Sincronizza", self)
        sync_action.triggered.connect(self.sync_data)
        toolbar.addAction(sync_action)
        
    def show_section(self, section: str):
        """
        Mostra la sezione specificata.
        
        Args:
            section: Nome della sezione da mostrare
        """
        # Disattiva tutti i pulsanti
        self.dashboard_btn.setChecked(False)
        self.profiles_btn.setChecked(False)
        self.settings_btn.setChecked(False)
        
        # Attiva il pulsante corretto
        if section == "dashboard":
            self.dashboard_btn.setChecked(True)
            self.stack.setCurrentWidget(self.dashboard)
        elif section == "profiles":
            self.profiles_btn.setChecked(True)
            self.stack.setCurrentWidget(self.profiles)
        elif section == "settings":
            self.settings_btn.setChecked(True)
            self.stack.setCurrentWidget(self.settings)
            
    def sync_data(self):
        """Sincronizza i dati con Google Drive."""
        if self.sync_manager.sync_enabled:
            # Implementa la logica di sincronizzazione
            pass
        else:
            QMessageBox.information(
                self,
                "Sincronizzazione disattivata",
                "Attiva la sincronizzazione nelle impostazioni per utilizzare questa funzionalità."
            )
            
    def show_about(self):
        """Mostra informazioni sull'applicazione."""
        QMessageBox.about(
            self,
            "Informazioni",
            f"PsW {__version__}\n\n"
            f"Sviluppato da {__author__}\n\n"
            "Un moderno gestore di password sicuro e facile da usare.\n"
            "Proteggi le tue credenziali con crittografia AES-256."
        )
        
    def update_dashboard(self):
        """Aggiorna le statistiche della dashboard."""
        self.dashboard.update_stats() 