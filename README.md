# VRChat Discord Uploader

VRChatで撮影したスクリーンショットをDiscordチャンネルに自動転送するデスクトップアプリケーションです。

## 機能

- **自動転送**: VRChatスクリーンショットフォルダを監視し、新規画像を自動でDiscordに転送
- **画像圧縮**: 10MiB超過時に自動でリサイズ・PNG最適化
- **月別スレッド**: YYYY-MM形式でスレッドを自動作成・整理（オプション）
- **タスクトレイ**: バックグラウンド動作対応
- **自動起動**: Windows起動時の自動起動設定

## セットアップ

### 開発環境

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 依存ライブラリをインストール
pip install -r requirements.txt
```

### 実行

```bash
python main.py
```

### ビルド（exe作成）

```bash
# PyInstallerでビルド
pyinstaller build.spec

# または直接ビルド
pyinstaller --onefile --windowed --name "VRChatDiscordUploader" main.py
```

ビルド後、`dist/VRChatDiscordUploader.exe` が作成されます。

## 使い方

1. **初回起動**: アプリを起動し、設定画面からDiscord Webhook URLを入力
2. **Webhook取得方法**: Discord サーバー設定 → ウェブフック → 「新しいウェブフック」作成 → URLをコピー
3. **監視開始**: メイン画面の「▶️ 開始」ボタンをクリック
4. **自動転送**: VRChatで撮影すると自動的にDiscordに転送されます

## 設定ファイル

設定は以下に保存されます：
- `%APPDATA%\VRChatDiscordUploader\config.json`

ログファイル：
- `%APPDATA%\VRChatDiscordUploader\logs\app.log`

## ライセンス

MIT License
