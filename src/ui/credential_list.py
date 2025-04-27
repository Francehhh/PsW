"""
Widget che mostra la lista delle credenziali di un profilo.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

class CredentialList(QWidget):
    """Widget che mostra la lista delle credenziali di un profilo."""
    
    credential_selected = Signal(object)
    
    def __init__(self, profile_name="", parent=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self.credentials = []
        self.selected_credential = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
        self.setStyleSheet("""
            QWidget { 
                background-color: #1e1e1e; 
            }
            QFrame#mainBox {
                background-color: #232a36;
                border: 2px solid #4a9eff;
                border-radius: 12px;
                margin: 8px 4px 4px 4px;
                padding: 0;
            }
            QLabel#profileTitle { 
                color: white; 
                font-size: 18px; 
                font-weight: bold; 
                padding: 16px;
                background-color: #1a1f2b;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QPushButton#copyBtn {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                min-width: 70px;
                font-weight: bold;
            }
            QPushButton#copyBtn:hover { 
                background-color: #1976d2;
            }
            QFrame#credentialBox {
                background-color: #2d364d;
                border: 1px solid #3d4663;
                border-radius: 10px;
                margin: 4px 8px;
                padding: 12px;
                min-height: 75px;
            }
            QFrame#credentialBox[selected="true"] {
                background-color: #364061;
                border: 2px solid #4a9eff;
                margin: 3px 7px;
            }
            QFrame#credentialBox:hover {
                background-color: #364061;
                border: 2px solid #4a9eff;
                margin: 3px 7px;
            }
            QLabel#appNameLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 2px 0;
            }
            QLabel#usernameLabel {
                color: #b0b0b0;
                font-size: 13px;
                padding: 2px 0;
            }
            QLabel#fieldLabel {
                color: #8b95b3;
                font-size: 12px;
                margin-right: 6px;
            }
            QCheckBox {
                margin-right: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #4a9eff;
            }
            QCheckBox::indicator:checked {
                background-color: #4a9eff;
                image: url(check.png);
            }
            QCheckBox::indicator:hover {
                border-color: #1976d2;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #232a36;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #4a9eff;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #1976d2;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main box che contiene header e lista credenziali
        self.main_box = QFrame()
        self.main_box.setObjectName("mainBox")
        main_box_layout = QVBoxLayout(self.main_box)
        main_box_layout.setSpacing(0)
        main_box_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titolo del profilo
        self.profile_title = QLabel(self.profile_name)
        self.profile_title.setObjectName("profileTitle")
        self.profile_title.setAlignment(Qt.AlignCenter)
        main_box_layout.addWidget(self.profile_title)
        
        # Scroll area per la lista credenziali
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cred_list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.cred_list_widget)
        self.list_layout.setSpacing(8)
        self.list_layout.setContentsMargins(8, 12, 8, 12)
        self.scroll_area.setWidget(self.cred_list_widget)
        main_box_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.main_box)
        
    def set_profile_name(self, name: str):
        """Imposta il nome del profilo."""
        self.profile_name = name
        self.profile_title.setText(name)
        
    def add_credential(self, credential):
        """Aggiunge una credenziale alla lista."""
        cred_box = QFrame()
        cred_box.setObjectName("credentialBox")
        cred_box.setCursor(Qt.PointingHandCursor)
        cred_box.setProperty("selected", False)
        box_layout = QVBoxLayout(cred_box)
        box_layout.setContentsMargins(8, 8, 8, 8)
        box_layout.setSpacing(4)
        
        # Layout superiore per checkbox e nome app
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)
        
        # Checkbox per selezione
        checkbox = QCheckBox()
        checkbox.setStyleSheet("QCheckBox { color: white; }")
        top_layout.addWidget(checkbox)
        
        # Layout per il nome dell'app con etichetta
        app_name_layout = QHBoxLayout()
        app_name_layout.setSpacing(4)
        
        app_label = QLabel("App:")
        app_label.setObjectName("fieldLabel")
        app_name_layout.addWidget(app_label)
        
        app_name = QLabel(credential.app_name)
        app_name.setObjectName("appNameLabel")
        app_name_layout.addWidget(app_name)
        app_name_layout.addStretch()
        
        top_layout.addLayout(app_name_layout)
        
        # Pulsante copia password
        copy_btn = QPushButton("Copia")
        copy_btn.setObjectName("copyBtn")
        copy_btn.clicked.connect(lambda: self.copy_password(credential))
        top_layout.addWidget(copy_btn)
        
        box_layout.addLayout(top_layout)
        
        # Layout per username con etichetta
        username_layout = QHBoxLayout()
        username_layout.setSpacing(4)
        
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        username_layout.addWidget(username_label)
        
        username = QLabel(credential.username)
        username.setObjectName("usernameLabel")
        username_layout.addWidget(username)
        username_layout.addStretch()
        
        box_layout.addLayout(username_layout)
        
        # Gestione del click sulla credenziale
        cred_box.mousePressEvent = lambda e: self.on_credential_clicked(e, credential, cred_box)
        
        self.list_layout.addWidget(cred_box)
        self.credentials.append(credential)
        
    def on_credential_clicked(self, event, credential, box):
        """Gestisce il click su una credenziale."""
        if event.button() == Qt.LeftButton:
            # Deseleziona tutte le altre credenziali
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setProperty("selected", False)
                    item.widget().setStyleSheet(item.widget().styleSheet())
            
            # Seleziona questa credenziale
            box.setProperty("selected", True)
            box.setStyleSheet(box.styleSheet())
            self.selected_credential = credential
            self.credential_selected.emit(credential)
        
    def copy_password(self, credential):
        """Copia la password negli appunti."""
        clipboard = self.window().clipboard()
        if clipboard:
            clipboard.setText(credential.password)
            
    def clear(self):
        """Rimuove tutte le credenziali dalla lista."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.credentials = []
        
    def get_selected_credentials(self):
        """Restituisce la lista delle credenziali selezionate."""
        selected = []
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            if item and item.widget():
                cred_box = item.widget()
                # Ottieni la checkbox (primo widget nel layout)
                checkbox = cred_box.layout().itemAt(0).itemAt(0).widget()
                if checkbox.isChecked():
                    selected.append(self.credentials[i])
        return selected 