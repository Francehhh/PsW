"""
Finestra principale dell'applicazione PsW.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QListWidget, QListWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QMenuBar, QMenu, QToolBar, QButtonGroup, QStyle, QToolButton, QScrollBar
)
from PySide6.QtGui import QAction, QIcon, QFont, QCursor
from PySide6.QtCore import Qt, Slot, QPropertyAnimation, QEasingCurve, Property
from ..core.profile_manager import ProfileManager
from ..core.credential_manager import CredentialManager
from ..utils.sync_manager import SyncManager
from .settings_dialog import SettingsDialog
from .dashboard_widget import DashboardWidget
from .profile_widget import ProfileWidget
from .. import __version__, __author__
# Import hotkey listener signal emitter
from ..core.hotkey_listener import signal_emitter
# Import the new dialog
from .quick_credential_dialog import QuickCredentialDialog
from .auth_dialog import AuthDialog
from .registration_dialog import RegistrationDialog
from PySide6.QtWidgets import QGraphicsOpacityEffect

# --- Define the QSS Stylesheet --- 
# Palette:
# BG_BASE = "#161B22"
# BG_SECONDARY = "#21262D"
# BG_TERTIARY = "#30363D"
# TEXT_PRIMARY = "#E6EDF3"
# TEXT_SECONDARY = "#8B949E"
# ACCENT_PRIMARY = "#58A6FF" # Blu brillante
# ACCENT_HOVER = "#79C0FF"
# ACCENT_PRESSED = "#388BFD"
# BORDER_PRIMARY = "#30363D"
# BORDER_SECONDARY = "rgba(139, 148, 158, 0.3)"
# ERROR_COLOR = "#F85149"
# SUCCESS_COLOR = "#3FB950"

MODERN_STYLESHEET = """
/* === Global Styles === */
QWidget {
    background-color: #161B22; /* BG_BASE */
    color: #E6EDF3; /* TEXT_PRIMARY */
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 10pt;
    /* Disabilita outline di focus generico, lo gestiamo noi */
    outline: 0;
}

/* === Layout & Containers === */
QFrame {
    background-color: transparent;
    border: none;
}

QFrame#header {
    background-color: #21262D; /* BG_SECONDARY */
    border-bottom: 1px solid #30363D; /* BORDER_PRIMARY */
    padding: 8px 15px; /* Aggiusta padding */
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QSplitter::handle {
    background-color: #30363D; 
}
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:hover { background-color: #58A6FF; }

QGroupBox {
    color: #E6EDF3;
    font-size: 11pt;
    font-weight: bold;
    border: 1px solid #30363D;
    border-radius: 8px; /* Aumenta radius */
    margin-top: 12px; /* Aumenta margine */
    padding: 25px 15px 15px 15px; /* Aumenta padding top */
    background-color: #21262D;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px; /* Sposta titolo */
    padding: 0 8px; /* Aumenta padding titolo */
    background-color: #161B22;
    color: #79C0FF; /* ACCENT_HOVER (più leggibile?) */
    font-size: 10pt;
    font-weight: bold;
}

/* === Sidebar === */
QFrame#sidebarFrame {
    background-color: #0D1117; /* Più scuro per staccare */
    border-right: 1px solid #30363D;
    min-width: 200px; /* Leggermente più larga */
    max-width: 200px;
}

#sidebarFrame QToolButton {
    background-color: transparent;
    border: none; 
    color: #C9D1D9; /* TEXT_SECONDARY chiaro */
    padding: 10px 20px; /* Padding uniforme */
    text-align: left;
    border-radius: 6px; 
    font-size: 10pt; 
    font-weight: 500;
    /* Imposta dimensione icona esplicita */
    qproperty-iconSize: 20px 20px; /* O usa QSize(20, 20) nel codice */
    margin: 2px 5px; /* Margine tra bottoni */
}

#sidebarFrame QToolButton:hover {
    background-color: #21262D;
    color: #E6EDF3;
}

