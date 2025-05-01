"""
Applicazione principale del Password Manager.
"""

import sys
import os
from PySide6.QtCore import Qt # Import Qt for cursor
# --- ADD HASHING/SALT IMPORTS --- 
import hashlib
import base64
# --- END IMPORTS --- 
import logging # Add logging import

# Aggiungi la directory src al path di Python
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Commented out for PyInstaller compatibility

# --- ADD QDIALOG IMPORT --- 
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
# --- END QDIALOG IMPORT --- 
# Rimuovi AuthManager, useremo ProfileManager
# from src.core.auth_manager import AuthManager
from src.core.profile_manager import ProfileManager # Import ProfileManager
# Importa anche CredentialManager
from src.core.credential_manager import CredentialManager
# AuthDialog non è più usato qui, la verifica avviene con MasterPasswordDialog
from src.ui.auth_dialog import AuthDialog
from src.ui.registration_dialog import RegistrationDialog
from src.ui.main_window import MainWindow
# --- REMOVE UNUSED/NON-EXISTENT IMPORT --- 
# from src.ui.signal_emitter import signal_emitter # Import corrected
# --- END REMOVE --- 
# Import hotkey listener
from src.core import hotkey_listener
# Importa il MasterPasswordDialog per gestire il caso in cui la password sia impostata ma non verificata
from src.ui.master_password_dialog import MasterPasswordDialog
from src.utils.sync_manager import SyncManager # Added import
# --- MODIFY HOTKEY IMPORT --- 
# Import the module itself, not a non-existent class
from src.core import hotkey_listener 
# --- END MODIFY HOTKEY IMPORT --- 


