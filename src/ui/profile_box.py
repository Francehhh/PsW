"""
Widget per il box del profilo e la visualizzazione delle credenziali.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QStyle, QApplication, QCheckBox, QGridLayout, QSizePolicy,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QEvent, Property, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QMouseEvent, QIcon, QFont, QCursor, QColor, QPalette
from ..core.profile_manager import Profile
from ..core.credential import Credential

class ProfileBox(QFrame):
    """Box che rappresenta un profilo con le sue credenziali."""
    
    double_clicked = Signal(Profile)
    add_credential = Signal(Profile)
    delete_credential = Signal(Credential)
    edit_profile = Signal(Profile)
    selected_changed = Signal(Profile, bool)  # Nuovo segnale per la selezione
    
    def __init__(self, profile: Profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setObjectName("profileBox")
        self.setProperty("selected", False)
        
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
        """Configura l'interfaccia del box."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 10, 12, 10)

        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(10)

        # Checkbox per selezione
        self.select_checkbox = QCheckBox()
        self.select_checkbox.clicked.connect(self.on_selection_changed)
        top_row_layout.addWidget(self.select_checkbox, 0, Qt.AlignTop)
        
        # Colonna nome profilo 
        name_label = QLabel(self.profile.name)
        name_label.setObjectName("profileNameLabel")
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        top_row_layout.addWidget(name_label, 1)

        # Pulsante di modifica (a destra del nome)
        edit_btn = QPushButton()
        edit_btn.setObjectName("editProfileBtn")
        icon = QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        try:
             # Try to get a pencil icon (might require theme support)
             pencil_icon = QIcon.fromTheme("document-edit", icon)
             if not pencil_icon.isNull(): icon = pencil_icon
        except Exception:
             pass
        edit_btn.setIcon(icon)
        edit_btn.setFixedSize(22, 22)
        edit_btn.setToolTip("Modifica Profilo")
        edit_btn.setStyleSheet("QPushButton#editProfileBtn { background: transparent; border: none; padding: 0;} QPushButton#editProfileBtn:hover { background: #444; border-radius: 3px; }")
        edit_btn.clicked.connect(lambda: self.edit_profile.emit(self.profile))
        top_row_layout.addWidget(edit_btn, 0, Qt.AlignTop)
        
        layout.addLayout(top_row_layout)

        # Info container (Email, User, Tel, Via) - Keep compact
        info_container = QWidget()
        info_container.setObjectName("infoGridWidget")
        info_layout = QGridLayout(info_container)
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(0, 5, 0, 0)
        info_layout.setColumnStretch(1, 1)
        
        # Email
        email_label = QLabel("Email:")
        email_label.setObjectName("infoLabel")
        email_value = QLabel(self.profile.email or "-")
        email_value.setObjectName("infoValue")
        email_value.setToolTip(self.profile.email or "")
        info_layout.addWidget(email_label, 0, 0)
        info_layout.addWidget(email_value, 0, 1)

        # Username
        username_label = QLabel("Username:")
        username_label.setObjectName("infoLabel")
        username_value = QLabel(self.profile.username or "-")
        username_value.setObjectName("infoValue")
        username_value.setToolTip(self.profile.username or "")
        info_layout.addWidget(username_label, 1, 0)
        info_layout.addWidget(username_value, 1, 1)
        
        # Telefono
        phone_label = QLabel("Tel:")
        phone_label.setObjectName("infoLabel")
        phone_value = QLabel(self.profile.phone or "-")
        phone_value.setObjectName("infoValue")
        phone_value.setToolTip(self.profile.phone or "")
        info_layout.addWidget(phone_label, 0, 2)
        info_layout.addWidget(phone_value, 0, 3)

        # Via (Indirizzo)
        address_label = QLabel("Via:")
        address_label.setObjectName("infoLabel")
        address_text = self.profile.address[:20] + "..." if self.profile.address and len(self.profile.address) > 20 else (self.profile.address or "-")
        address_value = QLabel(address_text)
        address_value.setObjectName("infoValue")
        address_value.setToolTip(self.profile.address or "")
        info_layout.addWidget(address_label, 1, 2)
        info_layout.addWidget(address_value, 1, 3)

        layout.addWidget(info_container)
        
        # Ensure the main frame respects the size policy of the layout
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
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

    def mousePressEvent(self, event: QMouseEvent):
        """Gestisce il click sul box."""
        if event.button() == Qt.LeftButton:
            if event.type() == QEvent.MouseButtonDblClick:
                self.double_clicked.emit(self.profile)
                
    def on_selection_changed(self, checked: bool):
        """Gestisce il cambio di stato della checkbox."""
        self.selected_changed.emit(self.profile, checked)
        
    def is_selected(self) -> bool:
        """Restituisce True se il profilo è selezionato."""
        return self.select_checkbox.isChecked()
        
    def set_selected(self, selected: bool):
        """Imposta lo stato di selezione del profilo."""
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update() 