#sidebarFrame QToolButton:checked {
    background-color: rgba(88, 166, 255, 0.1); /* Sfondo accento più tenue */
    color: #79C0FF; /* Testo Accento */
    font-weight: bold;
    /* Indicatore selezione a sinistra */
    border-left: 3px solid #58A6FF; 
    padding-left: 17px; /* Compensa per il bordo aggiunto */
}

/* === Text & Labels === */
QLabel {
    background-color: transparent; 
    padding: 2px;
    color: #C9D1D9; 
}
QLabel#titleLabel { 
    font-size: 16pt;
    font-weight: 600; 
    padding: 10px 15px;
    color: #E6EDF3; 
}
QLabel#headerLabel { 
    font-size: 12pt;
    font-weight: bold;
    color: #E6EDF3;
    padding-bottom: 8px; /* Aumenta spazio sotto */
    border-bottom: 1px solid #30363D;
    margin-bottom: 12px; /* Aumenta margine sotto */
}

/* === Input Fields === */
QLineEdit, QTextEdit, QSpinBox {
    background-color: #0D1117;
    color: #E6EDF3;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 9px 12px; /* Aumenta padding */
    font-size: 10pt;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid #58A6FF;
    background-color: #161B22;
}

QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled {
    background-color: #21262D;
    color: #8B949E;
    border-color: #30363D;
}

QTextEdit { 
    min-height: 70px; /* Leggermente più alto */
}

/* === Buttons === */
QPushButton {
    background-color: #21262D;
    color: #79C0FF; /* Colore accento più brillante */
    border: 1px solid #30363D;
    padding: 9px 18px; /* Padding leggermente aumentato */
    border-radius: 6px;
    font-size: 10pt;
    font-weight: 500;
    min-width: 90px; /* Leggermente più largo */
    outline: none; 
}
QPushButton:hover {
    background-color: #30363D;
    border-color: #8B949E;
    color: #E6EDF3; /* Testo primario su hover */
}
QPushButton:pressed {
    background-color: #388BFD;
    color: #FFFFFF;
    border-color: #58A6FF;
}
QPushButton:disabled {
    background-color: rgba(33, 38, 45, 0.7);
    color: #8B949E;
    border-color: rgba(48, 54, 61, 0.5);
}

/* Pulsante Primario (es. Salva, OK, Conferma) */
QPushButton#primaryButton,
QPushButton[primary="true"],
QPushButton#saveButton, 
QPushButton#confirmButton,
QPushButton#confirmNewPasswordBtn,
QPushButton#okButton {
    background-color: #238636; /* Verde GitHub più scuro */
    color: #FFFFFF;
    border-color: rgba(46, 160, 67, 0.7);
    font-weight: bold;
}
QPushButton#primaryButton:hover,
QPushButton[primary="true"]:hover,
QPushButton#saveButton:hover, 
QPushButton#confirmButton:hover,
QPushButton#confirmNewPasswordBtn:hover,
QPushButton#okButton:hover {
    background-color: #2EA043;
    border-color: #238636;
}
QPushButton#primaryButton:pressed,
QPushButton[primary="true"]:pressed,
QPushButton#saveButton:pressed, 
QPushButton#confirmButton:pressed,
QPushButton#confirmNewPasswordBtn:pressed,
QPushButton#okButton:pressed {
    background-color: #238636;
}

/* Pulsante Eliminazione */
QPushButton#deleteButton, QPushButton#deleteBtn {
    background-color: transparent;
    color: #DA3633; /* Rosso GitHub */
    border: 1px solid rgba(218, 54, 51, 0.7);
}
QPushButton#deleteButton:hover, QPushButton#deleteBtn:hover {
    background-color: rgba(218, 54, 51, 0.1);
    color: #F85149;
    border-color: #F85149;
}
QPushButton#deleteButton:pressed, QPushButton#deleteBtn:pressed {
    background-color: rgba(218, 54, 51, 0.2);
    color: #FFFFFF;
}

