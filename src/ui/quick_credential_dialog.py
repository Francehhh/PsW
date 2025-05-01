#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialogo per l'inserimento rapido delle credenziali.
"""
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QCompleter, QMessageBox, QScrollArea, QWidget, QSizePolicy,
    QFrame, QListWidget, QListWidgetItem, QApplication
)
from PySide6.QtGui import QIcon, QAction, QFont, Qt
from PySide6.QtCore import Qt as QtCoreQt, Signal
import os

from ..core.profile_manager import ProfileManager, Profile
from ..core.credential_manager import CredentialManager, Credential

class QuickCredentialDialog(QDialog):
    """Dialog per ricerca e copia rapida credenziali."""

    def __init__(self, profile_manager: ProfileManager, credential_manager: CredentialManager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.credential_manager = credential_manager
        self.current_profile_credentials = []

        self.setWindowTitle("Accesso Rapido Credenziali")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint | Qt.WindowType.WindowStaysOnTopHint) # Finestra senza bordi, sempre in cima
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Per angoli arrotondati con QSS
        self.setModal(False) # Non modale, così si può cliccare fuori

        self.setObjectName("quickCredentialDialog") # Per styling
        # self.setProperty("class", "glassPane") # Applica stile vetro se definito nel QSS globale

        self._offset = None # Per trascinare la finestra

        self.setup_ui()
        self.load_profiles()

    def setup_ui(self):
        """Configura l'interfaccia."""
        # Stile specifico per questo dialogo (angoli arrotondati, sfondo, etc)
        # Potrebbe sovrascrivere/integrare lo stile globale
        self.setStyleSheet("""
            #quickCredentialDialog {
                background-color: rgba(40, 42, 45, 0.92); /* Sfondo scuro semi-trasparente */
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e0;
                background-color: transparent;
                font-size: 10pt;
            }
            QComboBox {
                padding: 6px 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                background-color: rgba(50, 52, 55, 0.9);
                color: #e0e0e0;
                min-height: 2em; /* Altezza minima */
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(icons/down_arrow.png); /* Sostituire con icona valida */
                width: 12px;
                height: 12px;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView { /* Stile menu dropdown */
                background-color: #25272a;
                border: 1px solid rgba(255, 255, 255, 0.2);
                selection-background-color: #0d6efd;
                color: #e0e0e0;
                padding: 4px;
            }
            QLineEdit#searchLineEdit {
                padding: 7px 10px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                background-color: rgba(30, 31, 32, 0.9);
                color: #e0e0e0;
            }
            QListWidget {
                border: 1px solid rgba(255, 255, 255, 0.15);
                background-color: rgba(30, 31, 32, 0.85);
                border-radius: 4px;
                padding: 5px;
                outline: 0;
            }
            QListWidget::item {
                padding: 6px 8px;
                color: #ccc;
                border-radius: 3px;
                margin: 1px 0;
            }
            QListWidget::item:hover {
                background-color: rgba(70, 72, 75, 0.9);
                color: #fff;
            }
            QListWidget::item:selected {
                background-color: rgba(13, 110, 253, 0.7);
                color: white;
                border: none;
            }
             QPushButton#copyUsernameBtn, QPushButton#copyPasswordBtn {
                 background-color: #565e64; /* Grigio */
                 color: white;
                 border: 1px solid rgba(255, 255, 255, 0.1);
                 padding: 6px 10px;
                 border-radius: 4px;
                 font-size: 9pt;
                 min-width: 100px;
             }
             QPushButton#copyUsernameBtn:hover, QPushButton#copyPasswordBtn:hover {
                 background-color: #495057;
             }
             QLabel#detailAppNameLabel { font-weight: bold; font-size: 11pt; color: #f0f0f0; }
             QLabel#detailUsernameLabel { color: #bbb; font-size: 10pt; }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 10, 15, 15) # Margini interni
        self.main_layout.setSpacing(10)

        # --- Header (per trascinamento e chiusura) ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("Accesso Rapido PsW")
        title_label.setStyleSheet("color: #aaa; font-size: 8pt;") # Titolo piccolo
        close_button = QPushButton("X") # Pulsante chiusura
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("QPushButton { color: #aaa; background-color: transparent; border: none; font-size: 12pt; font-weight: bold; } QPushButton:hover { color: red; }")
        close_button.clicked.connect(self.reject) # Chiude il dialogo
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        self.main_layout.addWidget(header_widget)
        # Abilita trascinamento su header
        header_widget.mousePressEvent = self.mousePressEventHeader
        header_widget.mouseMoveEvent = self.mouseMoveEventHeader

        # --- Controlli Principali ---
        # Selezione Profilo
        self.profile_combo = QComboBox()
        self.profile_combo.setPlaceholderText("Seleziona Profilo...")
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        self.main_layout.addWidget(self.profile_combo)

        # Ricerca Credenziale
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchLineEdit")
        self.search_edit.setPlaceholderText("Cerca credenziale (App/User)...")
        self.search_edit.textChanged.connect(self.filter_credentials)
        self.search_edit.setVisible(False) # Nascondi finché profilo non selezionato
        self.main_layout.addWidget(self.search_edit)

        # Lista Credenziali
        self.credential_list_widget = QListWidget()
        self.credential_list_widget.setVisible(False) # Nascondi finché profilo non selezionato
        self.credential_list_widget.currentItemChanged.connect(self.on_credential_item_selected)
        self.credential_list_widget.setMinimumHeight(100) # Altezza minima lista
        self.credential_list_widget.setMaximumHeight(250) # Altezza massima lista
        self.main_layout.addWidget(self.credential_list_widget)

        # Dettaglio/Azioni Credenziale Selezionata
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(5, 5, 5, 5)
        self.detail_layout.setSpacing(6)
        self.detail_app_name_label = QLabel("")
        self.detail_app_name_label.setObjectName("detailAppNameLabel")
        self.detail_username_label = QLabel("")
        self.detail_username_label.setObjectName("detailUsernameLabel")
        self.copy_username_button = QPushButton("Copia Username")
        self.copy_username_button.setObjectName("copyUsernameBtn")
        self.copy_username_button.clicked.connect(self.copy_username)
        self.copy_password_button = QPushButton("Copia Password")
        self.copy_password_button.setObjectName("copyPasswordBtn")
        self.copy_password_button.clicked.connect(self.copy_password)
        self.detail_layout.addWidget(self.detail_app_name_label)
        self.detail_layout.addWidget(self.detail_username_label)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.copy_username_button)
        btn_layout.addWidget(self.copy_password_button)
        self.detail_layout.addLayout(btn_layout)
        self.detail_widget.setVisible(False) # Nascondi finché credenziale non selezionata
        self.main_layout.addWidget(self.detail_widget)

        # Imposta dimensione iniziale (compatta)
        self.setFixedSize(380, 100) # Dimensione iniziale minima, si espanderà
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)

    # --- Funzioni Logiche --- 

    def load_profiles(self):
        """Carica i profili nel ComboBox."""
        self.profile_combo.clear()
        self.profile_combo.addItem("Seleziona Profilo...", None) # Placeholder
        for profile in self.profile_manager.profiles:
            self.profile_combo.addItem(profile.name, profile) # Aggiunge nome e oggetto Profile

    def on_profile_selected(self, index):
        """Chiamato quando un profilo viene selezionato."""
        selected_profile = self.profile_combo.itemData(index)
        self.credential_list_widget.clear()
        self.detail_widget.setVisible(False)
        self.search_edit.clear()
        self._selected_credential = None # Resetta credenziale selezionata

        if selected_profile:
            self.current_profile_credentials = self.credential_manager.get_profile_credentials(selected_profile)
            self.search_edit.setVisible(True)
            self.credential_list_widget.setVisible(True)
            self.filter_credentials("") # Mostra tutte le credenziali del profilo
            self.adjust_dialog_height() # Adatta altezza
        else:
            self.current_profile_credentials = []
            self.search_edit.setVisible(False)
            self.credential_list_widget.setVisible(False)
            self.setFixedHeight(100) # Torna ad altezza minima

    def filter_credentials(self, text):
        """Filtra la lista delle credenziali in base al testo di ricerca."""
        self.credential_list_widget.clear()
        self.detail_widget.setVisible(False)
        self._selected_credential = None
        search_term = text.lower()

        for credential in self.current_profile_credentials:
            app_name_lower = credential.app_name.lower()
            username_lower = credential.username.lower()
            if search_term in app_name_lower or search_term in username_lower:
                item_text = f"{credential.app_name}  ({credential.username})"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, credential) # Associa oggetto Credential
                self.credential_list_widget.addItem(list_item)
        self.adjust_dialog_height()

    def on_credential_item_selected(self, current_item, previous_item):
        """Chiamato quando una credenziale è selezionata nella lista."""
        if current_item:
            self._selected_credential = current_item.data(Qt.ItemDataRole.UserRole)
            self.detail_app_name_label.setText(self._selected_credential.app_name)
            self.detail_username_label.setText(f"Username: {self._selected_credential.username}")
            self.detail_widget.setVisible(True)
        else:
            self._selected_credential = None
            self.detail_widget.setVisible(False)
        self.adjust_dialog_height()

    def copy_username(self):
        """Copia l'username negli appunti."""
        if hasattr(self, '_selected_credential') and self._selected_credential:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._selected_credential.username)
            # self.flash_button(self.copy_username_button)
            # print(f"Username '{self._selected_credential.username}' copiato!")
            self.close_after_copy()

    def copy_password(self):
        """Copia la password negli appunti."""
        if hasattr(self, '_selected_credential') and self._selected_credential:
            # NOTA: La password qui è ancora criptata! Deve essere decriptata.
            # Assumiamo che CredentialManager abbia un metodo per decriptare
            # password_decrypted = self.credential_manager.decrypt_password(self._selected_credential.password)
            password_decrypted = self._selected_credential.password # Placeholder - USA QUELLA DECRIPTATA
            if password_decrypted:
                clipboard = QApplication.clipboard()
                clipboard.setText(password_decrypted)
                # self.flash_button(self.copy_password_button)
                # print("Password copiata!")
                self.close_after_copy()
            else:
                print("Errore: impossibile decriptare la password per la copia.")

    def close_after_copy(self):
        """Chiude il dialogo dopo un breve ritardo."""
        # Potrebbe essere utile dare un feedback visivo prima di chiudere
        # QTimer.singleShot(200, self.accept)
        self.accept() # Chiude immediatamente per ora

    def adjust_dialog_height(self):
        """Adatta l'altezza del dialogo al contenuto."""
        # Calcola l'altezza necessaria basata sui widget visibili
        base_height = self.main_layout.contentsMargins().top() + \
                      self.main_layout.contentsMargins().bottom() + \
                      self.main_layout.spacing() * (self.main_layout.count() -1) + \
                      self.main_layout.itemAt(0).widget().sizeHint().height() # Header
        
        height = base_height + self.profile_combo.sizeHint().height()
        
        if self.search_edit.isVisible():
            height += self.search_edit.sizeHint().height() + self.main_layout.spacing()
        
        if self.credential_list_widget.isVisible():
            # Calcola altezza lista basata sugli item, ma limitata
            list_content_height = self.credential_list_widget.sizeHintForRow(0) * self.credential_list_widget.count() + 10 # Aggiunge padding
            list_height = min(max(list_content_height, 50), self.credential_list_widget.maximumHeight()) # Min 50, max 250
            height += list_height + self.main_layout.spacing()
            
        if self.detail_widget.isVisible():
            height += self.detail_widget.sizeHint().height() + self.main_layout.spacing()
            
        # Aggiungi un po' di padding extra in basso
        height += 10 
            
        self.setFixedHeight(int(height))

    # --- Gestione Finestra Frameless --- 
    def mousePressEventHeader(self, event):
        if event.button() == Qt.LeftButton:
            # Calcola l'offset rispetto all'angolo superiore sinistro
            self._offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEventHeader(self, event):
        if self._offset is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEventHeader(self, event):
        self._offset = None
        super().mouseReleaseEvent(event)

    # Chiudi se si clicca fuori (se non modale)
    # def focusOutEvent(self, event):
    #     self.reject() # Chiude il dialogo
    #     super().focusOutEvent(event)

    # Chiudi con tasto Escape
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

# Esempio di utilizzo (da chiamare da MainWindow.handle_hotkey_press)
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Creare dummy managers per test
    class DummyProfileManager:
        profiles = [
            Profile(id='1', name='Lavoro', email='work@test.com', username='worker'),
            Profile(id='2', name='Personale', email='me@test.com', username='me')
        ]
    class DummyCredentialManager:
        creds = {
            '1': [Credential(id='c1', profile_id='1', app_name='Google', username='worker@google', password='pwd-google-work'),
                  Credential(id='c2', profile_id='1', app_name='Office 365', username='worker@office', password='pwd-office-work')],
            '2': [Credential(id='c3', profile_id='2', app_name='Steam', username='gamer', password='pwd-steam'),
                  Credential(id='c4', profile_id='2', app_name='Google', username='me@gmail', password='pwd-google-pers')]
        }
        def get_profile_credentials(self, profile):
            return self.creds.get(profile.id, [])
        # def decrypt_password(self, encrypted_pass):
        #     return encrypted_pass # Dummy decryption

    profile_mgr = DummyProfileManager()
    credential_mgr = DummyCredentialManager()

    dialog = QuickCredentialDialog(profile_mgr, credential_mgr)
    dialog.show()

    sys.exit(app.exec()) 