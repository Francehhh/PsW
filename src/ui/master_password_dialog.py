"""
Dialogo modale per richiedere l'inserimento della Master Password.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
# Import Optional for type hinting
from typing import Optional

class MasterPasswordDialog(QDialog):
    """Dialogo per inserire la Master Password."""

    def __init__(self, prompt_message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Master Password Richiesta")
        self.setMinimumWidth(350)
        self.setModal(True) # Blocca altre finestre dell'app

        layout = QVBoxLayout(self)

        self.label = QLabel(prompt_message)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Pulsanti OK e Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.password = None # Per memorizzare la password inserita

    def accept(self):
        """Memorizza la password quando OK viene premuto."""
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Input Mancante", "Per favore inserisci la master password.")
            self.password_input.setFocus()
            return # Non chiudere il dialogo
            
        self.password = password
        super().accept() # Chiude il dialogo con stato Accepted

    @staticmethod
    def get_password(parent=None, prompt_message="Inserisci la Master Password:") -> Optional[str]:
        """
        Metodo statico per mostrare il dialogo e ottenere la password.

        Returns:
            La password inserita se l'utente preme OK, None altrimenti.
        """
        dialog = MasterPasswordDialog(prompt_message, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.password
        return None

# Esempio di utilizzo (non verrà eseguito nel contesto dell'app)
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    # Simula richiesta password
    pwd = MasterPasswordDialog.get_password(prompt_message="Inserisci la password per continuare:")
    
    if pwd:
        print(f"Password inserita: {pwd}")
    else:
        print("Operazione annullata.")
        
    sys.exit() 