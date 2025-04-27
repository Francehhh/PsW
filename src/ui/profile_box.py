"""
Widget per il box del profilo e la visualizzazione delle credenziali.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QStyle, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QIcon
from ..core.profile_manager import Profile
from ..core.credential import Credential

class ProfileBox(QFrame):
    """Box che rappresenta un profilo con le sue credenziali."""
    
    double_clicked = Signal(Profile)
    add_credential = Signal(Profile)
    delete_credential = Signal(Credential)
    edit_profile = Signal(Profile)
    
    def __init__(self, profile: Profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del box."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 10px;
                margin: 4px;
                max-width: 420px;
                min-height: 80px;
                max-height: 90px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QLabel#profileName {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 0px;
                margin: 0px;
            }
            QLabel#infoLabel {
                color: #aaaaaa;
                font-size: 12px;
                padding: 0px;
                margin: 0px;
            }
            QLabel#infoValue {
                color: #ffffff;
                font-size: 12px;
                padding: 0px;
                margin: 0px;
                margin-right: 12px;
            }
            QPushButton#editBtn {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QPushButton#editBtn:hover {
                background: #444444;
                border-radius: 6px;
            }
            QWidget#container {
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 8, 16, 8)
        main_layout.setAlignment(Qt.AlignVCenter)
        # Colonna sinistra: nome profilo centrato
        name_col = QVBoxLayout()
        name_col.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        name_label = QLabel(self.profile.name)
        name_label.setObjectName("profileName")
        name_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        name_col.addWidget(name_label)
        main_layout.addLayout(name_col)
        # Colonna centrale: info centrate su due righe
        info_container = QWidget()
        info_container.setObjectName("container")
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        # Prima riga: Email e Username
        top_row = QHBoxLayout()
        top_row.setSpacing(4)
        top_row.setAlignment(Qt.AlignHCenter)
        email_label = QLabel("Email:")
        email_label.setObjectName("infoLabel")
        email_value = QLabel(self.profile.email or "-")
        email_value.setObjectName("infoValue")
        username_label = QLabel("Username:")
        username_label.setObjectName("infoLabel")
        username_value = QLabel(self.profile.username or "-")
        username_value.setObjectName("infoValue")
        top_row.addWidget(email_label)
        top_row.addWidget(email_value)
        top_row.addWidget(username_label)
        top_row.addWidget(username_value)
        info_layout.addLayout(top_row)
        # Seconda riga: Telefono e Via
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(4)
        bottom_row.setAlignment(Qt.AlignHCenter)
        phone_label = QLabel("Telefono:")
        phone_label.setObjectName("infoLabel")
        phone_value = QLabel(self.profile.phone or "-")
        phone_value.setObjectName("infoValue")
        address_label = QLabel("Via:")
        address_label.setObjectName("infoLabel")
        address_text = self.profile.address[:25] + "..." if self.profile.address and len(self.profile.address) > 25 else (self.profile.address or "-")
        address_value = QLabel(address_text)
        address_value.setObjectName("infoValue")
        bottom_row.addWidget(phone_label)
        bottom_row.addWidget(phone_value)
        bottom_row.addWidget(address_label)
        bottom_row.addWidget(address_value)
        info_layout.addLayout(bottom_row)
        main_layout.addWidget(info_container, 1)
        # Pulsante modifica
        edit_btn = QPushButton()
        edit_btn.setObjectName("editBtn")
        # Icona standard Qt
        style = QApplication.style()
        edit_btn.setIcon(style.standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.setFixedSize(28, 28)
        edit_btn.clicked.connect(lambda: self.edit_profile.emit(self.profile))
        main_layout.addWidget(edit_btn)
        # Abilita il doppio click
        self.setMouseTracking(True)
        
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Gestisce il doppio click sul box."""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.profile)
            event.accept() 