/* Pulsante Annulla/Indietro */
QPushButton#cancelButton, QPushButton#backBtn {
    background-color: #30363D; /* Sfondo leggermente più visibile */
    color: #C9D1D9;
    border: 1px solid #30363D;
}
QPushButton#cancelButton:hover, QPushButton#backBtn:hover {
    background-color: #484F58;
    color: #E6EDF3;
    border-color: #8B949E;
}
QPushButton#cancelButton:pressed, QPushButton#backBtn:pressed {
    background-color: #40464E;
}

/* Pulsanti piccoli/icone (Visibilità, Copia, Genera) */
QPushButton#visibilityToggleBtn {
    background-color: transparent;
    border: none;
    color: #8B949E;
    padding: 5px;
    margin: 0;
    min-width: 30px;
    max-width: 30px;
    font-size: 14pt;
}
QPushButton#visibilityToggleBtn:hover { 
    background-color: #30363D;
    color: #E6EDF3;
    border-radius: 4px; /* Arrotonda hover */
}
QPushButton#visibilityToggleBtn:checked {
    background-color: #58A6FF;
    color: #161B22;
    border-radius: 4px;
}
QPushButton#copyButton {
    background-color: #21262D; /* Sfondo per distinguerlo */
    border: 1px solid #30363D;
    color: #8B949E;
    padding: 5px;
    margin: 0 0 0 5px;
    min-width: 30px;
    max-width: 30px;
    font-size: 11pt;
    border-radius: 4px;
}
QPushButton#copyButton:hover { 
    background-color: #30363D;
    border-color: #58A6FF;
    color: #E6EDF3;
}
QPushButton#copyButton:pressed { 
    background-color: #388BFD;
    color: #FFFFFF;
}
QPushButton#generatePasswordBtn, QPushButton#generatePasswordEditBtn {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid #30363D;
    font-size: 9pt;
    padding: 7px 14px;
    min-width: auto;
}
QPushButton#generatePasswordBtn:hover, QPushButton#generatePasswordEditBtn:hover {
    background-color: #30363D;
    border-color: #8B949E;
    color: #E6EDF3;
}

/* === Scrollbar === */
QScrollBar:vertical {
    border: none;
    background: #0D1117; /* Sfondo molto scuro */
    width: 10px; /* Larghezza ridotta */
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #30363D; /* Grigio scuro handle */
    min-height: 20px;
    border-radius: 5px; /* Arrotonda handle */
}
QScrollBar::handle:vertical:hover {
    background: #484F58; /* Handle più chiaro su hover */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
/* Stili simili per QScrollBar:horizontal se necessario */
QScrollBar:horizontal { /* ... */ }
QScrollBar::handle:horizontal { /* ... */ }
/* ... */

/* === Card Specific Styles === */
.cardWidget, 
QFrame#statCard, 
QWidget#credentialDetailWidget,
QDialog 
{
    background-color: #161B22; /* Usa BG_BASE per più contrasto */
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 18px; /* Padding aumentato */
}
.cardWidget:hover,
QFrame#statCard:hover 
{
    border-color: #58A6FF;
    background-color: #21262D; /* BG_SECONDARY su hover */
}

/* === Profile Box === */
QFrame#profileBox {
    background-color: #161B22; /* BG_BASE */
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 12px 15px; /* Padding rivisto */
    min-width: 220px; /* Assicura larghezza minima */
}
QFrame#profileBox:hover {
    border-color: #58A6FF;
    background-color: #21262D;
}
QFrame#profileBox[selected="true"] { 
    border: 1.5px solid #58A6FF; 
    background-color: #21262D;
}

/* Elementi dentro ProfileBox */
#profileBox QLabel#profileNameLabel { 
    font-size: 11pt; /* Ridotto leggermente */
    font-weight: bold; 
    color: #E6EDF3; 
    margin-bottom: 1px; /* Spazio ridotto */
}
#profileBox QLabel#profileLastNameLabel {
    font-size: 10pt; /* Ridotto */
    color: #C9D1D9;
    margin-bottom: 4px;
}
#profileBox QLabel#profileEmailLabel { 
    color: #8B949E; 
    font-size: 9pt; 
    margin-top: 4px; /* Spazio sopra email */
}

