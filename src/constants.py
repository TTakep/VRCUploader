"""
VRChat Discord Uploader - 定数定義
"""
import os
from pathlib import Path

# アプリケーション情報
APP_NAME = "VRChat Discord Uploader"
APP_VERSION = "1.0.0"
APP_AUTHOR = "VRCUploader Team"

# ディレクトリパス
APPDATA_DIR = Path(os.environ.get("APPDATA", "")) / "VRChatDiscordUploader"
CONFIG_FILE = APPDATA_DIR / "config.json"
LOG_DIR = APPDATA_DIR / "logs"
DB_FILE = APPDATA_DIR / "history.db"

# VRChat デフォルト設定
VRCHAT_DEFAULT_PICTURES_PATH = Path.home() / "Pictures" / "VRChat"

# Discord 設定
DISCORD_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MiB
DISCORD_EMBED_COLOR = 0x2ECC71  # 緑色
DISCORD_RATE_LIMIT_PER_MINUTE = 120
DISCORD_MAX_RETRIES = 3

# 画像処理設定
IMAGE_MAX_RESOLUTION_4K = (3840, 2160)
IMAGE_MAX_RESOLUTION_1440P = (2560, 1440)
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# 暗号化設定
ENCRYPTION_KEY_FILE = APPDATA_DIR / ".key"

# ログ設定
LOG_ROTATION = "1 day"
LOG_RETENTION = "10 days"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
