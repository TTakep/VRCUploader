"""
VRChat Discord Uploader - 月別スレッド管理
"""
import requests
from typing import Optional, Tuple
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.helpers import get_month_thread_name
from src.db.repository import transfer_repository

logger = get_logger()


class ThreadManager:
    """Discord月別スレッド管理クラス"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self._thread_cache: dict[str, str] = {}  # month -> thread_id
    
    def get_or_create_monthly_thread(self, image_date: Optional[datetime] = None) -> Tuple[Optional[str], Optional[str]]:
        """指定された日付の月のスレッドIDを取得または作成
        
        Args:
            image_date: 画像の日付。未指定の場合は現在時刻。
            
        Returns:
            Tuple[スレッドID, エラーメッセージ]
        """
        thread_name = get_month_thread_name(image_date)
        
        # 1. キャッシュを確認
        if thread_name in self._thread_cache:
            return self._thread_cache[thread_name], None
        
        # 2. DBを確認
        db_thread_id = transfer_repository.get_thread_id_by_month(thread_name)
        if db_thread_id:
            self._thread_cache[thread_name] = db_thread_id
            return db_thread_id, None
        
        try:
            # 3. Webhookでスレッドを作成
            # NOTE: Webhookでの thread_name パラメータによる自動スレッド作成は、
            # チャンネルが「フォーラム」である必要があります。
            # 通常のテキストチャンネルの場合は、400 Bad Request になります。
            payload = {
                "content": f"📅 **{thread_name}** のスクリーンショットスレッドを開始しました",
                "thread_name": thread_name
            }
            
            params = {"wait": "true"}
            
            response = requests.post(
                self.webhook_url,
                params=params,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                data = response.json()
                # スレッドIDを取得 (フォーラム投稿の場合、返却されるMessageオブジェクトに含まれる)
                # 1. threadオブジェクト内のid (これが最も確実)
                thread_obj = data.get("thread", {})
                thread_id = thread_obj.get("id")
                
                # 2. メッセージのchannel_id (そのメッセージが属するスレッドID)
                if not thread_id:
                    thread_id = data.get("channel_id")
                
                if thread_id:
                    self._thread_cache[thread_name] = thread_id
                    transfer_repository.save_thread_id(thread_name, thread_id)
                    logger.info(f"月別スレッドを作成しました: {thread_name} (ID: {thread_id})")
                    return thread_id, None
                else:
                    return None, "スレッドIDをレスポンスから取得できませんでした"
            
            elif response.status_code == 400:
                # 通常のテキストチャンネル等の場合、スレッド作成が拒否されることがある
                error_msg = response.json().get("message", "")
                if "forum channels" in error_msg.lower():
                    logger.warning("現在のWebhookチャンネルはフォーラムではないため、スレッドを自動作成できません")
                    return None, "TEXT_CHANNEL_LIMIT"  # 特殊なエラーコードとして返す
                return None, f"スレッド作成失敗: {error_msg}"
            
            else:
                return None, f"スレッド作成失敗: HTTP {response.status_code}"
        
        except requests.exceptions.Timeout:
            return None, "スレッド作成タイムアウト"
        except Exception as e:
            return None, f"スレッド作成エラー: {str(e)}"
    
    def clear_cache(self):
        """スレッドキャッシュをクリア"""
        self._thread_cache.clear()