def main():
    # Configure logging level for production builds
    logging.basicConfig(level=logging.CRITICAL)
    app = QApplication(sys.argv)

    # --- Manager Instantiation --- 
    sync_manager = SyncManager() # Instantiate SyncManager first
    profile_manager = ProfileManager() # Instantiate ProfileManager (uses SyncManager)
    # CredentialManager is now instantiated in MainWindow using sync_manager
    # credential_manager = CredentialManager(profile_manager=profile_manager)
    # --- End Manager Instantiation ---

    verified_password = None
    master_password_set = sync_manager.is_master_password_set()

    if master_password_set:
        print("Master password is set, prompting for verification...")
        auth_dialog = AuthDialog(sync_manager=sync_manager) # Pass sync_manager
        if auth_dialog.exec() == QDialog.Accepted:
            verified_password = auth_dialog.password # Get verified password from dialog
            print("Master password verified by user.")
            # The _verify_session_master_password call below is sufficient to set the state
            # No need to call it twice.
            if not sync_manager._verify_session_master_password(verified_password):
                 print("[main] CRITICAL ERROR: AuthDialog accepted but SyncManager verification failed!")
                 QMessageBox.critical(None, "Errore Verifica Interna", "Verifica password fallita dopo l'autenticazione. L'applicazione terminerà.")
                 sys.exit(1)
            # REMOVED REDUNDANT VERIFICATION CALL
        else:
            print("Authentication cancelled or failed. Exiting.")
            sys.exit(0)
    else:
        print("No master password set, prompting for registration...")
        # --- CORRECT RegistrationDialog CALL --- 
        # Remove arguments profile_manager and sync_manager
        reg_dialog = RegistrationDialog()
        # --- END CORRECTION --- 
        
        # --- Define on_registered locally --- 
        # Define the slot function here to handle the registered signal
        def on_registered(password_from_dialog):
            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                
                # --- GENERATE HASH/SALT and CALL SYNC MANAGER --- 
                # Generate salt and hash
                new_salt = os.urandom(16) 
                # Use parameters consistent with SyncManager/ProfileManager
                new_hash = hashlib.pbkdf2_hmac('sha256', password_from_dialog.encode('utf-8'), new_salt, 600000) 
                
                # Set hash/salt directly via SyncManager
                sync_manager.set_master_password_hash_salt(new_hash, new_salt)
                
                # Explicitly save settings AFTER setting hash/salt, passing password to encrypt
                sync_manager.save_settings(verified_password_override=password_from_dialog)
                # --- END HASH/SALT and SYNC MANAGER CALL --- 
                
                # Assume success if no exceptions during set/save
                success = True 
                
                if QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()

                if success:
                    print("[main] Master password successfully set and saved via registration.")
                    # Update verified_password for this session
                    nonlocal verified_password
                    verified_password = password_from_dialog 
                    # --- SET SESSION STATE in SyncManager --- 
                    # Mark the password as verified for the current session in SyncManager
                    sync_manager._verify_session_master_password(password_from_dialog)
                    # --- END SET SESSION STATE --- 
                    # Don't exit or proceed here, the main flow continues after exec_
                else:
                    QMessageBox.critical(None, "Errore Registrazione", "Impossibile impostare la master password. Controlla i log.")
                    sys.exit(1) # Exit if registration fails
            except Exception as e:
                if QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()
                QMessageBox.critical(None, "Errore Inaspettato", f"Errore critico durante la registrazione: {e}")
                sys.exit(1)
        # --- End define on_registered --- 

        # Connect the signal to the local slot BEFORE exec_
        reg_dialog.registered.connect(on_registered)

        # Execute the dialog
        if reg_dialog.exec() == QDialog.Accepted:
             # If accepted, on_registered was called and set the password.
             # verified_password should now hold the new password.
             print("Master password registered by user.")
             # Verify that verified_password is set after dialog acceptance
             if not verified_password:
                  print("[main] ERROR: Registration dialog accepted, but verified_password not set.")
                  sys.exit(1)
        else:
            print("Registration cancelled. Exiting.")
            # Exit if registration is cancelled
            sys.exit(0)

    # --- Load Settings and Profiles AFTER Authentication/Registration --- 
    print("[main] Authentication/Registration complete. Loading settings and profiles...")
    try:
        sync_manager.load_settings() # Now this can potentially decrypt client_secret using verified session pwd
        profile_manager.load_profiles() # Now this can decrypt profiles using verified session pwd
        print("[main] Settings and profiles loaded.")
    except Exception as load_err:
         print(f"[main] CRITICAL ERROR loading settings/profiles after auth: {load_err}")
         QMessageBox.critical(None, "Errore Caricamento Dati", f"Impossibile caricare i dati dopo l'autenticazione: {load_err}. L'applicazione terminerà.")
         sys.exit(1)
    # --- End Load --- 
    
    # CredentialManager loading happens in its __init__ now

    # --- Pass SyncManager to MainWindow --- 
    window = MainWindow(profile_manager=profile_manager, sync_manager=sync_manager)
    # --- End Pass SyncManager --- 

    # --- REMOVE Hotkey Listener INSTANCE --- 
    # Hotkey Listener Setup
    # hotkey_listener = HotkeyListener(window) # This class doesn't exist
    # --- END REMOVE --- 

    # Start the hotkey listener thread using the module function
    try:
        # --- CALL MODULE FUNCTION --- 
        hotkey_listener.start()
        # --- END CALL MODULE FUNCTION --- 
    except Exception as hk_err:
        QMessageBox.warning(None, "Errore Hotkey", f"Impossibile avviare l'hotkey listener: {hk_err}")
        # Non terminare necessariamente l'app, potrebbe funzionare senza hotkey

    # --- Show MainWindow --- 
    # The main window was already created earlier AFTER authentication
    # Just need to show it here.
    window.show()
    # --- End Show MainWindow --- 

    # --- Avvio Application Event Loop --- 
    # Questo codice viene raggiunto solo se la registrazione o la verifica hanno successo
    exit_code = 0
    if window: # Assicurati che la finestra sia stata creata
        try:
            print("[main] Starting application event loop...")
            exit_code = app.exec()
            print(f"[main] Application event loop finished with code: {exit_code}")
        except Exception as app_exec_err:
             print(f"[main] CRITICAL ERROR during app.exec(): {app_exec_err}")
             exit_code = 1 # Segnala errore
    else:
         # Questo non dovrebbe accadere se la logica sopra è corretta
         print("[main] ERROR: Main window was not created before starting event loop.")
         exit_code = 1 # Segnala errore

    # --- Cleanup --- 
    print("[main] Stopping hotkey listener...")
    try:
        # --- CALL MODULE FUNCTION --- 
        hotkey_listener.stop()
        # --- END CALL MODULE FUNCTION --- 
    except Exception as hk_stop_err:
        print(f"[main] Error stopping hotkey listener: {hk_stop_err}")

    print(f"[main] Exiting with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    print("--- Application Start ---")
    main()
    print("--- Application End ---") 