"""
VRChat Discord Uploader - DBモデル
SQLiteスキーマ定義
"""
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from src.constants import DB_FILE, APPDATA_DIR
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class TransferRecord:
    """転送記録"""
    id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    file_hash: str = ""
    file_size_original: int = 0
    file_size_compressed: Optional[int] = None
    transferred_at: Optional[datetime] = None
    discord_message_id: Optional[str] = None
    discord_channel_id: Optional[str] = None
    discord_thread_id: Optional[str] = None
    was_compressed: bool = False
    compression_ratio: Optional[float] = None
    notes: Optional[str] = None


def init_database() -> None:
    """データベースを初期化"""
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transferred_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            file_size_original INTEGER,
            file_size_compressed INTEGER,
            transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            discord_message_id TEXT,
            discord_channel_id TEXT,
            discord_thread_id TEXT,
            was_compressed BOOLEAN DEFAULT 0,
            compression_ratio REAL,
            notes TEXT
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_filename 
        ON transferred_images(filename)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transferred_at 
        ON transferred_images(transferred_at)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_file_hash 
        ON transferred_images(file_hash)
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_threads (
            month TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    logger.info("データベースを初期化しました")