/* === Credential Box === */
QFrame#credentialBox {
    background-color: #161B22; /* BG_BASE */
    border: 1px solid #30363D;
    border-radius: 6px; /* Meno arrotondato */
    padding: 10px 12px;
}
QFrame#credentialBox:hover {
    border-color: #58A6FF;
    background-color: #21262D;
}
QFrame#credentialBox[selected="true"] {
    border: 1.5px solid #58A6FF; 
    background-color: #21262D;
}

/* Credential List Items - Labels */
#credentialBox QLabel { margin-bottom: 2px; } /* Spazio sotto ogni label */

#credentialBox QLabel#appNameLabel {
    font-weight: bold; 
    font-size: 10pt; /* Ridotto */
    color: #E6EDF3;
    margin-bottom: 5px; /* Più spazio sotto nome app */
}
#credentialBox QLabel#credFirstNameLabel, 
#credentialBox QLabel#credLastNameLabel, 
#credentialBox QLabel#credEmailLabel {
    color: #C9D1D9;
    font-size: 9pt;
}
#credentialBox QLabel#usernameLabel {
    color: #8B949E; 
    font-size: 9pt; /* Ridotto */
    margin-top: 3px; /* Spazio sopra username */
}

/* Statistiche Dashboard */
QLabel#statTitleLabel { font-size: 11pt; font-weight: bold; color: #C9D1D9; margin-bottom: 4px;}
QLabel#statValueLabel { font-size: 20pt; font-weight: bold; color: #58A6FF; padding-top: 2px; }
QLabel#statDescLabel { color: #8B949E; font-size: 9pt; padding-top: 8px; }

/* Quick Dialog Specific */
QuickCredentialDialog {
    /* Esempio: bordo più evidente? */
    /* border: 1px solid #58A6FF; */
}

