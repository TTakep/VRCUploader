"""
VRChat Discord Uploader - VRChatログパーサー
VRChatログからワールド情報を取得
"""
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from src.utils.logger import get_logger

logger = get_logger()

# VRChatログディレクトリ
VRCHAT_LOG_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / ".." / "LocalLow" / "VRChat" / "VRChat"


class VRChatLogParser:
    """VRChatログを解析してワールド情報を取得するクラス"""
    
    # ログファイル名のパターン: output_log_YYYY-MM-DD_HH-MM-SS.txt
    LOG_FILE_PATTERN = re.compile(r"output_log_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.txt")
    
    # ワールド参加ログのパターン
    ENTERING_ROOM_PATTERN = re.compile(
        r"(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}) Debug\s+-\s+\[Behaviour\] Entering Room: (.+)"
    )
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Args:
            log_dir: VRChatログディレクトリ（指定がない場合はデフォルト）
        """
        self.log_dir = Path(log_dir) if log_dir else VRCHAT_LOG_DIR.resolve()
    
    def get_log_files(self) -> List[Tuple[Path, datetime]]:
        """ログファイル一覧を取得（日時でソート）
        
        Returns:
            (ファイルパス, ログ開始日時) のリスト（新しい順）
        """
        log_files = []
        
        if not self.log_dir.exists():
            logger.warning(f"VRChatログディレクトリが存在しません: {self.log_dir}")
            return log_files
        
        for file_path in self.log_dir.glob("output_log_*.txt"):
            match = self.LOG_FILE_PATTERN.match(file_path.name)
            if match:
                try:
                    # ファイル名から日時をパース
                    datetime_str = match.group(1)
                    log_datetime = datetime.strptime(datetime_str, "%Y-%m-%d_%H-%M-%S")
                    log_files.append((file_path, log_datetime))
                except ValueError:
                    continue
        
        # 新しい順にソート
        log_files.sort(key=lambda x: x[1], reverse=True)
        return log_files
    
    def find_log_file_for_time(self, target_time: datetime) -> Optional[Path]:
        """指定した時刻に対応するログファイルを見つける
        
        Args:
            target_time: 対象の日時
            
        Returns:
            対応するログファイルのパス（見つからない場合はNone）
        """
        log_files = self.get_log_files()
        
        # target_time以前で最も近いログファイルを探す
        for file_path, log_start_time in log_files:
            if log_start_time <= target_time:
                return file_path
        
        return None
    
    def parse_log_line_time(self, time_str: str) -> Optional[datetime]:
        """ログ行の日時をパース
        
        Args:
            time_str: "YYYY.MM.DD HH:MM:SS" 形式の文字列
            
        Returns:
            datetimeオブジェクト
        """
        try:
            return datetime.strptime(time_str, "%Y.%m.%d %H:%M:%S")
        except ValueError:
            return None
    
    def get_world_name_at_time(self, target_time: datetime) -> Optional[str]:
        """指定した時刻に居たワールド名を取得
        
        Args:
            target_time: 対象の日時（写真撮影時刻）
            
        Returns:
            ワールド名（見つからない場合はNone）
        """
        log_file = self.find_log_file_for_time(target_time)
        if not log_file:
            logger.debug(f"対応するログファイルが見つかりません: {target_time}")
            return None
        
        logger.debug(f"ログファイルを解析中: {log_file.name}")
        
        last_world_name = None
        last_world_time = None
        
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = self.ENTERING_ROOM_PATTERN.match(line.strip())
                    if match:
                        time_str = match.group(1)
                        world_name = match.group(2)
                        
                        log_time = self.parse_log_line_time(time_str)
                        if log_time and log_time <= target_time:
                            # target_time以前で最新のワールド参加を記録
                            if last_world_time is None or log_time > last_world_time:
                                last_world_name = world_name
                                last_world_time = log_time
                        elif log_time and log_time > target_time:
                            # target_time を超えたら終了（ファイルは時刻順なので）
                            break
        except Exception as e:
            logger.error(f"ログファイルの解析に失敗しました: {e}")
            return None
        
        if last_world_name:
            logger.debug(f"ワールド名を取得: {last_world_name} ({last_world_time})")
        else:
            logger.debug(f"ワールド名が見つかりませんでした: {target_time}")
        
        return last_world_name


# シングルトンインスタンス
vrchat_log_parser = VRChatLogParser()
