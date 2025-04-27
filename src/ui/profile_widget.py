"""
Widget per la gestione dei profili utente.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QStackedWidget, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ..core.profile_manager import ProfileManager, Profile
from ..core.credential_manager import CredentialManager, Credential
from .profile_box import ProfileBox
from .credential_list import CredentialList
from datetime import datetime
import uuid

class ProfileWidget(QWidget):
    """
    Widget per la gestione dei profili utente.
    """
    
    def __init__(self, profile_manager: ProfileManager, credential_manager: CredentialManager):
        """Inizializza il widget dei profili."""
        super().__init__()
        self.profile_manager = profile_manager
        self.credential_manager = credential_manager
        self.profile_boxes = []
        self.current_profile = None
        self.current_credential = None
        self.editing_profile = None
        
        self.setup_ui()
        self.load_profiles()
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; }
            QLabel { color: white; }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0b5ed7; }
            QPushButton#backBtn {
                background-color: #6c757d;
                margin-right: 8px;
            }
            QPushButton#backBtn:hover { background-color: #5a6268; }
            QPushButton#deleteBtn {
                background-color: #dc3545;
            }
            QPushButton#deleteBtn:hover { background-color: #bb2d3b; }
            QPushButton#infoBtn {
                background-color: transparent;
                border: none;
                padding: 4px;
                margin-left: 8px;
            }
            QPushButton#infoBtn:hover { background-color: #2b2b2b; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header = QFrame()
        self.header.setStyleSheet("background-color: #232323; border-bottom: 1px solid #333;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Pulsante indietro
        self.back_btn = QPushButton("← Indietro")
        self.back_btn.setObjectName("backBtn")
        self.back_btn.clicked.connect(self.show_profiles)
        header_layout.addWidget(self.back_btn)
        
        # Titolo
        self.title_label = QLabel("Profili")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Pulsanti azione profili (visibili solo nella vista profili)
        self.profile_actions = QHBoxLayout()
        self.profile_actions.setSpacing(8)
        
        # Pulsante nuovo profilo
        self.new_profile_btn = QPushButton("Nuovo Profilo")
        self.new_profile_btn.clicked.connect(self.show_new_profile_dialog)
        self.profile_actions.addWidget(self.new_profile_btn)
        
        # Pulsante elimina profilo
        self.delete_profile_btn = QPushButton("Elimina Profilo")
        self.delete_profile_btn.setObjectName("deleteBtn")
        self.delete_profile_btn.clicked.connect(self.delete_selected_profile)
        self.profile_actions.addWidget(self.delete_profile_btn)
        
        header_layout.addLayout(self.profile_actions)
        
        main_layout.addWidget(self.header)
        
        # Stack widget per gestire le diverse viste
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Vista profili
        self.profiles_widget = QWidget()
        profiles_layout = QHBoxLayout(self.profiles_widget)
        profiles_layout.setSpacing(0)
        profiles_layout.setContentsMargins(0, 0, 0, 0)
        
        # Lista profili (sinistra)
        self.profiles_list = QWidget()
        self.profiles_list.setStyleSheet("background-color: #1e1e1e;")
        self.profiles_layout = QVBoxLayout(self.profiles_list)
        self.profiles_layout.setSpacing(8)
        self.profiles_layout.setContentsMargins(16, 16, 16, 16)
        self.profiles_layout.addStretch()
        profiles_layout.addWidget(self.profiles_list)
        
        # Informazioni profilo (destra)
        self.profile_info = QWidget()
        self.profile_info.setStyleSheet("background-color: #232a36; border-left: 1px solid #333;")
        self.profile_info.setMinimumWidth(300)
        self.profile_info.setMaximumWidth(400)
        profile_info_layout = QVBoxLayout(self.profile_info)
        profile_info_layout.setContentsMargins(20, 20, 20, 20)
        profile_info_layout.setSpacing(12)
        # Form campi profilo
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.notes_edit = QTextEdit()
        form = QFormLayout()
        form.addRow("Nome:", self.name_edit)
        form.addRow("Email:", self.email_edit)
        form.addRow("Username:", self.username_edit)
        form.addRow("Telefono:", self.phone_edit)
        form.addRow("Indirizzo:", self.address_edit)
        form.addRow("Note:", self.notes_edit)
        profile_info_layout.addLayout(form)
        # Pulsanti Salva/Annulla
        btns = QHBoxLayout()
        self.save_profile_btn = QPushButton("Salva Modifiche")
        self.save_profile_btn.clicked.connect(self.save_profile_changes)
        btns.addWidget(self.save_profile_btn)
        self.cancel_profile_btn = QPushButton("Annulla")
        self.cancel_profile_btn.clicked.connect(self.cancel_profile_changes)
        btns.addWidget(self.cancel_profile_btn)
        profile_info_layout.addLayout(btns)
        self.profile_info.hide()
        profiles_layout.addWidget(self.profile_info)
        
        self.stack.addWidget(self.profiles_widget)
        
        # Widget per la vista delle credenziali
        self.credentials_widget = QWidget()
        credentials_layout = QVBoxLayout(self.credentials_widget)
        credentials_layout.setSpacing(0)
        credentials_layout.setContentsMargins(0, 0, 0, 0)
        # Splitter per dividere la lista delle credenziali e il dettaglio
        self.credentials_splitter = QSplitter(Qt.Horizontal)
        credentials_layout.addWidget(self.credentials_splitter)
        # Sidebar credenziali: solo CredentialList
        self.credential_list = None
        # Widget per il dettaglio della credenziale (destra)
        self.credential_detail = QWidget()
        self.credential_detail.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 8px;
            }
            QGroupBox {
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        detail_layout = QVBoxLayout(self.credential_detail)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(16)
        self.credential_group = QGroupBox("Dettagli Credenziale")
        credential_layout = QFormLayout(self.credential_group)
        self.app_name_edit = QLineEdit()
        credential_layout.addRow("Nome App:", self.app_name_edit)
        self.username_edit = QLineEdit()
        credential_layout.addRow("Username:", self.username_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        credential_layout.addRow("Password:", self.password_edit)
        self.url_edit = QLineEdit()
        credential_layout.addRow("URL:", self.url_edit)
        self.notes_edit = QTextEdit()
        credential_layout.addRow("Note:", self.notes_edit)
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Salva Modifiche")
        self.save_btn.clicked.connect(self.save_credential_changes)
        buttons_layout.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Annulla")
        self.cancel_btn.clicked.connect(self.cancel_credential_changes)
        buttons_layout.addWidget(self.cancel_btn)
        credential_layout.addRow(buttons_layout)
        detail_layout.addWidget(self.credential_group)
        detail_layout.addStretch()
        self.credentials_splitter.addWidget(self.credential_detail)
        self.credentials_splitter.setSizes([300, 600])
        self.stack.addWidget(self.credentials_widget)
        
    def load_profiles(self):
        """Carica i profili nella lista."""
        # Rimuovi i box esistenti
        for box in self.profile_boxes:
            box.deleteLater()
        self.profile_boxes.clear()
        
        # Rimuovi lo stretch
        if self.profiles_layout.count() > 0:
            self.profiles_layout.takeAt(self.profiles_layout.count() - 1)
        
        # Crea i nuovi box
        for profile in self.profile_manager.profiles:
            box = ProfileBox(profile)
            box.double_clicked.connect(self.on_profile_double_clicked)
            box.add_credential.connect(self.show_new_credential_dialog)
            box.delete_credential.connect(self.delete_credential)
            box.edit_profile.connect(self.on_edit_profile)
            box.selected_changed.connect(self.on_profile_selection_changed)
            
            self.profiles_layout.addWidget(box)
            self.profile_boxes.append(box)
            
        # Aggiungi lo stretch alla fine
        self.profiles_layout.addStretch()
        
    def show_new_profile_dialog(self):
        """Mostra il dialog per creare un nuovo profilo."""
        dialog = NewProfileDialog(self)
        if dialog.exec() == QDialog.Accepted:
            profile = Profile(
                id=str(uuid.uuid4()),
                name=dialog.name_edit.text(),
                email=dialog.email_edit.text(),
                username=dialog.username_edit.text(),
                phone=dialog.phone_edit.text() or None,
                address=dialog.address_edit.toPlainText() or None,
                notes=dialog.notes_edit.toPlainText() or None,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self.profile_manager.add_profile(profile)
            self.load_profiles()
            
    def show_new_credential_dialog(self, profile: Profile):
        """Mostra il dialog per creare una nuova credenziale."""
        dialog = NewCredentialDialog(self)
        if dialog.exec() == QDialog.Accepted:
            credential = Credential(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                app_name=dialog.app_name_edit.text(),
                username=dialog.username_edit.text(),
                password=dialog.password_edit.text(),
                url=dialog.url_edit.text() or None,
                notes=dialog.notes_edit.toPlainText() or None
            )
            self.credential_manager.add_credential(credential)
            # Aggiorna la vista delle credenziali se è visibile
            if self.current_profile and self.current_profile.id == profile.id:
                self.show_credentials(profile)
                    
    def delete_credential(self, credential: Credential):
        """Elimina una credenziale."""
        reply = QMessageBox.question(
            self,
            "Conferma eliminazione",
            "Sei sicuro di voler eliminare questa credenziale?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.credential_manager.delete_credential(credential)
            # Aggiorna la vista delle credenziali se è visibile
            if self.current_profile:
                self.show_credentials(self.current_profile)

    def on_profile_double_clicked(self, profile: Profile):
        """Gestisce il doppio click su un profilo."""
        self.current_profile = profile
        self.show_credentials(profile)
        
    def show_credentials(self, profile: Profile):
        """Mostra le credenziali del profilo selezionato."""
        self.new_profile_btn.hide()
        self.delete_profile_btn.hide()
        self.header.show()
        self.profile_info.hide()  # Nascondi le informazioni del profilo
        
        # Rimuovi tutti i widget dalla sidebar credenziali
        while self.credentials_splitter.count() > 1:
            w = self.credentials_splitter.widget(0)
            self.credentials_splitter.widget(0).setParent(None)
            w.deleteLater()
            
        # Crea il container per la sidebar sinistra
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)
        
        # Layout orizzontale per i pulsanti
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        # Pulsante nuova credenziale
        new_cred_btn = QPushButton("Nuova")
        new_cred_btn.setObjectName("newBtn")
        new_cred_btn.setStyleSheet("""
            QPushButton#newBtn {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton#newBtn:hover {
                background-color: #0b5ed7;
            }
        """)
        new_cred_btn.clicked.connect(lambda: self.show_new_credential_dialog(profile))
        buttons_layout.addWidget(new_cred_btn)
        
        # Pulsante elimina selezionate
        delete_btn = QPushButton("Elimina")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.setStyleSheet("""
            QPushButton#deleteBtn {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton#deleteBtn:hover {
                background-color: #bb2d3b;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_selected_credentials())
        buttons_layout.addWidget(delete_btn)
        
        # Aggiungi il layout dei pulsanti alla sidebar
        sidebar_layout.addLayout(buttons_layout)
        
        # Crea e inserisci il nuovo CredentialList con il nome del profilo
        self.credential_list = CredentialList(profile_name=profile.name)
        
        # Aggiungi le credenziali del profilo
        for credential in self.credential_manager.get_profile_credentials(profile):
            self.credential_list.add_credential(credential)
            
        # Collega solo il segnale di selezione credenziale
        self.credential_list.credential_selected.connect(self.on_credential_selected)
        
        # Aggiungi la lista delle credenziali al layout della sidebar
        sidebar_layout.addWidget(self.credential_list)
        
        # Aggiungi il container alla sidebar
        self.credentials_splitter.insertWidget(0, sidebar_container)
        self.selected_credential_box = None
        self.stack.setCurrentWidget(self.credentials_widget)
        
    def delete_selected_credentials(self):
        """Elimina le credenziali selezionate."""
        selected_credentials = self.credential_list.get_selected_credentials()
        if not selected_credentials:
            QMessageBox.information(self, "Nessuna selezione", "Seleziona le credenziali da eliminare.")
            return
            
        reply = QMessageBox.question(
            self,
            "Conferma eliminazione",
            f"Sei sicuro di voler eliminare {len(selected_credentials)} credenziali?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for credential in selected_credentials:
                self.credential_manager.delete_credential(credential)
            self.show_credentials(self.current_profile)
            QMessageBox.information(self, "Eliminazione completata", "Le credenziali selezionate sono state eliminate con successo.")

    def show_profiles(self):
        """Mostra la lista dei profili."""
        self.header.show()
        self.new_profile_btn.show()
        self.delete_profile_btn.show()
        self.stack.setCurrentWidget(self.profiles_widget)
        
    def on_credential_selected(self, credential: Credential):
        """Gestisce la selezione di una credenziale."""
        # Selezione esclusiva
        for box in getattr(self, 'credential_boxes', []):
            if box.credential == credential:
                box.set_selected(True)
                self.selected_credential_box = box
            else:
                box.set_selected(False)
        self.current_credential = credential
        # Aggiorna i campi del form
        self.app_name_edit.setText(credential.app_name)
        self.username_edit.setText(credential.username)
        self.password_edit.setText(credential.password)
        self.url_edit.setText(credential.url or "")
        self.notes_edit.setText(credential.notes or "")
        
    def save_credential_changes(self):
        """Salva le modifiche alla credenziale."""
        if not self.current_credential:
            return
        # Aggiorna la credenziale
        updated_credential = Credential(
            id=self.current_credential.id,
            profile_id=self.current_credential.profile_id,
            app_name=self.app_name_edit.text(),
            username=self.username_edit.text(),
            password=self.password_edit.text(),
            url=self.url_edit.text() or None,
            notes=self.notes_edit.toPlainText() or None,
            created_at=self.current_credential.created_at,
            updated_at=datetime.now().isoformat()
        )
        # Salva le modifiche
        self.credential_manager.update_credential(self.current_credential.id, updated_credential)
        # Aggiorna la vista
        if self.current_profile:
            self.show_credentials(self.current_profile)
        QMessageBox.information(self, "Modifica completata", "Le modifiche alla credenziale sono state salvate con successo.")

    def cancel_credential_changes(self):
        """Annulla le modifiche alla credenziale."""
        if self.current_credential:
            self.on_credential_selected(self.current_credential)
            
    def on_edit_profile(self, profile: Profile):
        self.editing_profile = profile
        self.name_edit.setText(profile.name)
        self.email_edit.setText(profile.email)
        self.username_edit.setText(profile.username)
        self.phone_edit.setText(profile.phone or "")
        self.address_edit.setText(profile.address or "")
        self.notes_edit.setText(profile.notes or "")
        self.profile_info.show()
        self.stack.setCurrentWidget(self.profiles_widget)

    def save_profile_changes(self):
        if not self.editing_profile:
            return
        self.editing_profile.name = self.name_edit.text()
        self.editing_profile.email = self.email_edit.text()
        self.editing_profile.username = self.username_edit.text()
        self.editing_profile.phone = self.phone_edit.text()
        self.editing_profile.address = self.address_edit.toPlainText()
        self.editing_profile.notes = self.notes_edit.toPlainText()
        self.profile_manager.update_profile(self.editing_profile)
        self.profile_info.hide()
        self.stack.setCurrentWidget(self.profiles_widget)
        self.load_profiles()
        QMessageBox.information(self, "Modifica completata", "Le modifiche al profilo sono state salvate con successo.")

    def cancel_profile_changes(self):
        self.profile_info.hide()
        self.stack.setCurrentWidget(self.profiles_widget)
        self.editing_profile = None

    def delete_selected_profile(self):
        """Elimina i profili selezionati."""
        # Ottieni i profili selezionati
        selected_profiles = [box.profile for box in self.profile_boxes if box.is_selected()]
        
        if not selected_profiles:
            QMessageBox.warning(self, "Nessun profilo selezionato", 
                              "Seleziona almeno un profilo da eliminare.")
            return
            
        reply = QMessageBox.question(
            self,
            "Conferma eliminazione",
            f"Sei sicuro di voler eliminare {len(selected_profiles)} profili?\n"
            "Questa azione eliminerà anche tutte le credenziali associate.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for profile in selected_profiles:
                # Elimina tutte le credenziali associate al profilo
                credentials = self.credential_manager.get_profile_credentials(profile)
                for credential in credentials:
                    self.credential_manager.delete_credential(credential)
                
                # Elimina il profilo
                self.profile_manager.delete_profile(profile.id)
            
            # Aggiorna l'interfaccia
            self.current_profile = None
            self.load_profiles()
            self.show_profiles()
            
            QMessageBox.information(self, "Eliminazione completata", 
                                  f"{len(selected_profiles)} profili sono stati eliminati con successo.")

    def on_profile_selection_changed(self, profile: Profile, selected: bool):
        """Gestisce il cambio di selezione di un profilo."""
        if selected:
            self.current_profile = profile
        else:
            # Se è stato deselezionato l'ultimo profilo selezionato
            if self.current_profile == profile:
                self.current_profile = None

class NewProfileDialog(QDialog):
    """Dialog per la creazione di un nuovo profilo."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuovo Profilo")
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog."""
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        layout.addRow("Nome:", self.name_edit)
        
        self.email_edit = QLineEdit()
        layout.addRow("Email:", self.email_edit)
        
        self.username_edit = QLineEdit()
        layout.addRow("Username:", self.username_edit)
        
        self.phone_edit = QLineEdit()
        layout.addRow("Telefono:", self.phone_edit)
        
        self.address_edit = QTextEdit()
        layout.addRow("Indirizzo:", self.address_edit)
        
        self.notes_edit = QTextEdit()
        layout.addRow("Note:", self.notes_edit)
        
        buttons = QHBoxLayout()
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        
        layout.addRow(buttons)

class NewCredentialDialog(QDialog):
    """Dialog per la creazione di una nuova credenziale."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuova Credenziale")
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog."""
        layout = QFormLayout(self)
        
        self.app_name_edit = QLineEdit()
        layout.addRow("Nome App:", self.app_name_edit)
        
        self.username_edit = QLineEdit()
        layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_edit)
        
        self.url_edit = QLineEdit()
        layout.addRow("URL:", self.url_edit)
        
        self.notes_edit = QTextEdit()
        layout.addRow("Note:", self.notes_edit)
        
        buttons = QHBoxLayout()
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        save_btn = QPushButton("Salva")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(save_btn)
        
        layout.addRow(buttons) 