"""
# --- End Stylesheet --- 

class MainWindow(QMainWindow):
    """
    Finestra principale dell'applicazione PsW.
    """
    
    def __init__(self, profile_manager: ProfileManager, sync_manager: SyncManager, parent=None):
        """Inizializza la finestra principale.

        Args:
            profile_manager: Istanza del gestore profili.
            sync_manager: Istanza del gestore di sincronizzazione.
            parent: Widget genitore.
        """
        super().__init__(parent)
        
        self.profile_manager = profile_manager
        # --- Store SyncManager --- 
        self.sync_manager = sync_manager
        # --- End Store SyncManager --- 
        
        # --- INITIALIZE CredentialManager with SyncManager ---
        self.credential_manager = CredentialManager(sync_manager=self.sync_manager)
        # --- END INITIALIZE ---
        
        self.setWindowTitle("PsW - Password Manager")
        self.setGeometry(100, 100, 1200, 700)
        
        # Apply the global stylesheet
        self.setStyleSheet(MODERN_STYLESHEET)
        
        # Setup dell'interfaccia
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        
        # Connect to the hotkey signal
        signal_emitter.hotkey_pressed.connect(self.handle_hotkey_press)
        
        self.quick_dialog_instance = None # Keep track of the dialog instance
        
    def setup_ui(self):
        """Configura l'interfaccia principale con Sidebar + StackedWidget + Animazione."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout Orizzontale Principale
        self.main_h_layout = QHBoxLayout(self.central_widget)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)
        
        # --- Sidebar --- 
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebarFrame")
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(10, 10, 10, 10) # Margini interni sidebar
        sidebar_layout.setSpacing(8) # Spaziatura tra bottoni

        # Gruppo per rendere i bottoni esclusivi
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        # Pulsanti di Navigazione Sidebar (QToolButton)
        # Icone standard Qt: https://doc.qt.io/qt-6/qstyle.html#StandardPixmap-enum
        style = self.style() # Get the current application style
        
        self.dashboard_btn = QToolButton()
        self.dashboard_btn.setText(" Dashboard") # Spazio per separare da icona
        self.dashboard_btn.setIcon(style.standardIcon(QStyle.SP_ComputerIcon))
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(True) # Sezione iniziale
        self.dashboard_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.dashboard_btn.clicked.connect(lambda: self.show_section("dashboard"))
        sidebar_layout.addWidget(self.dashboard_btn)
        self.nav_button_group.addButton(self.dashboard_btn)
        
        self.profiles_btn = QToolButton()
        self.profiles_btn.setText(" Profili")
        self.profiles_btn.setIcon(style.standardIcon(QStyle.SP_DirHomeIcon))
        self.profiles_btn.setCheckable(True)
        self.profiles_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.profiles_btn.clicked.connect(lambda: self.show_section("profiles"))
        sidebar_layout.addWidget(self.profiles_btn)
        self.nav_button_group.addButton(self.profiles_btn)
        
        self.settings_btn = QToolButton()
        self.settings_btn.setText(" Impostazioni")
        self.settings_btn.setIcon(style.standardIcon(QStyle.SP_FileDialogDetailedView))
        self.settings_btn.setCheckable(True)
        self.settings_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.settings_btn.clicked.connect(lambda: self.show_section("settings"))
        sidebar_layout.addWidget(self.settings_btn)
        self.nav_button_group.addButton(self.settings_btn)
        
        sidebar_layout.addStretch() # Spinge i bottoni in alto
        # Aggiungi la sidebar al layout principale
        self.main_h_layout.addWidget(self.sidebar_frame)
        
        # --- Content Area (Stacked Widget) --- 
        self.stack = QStackedWidget()
        # Aggiungi lo stack al layout principale
        self.main_h_layout.addWidget(self.stack, 1) # Stretch factor 1 per prendere spazio

        # --- Setup Animazione Transizione Stack --- 
        self.stack_opacity_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.stack_opacity_effect)
        self.stack_opacity_effect.setOpacity(1.0) # Inizia visibile
        
        self.stack_fade_animation = QPropertyAnimation(self.stack_opacity_effect, b"opacity", self)
        self.stack_fade_animation.setDuration(200) # Durata fade (ms)
        self.stack_fade_animation.setEasingCurve(QEasingCurve.InOutQuad) # Curva morbida
        # --- Fine Setup Animazione --- 

        # --- Popola lo Stack Widget (come prima) ---
        # Dashboard
        self.dashboard = DashboardWidget(self.profile_manager, self.credential_manager)
        self.stack.addWidget(self.dashboard)
        
        # Profili
        self.profiles = ProfileWidget(self.profile_manager, self.credential_manager)
        self.stack.addWidget(self.profiles)
        
        # Impostazioni
        self.settings = SettingsDialog(self)
        self.stack.addWidget(self.settings)
        
        # Imposta la sezione iniziale (Dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        
        # --- CORRECT SIGNAL CONNECTIONS --- 
        # Connect signals using .connect() instead of assignment
        # Collego segnali custom per aggiornare la dashboard
        if hasattr(self.profile_manager, 'profile_changed') and self.profile_manager.profile_changed:
            self.profile_manager.profile_changed.connect(self.update_dashboard)
            print("[MainWindow] Connected profile_manager.profile_changed to update_dashboard.")
        else:
             print("[MainWindow] WARNING: profile_manager has no profile_changed signal.")
             
        if hasattr(self.credential_manager, 'credential_changed') and self.credential_manager.credential_changed:
            # Connect credential_changed signal (assuming it exists and is defined correctly)
            # Note: credential_changed might pass profile_id, update_dashboard needs to handle it or ignore it.
            self.credential_manager.credential_changed.connect(self.update_dashboard)
            print("[MainWindow] Connected credential_manager.credential_changed to update_dashboard.")
        else:
            print("[MainWindow] WARNING: credential_manager has no credential_changed signal.")
        # --- END CORRECTION --- 
        
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
        Mostra la sezione specificata con animazione fade.
        
        Args:
            section: Nome della sezione da mostrare ("dashboard", "profiles", "settings")
        """
        newWidget = None
        if section == "dashboard": newWidget = self.dashboard
        elif section == "profiles": newWidget = self.profiles
        elif section == "settings": newWidget = self.settings

        # Esegui solo se il widget è diverso e valido
        if newWidget and self.stack.currentWidget() != newWidget:
            
            # Ferma animazione precedente se in corso
            self.stack_fade_animation.stop()
        
            # Imposta il widget di destinazione (sarà visualizzato dopo il fade-out)
            self._target_widget_for_fade = newWidget 

            # Connetti il segnale finished SOLO se non già connesso (o disconnetti prima)
            try: self.stack_fade_animation.finished.disconnect(self._on_fade_out_finished) 
            except RuntimeError: pass # Ignora se non era connesso
            self.stack_fade_animation.finished.connect(self._on_fade_out_finished)

            # Avvia fade-out
            self.stack_fade_animation.setStartValue(1.0)
            self.stack_fade_animation.setEndValue(0.0)
            self.stack_fade_animation.start()
            
    def _on_fade_out_finished(self):
        """Slot chiamato al termine dell'animazione di fade-out."""
        # Disconnetti subito per evitare chiamate multiple durante fade-in
        try: self.stack_fade_animation.finished.disconnect(self._on_fade_out_finished)
        except RuntimeError: pass 
        
        # Cambia widget
        if hasattr(self, '_target_widget_for_fade') and self._target_widget_for_fade:
            self.stack.setCurrentWidget(self._target_widget_for_fade)
            self._target_widget_for_fade = None # Pulisci target

            # Avvia fade-in
            self.stack_fade_animation.setStartValue(0.0)
            self.stack_fade_animation.setEndValue(1.0)
            self.stack_fade_animation.start()
            
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

    # --- Hotkey Handler Slot --- 
    @Slot(str, str)
    def handle_hotkey_press(self, process_name, window_title):
        print(f"---> MainWindow received hotkey signal: Proc='{process_name}', Title='{window_title}'")
        
        # Porta la finestra principale (dietro le quinte) in uno stato utilizzabile
        self.showNormal() 
        self.activateWindow() 
        # Non usare self.raise_() qui, vogliamo che il nuovo dialogo sia in cima

        # Se il dialogo è già aperto, portalo solo in primo piano
        if self.quick_dialog_instance and self.quick_dialog_instance.isVisible():
             self.quick_dialog_instance.activateWindow()
             self.quick_dialog_instance.raise_()
             print("QuickDialog already open, bringing to front.")
             return

        # Crea e mostra il nuovo dialogo di accesso rapido
        # Passa i manager necessari
        self.quick_dialog_instance = QuickCredentialDialog(self.profile_manager, self.credential_manager, self)
        
        # Prova a posizionare il dialogo vicino al cursore o al centro dello schermo
        cursor_pos = QCursor.pos()
        dialog_geom = self.quick_dialog_instance.geometry()
        # TODO: Aggiustare posizione per assicurarsi che sia sullo schermo
        self.quick_dialog_instance.move(cursor_pos.x() - dialog_geom.width() // 2, cursor_pos.y() - dialog_geom.height() // 2)
        
        # Mostra il dialogo
        # Usare exec() lo rende modale all'applicazione, show() no.
        # Dato che è frameless e gestiamo la chiusura, show() è ok.
        self.quick_dialog_instance.show()
        self.quick_dialog_instance.activateWindow() # Assicura focus iniziale

        # Rimuovere il QMessageBox di debug
        # QMessageBox.information(self, "Hotkey Premuto", 
        #                         f"Rilevata app: {process_name}\nTitolo: {window_title}\n\n(Logica di ricerca e pop-up da implementare)")

    def closeEvent(self, event):
        """Gestisce l'evento di chiusura della finestra."""
        # Implementa la logica di salvataggio o di chiusura dell'applicazione
        event.accept()

        # Aggiungi qui la logica di chiusura dell'applicazione
        print("Applicazione chiusa")

        # Chiamata al closeEvent della classe base
        super().closeEvent(event) 