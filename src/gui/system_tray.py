"""
VRChat Discord Uploader - タスクトレイ
システムトレイアイコン・メニュー
"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from src.constants import APP_NAME
from src.utils.logger import get_logger

logger = get_logger()


class SystemTray(QObject):
    """システムトレイクラス"""
    
    # シグナル
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray_icon: QSystemTrayIcon = None
        self._menu: QMenu = None
    
    def setup(self, icon: QIcon) -> bool:
        """トレイアイコンをセットアップ"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("システムトレイが利用できません")
            return False
        
        self._tray_icon = QSystemTrayIcon(icon, self.parent())
        self._tray_icon.setToolTip(APP_NAME)
        
        # メニューを作成
        self._menu = QMenu()
        
        # 表示アクション
        show_action = QAction("表示", self._menu)
        show_action.triggered.connect(self._on_show)
        self._menu.addAction(show_action)
        
        self._menu.addSeparator()
        
        # 終了アクション
        quit_action = QAction("終了", self._menu)
        quit_action.triggered.connect(self._on_quit)
        self._menu.addAction(quit_action)
        
        self._tray_icon.setContextMenu(self._menu)
        
        # ダブルクリックで表示
        self._tray_icon.activated.connect(self._on_activated)
        
        return True
    
    def show(self) -> None:
        """トレイアイコンを表示"""
        if self._tray_icon:
            self._tray_icon.show()
    
    def hide(self) -> None:
        """トレイアイコンを非表示"""
        if self._tray_icon:
            self._tray_icon.hide()
    
    def show_message(self, title: str, message: str, 
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                     duration: int = 3000) -> None:
        """トースト通知を表示"""
        if self._tray_icon:
            self._tray_icon.showMessage(title, message, icon, duration)
    
    def _on_show(self) -> None:
        """表示アクション"""
        self.show_window_requested.emit()
    
    def _on_quit(self) -> None:
        """終了アクション"""
        self.quit_requested.emit()
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """トレイアイコンがクリックされた"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
