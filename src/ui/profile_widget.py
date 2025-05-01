"""
Widget per la gestione dei profili utente.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QStackedWidget, QSplitter, QGroupBox, QApplication, QStyle, QSlider, QSpinBox, QGridLayout,
)
from PySide6.QtCore import Qt, Signal, Slot, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPalette, QColor
from ..core.profile_manager import ProfileManager, Profile
from ..core.credential_manager import CredentialManager, Credential
from ..core.password_generator import generate_secure_password, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH, DEFAULT_PASSWORD_LENGTH
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
        
        self.setObjectName("profileWidgetContainer") # Name for the root widget if needed
        self.setup_ui()
        self.load_profiles()
        
        # --- Connect Signals for UI Update After Decryption/Changes --- 
        try:
             if hasattr(self.profile_manager, 'profile_changed') and self.profile_manager.profile_changed is not None:
                 self.profile_manager.profile_changed.connect(self._on_profiles_updated)
                 print("[ProfileWidget] Connected profile_changed signal.")
             else:
                  print("[ProfileWidget] WARNING: ProfileManager has no profile_changed signal or it is None.")
            
             # Assuming MainWindow sets the signal on CredentialManager like ProfileManager
             if hasattr(self.credential_manager, 'credential_changed') and self.credential_manager.credential_changed is not None:
                 self.credential_manager.credential_changed.connect(self._on_credentials_updated)
                 print("[ProfileWidget] Connected credential_changed signal.")
             else:
                  print("[ProfileWidget] WARNING: CredentialManager has no credential_changed signal or it is None.")
        except Exception as e:
             print(f"[ProfileWidget] Error connecting signals: {e}")
        # --- End Signal Connection ---
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
        # Remove local stylesheet if covered globally
        # self.setStyleSheet(""" ... """) 
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header = QFrame()
        self.header.setObjectName("header")
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
        self.profiles_scroll_area = QScrollArea() # Use a scroll area
        self.profiles_scroll_area.setWidgetResizable(True)
        self.profiles_scroll_area.setObjectName("profilesScrollArea")
        self.profiles_scroll_area.setStyleSheet("QScrollArea#profilesScrollArea { border: none; }")

        self.profiles_list_container = QWidget() # Container for the grid
        self.profiles_scroll_area.setWidget(self.profiles_list_container)
        
        # Use QGridLayout instead of QVBoxLayout
        self.profiles_layout = QGridLayout(self.profiles_list_container)
        self.profiles_layout.setSpacing(15) # Spacing between grid items
        self.profiles_layout.setContentsMargins(16, 16, 16, 16)
        # self.profiles_layout.addStretch() # Not typically used with grid like this
        
        # profiles_layout in the main view should contain the scroll area
        profiles_layout.addWidget(self.profiles_scroll_area, 1) # Add scroll area with stretch factor 1
        
        # Informazioni profilo (destra)
        self.profile_info = QWidget()
        self.profile_info.setProperty("class", "cardWidget")
        self.profile_info.setObjectName("profileInfoPanel")
        self.profile_info.setMinimumWidth(350)
        self.profile_info.setMaximumWidth(450)
        # --- Setup Animazione Altezza Profile Info --- 
        self.profile_info.setVisible(False) # Inizia nascosto
        self.profile_info.setMaximumHeight(0) # Inizia con altezza 0
        self.profile_info_anim = QPropertyAnimation(self.profile_info, b"maximumHeight", self)
        self.profile_info_anim.setDuration(300) # Durata leggermente maggiore per slide
        self.profile_info_anim.setEasingCurve(QEasingCurve.InOutQuad)
        # --- Fine Setup Animazione Altezza --- 
        profile_info_layout = QVBoxLayout(self.profile_info)
        # Form campi profilo
        self.name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.notes_edit = QTextEdit()
        form = QFormLayout()
        form.addRow("Nome Profilo:", self.name_edit)
        form.addRow("Cognome Profilo:", self.last_name_edit)
        form.addRow("Email Profilo:", self.email_edit)
        form.addRow("Username Profilo:", self.username_edit)
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
        profiles_layout.addWidget(self.profile_info, 0)
        profiles_layout.setStretchFactor(self.profiles_scroll_area, 1) # Ensure scroll area takes available space
        profiles_layout.setStretchFactor(self.profile_info, 0)

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
        self.credential_detail.setObjectName("credentialDetailWidget")
        # Usa la classe cardWidget per lo stile
        self.credential_detail.setProperty("class", "cardWidget") 
        # --- Setup Animazione Altezza Credential Detail --- 
        self.credential_detail.setVisible(False) # Inizia nascosto
        self.credential_detail.setMaximumHeight(0) # Inizia con altezza 0
        self.credential_detail_anim = QPropertyAnimation(self.credential_detail, b"maximumHeight", self)
        self.credential_detail_anim.setDuration(300)
        self.credential_detail_anim.setEasingCurve(QEasingCurve.InOutQuad)
        # --- Fine Setup Animazione Altezza --- 
        credential_detail_layout = QVBoxLayout(self.credential_detail)
        # Form per i dettagli - usare QGridLayout per flessibilità
        detail_grid_layout = QGridLayout() 
        detail_grid_layout.setSpacing(10)
        detail_grid_layout.setColumnStretch(1, 1) # Allow field to stretch

        # Row 0: App Name
        app_name_label = QLabel("Nome App:")
        self.cred_app_name_edit = QLineEdit()
        self.app_name_copy_btn = QPushButton("📄") # Use copy icon/char
        self.app_name_copy_btn.setObjectName("copyButton")
        self.app_name_copy_btn.setToolTip("Copia nome app")
        self.app_name_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.cred_app_name_edit.text()))
        detail_grid_layout.addWidget(app_name_label, 0, 0)
        detail_grid_layout.addWidget(self.cred_app_name_edit, 0, 1)
        detail_grid_layout.addWidget(self.app_name_copy_btn, 0, 2)
        
        # Row 1: First Name (Credential)
        cred_first_name_label = QLabel("Nome:")
        self.cred_first_name_edit = QLineEdit()
        self.cred_first_name_copy_btn = QPushButton("📄")
        self.cred_first_name_copy_btn.setObjectName("copyButton")
        self.cred_first_name_copy_btn.setToolTip("Copia nome")
        self.cred_first_name_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.cred_first_name_edit.text()))
        detail_grid_layout.addWidget(cred_first_name_label, 1, 0)
        detail_grid_layout.addWidget(self.cred_first_name_edit, 1, 1)
        detail_grid_layout.addWidget(self.cred_first_name_copy_btn, 1, 2)
        
        # Row 2: Last Name (Credential)
        cred_last_name_label = QLabel("Cognome:")
        self.cred_last_name_edit = QLineEdit()
        self.cred_last_name_copy_btn = QPushButton("📄")
        self.cred_last_name_copy_btn.setObjectName("copyButton")
        self.cred_last_name_copy_btn.setToolTip("Copia cognome")
        self.cred_last_name_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.cred_last_name_edit.text()))
        detail_grid_layout.addWidget(cred_last_name_label, 2, 0)
        detail_grid_layout.addWidget(self.cred_last_name_edit, 2, 1)
        detail_grid_layout.addWidget(self.cred_last_name_copy_btn, 2, 2)
        
        # Row 3: Email (Credential)
        cred_email_label = QLabel("Email:")
        self.cred_email_edit = QLineEdit()
        self.cred_email_copy_btn = QPushButton("📄")
        self.cred_email_copy_btn.setObjectName("copyButton")
        self.cred_email_copy_btn.setToolTip("Copia email")
        self.cred_email_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.cred_email_edit.text()))
        detail_grid_layout.addWidget(cred_email_label, 3, 0)
        detail_grid_layout.addWidget(self.cred_email_edit, 3, 1)
        detail_grid_layout.addWidget(self.cred_email_copy_btn, 3, 2)
        
        # Row 4: Username (Credential)
        cred_username_label = QLabel("Username:")
        self.cred_username_edit = QLineEdit()
        self.username_copy_btn = QPushButton("📄")
        self.username_copy_btn.setObjectName("copyButton")
        self.username_copy_btn.setToolTip("Copia username")
        self.username_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.cred_username_edit.text()))
        detail_grid_layout.addWidget(cred_username_label, 4, 0)
        detail_grid_layout.addWidget(self.cred_username_edit, 4, 1)
        detail_grid_layout.addWidget(self.username_copy_btn, 4, 2)
        
        # Row 5: Password Section
        password_label = QLabel("Password:")
        # --- Password Section for Editing (already QVBoxLayout) ---
        password_edit_layout = QVBoxLayout()
        password_edit_layout.setSpacing(5) 
        # (Existing password fields, toggle, generator...)
        # Row 1: Password field and visibility toggle
        password_hbox = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_hbox.addWidget(self.password_edit)

        self.edit_toggle_password_btn = QPushButton("👁️")
        self.edit_toggle_password_btn.setObjectName("visibilityToggleBtn") 
        self.edit_toggle_password_btn.setCheckable(True)
        self.edit_toggle_password_btn.setToolTip("Mostra/Nascondi Password")
        self.edit_toggle_password_btn.clicked.connect(self.toggle_edit_password_visibility)
        password_hbox.addWidget(self.edit_toggle_password_btn)
        
        # Add Copy button for password field
        self.password_copy_btn = QPushButton("📄")
        self.password_copy_btn.setObjectName("copyButton")
        self.password_copy_btn.setToolTip("Copia password")
        self.password_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.password_edit.text()))
        password_hbox.addWidget(self.password_copy_btn) 
        
        password_edit_layout.addLayout(password_hbox)
        # (Existing generator button and generated password display)
        self.generate_password_edit_btn = QPushButton("Genera Nuova Password")
        self.generate_password_edit_btn.setObjectName("generatePasswordEditBtn")
        self.generate_password_edit_btn.clicked.connect(self.generate_password_for_edit)
        password_edit_layout.addWidget(self.generate_password_edit_btn)
        # ... (rest of generated_password_widget setup) ...
        generated_password_hbox = QHBoxLayout()
        generated_password_hbox.setContentsMargins(0, 5, 0, 0) 
        self.generated_password_label = QLabel("Nuova:") 
        self.generated_password_label.setObjectName("generatedPasswordLabel")
        generated_password_hbox.addWidget(self.generated_password_label)
        self.generated_password_display = QLineEdit()
        self.generated_password_display.setObjectName("generatedPasswordDisplay") 
        self.generated_password_display.setReadOnly(True) 
        generated_password_hbox.addWidget(self.generated_password_display, 1) 
        self.confirm_new_password_btn = QPushButton("Conferma") 
        self.confirm_new_password_btn.setObjectName("confirmNewPasswordBtn")
        self.confirm_new_password_btn.clicked.connect(self.confirm_generated_password)
        generated_password_hbox.addWidget(self.confirm_new_password_btn)
        self.generated_password_widget = QWidget()
        self.generated_password_widget.setLayout(generated_password_hbox)
        self.generated_password_widget.setVisible(False) 
        password_edit_layout.addWidget(self.generated_password_widget)
        # --- End Password Section --- 
        detail_grid_layout.addWidget(password_label, 5, 0, Qt.AlignTop) # Adjust row index
        detail_grid_layout.addLayout(password_edit_layout, 5, 1, 1, 2) # Adjust row index
        
        # Row 6: URL
        url_label = QLabel("URL:")
        self.cred_url_edit = QLineEdit()
        self.url_copy_btn = QPushButton("📄")
        self.url_copy_btn.setObjectName("copyButton")
        self.url_copy_btn.setToolTip("Copia URL")
        self.url_copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.cred_url_edit.text()))
        detail_grid_layout.addWidget(url_label, 6, 0) # Adjust row index
        detail_grid_layout.addWidget(self.cred_url_edit, 6, 1) # Adjust row index
        detail_grid_layout.addWidget(self.url_copy_btn, 6, 2) # Adjust row index

        # Row 7: Notes
        cred_notes_label = QLabel("Note:")
        self.cred_notes_edit = QTextEdit()
        self.cred_notes_edit.setMinimumHeight(80)
        detail_grid_layout.addWidget(cred_notes_label, 7, 0, Qt.AlignTop) # Adjust row index
        detail_grid_layout.addWidget(self.cred_notes_edit, 7, 1, 1, 2) # Adjust row index
        
        credential_detail_layout.addLayout(detail_grid_layout) # Add the grid layout
        credential_detail_layout.addStretch()

        # Pulsanti Salva/Annulla
        detail_btns_layout = QHBoxLayout()
        self.cancel_credential_btn = QPushButton("Annulla Modifiche")
        self.cancel_credential_btn.setObjectName("cancelCredentialBtn") # Add ID
        self.cancel_credential_btn.clicked.connect(self.cancel_credential_changes)
        detail_btns_layout.addWidget(self.cancel_credential_btn)

        self.save_credential_btn = QPushButton("Salva Modifiche")
        self.save_credential_btn.setObjectName("saveCredentialBtn") # Add ID
        self.save_credential_btn.clicked.connect(self.save_credential_changes)
        detail_btns_layout.addWidget(self.save_credential_btn)
        credential_detail_layout.addLayout(detail_btns_layout)
        
        # Initial state - Rimosso setEnabled, gestiamo con visibilità/opacità
        # self.credential_detail.setEnabled(False)
        self.credentials_splitter.addWidget(self.credential_detail)
        # Make detail view take more space initially
        self.credentials_splitter.setSizes([250, 450]) 

        self.stack.addWidget(self.credentials_widget)

        # Set initial view
        self.show_profiles()
        # Connect signals AFTER UI setup might be slightly safer
        self._connect_manager_signals() 
        
    def _connect_manager_signals(self):
         # --- Connect Signals for UI Update After Decryption/Changes --- 
         # Moved connection logic here from __init__
         try:
             if hasattr(self.profile_manager, 'profile_changed') and self.profile_manager.profile_changed is not None:
                 self.profile_manager.profile_changed.connect(self._on_profiles_updated)
                 print("[ProfileWidget] Connected profile_changed signal.")
             else:
                  print("[ProfileWidget] WARNING: ProfileManager has no profile_changed signal or it is None.")
            
             if hasattr(self.credential_manager, 'credential_changed') and self.credential_manager.credential_changed is not None:
                 self.credential_manager.credential_changed.connect(self._on_credentials_updated)
                 print("[ProfileWidget] Connected credential_changed signal.")
             else:
                  print("[ProfileWidget] WARNING: CredentialManager has no credential_changed signal or it is None.")
         except Exception as e:
             print(f"[ProfileWidget] Error connecting signals: {e}")
         # --- End Signal Connection ---
        
    def load_profiles(self):
        """Carica i profili nella griglia, ensuring data is decrypted if possible."""
        # Clear existing items from grid layout
        while self.profiles_layout.count():
            item = self.profiles_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.profile_boxes.clear()
        
        COLUMNS = 3 # Number of columns in the grid
        row = 0
        col = 0
        
        # Get profiles - the manager handles decryption internally now
        profiles_to_display = self.profile_manager.get_all_profiles()
        print(f"[ProfileWidget.load_profiles] Displaying {len(profiles_to_display)} profiles.")
        
        # Rimosso il check per is_encrypted_in_memory, non più presente
        # if profiles_to_display and profiles_to_display[0].is_encrypted_in_memory:
        #     print("[ProfileWidget.load_profiles] WARNING: Profiles are still encrypted...")
             
        # Add new profile boxes to the grid
        for index, profile in enumerate(profiles_to_display):
            box = ProfileBox(profile)
            # Connect signals
            box.double_clicked.connect(self.on_profile_double_clicked)
            box.add_credential.connect(self.show_new_credential_dialog)
            box.delete_credential.connect(self.delete_credential)
            box.edit_profile.connect(self.on_edit_profile)
            box.selected_changed.connect(self.on_profile_selection_changed)
            
            self.profiles_layout.addWidget(box, row, col) # Add to grid at row, col
            self.profile_boxes.append(box)
            
            col += 1
            if col >= COLUMNS:
                col = 0
                row += 1
                
        # Add vertical stretch at the bottom of the grid? Might not be needed
        # self.profiles_layout.setRowStretch(row + 1, 1)

    def show_new_profile_dialog(self):
        """Mostra il dialog per creare un nuovo profilo."""
        dialog = NewProfileDialog(self)
        if dialog.exec() == QDialog.Accepted:
            profile = Profile(
                id=str(uuid.uuid4()),
                name=dialog.name_edit.text(),
                last_name=dialog.last_name_edit.text() or None,
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
        dialog = NewCredentialDialog(profile, self)
        if dialog.exec() == QDialog.Accepted:
            credential = Credential(
                id=str(uuid.uuid4()),
                profile_id=profile.id,
                app_name=dialog.app_name_edit.text(),
                first_name=dialog.first_name_edit.text() or None,
                last_name=dialog.last_name_edit.text() or None,
                email=dialog.email_edit.text() or None,
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
        
        # --- DEBUG: Check credentials retrieved --- 
        credentials_to_display = self.credential_manager.get_profile_credentials(profile.id) # Pass profile ID
        # RIMOSSO DEBUG PRINT
        # print(f"[ProfileWidget.show_credentials] DEBUG: Retrieved {len(credentials_to_display)} credentials for profile {profile.id}.")
        # for i, cred in enumerate(credentials_to_display):
            # Check crucial fields and encryption status
            # print(f"    DEBUG Cred {i}: ID={cred.id}, App='{cred.app_name}', User='{cred.username[:5]}...', Pwd='{cred.password[:5]}...', EncryptedInMemory={cred.is_encrypted_in_memory}")
        # --- END DEBUG --- 
        
        # Aggiungi le credenziali del profilo
        if not credentials_to_display:
             print("[ProfileWidget.show_credentials] No credentials found to display.")
        else:
             for credential in credentials_to_display:
                 self.credential_list.add_credential(credential)
            
        # Collega solo il segnale di selezione credenziale
        self.credential_list.credential_selected.connect(self.on_credential_selected)
        
        # Aggiungi la lista delle credenziali al layout della sidebar
        sidebar_layout.addWidget(self.credential_list)
        
        # Aggiungi il container alla sidebar
        self.credentials_splitter.insertWidget(0, sidebar_container)
        self.selected_credential_box = None
        self.stack.setCurrentWidget(self.credentials_widget)
        
        # Explicitly populate the credential detail if one was selected previously (might be needed after refresh)
        if self.credential_list and self.selected_credential_box:
             # Find the credential object again in the new list
             selected_cred_id = self.selected_credential_box.credential.id
             found_cred = None
             for cred in self.credential_manager.get_profile_credentials(profile):
                  if cred.id == selected_cred_id:
                       found_cred = cred
                       break
             if found_cred:
                  self.on_credential_selected(found_cred) # Refresh detail view
             else:
                  # Credential might have been deleted, clear detail view
                  self._animate_widget_visibility(self.credential_detail, self.credential_detail_anim, False)
        else:
             # No credential was previously selected, disable detail view
             self._animate_widget_visibility(self.credential_detail, self.credential_detail_anim, False)
        
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
        """Mostra i dettagli della credenziale selezionata con animazione."""
        # Deseleziona le altre
        for box in getattr(self, 'credential_boxes', []):
            if box.credential == credential:
                box.set_selected(True)
                self.selected_credential_box = box
            else:
                box.set_selected(False)
        self.current_credential = credential
        
        # Popola i campi PRIMA di mostrare/animare
        self.cred_app_name_edit.setText(credential.app_name)
        self.cred_first_name_edit.setText(credential.first_name or "")
        self.cred_last_name_edit.setText(credential.last_name or "")
        self.cred_email_edit.setText(credential.email or "")
        self.cred_username_edit.setText(credential.username or "")
        self.password_edit.setText(credential.password or "")
        self.cred_url_edit.setText(credential.url or "")
        self.cred_notes_edit.setText(credential.notes or "")
        # Reset generated password section
        self.generated_password_widget.setVisible(False)
        self.generated_password_display.clear()
        # Ensure password visibility is off and button text is correct
        if self.edit_toggle_password_btn.isChecked():
            self.edit_toggle_password_btn.setChecked(False)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.edit_toggle_password_btn.setText("👁️") # Set text instead of icon
        
        # Anima la comparsa del pannello dettagli
        self._animate_widget_visibility(self.credential_detail, self.credential_detail_anim, True)
        
    def save_credential_changes(self):
        """Salva le modifiche apportate alla credenziale selezionata."""
        if self.current_credential:
            try:
                # Update the Credential object attributes
                self.current_credential.app_name = self.cred_app_name_edit.text().strip()
                self.current_credential.first_name = self.cred_first_name_edit.text().strip()
                self.current_credential.last_name = self.cred_last_name_edit.text().strip()
                self.current_credential.email = self.cred_email_edit.text().strip()
                self.current_credential.username = self.cred_username_edit.text().strip()
                # Password needs careful handling due to generator/visibility
                # Assume self.password_edit holds the final intended password
                new_password = self.password_edit.text()
                # Only update if password changed
                # TODO: Need a way to reliably detect if password field was intentionally changed
                # For now, assume any non-empty value is the new intended password.
                # A better approach might involve checking against the original decrypted password,
                # but that requires storing it temporarily or re-decrypting.
                if new_password: # Simplistic check, might overwrite with same value
                    self.current_credential.password = new_password
                    
                self.current_credential.url = self.cred_url_edit.text().strip()
                self.current_credential.notes = self.cred_notes_edit.toPlainText().strip()
                
                # Call the updated manager method with the Credential object
                self.credential_manager.update_credential(self.current_credential)
                
                QMessageBox.information(self, "Successo", "Credenziale aggiornata con successo.")
                # Opzionale: Anima la scomparsa dopo salvataggio?
                # self._animate_widget_visibility(self.credential_detail, self.credential_detail_anim, False)
                # self.current_credential = None # Deseleziona?

            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio della credenziale: {e}")
        else:
            QMessageBox.warning(self, "Errore", "Nessuna credenziale selezionata per la modifica.")

    def cancel_credential_changes(self):
        """Annulla le modifiche alla credenziale e nasconde il pannello con animazione."""
        if self.current_credential:
            # Ripopola i campi con i valori originali PRIMA di animare la scomparsa
            # self.on_credential_selected(self.current_credential) # Questo ri-mostrerebbe il pannello!
            # Meglio solo nascondere:
            self._animate_widget_visibility(self.credential_detail, self.credential_detail_anim, False)
            # Deseleziona logicamente
            if self.credential_list: self.credential_list.clearSelection()
            self.current_credential = None
            
    def on_edit_profile(self, profile: Profile):
        """Mostra il pannello modifica profilo con animazione."""
        self.editing_profile = profile
        # Popola i campi PRIMA di animare
        self.name_edit.setText(profile.name)
        self.last_name_edit.setText(profile.last_name or "")
        self.email_edit.setText(profile.email or "")
        self.username_edit.setText(profile.username or "")
        self.phone_edit.setText(profile.phone or "")
        self.address_edit.setText(profile.address or "")
        self.notes_edit.setText(profile.notes or "")
        
        # Anima la comparsa
        # Assicurati che sia nel widget corretto dello stack (profiles_widget)
        self.stack.setCurrentWidget(self.profiles_widget)
        self._animate_widget_visibility(self.profile_info, self.profile_info_anim, True)

    def save_profile_changes(self):
        """Salva le modifiche apportate al profilo in modifica."""
        if self.editing_profile:
            try:
                # Update the attributes of the existing Profile object
                self.editing_profile.name = self.name_edit.text().strip()
                self.editing_profile.last_name = self.last_name_edit.text().strip()
                self.editing_profile.email = self.email_edit.text().strip()
                self.editing_profile.username = self.username_edit.text().strip()
                self.editing_profile.phone = self.phone_edit.text().strip()
                self.editing_profile.address = self.address_edit.toPlainText().strip()
                self.editing_profile.notes = self.notes_edit.toPlainText().strip()
                self.editing_profile.last_modified = datetime.now().isoformat() # Update timestamp

                # Validate name (example)
                if not self.editing_profile.name:
                    QMessageBox.warning(self, "Errore", "Il nome del profilo non può essere vuoto.")
                    return

                # Call the updated manager method with the Profile object ID and the object itself
                success = self.profile_manager.update_profile(self.editing_profile.id, self.editing_profile)
                
                if success:
                    # Nascondi il pannello con animazione
                    self._animate_widget_visibility(self.profile_info, self.profile_info_anim, False)
                    self.editing_profile = None # Resetta stato
                    QMessageBox.information(self, "Successo", "Profilo aggiornato con successo.")
                else:
                    # Display error if update failed at manager/DB level
                    QMessageBox.critical(self, "Errore", "Salvataggio del profilo fallito nel database.")
            except Exception as e:
                 QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio del profilo: {e}")
                 # Potrebbe aver senso nascondere comunque il pannello o lasciarlo per correggere
                 # self._animate_widget_visibility(self.profile_info, self.profile_info_anim, False)
        else:
            QMessageBox.warning(self, "Errore", "Nessun profilo selezionato per la modifica.")

    def cancel_profile_changes(self):
        """Annulla le modifiche al profilo e nasconde il pannello con animazione."""
        # self.profile_info.hide() # Sostituito da animazione
        self._animate_widget_visibility(self.profile_info, self.profile_info_anim, False)
        # self.stack.setCurrentWidget(self.profiles_widget) # Non serve se è già visibile
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

    def copy_to_clipboard(self, value):
        clipboard = QApplication.clipboard()
        clipboard.setText(value)

    # --- New methods for password generation in edit mode ---
    def toggle_edit_password_visibility(self, checked):
        """Toggles the echo mode of the main password field in edit view."""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.edit_toggle_password_btn.setText("🔒") # Or other symbol for hidden
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.edit_toggle_password_btn.setText("👁️")

    def generate_password_for_edit(self):
        """Generates a new password and displays it for confirmation."""
        try:
            # Using default length for modification for simplicity, could be configurable
            new_password = generate_secure_password(length=DEFAULT_PASSWORD_LENGTH)
            self.generated_password_display.setText(new_password)
            self.generated_password_widget.setVisible(True)
        except ValueError as e:
            QMessageBox.warning(self, "Errore Generazione", str(e))

    def confirm_generated_password(self):
        """Copies the generated password to the main password field."""
        new_password = self.generated_password_display.text()
        if new_password:
            self.password_edit.setText(new_password)
            self.generated_password_widget.setVisible(False) # Hide after confirming
            # Ensure visibility is off after confirming and button text is correct
            if self.edit_toggle_password_btn.isChecked():
                 self.edit_toggle_password_btn.setChecked(False)
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.edit_toggle_password_btn.setText("👁️")
        
    # --- End new methods ---

    # --- Slots for Updating UI --- 
    @Slot()
    def _on_profiles_updated(self):
        """Slot called when profiles potentially change (add, delete, decrypt)."""
        print("[ProfileWidget._on_profiles_updated] Received profile changed signal. Reloading profile list.")
        # Reload the entire profile list view
        # This should now display decrypted data if decryption just occurred
        self.load_profiles()
        
        # If a profile was selected, its details might need refreshing too,
        # but load_profiles() clears selection. We might need to re-select 
        # or simply rely on the user re-selecting.
        # For simplicity, let's just reload the list for now.
        # If self.current_profile:
        #    self.on_profile_selection_changed(self.current_profile, True) # Re-trigger display
        
    @Slot()
    def _on_credentials_updated(self):
        """Slot called when credentials potentially change (add, delete, decrypt)."""
        print("[ProfileWidget._on_credentials_updated] Received credential changed signal.")
        # If a profile is currently selected, refresh its credential view
        if self.current_profile:
             print(f"    Refreshing credentials for profile: {self.current_profile.id}")
             self.show_credentials(self.current_profile)
        else:
             print("    No profile selected, credential view not updated.")
    # --- End Slots --- 

    # --- Metodo helper per animare visibilità (REVISIONATO per Altezza) --- 
    def _animate_widget_visibility(self, widget, animation, make_visible: bool):
        # Calcola altezza target (usa sizeHint)
        target_height = widget.sizeHint().height() if make_visible else 0
        current_height = widget.maximumHeight()
        
        animation.stop() # Ferma animazione precedente

        # Disconnetti sempre prima, per sicurezza
        try: animation.finished.disconnect()
        except RuntimeError:
            # Ignora l'errore se non c'erano connessioni da rimuovere
            # Questo evita il RuntimeWarning
            pass

        if make_visible:
            animation.setStartValue(current_height) 
            animation.setEndValue(target_height)
            widget.setVisible(True) # Rendi visibile PRIMA di iniziare l'animazione
        else: # Nascondi
            animation.setStartValue(current_height)
            animation.setEndValue(0)
            # Connetti setVisible(False) SOLO quando si avvia il fade-out
            animation.finished.connect(lambda: widget.setVisible(False)) 
            
        animation.start()

class NewProfileDialog(QDialog):
    """Dialog per la creazione di un nuovo profilo."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuovo Profilo")
        self.setProperty("class", "glassPane") # Apply glass effect
        self.setObjectName("newProfileDialog") # Optional ID
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog."""
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        layout.addRow("Nome Profilo:", self.name_edit)
        
        self.last_name_edit = QLineEdit()
        layout.addRow("Cognome Profilo:", self.last_name_edit)
        
        self.email_edit = QLineEdit()
        layout.addRow("Email Profilo:", self.email_edit)
        
        self.username_edit = QLineEdit()
        layout.addRow("Username Profilo:", self.username_edit)
        
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
    
    def __init__(self, profile: Profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Nuova Credenziale")
        self.setProperty("class", "glassPane") # Apply glass effect
        self.setObjectName("newCredentialDialog") # Optional ID
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog."""
        layout = QFormLayout(self)
        
        # Add Fill Credentials button
        fill_btn_layout = QHBoxLayout()
        fill_btn = QPushButton("Compila da Profilo")
        fill_btn.clicked.connect(self.fill_from_profile)
        fill_btn_layout.addWidget(fill_btn)
        fill_btn_layout.addStretch()
        layout.addRow(fill_btn_layout)

        self.app_name_edit = QLineEdit()
        layout.addRow("Nome App:", self.app_name_edit)
        
        self.first_name_edit = QLineEdit()
        layout.addRow("Nome:", self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        layout.addRow("Cognome:", self.last_name_edit)
        
        self.email_edit = QLineEdit()
        layout.addRow("Email:", self.email_edit)
        
        self.username_edit = QLineEdit()
        layout.addRow("Username:", self.username_edit)
        
        # --- Password Section ---
        password_layout = QVBoxLayout()
        password_hbox = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_hbox.addWidget(self.password_edit)

        # Button to toggle password visibility
        self.toggle_password_btn = QPushButton("👁️") # Use Unicode char
        self.toggle_password_btn.setObjectName("visibilityToggleBtn") # Use specific ID
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.setToolTip("Mostra/Nascondi Password")
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        password_hbox.addWidget(self.toggle_password_btn)
        password_layout.addLayout(password_hbox)

        # Password Generator Controls
        generator_layout = QHBoxLayout()
        generator_layout.setContentsMargins(0, 5, 0, 0)

        self.length_label = QLabel(f"Lunghezza: {DEFAULT_PASSWORD_LENGTH}")
        generator_layout.addWidget(self.length_label)

        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setRange(MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH)
        self.length_slider.setValue(DEFAULT_PASSWORD_LENGTH)
        self.length_slider.valueChanged.connect(self.update_length_label)
        generator_layout.addWidget(self.length_slider)

        generate_btn = QPushButton("Genera") # Shorter text
        generate_btn.clicked.connect(self.generate_password)
        generator_layout.addWidget(generate_btn)
        
        password_layout.addLayout(generator_layout)
        layout.addRow("Password:", password_layout)
        # --- End Password Section ---
        
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

    def toggle_password_visibility(self, checked):
        """Toggles the echo mode of the password field."""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🔒") # Or other symbol for hidden
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁️")

    def update_length_label(self, value):
        """Updates the label showing the selected password length."""
        self.length_label.setText(f"Lunghezza: {value}")

    def generate_password(self):
        """Generates a secure password and puts it in the password field."""
        length = self.length_slider.value()
        try:
            password = generate_secure_password(length=length)
            self.password_edit.setText(password)
            # Ensure visibility is off after generating and button text is correct
            if self.toggle_password_btn.isChecked():
                self.toggle_password_btn.setChecked(False) 
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁️")
        except ValueError as e:
            QMessageBox.warning(self, "Errore Generazione", str(e))

    def fill_from_profile(self):
        """Fills credential fields using data from the current profile."""
        if self.profile:
            # Assuming profile has 'username' and potentially other relevant fields
            # Adapt this logic based on the actual Profile object attributes
            if self.profile.username:
                 self.username_edit.setText(self.profile.username)
            # Riempire anche i nuovi campi se disponibili nel profilo
            if self.profile.name: # Usa 'name' del profilo per 'first_name' della credenziale?
                 self.first_name_edit.setText(self.profile.name)
            if self.profile.last_name:
                 self.last_name_edit.setText(self.profile.last_name)
            if self.profile.email:
                 self.email_edit.setText(self.profile.email)
        else:
            QMessageBox.warning(self, "Errore", "Nessun profilo selezionato per il riempimento.")

    # Ensure the method calling this dialog passes the profile
    # Example modification in ProfileWidget.show_new_credential_dialog:
    # def show_new_credential_dialog(self, profile: Profile):
    #    dialog = NewCredentialDialog(profile, self) # Pass profile here
    #    ... rest of the method ... 