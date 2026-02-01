"""
VRChat Discord Uploader - ロガー設定
"""
import sys
from loguru import logger

from src.constants import LOG_DIR, LOG_FORMAT, LOG_ROTATION, LOG_RETENTION, APPDATA_DIR


def setup_logger(level: str = "INFO") -> None:
    """ロガーを設定する"""
    # ディレクトリを作成
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # デフォルトのハンドラを削除
    logger.remove()
    
    # コンソール出力（PyInstallerでビルド時はsys.stderrがNoneになるためチェック）
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format=LOG_FORMAT,
            level=level,
            colorize=True
        )
    
    # ファイル出力
    logger.add(
        LOG_DIR / "app.log",
        format=LOG_FORMAT,
        level=level,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        encoding="utf-8"
    )
    
    logger.info(f"ログシステムを初期化しました (レベル: {level})")


def get_logger():
    """ロガーインスタンスを取得"""
    return logger
