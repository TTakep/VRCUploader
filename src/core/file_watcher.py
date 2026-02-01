"""
VRChat Discord Uploader - ファイル監視
VRChatスクリーンショットフォルダの監視
"""
import time
from pathlib import Path
from typing import Callable, Optional
from threading import Thread, Event

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.constants import SUPPORTED_IMAGE_EXTENSIONS
from src.utils.logger import get_logger

logger = get_logger()


class ImageFileHandler(FileSystemEventHandler):
    """画像ファイル作成イベントハンドラ"""
    
    def __init__(self, callback: Callable[[Path], None]):
        super().__init__()
        self.callback = callback
        self._processing = set()  # 処理中のファイルを追跡
    
    def on_created(self, event):
        """ファイル作成時のイベント"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # 拡張子チェック
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            return
        
        # 一時ファイルはスキップ
        if ".compressed." in file_path.name:
            return
        
        # 重複処理防止
        if str(file_path) in self._processing:
            return
        
        self._processing.add(str(file_path))
        
        # ファイル書き込み完了を待つ
        Thread(target=self._wait_and_process, args=(file_path,), daemon=True).start()
    
    def _wait_and_process(self, file_path: Path):
        """ファイル書き込み完了を待ってからコールバックを実行"""
        try:
            # ファイルサイズが安定するまで待機
            last_size = -1
            stable_count = 0
            
            for _ in range(30):  # 最大30秒待機
                if not file_path.exists():
                    return
                
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:  # 2秒間サイズが安定
                        break
                else:
                    stable_count = 0
                    last_size = current_size
                
                time.sleep(1)
            
            logger.info(f"新しい画像を検出: {file_path.name}")
            self.callback(file_path)
        
        except Exception as e:
            logger.error(f"ファイル処理エラー: {e}")
        
        finally:
            self._processing.discard(str(file_path))


class FileWatcher:
    """ファイル監視クラス"""
    
    def __init__(self, watch_folder: Path, callback: Callable[[Path], None]):
        self.watch_folder = Path(watch_folder)
        self.callback = callback
        self._observer: Optional[Observer] = None
        self._running = Event()
    
    @property
    def is_running(self) -> bool:
        """監視が実行中かどうか"""
        return self._running.is_set()
    
    def start(self) -> bool:
        """監視を開始"""
        if self.is_running:
            logger.warning("監視は既に実行中です")
            return False
        
        if not self.watch_folder.exists():
            logger.error(f"監視フォルダが存在しません: {self.watch_folder}")
            return False
        
        try:
            self._observer = Observer()
            handler = ImageFileHandler(self.callback)
            self._observer.schedule(handler, str(self.watch_folder), recursive=True)
            self._observer.start()
            self._running.set()
            
            logger.info(f"ファイル監視を開始: {self.watch_folder}")
            return True
        
        except Exception as e:
            logger.error(f"監視開始エラー: {e}")
            return False
    
    def stop(self) -> None:
        """監視を停止"""
        if self._observer and self.is_running:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._running.clear()
            logger.info("ファイル監視を停止しました")
    
    def restart(self) -> bool:
        """監視を再起動"""
        self.stop()
        return self.start()
