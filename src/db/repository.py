"""
VRChat Discord Uploader - DBリポジトリ
転送履歴の記録・検索・重複検出
"""
import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from src.constants import DB_FILE
from src.db.models import TransferRecord, init_database
from src.utils.logger import get_logger

logger = get_logger()


class TransferRepository:
    """転送履歴リポジトリ"""
    
    def __init__(self):
        init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """DB接続を取得"""
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_record(self, record: TransferRecord) -> bool:
        """転送記録を追加"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transferred_images (
                    filename, file_path, file_hash, file_size_original,
                    file_size_compressed, discord_message_id, discord_channel_id,
                    discord_thread_id, was_compressed, compression_ratio, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.filename,
                record.file_path,
                record.file_hash,
                record.file_size_original,
                record.file_size_compressed,
                record.discord_message_id,
                record.discord_channel_id,
                record.discord_thread_id,
                record.was_compressed,
                record.compression_ratio,
                record.notes
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"転送記録を追加: {record.filename}")
            return True
        
        except sqlite3.IntegrityError:
            logger.warning(f"重複レコード: {record.filename}")
            return False
        except Exception as e:
            logger.error(f"レコード追加エラー: {e}")
            return False
    
    def exists_by_hash(self, file_hash: str) -> bool:
        """ハッシュで存在確認"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM transferred_images WHERE file_hash = ?",
            (file_hash,)
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    def exists_by_path(self, file_path: str) -> bool:
        """パスで存在確認"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM transferred_images WHERE file_path = ?",
            (file_path,)
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    def get_recent_records(self, limit: int = 10) -> List[TransferRecord]:
        """最近の転送記録を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM transferred_images 
            ORDER BY transferred_at DESC 
            LIMIT ?
        """, (limit,))
        
        records = []
        for row in cursor.fetchall():
            records.append(TransferRecord(
                id=row["id"],
                filename=row["filename"],
                file_path=row["file_path"],
                file_hash=row["file_hash"],
                file_size_original=row["file_size_original"],
                file_size_compressed=row["file_size_compressed"],
                transferred_at=datetime.fromisoformat(row["transferred_at"]) if row["transferred_at"] else None,
                discord_message_id=row["discord_message_id"],
                was_compressed=bool(row["was_compressed"]),
                compression_ratio=row["compression_ratio"]
            ))
        
        conn.close()
        return records
    
    def get_today_count(self) -> int:
        """本日の転送数を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # ローカルタイムゾーンでの本日の開始時刻と終了時刻を計算
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # ローカル時刻をUTCに変換（JSTはUTC+9）
        # DBはCURRENT_TIMESTAMPでUTCとして保存されているため
        import time
        utc_offset = timedelta(seconds=time.timezone if time.daylight == 0 else time.altzone)
        today_start_utc = today_start + utc_offset
        today_end_utc = today_end + utc_offset
        
        cursor.execute("""
            SELECT COUNT(*) FROM transferred_images 
            WHERE transferred_at >= ? AND transferred_at < ?
        """, (today_start_utc.strftime("%Y-%m-%d %H:%M:%S"), 
              today_end_utc.strftime("%Y-%m-%d %H:%M:%S")))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_total_count(self) -> int:
        """総転送数を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transferred_images")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear_all(self) -> bool:
        """全レコードを削除"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transferred_images")
            cursor.execute("DELETE FROM monthly_threads")
            conn.commit()
            conn.close()
            logger.info("全転送履歴を削除しました")
            return True
        except Exception as e:
            logger.error(f"履歴削除エラー: {e}")
            return False

    def get_thread_id_by_month(self, month: str) -> Optional[str]:
        """月別スレッドIDを取得"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT thread_id FROM monthly_threads WHERE month = ?", (month,))
            row = cursor.fetchone()
            conn.close()
            return row["thread_id"] if row else None
        except Exception as e:
            logger.error(f"スレッドID取得エラー: {e}")
            return None

    def save_thread_id(self, month: str, thread_id: str) -> bool:
        """スレッドIDを保存"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO monthly_threads (month, thread_id)
                VALUES (?, ?)
            """, (month, thread_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"スレッドID保存エラー: {e}")
            return False


# シングルトンインスタンス
transfer_repository = TransferRepository()
