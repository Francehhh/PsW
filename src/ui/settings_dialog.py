"""
Finestra di impostazioni per la gestione della sincronizzazione con Google Drive.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFormLayout, QLineEdit,
    QMessageBox, QSpacerItem, QSizePolicy, QToolButton, QApplication, QStyle
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QFont, QKeyEvent, QKeySequence, QIcon
from typing import Optional # Needed for type hint

from ..utils.sync_manager import SyncManager
# Import Profile Manager to call password methods
from ..core.profile_manager import ProfileManager
# Import Master Password Dialog for verification step during change/remove
from .master_password_dialog import MasterPasswordDialog

# Import hotkey_listener to call update function
from ..core import hotkey_listener

# --- Hotkey Specific Imports & Constants ---
try:
    import win32gui
    import win32con
    import win32api # Needed for GetLastError
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    print("[SettingsDialog] WARNING: pywin32 not installed. Hotkey configuration will be disabled.")

CONFLICT_CHECK_ID = 9999 # Temporary ID for conflict checking

WIN32_MODIFIERS = {
    "Ctrl": win32con.MOD_CONTROL if PYWIN32_AVAILABLE else 0,
    "Alt": win32con.MOD_ALT if PYWIN32_AVAILABLE else 0,
    "Shift": win32con.MOD_SHIFT if PYWIN32_AVAILABLE else 0,
    "Win": win32con.MOD_WIN if PYWIN32_AVAILABLE else 0,
}

# Map Qt Keys to sensible strings and VK codes (Expand this map further!)
QT_KEY_TO_VK = {}
if PYWIN32_AVAILABLE:
     QT_KEY_TO_VK = {
        # Letters & Numbers (as before)
        **{Qt.Key_A + i: (chr(ord('A') + i), ord('A') + i) for i in range(26)},
        **{Qt.Key_0 + i: (chr(ord('0') + i), ord('0') + i) for i in range(10)},
        # Function Keys (as before)
        **{Qt.Key_F1 + i: (f"F{i+1}", win32con.VK_F1 + i) for i in range(12)}, 
        # Navigation & Others (as before)
        Qt.Key_PageUp: ("PageUp", win32con.VK_PRIOR),
        Qt.Key_PageDown: ("PageDown", win32con.VK_NEXT),
        Qt.Key_Home: ("Home", win32con.VK_HOME),
        Qt.Key_End: ("End", win32con.VK_END),
        Qt.Key_Insert: ("Insert", win32con.VK_INSERT),
        Qt.Key_Delete: ("Delete", win32con.VK_DELETE),
        Qt.Key_Left: ("Left", win32con.VK_LEFT),
        Qt.Key_Up: ("Up", win32con.VK_UP),
        Qt.Key_Right: ("Right", win32con.VK_RIGHT),
        Qt.Key_Down: ("Down", win32con.VK_DOWN),
        Qt.Key_Tab: ("Tab", win32con.VK_TAB),
        Qt.Key_Space: ("Space", win32con.VK_SPACE),
        Qt.Key_Return: ("Enter", win32con.VK_RETURN),
        Qt.Key_Enter: ("Enter", win32con.VK_RETURN), 
        Qt.Key_Escape: ("Esc", win32con.VK_ESCAPE),
        # --- Added Mappings ---
        # Punctuation / Symbols (Common US Keyboard Layout - use hex codes for VK_OEM)
        Qt.Key_Comma: (",", 0xBC), # VK_OEM_COMMA
        Qt.Key_Period: (".", 0xBE), # VK_OEM_PERIOD
        Qt.Key_Slash: ("/", 0xBF), # VK_OEM_2
        Qt.Key_Semicolon: (";", 0xBA), # VK_OEM_1
        Qt.Key_Apostrophe: ("'", 0xDE), # VK_OEM_7 (Quote)
        Qt.Key_BracketLeft: ("[", 0xDB), # VK_OEM_4
        Qt.Key_BracketRight: ("]", 0xDD), # VK_OEM_6
        Qt.Key_Backslash: ("\\", 0xDC), # VK_OEM_5
        Qt.Key_Minus: ("-", 0xBD), # VK_OEM_MINUS
        Qt.Key_Equal: ("=", 0xBB), # VK_OEM_PLUS
        Qt.Key_QuoteLeft: ("`", 0xC0), # VK_OEM_3 (Backtick/Grave)
        # Numpad keys (as before, add more if needed)
        Qt.Key_Asterisk: ("Num *", win32con.VK_MULTIPLY),
        Qt.Key_Plus: ("Num +", win32con.VK_ADD),
        Qt.Key_Minus: ("Num -", win32con.VK_SUBTRACT), # Numpad minus
        Qt.Key_Period: ("Num .", win32con.VK_DECIMAL), # Numpad decimal
        Qt.Key_Slash: ("Num /", win32con.VK_DIVIDE),  # Numpad divide
        # Numpad 0-9 (VK codes are different from regular numbers)
        # Use direct VK codes for numpad numbers for reliability
        Qt.Key_0: ("Num 0", win32con.VK_NUMPAD0), # Qt.Key_0 corresponds to multiple keys...
        Qt.Key_1: ("Num 1", win32con.VK_NUMPAD1), # Need to check if event source is numpad if possible
        Qt.Key_2: ("Num 2", win32con.VK_NUMPAD2),
        Qt.Key_3: ("Num 3", win32con.VK_NUMPAD3),
        Qt.Key_4: ("Num 4", win32con.VK_NUMPAD4),
        Qt.Key_5: ("Num 5", win32con.VK_NUMPAD5),
        Qt.Key_6: ("Num 6", win32con.VK_NUMPAD6),
        Qt.Key_7: ("Num 7", win32con.VK_NUMPAD7),
        Qt.Key_8: ("Num 8", win32con.VK_NUMPAD8),
        Qt.Key_9: ("Num 9", win32con.VK_NUMPAD9),
        # **{Qt.Key_0 + i: (f"Num {i}", win32con.VK_NUMPAD0 + i) for i in range(10)}, # Previous less reliable mapping
        # Note: Mapping Numpad 0-9 via Qt.Key can be tricky, might need VK directly sometimes.
     }

# Reverse mapping for loading (ensure it uses the same hex codes)
VK_TO_QT_KEY = {vk: (name, qt_key) for qt_key, (name, vk) in QT_KEY_TO_VK.items()}
# Manually ensure hex codes are correctly mapped back if duplicates exist (e.g. Qt.Key_Period)
VK_TO_QT_KEY[0xBE] = (".", Qt.Key_Period) # Prioritize non-numpad period
VK_TO_QT_KEY[win32con.VK_DECIMAL] = ("Num .", Qt.Key_Period) # Map numpad decimal
# Add similar manual overrides if other Qt.Key enums map to multiple VK codes


class SettingsDialog(QDialog):
    """
    Dialog per le impostazioni dell'applicazione. Uses Checkboxes + LineEdit for hotkey.
    """
    
    def __init__(self, parent=None):
        """Inizializza il dialog delle impostazioni."""
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setMinimumWidth(500)
        self.setProperty("class", "glassPane") 
        
        self.sync_manager = SyncManager()
        # Store pending hotkey state derived from UI
        self.pending_modifiers = 0 
        self.pending_vk_code = 0   
        self.pending_config_str = "Nessuno"
        self.current_hotkey_valid = True # Assume valid until checked
        
        # Need reference to ProfileManager instance
        self.profile_manager = ProfileManager() 
        
        self.setup_ui()
        self.load_settings() # Load existing settings after UI is set up
        
    def setup_ui(self):
        """Configura l'interfaccia del dialog con CheckBox + LineEdit per hotkey."""
        main_layout = QVBoxLayout(self)
        
        # Titolo
        title = QLabel("Impostazioni")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Spacer
        main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Hotkey Configuration Section ---
        hotkey_group_layout = QVBoxLayout()

        hotkey_title = QLabel("Hotkey Applicazione")
        hotkey_title.setFont(QFont("Arial", 12, QFont.Bold))
        hotkey_group_layout.addWidget(hotkey_title)

        # Layout for Modifiers (Checkboxes) + Key Input (LineEdit)
        hotkey_input_row_layout = QHBoxLayout()
        
        # Checkboxes for Modifiers
        self.ctrl_checkbox = QCheckBox("Ctrl")
        self.alt_checkbox = QCheckBox("Alt")
        self.shift_checkbox = QCheckBox("Shift")
        self.win_checkbox = QCheckBox("Win")
        
        modifier_layout = QHBoxLayout()
        modifier_layout.addWidget(self.ctrl_checkbox)
        modifier_layout.addWidget(self.alt_checkbox)
        modifier_layout.addWidget(self.shift_checkbox)
        modifier_layout.addWidget(self.win_checkbox)
        modifier_layout.addStretch()
        
        hotkey_input_row_layout.addLayout(modifier_layout)
        hotkey_input_row_layout.addWidget(QLabel("+")) # Separator

        # LineEdit for the main key
        self.main_key_input = QLineEdit()
        self.main_key_input.setPlaceholderText("Tasto")
        self.main_key_input.setAlignment(Qt.AlignCenter)
        self.main_key_input.setReadOnly(True) # Prevent direct typing
        self.main_key_input.setFocusPolicy(Qt.StrongFocus)
        self.main_key_input.setMaximumWidth(120) # Adjust width as needed
        # Install event filter on the LineEdit to capture the key
        self.main_key_input.installEventFilter(self)
        hotkey_input_row_layout.addWidget(self.main_key_input)
        hotkey_input_row_layout.addStretch() # Space before clear button?

        # Clear button
        self.clear_hotkey_btn = QToolButton()
        try:
            clear_icon = QIcon.fromTheme("edit-clear", QIcon.fromTheme("window-close", self.style().standardIcon(QStyle.SP_LineEditClearButton)))
        except Exception:
            clear_icon = self.style().standardIcon(QStyle.SP_DialogCancelButton) 
        self.clear_hotkey_btn.setIcon(clear_icon)
        self.clear_hotkey_btn.setToolTip("Pulisci hotkey")
        self.clear_hotkey_btn.clicked.connect(self.clear_hotkey_fields)
        hotkey_input_row_layout.addWidget(self.clear_hotkey_btn)

        hotkey_group_layout.addLayout(hotkey_input_row_layout)

        # Status label
        self.hotkey_status_label = QLabel("Caricamento...") 
        self.hotkey_status_label.setAlignment(Qt.AlignCenter)
        hotkey_group_layout.addWidget(self.hotkey_status_label)

        # Connect checkbox state changes to update logic
        self.ctrl_checkbox.stateChanged.connect(self.update_hotkey_state)
        self.alt_checkbox.stateChanged.connect(self.update_hotkey_state)
        self.shift_checkbox.stateChanged.connect(self.update_hotkey_state)
        self.win_checkbox.stateChanged.connect(self.update_hotkey_state)

        # Disable group if pywin32 is not available
        if not PYWIN32_AVAILABLE:
            self.ctrl_checkbox.setEnabled(False)
            self.alt_checkbox.setEnabled(False)
            self.shift_checkbox.setEnabled(False)
            self.win_checkbox.setEnabled(False)
            self.main_key_input.setEnabled(False)
            self.clear_hotkey_btn.setEnabled(False)
            self.hotkey_status_label.setText("<font color='orange'>pywin32 non installato. Configurazione Hotkey disabilitata.</font>")

        main_layout.addLayout(hotkey_group_layout)

        # Spacer before Sync settings
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Sincronizzazione Section (remains the same) ---
        sync_group_layout = QVBoxLayout()
        sync_form_layout = QFormLayout()
        sync_form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        sync_form_layout.setLabelAlignment(Qt.AlignRight)

        sync_title_label = QLabel("Sincronizzazione Google Drive")
        sync_title_label.setFont(QFont("Arial", 12, QFont.Bold))
        sync_group_layout.addWidget(sync_title_label)

        self.sync_enabled = QCheckBox("Abilita sincronizzazione")
        self.sync_enabled.stateChanged.connect(self.on_sync_toggled)
        sync_form_layout.addRow(self.sync_enabled)
        
        self.client_id = QLineEdit()
        sync_form_layout.addRow("Client ID:", self.client_id)
        
        self.client_secret = QLineEdit()
        self.client_secret.setEchoMode(QLineEdit.Password) 
        sync_form_layout.addRow("Client Secret:", self.client_secret)

        sync_group_layout.addLayout(sync_form_layout)
        main_layout.addLayout(sync_group_layout)

        # Spacer before Master Password section
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # --- Master Password Section (remains the same) ---
        pwd_group_layout = QVBoxLayout()
        pwd_form_layout = QFormLayout()
        pwd_form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        pwd_form_layout.setLabelAlignment(Qt.AlignRight)

        pwd_title_label = QLabel("Master Password (per Crittografia Dati)")
        pwd_title_label.setFont(QFont("Arial", 12, QFont.Bold))
        pwd_group_layout.addWidget(pwd_title_label)

        self.master_pwd_status_label = QLabel("Stato: Caricamento...") 
        pwd_form_layout.addRow("Stato:", self.master_pwd_status_label)

        pwd_buttons_layout = QHBoxLayout()
        self.set_change_pwd_btn = QPushButton("Imposta / Modifica Password")
        self.remove_pwd_btn = QPushButton("Rimuovi Password")
        self.set_change_pwd_btn.clicked.connect(self.set_or_change_master_password)
        self.remove_pwd_btn.clicked.connect(self.remove_master_password)
        pwd_buttons_layout.addWidget(self.set_change_pwd_btn)
        pwd_buttons_layout.addWidget(self.remove_pwd_btn)
        pwd_buttons_layout.addStretch()
        
        pwd_form_layout.addRow("Azioni:", pwd_buttons_layout)

        pwd_group_layout.addLayout(pwd_form_layout)
        main_layout.addLayout(pwd_group_layout)

        # Spacer
        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Pulsanti Save/Cancel (remains the same) ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch() 

        self.save_btn = QPushButton("Salva")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setDefault(True)
        buttons_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Annulla")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(buttons_layout)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Filters key presses on the main hotkey input field."""
        if watched == self.main_key_input and event.type() == QEvent.KeyPress:
            key_event = QKeyEvent(event)
            key = key_event.key()
            key_text = key_event.text()

            # Handle Clear Keys (Backspace/Delete) -> Clear the main key input
            if key in (Qt.Key_Backspace, Qt.Key_Delete):
                self.main_key_input.clear()
                self.update_hotkey_state() # Update state (no key set)
                return True # Consume

            # Ignore modifier key presses when focus is on main key input
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return True # Consume modifier press

            # Process potential main key
            if key in QT_KEY_TO_VK:
                display_name, vk_code = QT_KEY_TO_VK[key]
                # Set the display name in the LineEdit
                self.main_key_input.setText(display_name)
                self.update_hotkey_state() # Update state with the new key
            else:
                # Key not mapped
                print(f"[SettingsDialog] Unmapped key pressed: {key}, Text: '{key_text}'")
                self.main_key_input.setText("?") # Indicate unmapped
                self.update_hotkey_state(force_invalid=True) # Force invalid state
                
            return True # Consume the event

        # Default processing for other events
        return super().eventFilter(watched, event)

    def clear_hotkey_fields(self):
        """Clears modifier checkboxes and the main key input field."""
        # Block signals to prevent update_hotkey_state triggering multiple times
        self.ctrl_checkbox.blockSignals(True)
        self.alt_checkbox.blockSignals(True)
        self.shift_checkbox.blockSignals(True)
        self.win_checkbox.blockSignals(True)
        
        self.ctrl_checkbox.setChecked(False)
        self.alt_checkbox.setChecked(False)
        self.shift_checkbox.setChecked(False)
        self.win_checkbox.setChecked(False)
        self.main_key_input.clear()
        
        # Unblock signals
        self.ctrl_checkbox.blockSignals(False)
        self.alt_checkbox.blockSignals(False)
        self.shift_checkbox.blockSignals(False)
        self.win_checkbox.blockSignals(False)
        
        # Trigger state update once after clearing everything
        self.update_hotkey_state() 
        # self.main_key_input.setFocus() # Maybe don't force focus here

    def ui_to_native_codes(self):
        """Converts the state of checkboxes and key input to win32 codes."""
        if not PYWIN32_AVAILABLE:
            return "Nessuno", 0, 0

        modifiers = 0
        vk_code = 0
        config_parts = []

        # Check modifiers
        if self.ctrl_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Ctrl"]
            config_parts.append("Ctrl")
        if self.alt_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Alt"]
            config_parts.append("Alt")
        if self.shift_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Shift"]
            config_parts.append("Shift")
        if self.win_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Win"]
            config_parts.append("Win")

        # Get main key
        key_text = self.main_key_input.text()
        if key_text and key_text != "?": # Check if a valid key was entered
            found = False
            for qt_key, (name, vk) in QT_KEY_TO_VK.items():
                 if name == key_text:
                      vk_code = vk
                      config_parts.append(key_text)
                      found = True
                      break
            if not found:
                 print(f"[SettingsDialog] Internal Error: Could not map UI key '{key_text}' back to VK code.")
                 return "Nessuno", 0, 0 # Treat unmappable UI text as invalid
        else:
            # No valid main key entered
            return "Nessuno", 0, 0
            
        # Optional: Disallow modifier-only or key-only hotkeys if desired
        # if modifiers == 0 or vk_code == 0:
        #     return "Nessuno", 0, 0
            
        config_str = "+".join(config_parts)
        return config_str, modifiers, vk_code

    def update_hotkey_state(self, force_invalid=False):
        """Updates the pending state and UI based on current hotkey UI state."""
        if not PYWIN32_AVAILABLE:
            self.current_hotkey_valid = False 
            return

        # Get potential hotkey from UI
        config_str, modifiers, vk_code = self.ui_to_native_codes()

        # Update pending state
        self.pending_config_str = config_str
        self.pending_modifiers = modifiers
        self.pending_vk_code = vk_code

        status_msg = ""
        style_sheet = "" 
        is_valid = False
        has_conflict = False

        if force_invalid: # e.g., unmapped key entered
            is_valid = False
            status_msg = "<font color='red'>Tasto non valido o non supportato.</font>"
            style_sheet = "background-color: #FFCCCC;" # Style only the key input?
            self.main_key_input.setStyleSheet(style_sheet)
        elif vk_code == 0: # No main key set
            is_valid = True # Valid state: no hotkey
            status_msg = "<font color='grey'>Nessun hotkey impostato (seleziona i modificatori e premi un tasto nel campo 'Tasto').</font>"
            self.main_key_input.setStyleSheet("") # Clear style
        else:
            # Valid main key exists, check conflict
            has_conflict = self.check_hotkey_conflict(modifiers, vk_code)
            is_valid = not has_conflict
            if is_valid:
                status_msg = "<font color='green'>Hotkey valido.</font>"
                style_sheet = "background-color: #CCFFCC;" # Greenish background for key input
            else:
                status_msg = "<font color='red'>Conflitto rilevato! Hotkey già in uso.</font>"
                style_sheet = "background-color: #FFCCCC;" # Red background for key input
            self.main_key_input.setStyleSheet(style_sheet)

        self.current_hotkey_valid = is_valid
        self.hotkey_status_label.setText(status_msg)
        self.save_btn.setEnabled(is_valid)

    def load_settings(self):
        """Carica le impostazioni e aggiorna la UI."""
        # Load Sync settings
        self.sync_enabled.setChecked(self.sync_manager.sync_enabled)
        self.client_id.setText(self.sync_manager.client_id or "")
        # Use the new getter method for client secret
        retrieved_secret = self.sync_manager.get_client_secret() 
        self.client_secret.setText(retrieved_secret if retrieved_secret else "")

        # Load Hotkey settings
        if PYWIN32_AVAILABLE:
            hotkey_conf = self.sync_manager.get_hotkey_config()
            initial_str = hotkey_conf.get('config_str', "Nessuno")
            initial_modifiers = hotkey_conf.get('modifiers', 0)
            initial_vk_code = hotkey_conf.get('vk_code', 0)
            
            # Block signals while setting initial state
            self.ctrl_checkbox.blockSignals(True)
            self.alt_checkbox.blockSignals(True)
            self.shift_checkbox.blockSignals(True)
            self.win_checkbox.blockSignals(True)

            # Set modifier checkboxes
            self.ctrl_checkbox.setChecked(bool(initial_modifiers & WIN32_MODIFIERS["Ctrl"]))
            self.alt_checkbox.setChecked(bool(initial_modifiers & WIN32_MODIFIERS["Alt"]))
            self.shift_checkbox.setChecked(bool(initial_modifiers & WIN32_MODIFIERS["Shift"]))
            self.win_checkbox.setChecked(bool(initial_modifiers & WIN32_MODIFIERS["Win"]))
            
            # Set main key text (find display name from VK code)
            key_display_name = ""
            if initial_vk_code in VK_TO_QT_KEY:
                 key_display_name = VK_TO_QT_KEY[initial_vk_code][0] # Get the name part
            elif initial_vk_code != 0:
                 print(f"[SettingsDialog] Warning: Loaded VK code {initial_vk_code} not found in reverse map.")
                 key_display_name = "?" # Indicate unknown loaded key
                 
            self.main_key_input.setText(key_display_name)

            # Unblock signals
            self.ctrl_checkbox.blockSignals(False)
            self.alt_checkbox.blockSignals(False)
            self.shift_checkbox.blockSignals(False)
            self.win_checkbox.blockSignals(False)

            # Set initial pending values (important for save logic)
            self.pending_config_str = initial_str
            self.pending_modifiers = initial_modifiers
            self.pending_vk_code = initial_vk_code

            # Update UI state based on loaded hotkey 
            self.update_hotkey_state() 

        else:
            # UI state handled in setup_ui if pywin32 is missing
            pass
            
        # Load Master Password status
        self.update_master_password_status_ui()

    def check_hotkey_conflict(self, modifiers, vk_code) -> bool:
        """
        Verifica se un hotkey è già registrato nel sistema. (Uses win32api)
        Returns: True se c'è un conflitto, False altrimenti.
        """
        if not PYWIN32_AVAILABLE or vk_code == 0: 
             return False 

        conflict = False
        hwnd = 0 
        try:
            if not win32gui.RegisterHotKey(hwnd, CONFLICT_CHECK_ID, modifiers, vk_code):
                last_error = win32api.GetLastError()
                # Consider conflict ONLY if the specific error code is returned
                if last_error == 1409: # ERROR_HOTKEY_ALREADY_REGISTERED
                     print(f"[SettingsDialog] Conflict detected (Error 1409) for Mod={modifiers}, VK={vk_code}.")
                     conflict = True
                else:
                    # Log other errors but treat as non-conflict for the check purpose
                    print(f"[SettingsDialog] RegisterHotKey check failed with non-conflict error code: {last_error} for Mod={modifiers}, VK={vk_code}. Assuming available.")
                    conflict = False # Assume available if error is not 1409
            else:
                # Succeeded registration, means it's available
                win32gui.UnregisterHotKey(hwnd, CONFLICT_CHECK_ID)
                print(f"[SettingsDialog] Hotkey Mod={modifiers}, VK={vk_code} seems available (check succeeded).")
                conflict = False

        except win32gui.error as e:
             # Check specific win32gui error exception for 1409
             if hasattr(e, 'winerror') and e.winerror == 1409:
                  print(f"[SettingsDialog] Conflict detected (win32gui.error 1409) for Mod={modifiers}, VK={vk_code}.")
                  conflict = True
             else:
                  # Treat other API errors as non-conflict for the check
                  print(f"[SettingsDialog] Unexpected win32gui.error during conflict check: {e}. Assuming available.")
                  conflict = False 
        except Exception as e:
            # Treat generic exceptions as non-conflict for the check
            print(f"[SettingsDialog] Generic exception during conflict check: {e}. Assuming available.")
            conflict = False 
        
        return conflict
        
    def save_settings(self):
        """Salva le impostazioni."""

        # --- Save Hotkey ---
        if PYWIN32_AVAILABLE:
            # Get the final state from UI based on last update
            config_str_to_save = self.pending_config_str
            mod_to_save = self.pending_modifiers
            vk_to_save = self.pending_vk_code

            # Check the validity flag as determined by the last UI update
            if not self.current_hotkey_valid:
                QMessageBox.warning(self, "Errore Hotkey", 
                                    "Impossibile salvare: l'hotkey configurato non è valido o è stato rilevato un conflitto durante la modifica. Scegli un'altra combinazione.")
                return

            # Get the initially loaded hotkey config to compare
            initial_conf = self.sync_manager.get_hotkey_config()
            initial_mod = initial_conf.get('modifiers', 0)
            initial_vk = initial_conf.get('vk_code', 0)

            # Check if the valid hotkey derived from UI has actually changed
            hotkey_changed = False
            if mod_to_save != initial_mod or vk_to_save != initial_vk:
                print(f"[SettingsDialog] Hotkey changed. Attempting update to Str='{config_str_to_save}', Mod={mod_to_save}, VK={vk_to_save}")
                hotkey_changed = True
                try:
                     # Attempt to update the listener immediately
                     hotkey_listener.update_hotkey_combination(config_str_to_save, mod_to_save, vk_to_save)
                     # Save the new config via SyncManager ONLY if listener update succeeds
                     # This will be saved again later, but ensures consistency if listener fails.
                     self.sync_manager.set_hotkey_config(config_str_to_save, mod_to_save, vk_to_save)
                     # Explicitly save settings file now to persist the hotkey change immediately
                     self.sync_manager.save_sync_settings() 
                except Exception as e:
                      print(f"[SettingsDialog] Error calling hotkey_listener.update_hotkey_combination: {e}")
                      QMessageBox.critical(self, "Errore Aggiornamento Hotkey", 
                                           f"Impossibile registrare l'hotkey attivo: {e}\n\n" 
                                           "L'impostazione verrà salvata, ma l'hotkey potrebbe non funzionare fino al riavvio dell'applicazione o alla risoluzione del conflitto esterno.")
                      # Decide if we should still save the *intended* setting even if listener failed
                      # For now, let's save the user's intent.
                      self.sync_manager.set_hotkey_config(config_str_to_save, mod_to_save, vk_to_save)
                      # Fall through to save other settings
            else:
                 print("[SettingsDialog] Hotkey not changed.")

        # --- Save Sync Settings & potentially Master Password changes --- 
        self.sync_manager.sync_enabled = self.sync_enabled.isChecked()
        self.sync_manager.client_id = self.client_id.text()
        self.sync_manager.client_secret = self.client_secret.text()
        
        try:
            # Save Drive credentials (if changed - handled internally by SyncManager)
            self.sync_manager.save_credentials()
            
            # Save general settings (sync enabled, interval, AND the hotkey config)
            # SyncManager now holds the potentially updated hotkey config either from initial load
            # or from the set_hotkey_config call above (even if listener update failed)
            self.sync_manager.save_sync_settings() 

            QMessageBox.information(self, "Successo", "Impostazioni salvate con successo.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore Salvataggio", f"Errore durante il salvataggio delle impostazioni generali: {str(e)}")

    # --- Master Password Methods (remain the same) ---
    def update_master_password_status_ui(self):
       # ... (implementation remains the same) ...
        if self.profile_manager.is_master_password_set():
            self.master_pwd_status_label.setText("<font color='green'>Impostata (Dati Criptati)</font>")
            self.set_change_pwd_btn.setText("Modifica Password")
            self.remove_pwd_btn.setEnabled(True)
        else:
            self.master_pwd_status_label.setText("<font color='orange'>Non impostata (Dati NON Criptati)</font>")
            self.set_change_pwd_btn.setText("Imposta Password")
            self.remove_pwd_btn.setEnabled(False)

    def set_or_change_master_password(self):
        # ... (implementation remains the same) ...
        is_currently_set = self.profile_manager.is_master_password_set()
        if is_currently_set:
            old_password = MasterPasswordDialog.get_password(self, "Inserisci la vecchia Master Password per modificarla:")
            if old_password is None: return
            if not self.profile_manager.verify_master_password(old_password):
                QMessageBox.critical(self, "Errore Verifica", "La vecchia master password non è corretta.")
                return
        new_password = MasterPasswordDialog.get_password(self, "Inserisci la NUOVA Master Password:")
        if not new_password: 
             QMessageBox.warning(self, "Password Mancante", "La nuova master password non può essere vuota.")
             return 
        confirm_password = MasterPasswordDialog.get_password(self, "Conferma la NUOVA Master Password:")
        if new_password != confirm_password:
            QMessageBox.critical(self, "Errore Conferma", "Le password inserite non corrispondono.")
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            success = self.profile_manager.set_master_password(new_password)
            if QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()
            if success:
                QMessageBox.information(self, "Successo", f"Master password {'modificata' if is_currently_set else 'impostata'} con successo.")
                self.update_master_password_status_ui()
            else:
                 QMessageBox.critical(self, "Errore", f"Impossibile {'modificare' if is_currently_set else 'impostare'} la master password. Controlla i log.")
        except Exception as e:
             if QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()
             QMessageBox.critical(self, "Errore Inaspettato", f"Errore durante l'impostazione della password: {e}")

    def remove_master_password(self):
        # ... (implementation remains the same) ...
        if not self.profile_manager.is_master_password_set(): return
        reply = QMessageBox.question(self, "Conferma Rimozione Password", "Sei sicuro...?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            success = self.profile_manager.set_master_password("")
            if QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()
            if success:
                 QMessageBox.information(self, "Successo", "Master password rimossa...")
                 self.update_master_password_status_ui()
            else:
                 QMessageBox.critical(self, "Errore", "Impossibile rimuovere la master password...")
        except Exception as e:
             if QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()
             QMessageBox.critical(self, "Errore Inaspettato", f"Errore durante la rimozione...: {e}")

    def on_sync_toggled(self, state):
        pass # Placeholder

    def update_hotkey_state(self, force_invalid=False):
        """Updates the pending state and UI based on current hotkey UI state."""
        if not PYWIN32_AVAILABLE:
            self.current_hotkey_valid = False 
            return

        # Get potential hotkey from UI
        config_str, modifiers, vk_code = self.ui_to_native_codes()

        # Update pending state
        self.pending_config_str = config_str
        self.pending_modifiers = modifiers
        self.pending_vk_code = vk_code

        status_msg = ""
        style_sheet = "" 
        is_valid = False
        has_conflict = False

        if force_invalid: # e.g., unmapped key entered
            is_valid = False
            status_msg = "<font color='red'>Tasto non valido o non supportato.</font>"
            style_sheet = "background-color: #FFCCCC;" # Style only the key input?
            self.main_key_input.setStyleSheet(style_sheet)
        elif vk_code == 0: # No main key set
            is_valid = True # Valid state: no hotkey
            status_msg = "<font color='grey'>Nessun hotkey impostato (seleziona i modificatori e premi un tasto nel campo 'Tasto').</font>"
            self.main_key_input.setStyleSheet("") # Clear style
        else:
            # Valid main key exists, check conflict
            has_conflict = self.check_hotkey_conflict(modifiers, vk_code)
            is_valid = not has_conflict
            if is_valid:
                status_msg = "<font color='green'>Hotkey valido.</font>"
                style_sheet = "background-color: #CCFFCC;" # Greenish background for key input
            else:
                status_msg = "<font color='red'>Conflitto rilevato! Hotkey già in uso.</font>"
                style_sheet = "background-color: #FFCCCC;" # Red background for key input
            self.main_key_input.setStyleSheet(style_sheet)

        self.current_hotkey_valid = is_valid
        self.hotkey_status_label.setText(status_msg)
        self.save_btn.setEnabled(is_valid)

    def clear_hotkey_fields(self):
        """Clears modifier checkboxes and the main key input field."""
        # Block signals to prevent update_hotkey_state triggering multiple times
        self.ctrl_checkbox.blockSignals(True)
        self.alt_checkbox.blockSignals(True)
        self.shift_checkbox.blockSignals(True)
        self.win_checkbox.blockSignals(True)
        
        self.ctrl_checkbox.setChecked(False)
        self.alt_checkbox.setChecked(False)
        self.shift_checkbox.setChecked(False)
        self.win_checkbox.setChecked(False)
        self.main_key_input.clear()
        
        # Unblock signals
        self.ctrl_checkbox.blockSignals(False)
        self.alt_checkbox.blockSignals(False)
        self.shift_checkbox.blockSignals(False)
        self.win_checkbox.blockSignals(False)
        
        # Trigger state update once after clearing everything
        self.update_hotkey_state() 
        # self.main_key_input.setFocus() # Maybe don't force focus here

    def ui_to_native_codes(self):
        """Converts the state of checkboxes and key input to win32 codes."""
        if not PYWIN32_AVAILABLE:
            return "Nessuno", 0, 0

        modifiers = 0
        vk_code = 0
        config_parts = []

        # Check modifiers
        if self.ctrl_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Ctrl"]
            config_parts.append("Ctrl")
        if self.alt_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Alt"]
            config_parts.append("Alt")
        if self.shift_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Shift"]
            config_parts.append("Shift")
        if self.win_checkbox.isChecked(): 
            modifiers |= WIN32_MODIFIERS["Win"]
            config_parts.append("Win")

        # Get main key
        key_text = self.main_key_input.text()
        if key_text and key_text != "?": # Check if a valid key was entered
            found = False
            for qt_key, (name, vk) in QT_KEY_TO_VK.items():
                 if name == key_text:
                      vk_code = vk
                      config_parts.append(key_text)
                      found = True
                      break
            if not found:
                 print(f"[SettingsDialog] Internal Error: Could not map UI key '{key_text}' back to VK code.")
                 return "Nessuno", 0, 0 # Treat unmappable UI text as invalid
        else:
            # No valid main key entered
            return "Nessuno", 0, 0
            
        # Optional: Disallow modifier-only or key-only hotkeys if desired
        # if modifiers == 0 or vk_code == 0:
        #     return "Nessuno", 0, 0
            
        config_str = "+".join(config_parts)
        return config_str, modifiers, vk_code

    def check_hotkey_conflict(self, modifiers, vk_code) -> bool:
        """
        Verifica se un hotkey è già registrato nel sistema. (Uses win32api)
        Returns: True se c'è un conflitto, False altrimenti.
        """
        if not PYWIN32_AVAILABLE or vk_code == 0: 
             return False 

        conflict = False
        hwnd = 0 
        try:
            if not win32gui.RegisterHotKey(hwnd, CONFLICT_CHECK_ID, modifiers, vk_code):
                last_error = win32api.GetLastError()
                # Consider conflict ONLY if the specific error code is returned
                if last_error == 1409: # ERROR_HOTKEY_ALREADY_REGISTERED
                     print(f"[SettingsDialog] Conflict detected (Error 1409) for Mod={modifiers}, VK={vk_code}.")
                     conflict = True
                else:
                    # Log other errors but treat as non-conflict for the check purpose
                    print(f"[SettingsDialog] RegisterHotKey check failed with non-conflict error code: {last_error} for Mod={modifiers}, VK={vk_code}. Assuming available.")
                    conflict = False # Assume available if error is not 1409
            else:
                # Succeeded registration, means it's available
                win32gui.UnregisterHotKey(hwnd, CONFLICT_CHECK_ID)
                print(f"[SettingsDialog] Hotkey Mod={modifiers}, VK={vk_code} seems available (check succeeded).")
                conflict = False

        except win32gui.error as e:
             # Check specific win32gui error exception for 1409
             if hasattr(e, 'winerror') and e.winerror == 1409:
                  print(f"[SettingsDialog] Conflict detected (win32gui.error 1409) for Mod={modifiers}, VK={vk_code}.")
                  conflict = True
             else:
                  # Treat other API errors as non-conflict for the check
                  print(f"[SettingsDialog] Unexpected win32gui.error during conflict check: {e}. Assuming available.")
                  conflict = False 
        except Exception as e:
            # Treat generic exceptions as non-conflict for the check
            print(f"[SettingsDialog] Generic exception during conflict check: {e}. Assuming available.")
            conflict = False 
        
        return conflict 