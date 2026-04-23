"""
VRChat Discord Uploader - Discord Webhook連携
Embed形式での画像転送、リトライ機構
"""
import time
import requests
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

from src.constants import (
    DISCORD_EMBED_COLOR,
    DISCORD_MAX_RETRIES,
    APP_NAME,
    APP_VERSION
)
from src.utils.logger import get_logger
from src.utils.helpers import format_file_size, get_file_modified_time

logger = get_logger()


class DiscordWebhook:
    """Discord Webhook送信クラス"""
    
    def __init__(self, webhook_url: str, username: str = "VRChat"):
        self.webhook_url = webhook_url
        self.username = username
    
    def test_connection(self) -> Tuple[bool, str]:
        """Webhook接続をテスト"""
        try:
            # GETリクエストでWebhookの有効性を確認
            response = requests.get(self.webhook_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                name = data.get("name", "Unknown")
                return True, f"接続成功: {name}"
            else:
                return False, f"接続失敗: HTTPステータス {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "接続タイムアウト"
        except requests.exceptions.RequestException as e:
            return False, f"接続エラー: {str(e)}"
    
    def send_image(
        self,
        image_path: Path,
        original_size: Optional[int] = None,
        compressed_size: Optional[int] = None,
        thread_id: Optional[str] = None,
        world_name: Optional[str] = None,
        instance_users: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """画像をDiscordに送信
        
        Returns:
            Tuple[成功フラグ, メッセージID, エラーメッセージ]
        """
        if not image_path.exists():
            return False, None, "ファイルが存在しません"
        
        # ファイル情報を取得
        filename = image_path.name
        file_size = image_path.stat().st_size
        modified_time = get_file_modified_time(image_path)
        
        # サイズ情報を構築
        if original_size and compressed_size and original_size != compressed_size:
            size_info = f"原: {format_file_size(original_size)} → 圧縮: {format_file_size(compressed_size)}"
            compression_status = "✓ 圧縮済み（4K）"
        else:
            size_info = format_file_size(file_size)
            compression_status = "圧縮なし"
        
        fields = []
        
        # ワールド名フィールドを追加
        if world_name:
            fields.append({
                "name": "🌍 撮影ワールド",
                "value": world_name,
                "inline": False
            })
            
        # インスタンスユーザーフィールドを追加
        if instance_users:
            users_str = ", ".join(instance_users)
            # Discord制限（1024文字）を超えないように切り詰め
            if len(users_str) > 1000:
                users_str = users_str[:997] + "..."
            fields.append({
                "name": f"👥 同一インスタンスのユーザー ({len(instance_users)}人)",
                "value": users_str,
                "inline": False
            })
        
        fields.extend([
            {
                "name": "ファイルサイズ",
                "value": size_info,
                "inline": True
            },
            {
                "name": "圧縮状況",
                "value": compression_status,
                "inline": True
            },
            {
                "name": "撮影時刻",
                "value": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": True
            }
        ])
        
        embed = {
            "title": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "color": DISCORD_EMBED_COLOR,
            "fields": fields,
            "image": {
                "url": f"attachment://{filename}"
            },
            "footer": {
                "text": f"{APP_NAME} v{APP_VERSION}"
            }
        }
        
        # ペイロードを構築
        payload = {
            "username": self.username,
            "embeds": [embed]
        }
        
        # リトライ付きで送信
        for attempt in range(DISCORD_MAX_RETRIES):
            try:
                url = self.webhook_url
                params = {"wait": "true"}  # レスポンスを受け取るためにwait=trueを追加
                
                if thread_id:
                    params["thread_id"] = thread_id
                
                with open(image_path, "rb") as f:
                    files = {
                        "file": (filename, f, "image/png")
                    }
                    data = {
                        "payload_json": requests.compat.json.dumps(payload)
                    }
                    
                    response = requests.post(
                        url,
                        params=params,
                        data=data,
                        files=files,
                        timeout=60
                    )
                
                if response.status_code in [200, 204]:
                    try:
                        result = response.json()
                        message_id = result.get("id")
                    except:
                        message_id = None
                    logger.info(f"画像を送信しました: {filename}")
                    return True, message_id, None
                
                elif response.status_code == 429:
                    # レート制限
                    retry_after = response.json().get("retry_after", 60)
                    logger.warning(f"レート制限中、{retry_after}秒後にリトライ")
                    time.sleep(retry_after)
                    continue
                
                else:
                    try:
                        error_resp = response.json()
                        error_detail = error_resp.get("message", response.text)
                    except:
                        error_detail = response.text
                        
                    error_msg = f"送信失敗: HTTP {response.status_code} - {error_detail}"
                    logger.error(error_msg)
                    if attempt < DISCORD_MAX_RETRIES - 1:
                        wait_time = (2 ** attempt) * 5  # 指数バックオフ
                        logger.info(f"{wait_time}秒後にリトライ")
                        time.sleep(wait_time)
                    else:
                        return False, None, error_msg
            
            except requests.exceptions.Timeout:
                error_msg = "送信タイムアウト"
                logger.error(error_msg)
                if attempt < DISCORD_MAX_RETRIES - 1:
                    time.sleep(5)
                else:
                    return False, None, error_msg
            
            except Exception as e:
                error_msg = f"送信エラー: {str(e)}"
                logger.error(error_msg)
                return False, None, error_msg
        
        return False, None, "最大リトライ回数を超えました"
