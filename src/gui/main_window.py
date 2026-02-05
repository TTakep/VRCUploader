"""
VRChat Discord Uploader - メインウィンドウ
ステータス表示、クイックアクション、転送ログ
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QCheckBox, QFrame, QMessageBox, QApplication, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QCloseEvent, QFont
import winsound

from src.constants import APP_NAME, APP_VERSION
from src.core.config_manager import config_manager
from src.core.discord_webhook import DiscordWebhook
from src.core.thread_manager import ThreadManager
from src.core.image_processor import ImageProcessor
from src.core.file_watcher import FileWatcher
from src.db.repository import transfer_repository
from src.db.models import TransferRecord
from src.gui.settings_widget import SettingsWidget
from src.gui.system_tray import SystemTray
from src.utils.helpers import calculate_file_hash, mask_webhook_url
from src.utils.logger import get_logger

logger = get_logger()


class TransferWorker(QThread):
    """画像転送ワーカースレッド"""
    
    finished = pyqtSignal(bool, str, str)  # success, filename, message
    
    def __init__(self, image_path: Path, webhook: DiscordWebhook, 
                 processor: ImageProcessor, thread_manager: Optional[ThreadManager] = None,
                 enable_monthly_thread: bool = False):
        super().__init__()
        self.image_path = image_path
        self.webhook = webhook
        self.processor = processor
        self.thread_manager = thread_manager
        self.enable_monthly_thread = enable_monthly_thread
    
    def run(self):
        try:
            filename = self.image_path.name
            
            # 重複チェック
            file_hash = calculate_file_hash(self.image_path)
            if transfer_repository.exists_by_hash(file_hash):
                self.finished.emit(False, filename, "既に転送済みです")
                return
            
            # 画像処理
            processed_path, original_size, final_size, was_compressed = \
                self.processor.process_image(self.image_path)
            
            # 日付を解析 (ファイル名から、失敗した場合は更新日時)
            from src.utils.helpers import parse_vrchat_filename, get_file_modified_time
            image_date = parse_vrchat_filename(filename)
            if not image_date:
                image_date = get_file_modified_time(self.image_path)
            
            # スレッドIDを取得
            thread_id = None
            if self.enable_monthly_thread and self.thread_manager:
                thread_id, error = self.thread_manager.get_or_create_monthly_thread(image_date)
                if error:
                    if error == "TEXT_CHANNEL_LIMIT":
                        logger.warning("テキストチャンネルのためスレッドを作成できませんでした。通常の投稿を行います。")
                    else:
                        logger.warning(f"スレッド作成エラー (日付: {image_date}): {error}")
            
            # 送信
            success, message_id, error = self.webhook.send_image(
                processed_path,
                original_size=original_size,
                compressed_size=final_size if was_compressed else None,
                thread_id=thread_id
            )
            
            # 一時ファイルを削除
            if was_compressed:
                self.processor.cleanup_temp_file(processed_path)
            
            if success:
                # 履歴に記録
                record = TransferRecord(
                    filename=filename,
                    file_path=str(self.image_path),
                    file_hash=file_hash,
                    file_size_original=original_size,
                    file_size_compressed=final_size if was_compressed else None,
                    discord_message_id=message_id,
                    discord_thread_id=thread_id,
                    was_compressed=was_compressed,
                    compression_ratio=final_size / original_size if was_compressed else None
                )
                transfer_repository.add_record(record)
                
                msg = "転送成功"
                if was_compressed:
                    msg += f" (圧縮: {original_size/1024/1024:.1f}MB → {final_size/1024/1024:.1f}MB)"
                self.finished.emit(True, filename, msg)
            else:
                self.finished.emit(False, filename, error or "転送失敗")
        
        except Exception as e:
            logger.error(f"転送エラー: {e}")
            self.finished.emit(False, self.image_path.name, str(e))


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        self.file_watcher: Optional[FileWatcher] = None
        self.webhook: Optional[DiscordWebhook] = None
        self.thread_manager: Optional[ThreadManager] = None
        self.image_processor = ImageProcessor()
        self.system_tray: Optional[SystemTray] = None
        self.transfer_workers = []
        
        self._setup_ui()
        self._setup_tray()
        self._load_config(initial=True)
        self._update_status()
        
        # 自動監視開始
        if config_manager.config.enable_auto_watch:
            QTimer.singleShot(100, self._start_watching)
        
        # 定期更新タイマー
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(5000)  # 5秒ごと
    
    def _setup_ui(self):
        """UIをセットアップ"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        
        # アイコン設定
        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # メインコンテナとStackedWidget
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # ダッシュボード（ページ0）
        self.dashboard_page = QWidget()
        self.stacked_widget.addWidget(self.dashboard_page)
        self._setup_dashboard_ui(self.dashboard_page)
        
        # 設定画面（ページ1）
        self.settings_page = SettingsWidget()
        self.settings_page.finished.connect(self._on_settings_finished)
        self.stacked_widget.addWidget(self.settings_page)
        
    def _setup_dashboard_ui(self, parent_widget):
        """ダッシュボードUIをセットアップ"""
        layout = QVBoxLayout(parent_widget)
        layout.setSpacing(15)
        
        # ステータスセクション
        status_group = QGroupBox("📊 ステータス")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("監視状態: 停止中")
        self.status_label.setFont(QFont("", 10))
        status_layout.addWidget(self.status_label)
        
        self.last_transfer_label = QLabel("最終転送: -")
        status_layout.addWidget(self.last_transfer_label)
        
        stats_layout = QHBoxLayout()
        self.today_count_label = QLabel("本日転送数: 0枚")
        stats_layout.addWidget(self.today_count_label)
        self.total_count_label = QLabel("累計転送数: 0枚")
        stats_layout.addWidget(self.total_count_label)
        status_layout.addLayout(stats_layout)
        
        layout.addWidget(status_group)
        
        # クイックアクションセクション
        action_group = QGroupBox("🎯 クイックアクション")
        action_layout = QHBoxLayout(action_group)
        
        self.open_folder_btn = QPushButton("📂 フォルダを開く")
        self.open_folder_btn.clicked.connect(self._open_folder)
        action_layout.addWidget(self.open_folder_btn)
        
        self.settings_btn = QPushButton("⚙️ 設定")
        self.settings_btn.clicked.connect(self._open_settings)
        action_layout.addWidget(self.settings_btn)
        
        self.toggle_watch_btn = QPushButton("▶️ 開始")
        self.toggle_watch_btn.clicked.connect(self._toggle_watch)
        action_layout.addWidget(self.toggle_watch_btn)
        
        layout.addWidget(action_group)
        
        # 転送ログセクション
        log_group = QGroupBox("📜 転送ログ（直近10件）")
        log_layout = QVBoxLayout(log_group)
        
        self.log_list = QListWidget()
        self.log_list.setAlternatingRowColors(True)
        log_layout.addWidget(self.log_list)
        
        layout.addWidget(log_group)
        
        # 設定クイックメニュー
        quick_group = QGroupBox("🔧 クイック設定")
        quick_layout = QVBoxLayout(quick_group)
        
        self.auto_startup_check = QCheckBox("Windows起動時に自動起動")
        self.auto_startup_check.stateChanged.connect(self._on_quick_setting_changed)
        quick_layout.addWidget(self.auto_startup_check)
        
        self.minimize_tray_check = QCheckBox("タスクトレイに最小化")
        self.minimize_tray_check.stateChanged.connect(self._on_quick_setting_changed)
        quick_layout.addWidget(self.minimize_tray_check)
        
        
        layout.addWidget(quick_group)
        
        # Webhook表示
        webhook_layout = QHBoxLayout()
        self.webhook_label = QLabel("🌐 Webhook URL: 未設定")
        webhook_layout.addWidget(self.webhook_label)
        
        self.test_connection_btn = QPushButton("接続確認")
        self.test_connection_btn.clicked.connect(self._test_connection)
        webhook_layout.addWidget(self.test_connection_btn)
        
        layout.addLayout(webhook_layout)
        
        # フッター
        footer = QLabel(f"v{APP_VERSION} | © {APP_NAME}")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: gray;")
        layout.addWidget(footer)
    
    def _setup_tray(self):
        """タスクトレイをセットアップ"""
        self.system_tray = SystemTray(self)
        
        # デフォルトアイコン
        icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = QApplication.style().standardIcon(
                QApplication.style().StandardPixmap.SP_ComputerIcon
            )
        
        if self.system_tray.setup(icon):
            self.system_tray.show_window_requested.connect(self._show_from_tray)
            self.system_tray.quit_requested.connect(self._quit_app)
            self.system_tray.show()
    
    def _load_config(self, initial: bool = False):
        """設定を読み込み"""
        config = config_manager.config
        
        # クイック設定を反映
        self.auto_startup_check.setChecked(config.enable_auto_startup)
        self.minimize_tray_check.setChecked(config.enable_minimize_to_tray)
        
        # Webhookを設定
        if config.webhook_url:
            self.webhook = DiscordWebhook(config.webhook_url)
            self.thread_manager = ThreadManager(config.webhook_url)
            self.webhook_label.setText(f"🌐 Webhook URL: {mask_webhook_url(config.webhook_url)}")
        
        # 圧縮閾値を設定
        self.image_processor = ImageProcessor(
            int(config.compression_threshold_mb * 1024 * 1024)
        )
        
        # 最小化起動
        if initial and config.enable_minimize_to_tray:
            QTimer.singleShot(100, self._minimize_to_tray)
    
    def _update_status(self):
        """ステータスを更新"""
        # 監視状態
        if self.file_watcher and self.file_watcher.is_running:
            self.status_label.setText("監視状態: ✓ 稼働中")
            self.status_label.setStyleSheet("color: green;")
            self.toggle_watch_btn.setText("⏹️ 停止")
        else:
            self.status_label.setText("監視状態: ⏸️ 停止中")
            self.status_label.setStyleSheet("color: gray;")
            self.toggle_watch_btn.setText("▶️ 開始")
        
        # 転送統計
        today_count = transfer_repository.get_today_count()
        total_count = transfer_repository.get_total_count()
        self.today_count_label.setText(f"本日転送数: {today_count}枚")
        self.total_count_label.setText(f"累計転送数: {total_count:,}枚")
        
        # 最近の転送
        recent = transfer_repository.get_recent_records(1)
        if recent:
            last = recent[0]
            if last.transferred_at:
                self.last_transfer_label.setText(
                    f"最終転送: {last.transferred_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
        
        # ログリスト更新
        self._update_log_list()
    
    def _update_log_list(self):
        """転送ログリストを更新"""
        self.log_list.clear()
        
        records = transfer_repository.get_recent_records(10)
        for record in records:
            icon = "✓" if record.id else "⚠"
            text = f"{icon} {record.filename}"
            if record.was_compressed and record.file_size_original and record.file_size_compressed:
                orig_mb = record.file_size_original / 1024 / 1024
                comp_mb = record.file_size_compressed / 1024 / 1024
                text += f" (圧縮: {orig_mb:.1f}MB → {comp_mb:.1f}MB)"
            
            item = QListWidgetItem(text)
            self.log_list.addItem(item)
    
    def _toggle_watch(self):
        """監視の開始/停止を切り替え"""
        if self.file_watcher and self.file_watcher.is_running:
            self.file_watcher.stop()
            self._add_log_message("ファイル監視を停止しました", is_error=False)
        else:
            self._start_watching()
        
        self._update_status()
    
    def _start_watching(self):
        """監視を開始"""
        # 既存の監視を停止
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher = None
            
        config = config_manager.config
        
        if not config.webhook_url:
            QMessageBox.warning(
                self, "エラー",
                "Webhook URLが設定されていません。\n設定画面から Webhook URL を入力してください。"
            )
            return
        
        watch_folder = Path(config.watch_folder)
        if not watch_folder.exists():
            QMessageBox.warning(
                self, "エラー",
                f"監視フォルダが存在しません:\n{watch_folder}"
            )
            return
        
        self.file_watcher = FileWatcher(watch_folder, self._on_new_image)
        if self.file_watcher.start():
            self._add_log_message(f"監視開始: {watch_folder}", is_error=False)
            if self.system_tray:
                self.system_tray.show_message(
                    APP_NAME,
                    "ファイル監視を開始しました"
                )
    
    def _on_new_image(self, image_path: Path):
        """新しい画像が検出された"""
        if not self.webhook:
            return
        
        config = config_manager.config
        
        worker = TransferWorker(
            image_path,
            self.webhook,
            self.image_processor,
            self.thread_manager,
            config.enable_monthly_thread
        )
        worker.finished.connect(self._on_transfer_finished)
        worker.start()
        
        self.transfer_workers.append(worker)
    
    def _on_transfer_finished(self, success: bool, filename: str, message: str):
        """転送完了"""
        self._add_log_message(f"{filename}: {message}", is_error=not success)
        self._update_status()
        
        # 音を鳴らす
        if success and config_manager.config.enable_sound_notification:
            try:
                # システムの通知音を再生
                winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                # 失敗した場合はビープ音
                winsound.MessageBeep(winsound.MB_OK)
        
        if self.system_tray and config_manager.config.enable_toast_notification:
            if success:
                self.system_tray.show_message(
                    "転送完了",
                    f"{filename}\n{message}"
                )
            else:
                self.system_tray.show_message(
                    "転送失敗",
                    f"{filename}\n{message}",
                    QSystemTrayIcon.MessageIcon.Warning
                )
    
    def _add_log_message(self, message: str, is_error: bool = False):
        """ログメッセージを追加"""
        icon = "⚠" if is_error else "✓"
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{timestamp}] {icon} {message}")
        if is_error:
            item.setForeground(Qt.GlobalColor.red)
        self.log_list.insertItem(0, item)
        
        # 最大100件に制限
        while self.log_list.count() > 100:
            self.log_list.takeItem(self.log_list.count() - 1)
    
    def _open_folder(self):
        """監視フォルダを開く"""
        folder = Path(config_manager.config.watch_folder)
        if folder.exists():
            os.startfile(folder)
    
    def _open_settings(self):
        """設定画面を開く"""
        # 最新の設定を読み込んでから表示（念のため）
        self.settings_page._load_settings()
        self.stacked_widget.setCurrentIndex(1)
    
    def _on_settings_finished(self):
        """設定画面から戻る"""
        self._load_config()
        
        # 監視を再起動（設定変更の可能性があるため）
        if self.file_watcher and self.file_watcher.is_running:
            self.file_watcher.restart()
            
        self.stacked_widget.setCurrentIndex(0)
    
    def _test_connection(self):
        """Webhook接続テスト"""
        if not self.webhook:
            QMessageBox.warning(self, "エラー", "Webhook URLが設定されていません")
            return
        
        success, message = self.webhook.test_connection()
        if success:
            QMessageBox.information(self, "接続成功", message)
        else:
            QMessageBox.warning(self, "接続失敗", message)
    
    def _on_quick_setting_changed(self):
        """クイック設定が変更された"""
        config_manager.update(
            enable_auto_startup=self.auto_startup_check.isChecked(),
            enable_minimize_to_tray=self.minimize_tray_check.isChecked()
        )
    
    def _minimize_to_tray(self):
        """タスクトレイに最小化"""
        self.hide()
        if self.system_tray:
            self.system_tray.show_message(
                APP_NAME,
                "タスクトレイで実行中です"
            )
    
    def _show_from_tray(self):
        """トレイからウィンドウを表示"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def _quit_app(self):
        """アプリケーションを終了"""
        if self.file_watcher:
            self.file_watcher.stop()
        QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        """ウィンドウを閉じる時"""
        if self.minimize_tray_check.isChecked():
            event.ignore()
            self._minimize_to_tray()
        else:
            if self.file_watcher:
                self.file_watcher.stop()
            event.accept()


# QSystemTrayIconのインポート (転送完了通知用)
from PyQt6.QtWidgets import QSystemTrayIcon
