"""
CredentialSection: mostra sidebar con credenziali e dettaglio credenziale selezionata.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from ..core.credential import Credential
from ..core.profile_manager import Profile
from datetime import datetime
from .credential_list import CredentialList

class CredentialSection(QWidget):
    def __init__(self, profile: Profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.credentials = profile.credentials if hasattr(profile, 'credentials') else []
        self.selected_credential = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar credenziali
        self.credential_list = CredentialList()
        self.credential_list.credential_selected.connect(self.on_credential_selected)
        layout.addWidget(self.credential_list)

        # Dettaglio credenziale
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(32, 32, 32, 32)
        detail_layout.setSpacing(16)

        self.title_label = QLabel("Seleziona una credenziale")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        detail_layout.addWidget(self.title_label)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 13px; color: #ccc;")
        self.info_label.setWordWrap(True)
        detail_layout.addWidget(self.info_label)

        # Password e pulsante copia
        pw_row = QHBoxLayout()
        self.pw_label = QLabel("Password: ********")
        self.pw_label.setStyleSheet("font-size: 14px; color: #fff;")
        pw_row.addWidget(self.pw_label)
        self.copy_btn = QPushButton("Copia")
        self.copy_btn.setStyleSheet("padding: 4px 12px; border-radius: 4px; background: #1976d2; color: #fff;")
        self.copy_btn.clicked.connect(self.copy_password)
        pw_row.addWidget(self.copy_btn)
        pw_row.addStretch()
        detail_layout.addLayout(pw_row)

        detail_layout.addStretch()
        layout.addWidget(self.detail_widget, 1)

        self.populate_credentials()

    def populate_credentials(self):
        self.credential_list.clear()
        for cred in self.credentials:
            self.credential_list.add_credential(cred)

    def on_credential_selected(self, credential):
        cred = credential
        self.selected_credential = cred
        self.title_label.setText(cred.app_name)
        info = f"""
Username: {cred.username}\nURL: {cred.url or 'N/A'}\nNote: {cred.notes or 'Nessuna nota'}\nData creazione: {self.format_date(cred.created_at)}
"""
        self.info_label.setText(info)
        self.pw_label.setText("Password: ********")
        self.copy_btn.setEnabled(True)

    def copy_password(self):
        if self.selected_credential:
            pw = self.selected_credential.password
            clipboard = self.parent().window().clipboard() if hasattr(self.parent().window(), 'clipboard') else None
            if clipboard:
                clipboard.setText(pw)

    @staticmethod
    def format_date(dt):
        try:
            return datetime.fromisoformat(dt).strftime("%d/%m/%Y")
        except Exception:
            return dt 