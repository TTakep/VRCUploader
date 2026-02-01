"""
VRChat Discord Uploader - 設定ウィジェット
タブ式設定画面 (StackedWidget用)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QFileDialog, QGroupBox, QFormLayout, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.config_manager import config_manager
from src.core.discord_webhook import DiscordWebhook
from src.utils.logger import get_logger

logger = get_logger()


class SettingsWidget(QWidget):
    """設定ウィジェット"""
    
    finished = pyqtSignal()  # 完了シグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("設定")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # タブウィジェット
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 各タブを追加
        self.tabs.addTab(self._create_basic_tab(), "基本設定")
        self.tabs.addTab(self._create_transfer_tab(), "転送設定")
        self.tabs.addTab(self._create_automation_tab(), "自動化")
        self.tabs.addTab(self._create_advanced_tab(), "詳細設定")
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存して戻る")
        self.save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self._cancel)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _create_basic_tab(self) -> QWidget:
        """基本設定タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Webhook設定
        webhook_group = QGroupBox("Discord Webhook")
        webhook_layout = QFormLayout(webhook_group)
        
        self.webhook_input = QLineEdit()
        self.webhook_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.webhook_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        webhook_layout.addRow("Webhook URL:", self.webhook_input)
        
        webhook_buttons = QHBoxLayout()
        self.show_webhook_btn = QPushButton("表示/非表示")
        self.show_webhook_btn.clicked.connect(self._toggle_webhook_visibility)
        webhook_buttons.addWidget(self.show_webhook_btn)
        
        self.test_webhook_btn = QPushButton("接続テスト")
        self.test_webhook_btn.clicked.connect(self._test_webhook)
        webhook_buttons.addWidget(self.test_webhook_btn)
        
        webhook_layout.addRow("", webhook_buttons)
        layout.addWidget(webhook_group)
        
        # 監視フォルダ設定
        folder_group = QGroupBox("監視フォルダ")
        folder_layout = QHBoxLayout(folder_group)
        
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        folder_layout.addWidget(self.folder_input)
        
        self.browse_btn = QPushButton("参照...")
        self.browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(self.browse_btn)
        
        layout.addWidget(folder_group)
        layout.addStretch()
        
        return widget
    
    def _create_transfer_tab(self) -> QWidget:
        """転送設定タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # スレッド設定
        thread_group = QGroupBox("スレッド設定")
        thread_layout = QVBoxLayout(thread_group)
        
        self.monthly_thread_check = QCheckBox("月別スレッド機能を有効にする (YYYY-MM形式)")
        thread_layout.addWidget(self.monthly_thread_check)
        
        layout.addWidget(thread_group)
        
        # 圧縮設定
        compress_group = QGroupBox("画像圧縮")
        compress_layout = QFormLayout(compress_group)
        
        self.compression_threshold = QSpinBox()
        self.compression_threshold.setRange(1, 25)
        self.compression_threshold.setSuffix(" MB")
        compress_layout.addRow("圧縮閾値:", self.compression_threshold)
        
        layout.addWidget(compress_group)
        layout.addStretch()
        
        return widget
    
    def _create_automation_tab(self) -> QWidget:
        """自動化タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 起動設定
        startup_group = QGroupBox("起動設定")
        startup_layout = QVBoxLayout(startup_group)
        
        self.auto_startup_check = QCheckBox("Windows起動時に自動起動")
        startup_layout.addWidget(self.auto_startup_check)
        
        self.minimize_to_tray_check = QCheckBox("起動時にタスクトレイに最小化")
        startup_layout.addWidget(self.minimize_to_tray_check)
        
        self.auto_watch_check = QCheckBox("起動時に自動的に監視を開始")
        startup_layout.addWidget(self.auto_watch_check)
        
        layout.addWidget(startup_group)
        
        # 通知設定
        notify_group = QGroupBox("通知設定")
        notify_layout = QVBoxLayout(notify_group)
        
        self.sound_notification_check = QCheckBox("転送完了時にサウンドを再生")
        notify_layout.addWidget(self.sound_notification_check)
        
        self.toast_notification_check = QCheckBox("転送完了時に通知を表示")
        notify_layout.addWidget(self.toast_notification_check)
        
        layout.addWidget(notify_group)
        layout.addStretch()
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """詳細設定タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ログ設定
        log_group = QGroupBox("ログ設定")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addRow("ログレベル:", self.log_level_combo)
        
        layout.addWidget(log_group)
        
        # データ管理
        data_group = QGroupBox("データ管理")
        data_layout = QVBoxLayout(data_group)
        
        self.clear_history_btn = QPushButton("転送履歴をクリア")
        self.clear_history_btn.clicked.connect(self._clear_history)
        data_layout.addWidget(self.clear_history_btn)
        
        self.reset_settings_btn = QPushButton("設定をリセット")
        self.reset_settings_btn.clicked.connect(self._reset_settings)
        data_layout.addWidget(self.reset_settings_btn)
        
        layout.addWidget(data_group)
        layout.addStretch()
        
        return widget
    
    def _load_settings(self):
        """設定を読み込んでUIに反映"""
        config = config_manager.config
        
        self.webhook_input.setText(config.webhook_url)
        self.folder_input.setText(config.watch_folder)
        self.monthly_thread_check.setChecked(config.enable_monthly_thread)
        self.compression_threshold.setValue(int(config.compression_threshold_mb))
        self.auto_startup_check.setChecked(config.enable_auto_startup)
        self.minimize_to_tray_check.setChecked(config.enable_minimize_to_tray)
        self.auto_watch_check.setChecked(config.enable_auto_watch)
        self.sound_notification_check.setChecked(config.enable_sound_notification)
        self.toast_notification_check.setChecked(config.enable_toast_notification)
        
        index = self.log_level_combo.findText(config.log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
    
    def _save_settings(self):
        """設定を保存"""
        config_manager.update(
            webhook_url=self.webhook_input.text(),
            watch_folder=self.folder_input.text(),
            enable_monthly_thread=self.monthly_thread_check.isChecked(),
            compression_threshold_mb=float(self.compression_threshold.value()),
            enable_auto_startup=self.auto_startup_check.isChecked(),
            enable_minimize_to_tray=self.minimize_to_tray_check.isChecked(),
            enable_auto_watch=self.auto_watch_check.isChecked(),
            enable_sound_notification=self.sound_notification_check.isChecked(),
            enable_toast_notification=self.toast_notification_check.isChecked(),
            log_level=self.log_level_combo.currentText()
        )
        
        # 自動起動設定を適用
        self._apply_auto_startup()
        
        # シグナルを発火して戻る
        self.finished.emit()
    
    def _cancel(self):
        """キャンセル（保存せずに戻る）"""
        # 現在の設定を再読み込みしてリセット
        self._load_settings()
        self.finished.emit()
    
    def _toggle_webhook_visibility(self):
        """Webhook URLの表示/非表示を切り替え"""
        if self.webhook_input.echoMode() == QLineEdit.EchoMode.Password:
            self.webhook_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.webhook_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _test_webhook(self):
        """Webhook接続テスト"""
        url = self.webhook_input.text()
        if not url:
            QMessageBox.warning(self, "エラー", "Webhook URLを入力してください")
            return
        
        webhook = DiscordWebhook(url)
        success, message = webhook.test_connection()
        
        if success:
            QMessageBox.information(self, "接続成功", message)
        else:
            QMessageBox.warning(self, "接続失敗", message)
    
    def _browse_folder(self):
        """フォルダ選択ダイアログ"""
        folder = QFileDialog.getExistingDirectory(
            self, "監視フォルダを選択",
            self.folder_input.text()
        )
        if folder:
            self.folder_input.setText(folder)
    
    def _clear_history(self):
        """履歴をクリア"""
        reply = QMessageBox.question(
            self, "確認",
            "全ての転送履歴を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from src.db.repository import transfer_repository
            transfer_repository.clear_all()
            QMessageBox.information(self, "完了", "転送履歴を削除しました")
    
    def _reset_settings(self):
        """設定をリセット"""
        reply = QMessageBox.question(
            self, "確認",
            "設定をデフォルトに戻しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config_manager.reset()
            self._load_settings()
            QMessageBox.information(self, "完了", "設定をリセットしました")
    
    def _apply_auto_startup(self):
        """自動起動設定を適用"""
        import sys
        import winreg
        
        app_path = sys.executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "VRChatDiscordUploader"
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
            )
            
            if self.auto_startup_check.isChecked():
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                logger.info("自動起動を有効にしました")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    logger.info("自動起動を無効にしました")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"自動起動設定エラー: {e}")
