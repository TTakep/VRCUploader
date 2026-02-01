"""
VRChat Discord Uploader - 画像処理
10MiB超過時の自動圧縮、リサイズ、PNG最適化
"""
import io
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image

from src.constants import (
    DISCORD_MAX_FILE_SIZE,
    IMAGE_MAX_RESOLUTION_4K,
    IMAGE_MAX_RESOLUTION_1440P
)
from src.utils.logger import get_logger

logger = get_logger()


class ImageProcessor:
    """画像処理クラス"""
    
    def __init__(self, threshold_bytes: int = DISCORD_MAX_FILE_SIZE):
        self.threshold_bytes = threshold_bytes
    
    def needs_compression(self, image_path: Path) -> bool:
        """圧縮が必要かどうかを判定"""
        return image_path.stat().st_size > self.threshold_bytes
    
    def process_image(self, image_path: Path) -> Tuple[Path, int, int, bool]:
        """画像を処理し、必要に応じて圧縮
        
        Returns:
            Tuple[処理後のパス, 元サイズ, 処理後サイズ, 圧縮したかどうか]
        """
        original_size = image_path.stat().st_size
        
        if not self.needs_compression(image_path):
            logger.debug(f"圧縮不要: {image_path.name} ({original_size} bytes)")
            return image_path, original_size, original_size, False
        
        logger.info(f"圧縮を開始: {image_path.name} ({original_size} bytes)")
        
        try:
            # 画像を読み込み
            with Image.open(image_path) as img:
                # RGBA -> RGB 変換（透明度がある場合）
                if img.mode == "RGBA":
                    # 白い背景に合成
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                
                # 最初に4Kにリサイズを試みる
                compressed_img, compressed_bytes = self._compress_with_resize(
                    img, IMAGE_MAX_RESOLUTION_4K
                )
                
                # まだ大きい場合は1440pにリサイズ
                if compressed_bytes > self.threshold_bytes:
                    logger.info("4Kでも大きいため、1440pにリサイズ")
                    compressed_img, compressed_bytes = self._compress_with_resize(
                        img, IMAGE_MAX_RESOLUTION_1440P
                    )
                
                # 圧縮後のファイルを保存（一時ファイル）
                output_path = image_path.with_suffix(".compressed.png")
                compressed_img.save(output_path, "PNG", optimize=True)
                
                final_size = output_path.stat().st_size
                logger.info(
                    f"圧縮完了: {image_path.name} "
                    f"({original_size} -> {final_size} bytes, "
                    f"{(1 - final_size/original_size)*100:.1f}% 削減)"
                )
                
                return output_path, original_size, final_size, True
        
        except Exception as e:
            logger.error(f"画像処理エラー: {e}")
            return image_path, original_size, original_size, False
    
    def _compress_with_resize(
        self, 
        img: Image.Image, 
        max_resolution: Tuple[int, int]
    ) -> Tuple[Image.Image, int]:
        """指定解像度にリサイズして圧縮サイズを返す"""
        # アスペクト比を維持してリサイズ
        img_copy = img.copy()
        img_copy.thumbnail(max_resolution, Image.Resampling.LANCZOS)
        
        # メモリ上でサイズを確認
        buffer = io.BytesIO()
        img_copy.save(buffer, "PNG", optimize=True)
        compressed_bytes = buffer.tell()
        
        return img_copy, compressed_bytes
    
    def cleanup_temp_file(self, file_path: Path) -> None:
        """一時ファイルを削除"""
        if ".compressed." in file_path.name and file_path.exists():
            try:
                file_path.unlink()
                logger.debug(f"一時ファイルを削除: {file_path}")
            except Exception as e:
                logger.warning(f"一時ファイル削除エラー: {e}")
