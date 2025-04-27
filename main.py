"""
Applicazione principale del Password Manager.
"""

import sys
import os

# Aggiungi la directory src al path di Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.core.auth_manager import AuthManager
from src.ui.auth_dialog import AuthDialog
from src.ui.registration_dialog import RegistrationDialog
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Inizializza l'AuthManager
    auth_manager = AuthManager()
    
    # Variabile per la finestra principale
    window = None
    
    # Funzione per gestire l'autenticazione riuscita
    def on_authenticated(password):
        nonlocal window
        window = MainWindow(password)
        window.show()
    
    # Se è la prima volta, mostra il dialog di registrazione
    if auth_manager.is_first_time():
        registration_dialog = RegistrationDialog()
        
        def on_registered(password):
            auth_manager.register_password(password)
            on_authenticated(password)
            
        registration_dialog.registered.connect(on_registered)
        
        if registration_dialog.exec() != RegistrationDialog.Accepted:
            sys.exit(0)
    else:
        # Altrimenti mostra il dialog di login
        auth_dialog = AuthDialog()
        auth_dialog.authenticated.connect(on_authenticated)
        
        if auth_dialog.exec() != AuthDialog.Accepted:
            sys.exit(0)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 