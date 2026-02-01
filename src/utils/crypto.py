"""
VRChat Discord Uploader - 暗号化ユーティリティ
Webhook URLのAES-256暗号化・復号化
"""
import os
from pathlib import Path
from cryptography.fernet import Fernet

from src.constants import ENCRYPTION_KEY_FILE, APPDATA_DIR


def _ensure_key_file() -> bytes:
    """暗号化キーファイルを確保し、キーを返す"""
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if ENCRYPTION_KEY_FILE.exists():
        return ENCRYPTION_KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        ENCRYPTION_KEY_FILE.write_bytes(key)
        # Windowsで読み取り専用にする
        os.chmod(ENCRYPTION_KEY_FILE, 0o600)
        return key


def encrypt(plaintext: str) -> str:
    """文字列を暗号化してBase64エンコードされた文字列を返す"""
    key = _ensure_key_file()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt(ciphertext: str) -> str:
    """暗号化された文字列を復号化して元の文字列を返す"""
    key = _ensure_key_file()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
    return decrypted.decode("utf-8")


def is_encrypted(text: str) -> bool:
    """文字列が暗号化されているかどうかを判定"""
    try:
        key = _ensure_key_file()
        fernet = Fernet(key)
        fernet.decrypt(text.encode("utf-8"))
        return True
    except Exception:
        return False
