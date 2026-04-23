"""
VRChat Discord Uploader - 自動アップデーター
GitHub Releases から最新バージョンを確認し、インストーラーをダウンロード・実行します。
"""
import os
import sys
import tempfile
import requests
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, QThread

from src.constants import GITHUB_API_URL, APP_VERSION
from src.utils.logger import get_logger

logger = get_logger()

class UpdateCheckWorker(QThread):
    """非同期でアップデート確認を行うワーカー"""
    update_available = pyqtSignal(str, str, str)  # version, release_notes, download_url
    error_occurred = pyqtSignal(str)
    no_update = pyqtSignal()
    
    def run(self):
        try:
            logger.info("アップデートの確認を開始します...")
            response = requests.get(GITHUB_API_URL, timeout=10)
            
            if response.status_code != 200:
                if response.status_code == 404:
                    logger.info("リポジトリまたはリリースが見つかりません。")
                else:
                    logger.warning(f"GitHub API エラー: {response.status_code}")
                self.error_occurred.emit(f"APIエラー: {response.status_code}")
                return
                
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            release_notes = data.get("body", "リリースノートはありません。")
            assets = data.get("assets", [])
            
            # exe アセットを探す
            download_url = None
            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    break
            
            if not latest_version or not download_url:
                logger.warning("有効なリリースバージョンまたはインストーラー(.exe)が見つかりません。")
                self.error_occurred.emit("インストーラーが見つかりませんでした。")
                return
            
            # バージョン比較
            def parse_version(v: str) -> Tuple[int, ...]:
                return tuple(int(x) for x in v.split(".") if x.isdigit())
                
            current = parse_version(APP_VERSION)
            latest = parse_version(latest_version)
            
            if latest > current:
                logger.info(f"アップデートが利用可能です: {APP_VERSION} -> {latest_version}")
                self.update_available.emit(latest_version, release_notes, download_url)
            else:
                logger.info("現在のバージョンは最新です。")
                self.no_update.emit()
                
        except Exception as e:
            logger.error(f"アップデート確認中のエラー: {e}")
            self.error_occurred.emit(str(e))

class UpdateDownloadWorker(QThread):
    """非同期でインストーラーをダウンロードするワーカー"""
    progress_changed = pyqtSignal(int)
    download_finished = pyqtSignal(str)  # downloaded file path
    error_occurred = pyqtSignal(str)
    
    def __init__(self, download_url: str):
        super().__init__()
        self.download_url = download_url
        
    def run(self):
        try:
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, "VRCUploader_Setup.exe")
            
            response = requests.get(self.download_url, stream=True, timeout=10)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(installer_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_changed.emit(progress)
            
            self.progress_changed.emit(100)
            self.download_finished.emit(installer_path)
            
        except Exception as e:
            logger.error(f"ダウンロードエラー: {e}")
            self.error_occurred.emit(str(e))

class Updater:
    """アップデートの適用（実行）を管理するクラス"""
    @staticmethod
    def execute_installer(installer_path: str):
        """インストーラーをバックグラウンドで起動し、現在のアプリを終了させる"""
        try:
            # /SILENT でバックグラウンド実行（Inno Setupのオプション）
            # 現在のプロセスを殺して強制上書きする場合は /FORCECLOSEAPPLICATIONS を加えるなど運用により調整
            subprocess.Popen([installer_path, "/SILENT", "/SP-"])
            logger.info("インストーラーを起動しました。アプリケーションを終了します。")
            sys.exit(0)
        except Exception as e:
            logger.error(f"インストーラーの起動に失敗しました: {e}")
