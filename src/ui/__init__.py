"""
Package per l'interfaccia utente dell'applicazione PsW.
"""

from .main_window import MainWindow
from .dashboard_widget import DashboardWidget
from .profile_widget import ProfileWidget
from .settings_dialog import SettingsDialog

__all__ = [
    'MainWindow',
    'DashboardWidget',
    'ProfileWidget',
    'SettingsDialog'
] 