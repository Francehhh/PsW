"""
Widget per la gestione dei profili.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QSplitter, QStackedWidget,
    QLabel, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor
from ..core.profile import Profile
from ..core.credential_manager import CredentialManager
from ..core.credential import Credential
from .profile_box import ProfileBox
from .credential_list import CredentialList

class CredentialDetailView(QWidget):
    """Widget per la visualizzazione dettagliata di una credenziale."""
    
    credential_updated = Signal(Credential)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_credential = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
            }
            QLineEdit, QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #4a9eff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Nome applicazione
        app_name_layout = QVBoxLayout()
        app_name_label = QLabel("Nome Applicazione")
        self.app_name_edit = QLineEdit()
        app_name_layout.addWidget(app_name_label)
        app_name_layout.addWidget(self.app_name_edit)
        layout.addLayout(app_name_layout)
        
        # Username
        username_layout = QVBoxLayout()
        username_label = QLabel("Username")
        self.username_edit = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        
        # Password
        password_layout = QVBoxLayout()
        password_label = QLabel("Password")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)
        
        # URL
        url_layout = QVBoxLayout()
        url_label = QLabel("URL")
        self.url_edit = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)
        
        # Note
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Note")
        self.notes_edit = QTextEdit()
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_edit)
        layout.addLayout(notes_layout)
        
        # Pulsante salva
        self.save_button = QPushButton("Salva Modifiche")
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)
        
        layout.addStretch()
        
    def set_credential(self, credential: Credential):
        """Imposta la credenziale da visualizzare."""
        self.current_credential = credential
        self.app_name_edit.setText(credential.app_name)
        self.username_edit.setText(credential.username)
        self.password_edit.setText(credential.password)
        self.url_edit.setText(credential.url)
        self.notes_edit.setText(credential.notes)
        
    def save_changes(self):
        """Salva le modifiche alla credenziale."""
        if self.current_credential:
            self.current_credential.app_name = self.app_name_edit.text()
            self.current_credential.username = self.username_edit.text()
            self.current_credential.password = self.password_edit.text()
            self.current_credential.url = self.url_edit.text()
            self.current_credential.notes = self.notes_edit.toPlainText()
            self.credential_updated.emit(self.current_credential)

class AnimatedStackedWidget(QStackedWidget):
    """StackedWidget con animazione di transizione."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def setCurrentIndex(self, index):
        if self.currentIndex() == index:
            return
            
        # Ottieni le dimensioni attuali
        current_rect = self.currentWidget().geometry()
        
        # Imposta la geometria iniziale per l'animazione
        if index > self.currentIndex():
            self.widget(index).setGeometry(
                current_rect.x() + current_rect.width(),
                current_rect.y(),
                current_rect.width(),
                current_rect.height()
            )
        else:
            self.widget(index).setGeometry(
                current_rect.x() - current_rect.width(),
                current_rect.y(),
                current_rect.width(),
                current_rect.height()
            )
            
        # Mostra il nuovo widget
        self.widget(index).show()
        
        # Configura l'animazione
        self.animation.setStartValue(self.widget(index).geometry())
        self.animation.setEndValue(current_rect)
        
        # Nascondi il widget corrente dopo l'animazione
        def hide_previous():
            self.widget(self.currentIndex()).hide()
            
        self.animation.finished.connect(hide_previous)
        
        # Esegui l'animazione
        super().setCurrentIndex(index)
        self.animation.start()

class ProfileManager(QWidget):
    """Widget che gestisce la lista dei profili e le loro credenziali."""
    
    profile_selected = Signal(Profile)
    add_profile = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credential_manager = CredentialManager()
        self.current_profile = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
            QLabel {
                color: white;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack per la transizione tra profili e credenziali
        self.left_stack = AnimatedStackedWidget()
        
        # Pannello profili
        profiles_panel = QWidget()
        profiles_layout = QVBoxLayout(profiles_panel)
        profiles_layout.setSpacing(0)
        profiles_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header con pulsante indietro
        header_layout = QHBoxLayout()
        self.back_button = QPushButton("← Indietro")
        self.back_button.setVisible(False)
        self.back_button.clicked.connect(self.show_profiles)
        header_layout.addWidget(self.back_button)
        header_layout.addStretch()
        profiles_layout.addLayout(header_layout)
        
        # Area scrollabile per i profili
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget contenitore per i profili
        self.profiles_container = QWidget()
        self.profiles_container.setObjectName("container")
        self.profiles_layout = QVBoxLayout(self.profiles_container)
        self.profiles_layout.setSpacing(8)
        self.profiles_layout.setContentsMargins(8, 8, 8, 8)
        self.profiles_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.profiles_container)
        profiles_layout.addWidget(scroll_area)
        
        # Aggiungi il pannello profili allo stack
        self.left_stack.addWidget(profiles_panel)
        
        # Pannello credenziali
        self.credential_list = CredentialList()
        self.credential_list.credential_selected.connect(self.on_credential_selected)
        
        # Aggiungi il pannello credenziali allo stack
        self.left_stack.addWidget(self.credential_list)
        
        # Vista dettagliata delle credenziali
        self.credential_detail = CredentialDetailView()
        self.credential_detail.credential_updated.connect(self.on_credential_updated)
        
        # Splitter per dividere le viste
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)
        
        # Aggiungi i widget allo splitter
        splitter.addWidget(self.left_stack)
        splitter.addWidget(self.credential_detail)
        splitter.setSizes([300, 400])
        
        main_layout.addWidget(splitter)
        
    def add_profile(self, profile: Profile):
        """Aggiunge un profilo alla lista."""
        box = ProfileBox(profile)
        box.double_clicked.connect(self.on_profile_double_clicked)
        self.profiles_layout.addWidget(box)
        
    def on_profile_double_clicked(self, profile: Profile):
        """Gestisce il doppio click su un profilo."""
        self.current_profile = profile
        self.credential_list.clear()
        credentials = self.credential_manager.get_profile_credentials(profile)
        for credential in credentials:
            self.credential_list.add_credential(credential)
        self.show_credentials()
        
    def show_credentials(self):
        """Mostra la lista delle credenziali."""
        self.left_stack.setCurrentIndex(1)
        self.back_button.setVisible(True)
        
    def show_profiles(self):
        """Torna alla vista dei profili."""
        self.left_stack.setCurrentIndex(0)
        self.back_button.setVisible(False)
        self.current_profile = None
        
    def on_credential_selected(self, credential: Credential):
        """Gestisce la selezione di una credenziale."""
        self.credential_detail.set_credential(credential)
        
    def on_credential_updated(self, credential: Credential):
        """Gestisce l'aggiornamento di una credenziale."""
        self.credential_manager.update_credential(credential)
            
    def clear(self):
        """Rimuove tutti i profili dalla lista."""
        while self.profiles_layout.count():
            item = self.profiles_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.credential_list.clear()
        self.show_profiles() 