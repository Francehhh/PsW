"""
Widget che mostra la lista delle credenziali di un profilo.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QCheckBox, QApplication, QStyle,
    QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtCore import Qt, Signal, Property, QPoint, QRectF, QPointF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QCursor, QColor, QPainter, QPen, QBrush, QPalette
from typing import List, Optional

# Nuova classe per rappresentare un singolo item credenziale
class CredentialBox(QFrame):
    # Segnali per interazione
    edit_requested = Signal()
    selected_changed = Signal(bool)
    
    def __init__(self, credential, parent=None):
        super().__init__(parent)
        self.credential = credential
        self._selected = False
        
        self.setObjectName("credentialBox")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("selected", self._selected)
        # self.setProperty("class", "cardWidget") # Ereditato da QSS globale o specifico per #credentialBox

        # Imposta colori base e hover (da QSS)
        self._base_color = QColor("#161B22") # BG_BASE da MODERN_STYLESHEET
        self._hover_color = QColor("#21262D") # BG_SECONDARY da MODERN_STYLESHEET
        self._current_bg_color = self._base_color
        
        # Abilita autoFillBackground per QPalette
        self.setAutoFillBackground(True)
        self.update_background(self._current_bg_color)

        self.setup_ui()
        self.setup_background_animation() # Nuova funzione

    def setup_ui(self):
        box_layout = QVBoxLayout(self)
        box_layout.setContentsMargins(10, 10, 10, 10) # Padding aggiornato
        box_layout.setSpacing(5) # Spaziatura interna ridotta

        # Layout superiore (Checkbox, Nome App, Bottone Modifica)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Checkbox (per selezione multipla? Manteniamola per ora)
        self.checkbox = QCheckBox()
        # self.checkbox.setStyleSheet("QCheckBox { color: white; }") # Stile da QSS
        top_layout.addWidget(self.checkbox)
        
        # Nome App (più prominente)
        self.app_name_label = QLabel(self.credential.app_name)
        self.app_name_label.setObjectName("appNameLabel") 
        # self.app_name_label.setFont(QFont("Arial", 11, QFont.Bold)) # Stile da QSS
        top_layout.addWidget(self.app_name_label, 1) # Stretch
        
        top_layout.addStretch(0)
        
        # Bottone Modifica (più piccolo, icona?)
        self.edit_btn = QPushButton("Modifica") # O usa icona QStyle.SP_DialogResetButton?
        self.edit_btn.setObjectName("editBtn") # Per stile specifico se serve
        self.edit_btn.setFixedSize(60, 24) # Dimensione fissa piccola
        self.edit_btn.setStyleSheet("QPushButton#editBtn { padding: 2px 5px; font-size: 8pt; min-width: 50px; }") # Stile inline rapido
        self.edit_btn.clicked.connect(self.edit_requested.emit)
        top_layout.addWidget(self.edit_btn)
        
        box_layout.addLayout(top_layout)

        # Layout inferiore (Nome, Cognome, Email, Username)
        # Usiamo un layout a griglia per allinearli?
        info_layout = QGridLayout()
        info_layout.setContentsMargins(25, 5, 0, 0) # Indenta sotto checkbox
        info_layout.setSpacing(4)
        info_layout.setColumnStretch(1, 1) # Colonna valori si espande

        if self.credential.first_name:
            fn_label = QLabel("Nome:")
            fn_label.setObjectName("credFirstNameLabel")
            fn_val = QLabel(self.credential.first_name)
            info_layout.addWidget(fn_label, 0, 0)
            info_layout.addWidget(fn_val, 0, 1)

        if self.credential.last_name:
            ln_label = QLabel("Cognome:")
            ln_label.setObjectName("credLastNameLabel")
            ln_val = QLabel(self.credential.last_name)
            info_layout.addWidget(ln_label, 1, 0)
            info_layout.addWidget(ln_val, 1, 1)

        if self.credential.email:
            em_label = QLabel("Email:")
            em_label.setObjectName("credEmailLabel")
            em_val = QLabel(self.credential.email)
            em_val.setToolTip(self.credential.email)
            info_layout.addWidget(em_label, 2, 0)
            info_layout.addWidget(em_val, 2, 1)

        if self.credential.username:
            un_label = QLabel("Username:")
            un_label.setObjectName("usernameLabel") # Mantiene ID vecchio
            un_val = QLabel(self.credential.username)
            un_val.setToolTip(self.credential.username)
            info_layout.addWidget(un_label, 3, 0)
            info_layout.addWidget(un_val, 3, 1)
        
        box_layout.addLayout(info_layout)
        
    def setup_background_animation(self):
        """Configura l'animazione per il colore di sfondo."""
        self.bg_color_animation = QPropertyAnimation(self, b"_backgroundColor", self)
        self.bg_color_animation.setDuration(200) # Durata animazione (ms)
        self.bg_color_animation.setEasingCurve(QEasingCurve.OutQuad)
        
    # --- Property per il colore di sfondo --- 
    def _get_background_color(self) -> QColor:
        return self._current_bg_color

    def _set_background_color(self, color: QColor):
        self._current_bg_color = color
        self.update_background(color)

    _backgroundColor = Property(QColor, _get_background_color, _set_background_color)
    # --- Fine Property --- 
    
    def update_background(self, color: QColor):
        """Aggiorna il colore di sfondo usando QPalette."""
        palette = self.palette()
        palette.setColor(QPalette.Window, color)
        self.setPalette(palette)

    def enterEvent(self, event): # Override
        """Anima il colore di sfondo verso lo stato hover."""
        # --- RIPRISTINO ANIMAZIONE COLORE SFONDO ---
        self.bg_color_animation.stop()
        self.bg_color_animation.setStartValue(self._current_bg_color)
        self.bg_color_animation.setEndValue(self._hover_color)
        self.bg_color_animation.start()
        # --- FINE RIPRISTINO ---
        super().enterEvent(event)

    def leaveEvent(self, event): # Override
        """Anima il colore di sfondo verso lo stato base."""
        # --- RIPRISTINO ANIMAZIONE COLORE SFONDO ---
        self.bg_color_animation.stop()
        self.bg_color_animation.setStartValue(self._current_bg_color)
        self.bg_color_animation.setEndValue(self._base_color)
        self.bg_color_animation.start()
        # --- FINE RIPRISTINO ---
        super().leaveEvent(event)

    def set_selected(self, selected: bool):
        if self._selected != selected:
            self._selected = selected
            self.setProperty("selected", self._selected)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
            self.selected_changed.emit(selected)

    def is_selected(self) -> bool:
        return self.checkbox.isChecked()
        
    def mousePressEvent(self, event):
        # Emettiamo il segnale di modifica quando si clicca sul box
        # Questo simula il vecchio comportamento di on_edit_credential
        self.edit_requested.emit()
        super().mousePressEvent(event)

