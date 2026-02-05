"""
VRChat Discord Uploader - ヘルパー関数
"""
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional


def calculate_file_hash(file_path: Path) -> str:
    """ファイルのSHA256ハッシュを計算"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_file_size_mb(file_path: Path) -> float:
    """ファイルサイズをMB単位で取得"""
    return file_path.stat().st_size / (1024 * 1024)


def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式にフォーマット"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_month_thread_name(dt: Optional[datetime] = None) -> str:
    """指定された月（指定がない場合は現在）のスレッド名を取得 (YYYY-MM形式)"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m")


def parse_vrchat_filename(filename: str) -> Optional[datetime]:
    """VRChatのファイル名から撮影日時をパース
    
    例: VRChat_2026-02-01_18-45-30.960_3840x2160.png
    """
    try:
        # VRChat_YYYY-MM-DD_HH-MM-SS 形式をパース
        parts = filename.split("_")
        if len(parts) >= 3 and parts[0] == "VRChat":
            date_str = parts[1]
            time_str = parts[2].split(".")[0]  # ミリ秒と拡張子を除去
            datetime_str = f"{date_str} {time_str.replace('-', ':')}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return None


def get_file_modified_time(file_path: Path) -> datetime:
    """ファイルの更新日時を取得"""
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def mask_webhook_url(url: str) -> str:
    """Webhook URLをマスク表示用に変換"""
    if not url:
        return ""
    if len(url) > 30:
        return url[:20] + "..." + url[-10:]
    return "●" * len(url)
