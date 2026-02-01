"""
VRChat Discord Uploader - エントリーポイント
"""
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.utils.logger import setup_logger, get_logger
from src.core.config_manager import config_manager
from src.db.models import init_database
from src.gui.main_window import MainWindow


def check_single_instance() -> bool:
    """二重起動チェック"""
    import socket
    
    try:
        # ローカルソケットでロックを取得
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 47891))  # 任意のポート
        return True
    except socket.error:
        return False


def main():
    """メインエントリーポイント"""
    # ログ初期化
    config = config_manager.config
    setup_logger(config.log_level)
    logger = get_logger()
    
    logger.info("=" * 50)
    logger.info("VRChat Discord Uploader を起動しています...")
    
    # 二重起動チェック
    if not check_single_instance():
        logger.warning("既に起動中のインスタンスがあります")
        from PyQt6.QtWidgets import QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None, "起動エラー",
            "VRChat Discord Uploader は既に起動しています。"
        )
        return 1
    
    # DB初期化
    init_database()
    
    # Qt アプリケーション
    app = QApplication(sys.argv)
    app.setApplicationName("VRChat Discord Uploader")
    app.setQuitOnLastWindowClosed(False)  # トレイアイコン用
    
    # ハイDPI対応
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # メインウィンドウ
    window = MainWindow()
    
    # タスクトレイ最小化でなければ表示
    if not config.enable_minimize_to_tray:
        window.show()
    
    logger.info("アプリケーションを開始しました")
    
    # イベントループ
    result = app.exec()
    
    logger.info("アプリケーションを終了しました")
    return result


if __name__ == "__main__":
    sys.exit(main())