# Modifica CredentialList per usare CredentialBox
class CredentialList(QWidget):
    """Widget che mostra la lista delle credenziali di un profilo."""
    
    credential_selected = Signal(object) # Segnale passa l'oggetto Credential
    
    def __init__(self, profile_name="", parent=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self.credential_boxes: List[CredentialBox] = [] # Lista di CredentialBox
        self.selected_credential_box: Optional[CredentialBox] = None # Riferimento al box selezionato
        self.setup_ui()
        
    def setup_ui(self):
        """Configura l'interfaccia del widget."""
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
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.cred_list_widget)
        main_box_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.main_box)
        
    def set_profile_name(self, name: str):
        """Imposta il nome del profilo."""
        self.profile_name = name
        self.profile_title.setText(name)
        
    def add_credential(self, credential):
        """Aggiunge una CredentialBox alla lista."""
        cred_box = CredentialBox(credential)
        cred_box.edit_requested.connect(lambda c=credential, b=cred_box: self.on_edit_credential(c, b))
        
        # Inserisce la nuova box in cima alla lista (o in fondo?) - In fondo è più semplice
        self.list_layout.insertWidget(self.list_layout.count() - 1, cred_box) # Inserisci prima dello stretch
        self.credential_boxes.append(cred_box)
        
    def on_edit_credential(self, credential, box: CredentialBox):
        # Deseleziona tutte le altre credenziali
        for other_box in self.credential_boxes:
            if other_box != box:
                other_box.set_selected(False)
        # Seleziona questa credenziale
        box.set_selected(True)
        self.selected_credential_box = box
        # Emetti il segnale con l'oggetto Credential
        self.credential_selected.emit(credential)
        
    def copy_password(self, credential):
        """Copia la password negli appunti."""
        clipboard = self.window().clipboard()
        if clipboard:
            clipboard.setText(credential.password)
            
    def copy_to_clipboard(self, value):
        clipboard = QApplication.clipboard()
        clipboard.setText(value)
        
    def clear(self):
        """Rimuove tutte le CredentialBox dalla lista."""
        # Rimuovi i widget dal layout
        while self.list_layout.count() > 1: # Lascia lo stretch
            item = self.list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        # Pulisci la lista di riferimenti
        self.credential_boxes = []
        self.selected_credential_box = None
        
    def get_selected_credentials(self) -> List[object]: # Ora ritorna oggetti Credential
        """Restituisce la lista delle credenziali selezionate tramite checkbox."""
        selected_creds = []
        for box in self.credential_boxes:
            if box.is_selected(): # Usa il metodo is_selected della box
                selected_creds.append(box.credential)
        return selected_creds 
        
    def clearSelection(self):
        """Deseleziona la CredentialBox attualmente selezionata (se esiste)."""
        if self.selected_credential_box:
            self.selected_credential_box.set_selected(False)
            self.selected_credential_box = None
            
    # --- Metodi update_item_display e copy_password rimossi o da adattare --- 
    # def update_item_display(self, updated_credential):
    #     # Trova la box corrispondente e aggiorna le sue label
    #     for box in self.credential_boxes:
    #         if box.credential.id == updated_credential.id:
    #             box.credential = updated_credential # Aggiorna dati interni
    #             # Aggiorna le label (richiede accesso alle label dentro box)
    #             box.app_name_label.setText(updated_credential.app_name)
    #             # ... aggiorna le altre label ...
    #             break

    # def copy_password(self, credential): ...
    # def copy_to_clipboard(self, value): ... (questo può stare in ProfileWidget) 