"""
VRChat Discord Uploader - 設定管理
JSON形式での設定保存、Webhook URL暗号化
"""
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

from src.constants import CONFIG_FILE, APPDATA_DIR, VRCHAT_DEFAULT_PICTURES_PATH
from src.utils.crypto import encrypt, decrypt, is_encrypted
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class Config:
    """アプリケーション設定"""
    # Webhook設定
    webhook_url: str = ""
    
    # 監視設定
    watch_folder: str = str(VRCHAT_DEFAULT_PICTURES_PATH)
    
    # 機能設定
    enable_monthly_thread: bool = True
    enable_auto_startup: bool = False
    enable_minimize_to_tray: bool = True
    enable_auto_watch: bool = False
    enable_sound_notification: bool = True
    enable_toast_notification: bool = True
    
    # 圧縮設定
    compression_threshold_mb: float = 10.0
    
    # ログ設定
    log_level: str = "INFO"
    
    # 統計
    total_transferred: int = 0


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self):
        self._config: Optional[Config] = None
    
    @property
    def config(self) -> Config:
        """現在の設定を取得"""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def load(self) -> Config:
        """設定ファイルを読み込む"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Webhook URLを復号化
                if "webhook_url" in data and data["webhook_url"]:
                    if is_encrypted(data["webhook_url"]):
                        data["webhook_url"] = decrypt(data["webhook_url"])
                
                config = Config(**data)
                logger.info("設定ファイルを読み込みました")
                return config
            else:
                logger.info("設定ファイルが存在しないため、デフォルト設定を使用します")
                return Config()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            return Config()
    
    def save(self, config: Optional[Config] = None) -> bool:
        """設定をファイルに保存"""
        try:
            if config is not None:
                self._config = config
            
            if self._config is None:
                return False
            
            # ディレクトリを作成
            APPDATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # 設定を辞書に変換
            data = asdict(self._config)
            
            # Webhook URLを暗号化
            if data["webhook_url"]:
                data["webhook_url"] = encrypt(data["webhook_url"])
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info("設定ファイルを保存しました")
            return True
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def update(self, **kwargs) -> bool:
        """設定を更新して保存"""
        config = self.config
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return self.save(config)
    
    def reset(self) -> bool:
        """設定をデフォルトにリセット"""
        self._config = Config()
        return self.save()


# シングルトンインスタンス
config_manager = ConfigManager()
