# VRChat Discord フォト転送ツール 要件定義書

**作成日:** 2026年2月1日  
**プロジェクト名:** VRChat Discord Uploader  
**対象環境:** Windows 11 (Python ベース)

---

## 1. プロジェクト概要

VRChat で撮影したカメラ写真を Discord チャンネルに自動転送するデスクトップアプリケーションです。Webhook を用いた軽量な実装により、24時間稼働サーバーとしても運用可能な設計とします。

---

## 2. 機能要件

### 2.1 コア機能（ユーザー要求）

#### 2.1.1 Discord Webhook 連携
- **要件 ID:** F001
- **内容:** Discord Webhook URL を設定して、画像を Embed形式で転送
- **詳細:**
  - Webhook URL の暗号化保存（セキュリティ考慮）
  - 転送失敗時の リトライ機構（最大3回、指数バックオフ）
  - API レート制限への対応（120メッセージ/分）

#### 2.1.2 月別スレッド管理（オプション）
- **要件 ID:** F002
- **内容:** Discord スレッドを月ごと（YYYY-MM形式）に自動作成・整理
- **詳細:**
  - 初回起動時に対象月のスレッドが存在しない場合、自動作成
  - スレッド存在確認 → 存在すれば その スレッド ID に投稿
  - スレッド名形式：`2026-02` （年-月）
  - オプション ON/OFF の UI トグル
  - スレッド作成権限がない場合の エラーハンドリング

#### 2.1.3 画像ファイルサイズ最適化
- **要件 ID:** F003
- **内容:** 容量超過時に自動的に解像度圧縮・PNG 形式で最適化
- **詳細:**
  - **圧縮条件:** 10MiB 超過時（Discord ファイルアップロード上限）
  - **解像度削減:**
    - 4K（3840×2160）への リサイズ を基本
    - 縦横比を維持（アスペクト比保持）
    - さらに圧縮必要な場合は 1440p に削減
  - **PNG 最適化:**
    - Pillow (PIL) で品質維持しながら圧縮
    - oxipng ライブラリ使用で高圧縮率実現（圧縮レベル 4）
    - 色深度の最適化（カラースペース自動検出）
  - **圧縮ログ:** 元ファイルサイズ/圧縮後サイズを記録

#### 2.1.4 ファイル名の Discord 連携
- **要件 ID:** F004
- **内容:** Discord 内での画像検索を補助するため、ファイル名を埋め込み情報として送信
- **詳細:**
  - Embed フィールドに元ファイル名を記載
    - フィールド名：「ファイル名」
    - フィールド値：`VRChat_2026-01-15_12-34-56.png` など
  - タイムスタンプ：撮影時刻（ファイル更新日時）を Embed に含める
  - 検索効率向上のため、Embed description に簡単な情報も付加

#### 2.1.5 VRChat 自動起動連携
- **要件 ID:** F005
- **内容:** VRChat 起動時に本ツールを自動起動するオプション
- **詳細:**
  - Windows スタートアップフォルダ への ショートカット登録機能
    - `C:\Users\{ユーザー名}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
  - または レジストリ設定（`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`）
  - UI 上でチェックボックスで ON/OFF 可能
  - 起動時に既に起動中かどうかを確認（二重起動防止）

#### 2.1.6 タスクトレイ最小化オプション
- **要件 ID:** F006
- **内容:** 起動時、メインウィンドウをタスクトレイに最小化するオプション
- **詳細:**
  - UI チェックボックスで設定可能
  - 起動時に本オプション有効なら、ウィンドウを非表示でスタート
  - タスクトレイアイコンクリック → ウィンドウ復帰
  - 右クリックメニュー：「表示」「終了」
  - Windows 11 の新タスクトレイ API に対応

---

### 2.2 追加推奨機能

#### 2.2.1 リアルタイムフォルダ監視
- **要件 ID:** F101
- **内容:** VRChat スクリーンショットフォルダを監視し、新規ファイル検出時に自動転送
- **詳細:**
  - `watchdog` ライブラリ使用（軽量で信頼性高）
  - VRChat デフォルト保存先：`C:\Users\{ユーザー名}\Pictures\VRChat`
  - カスタムパス指定可能（VRChat config.json の `picture_output_folder` に対応）
  - 画像ファイル拡張子フィルタ：`.png`, `.jpg`, `.jpeg`
  - 重複検出：同名ファイル転送時はスキップ or 上書き（設定可能）

#### 2.2.2 転送履歴管理
- **要件 ID:** F102
- **内容:** 転送済み画像の履歴を DB に記録
- **詳細:**
  - SQLite ローカル DB 使用
  - 記録項目：
    - ファイル名、ファイルハッシュ（SHA256）、転送日時、Discord メッセージ ID
    - 圧縮の有無、圧縮前/後ファイルサイズ
  - 重複転送防止（ハッシュベース）
  - 履歴検索・削除機能（UI から）

#### 2.2.3 転送キューと バッチ処理
- **要件 ID:** F103
- **内容:** 複数画像の同時転送を効率化
- **詳細:**
  - 転送キューを UI で表示（進行状況ゲージ）
  - バッチ転送：複数ファイル選択 → 連続転送
  - Discord API レート制限を自動調整
  - 転送中の キャンセル機能

#### 2.2.4 設定ファイル管理
- **要件 ID:** F104
- **内容:** 設定を JSON / TOML で永続化
- **詳細:**
  - 設定ファイル保存先：`%APPDATA%\VRChatDiscordUploader\config.json`
  - Webhook URL（AES-256 で暗号化保存）
  - 監視フォルダパス
  - 月別スレッド ON/OFF
  - 自動起動 ON/OFF
  - タスクトレイ最小化 ON/OFF
  - ユーザー環境の保持

#### 2.2.5 ログ・エラーハンドリング
- **要件 ID:** F105
- **内容:** 運用時のトラブルシューティングに対応するログ出力
- **詳細:**
  - ログレベル：DEBUG / INFO / WARNING / ERROR
  - ファイル保存：`%APPDATA%\VRChatDiscordUploader\logs\app.log`
  - ローテーション：日次 + 最大 10 ファイル保持
  - エラー発生時は UI トースト通知 + ログ記録
  - Webhook 失敗時の詳細エラーメッセージ表示

#### 2.2.6 ステータスウィンドウ・通知
- **要件 ID:** F106
- **内容:** 転送状態をリアルタイムで表示
- **詳細:**
  - ウィンドウ: 監視状態、最終転送時刻、転送数（本日/累計）
  - 通知：
    - 転送成功 → トースト通知（Windows 通知）
    - 転送失敗 → エラー通知 + サウンド
    - オプション：Discord DM での通知も可能

#### 2.2.7 マルチアカウント対応
- **要件 ID:** F107
- **内容:** 複数の Discord Webhook を設定・切り替え可能
- **詳細:**
  - プロファイル管理：「メイン」「配信用」など複数登録
  - ドロップダウンで切り替え
  - プロファイルごとの設定（スレッド、フォルダ等）を独立管理

#### 2.2.8 バージョン確認・自動アップデート
- **要件 ID:** F108
- **内容:** アプリケーション更新を自動確認
- **詳細:**
  - 起動時に GitHub Releases から最新版を確認
  - 新版検出時は UI で通知 → 手動更新ボタン提供
  - 自動アップデート機能（オプション）

---

## 3. 非機能要件

### 3.1 パフォーマンス
- **要件 ID:** NF001
- **監視ラグ:** ファイル作成検出から Webhook 送信まで 5秒以内
- **圧縮処理:** 5MB 画像で 10 秒以内に完了
- **メモリ使用量:** 常時 100 MB 以下（アイドル時）

### 3.2 セキュリティ
- **要件 ID:** NF002
- **Webhook URL 保護:**
  - ユーザーホーム配下の暗号化ファイルで保存
  - プレーンテキストでの表示は禁止（マスク表示）
- **通信:** HTTPS のみ使用（Discord Webhook は HTTPS 必須）
- **ログ:** Webhook URL をログに含めない

### 3.3 可用性
- **要件 ID:** NF003
- **稼働時間:** 24 時間継続稼働を想定
- **再起動耐性:** クラッシュ後の自動復旧（監視機能の再開）
- **設定ファイル破損時:** デフォルト値で起動

### 3.4 互換性
- **要件 ID:** NF004
- **プラットフォーム:** Windows 10 / 11（64 bit）
- **Python:** 3.10 以上
- **依存ライブラリの最小化**

### 3.5 ユーザビリティ
- **要件 ID:** NF005
- **言語:** 日本語対応（UI・ログ・通知すべて）
- **初期設定ウィザード:** 初回起動時に Webhook URL 入力を誘導
- **ヘルプ：** アプリ内ヘルプ + README に詳細記載

---

## 4. 技術仕様

### 4.1 使用技術スタック

| カテゴリ | 技術選定 | 理由 |
|---------|---------|------|
| **UI フレームワーク** | PyQt5 / PySimpleGUI | クロスプラットフォーム、日本語対応 |
| **画像処理** | Pillow + oxipng | 高速かつ高圧縮率 |
| **ファイル監視** | watchdog | 軽量で信頼性高 |
| **HTTP 通信** | requests ライブラリ | Discord Webhook 標準対応 |
| **DB** | SQLite | 設定・履歴管理 |
| **スケジューリング** | APScheduler | 定期タスク（月初のスレッド作成など） |
| **暗号化** | cryptography ライブラリ | Webhook URL 保護 |
| **ログ** | logging + loguru | 構造化ログ |
| **パッケージング** | PyInstaller + NSIS | exe 配布 |

### 4.2 システムアーキテクチャ

```
┌─────────────────────────────────────┐
│     VRChat Screenshot Folder        │
│  (C:\Users\{user}\Pictures\VRChat)  │
└────────────────┬────────────────────┘
                 │ (File System Events)
                 ↓
┌─────────────────────────────────────┐
│      File Watcher (watchdog)        │
│    - Detect new/modified files      │
│    - Filter by extension            │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│    Image Processing Pipeline        │
│  ┌─────────────────────────────────┐│
│  │1. Load Image (PIL)              ││
│  │2. Check File Size               ││
│  │3. If >8MB: Compress             ││
│  │   - Resize to 4K (if needed)    ││
│  │   - PNG Optimize (oxipng)       ││
│  │4. Generate Metadata (filename) ││
│  └─────────────────────────────────┘│
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│   Discord Webhook Post              │
│  ┌─────────────────────────────────┐│
│  │- Create/Fetch Thread (optional) ││
│  │- Build Embed (filename, size)   ││
│  │- multipart/form-data upload     ││
│  │- Retry on failure (max 3)       ││
│  └─────────────────────────────────┘│
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│    History DB (SQLite)              │
│  - Record: filename, hash, URL      │
│  - Prevent duplicate uploads        │
└─────────────────────────────────────┘
```

### 4.3 ディレクトリ構成

```
VRChatDiscordUploader/
├── main.py                          # エントリーポイント
├── config.json                      # 設定ファイル（暗号化）
├── requirements.txt                 # 依存ライブラリ
├── src/
│   ├── gui/
│   │   ├── main_window.py          # メインウィンドウ
│   │   ├── settings_dialog.py      # 設定ダイアログ
│   │   └── icons/                  # アイコン画像
│   ├── core/
│   │   ├── file_watcher.py         # ファイル監視ロジック
│   │   ├── image_processor.py      # 画像圧縮処理
│   │   ├── discord_webhook.py      # Webhook 送信
│   │   ├── thread_manager.py       # スレッド管理
│   │   └── config_manager.py       # 設定管理
│   ├── db/
│   │   ├── models.py               # DB スキーマ
│   │   └── repository.py           # DB アクセス層
│   ├── utils/
│   │   ├── crypto.py               # 暗号化・復号化
│   │   ├── logger.py               # ログ設定
│   │   └── helpers.py              # ユーティリティ関数
│   └── constants.py                # 定数定義
├── logs/                            # ログ出力先
├── tests/                           # ユニットテスト
├── build/                           # PyInstaller 出力
└── README.md                        # ドキュメント
```

---

## 5. UI / UX 設計

### 5.1 メインウィンドウ

```
┌──────────────────────────────────────────┐
│  VRChat Discord Uploader      [_][□][X]  │
├──────────────────────────────────────────┤
│ 📊 ステータス                             │
│  ├─ 監視状態：        ✓ 稼働中           │
│  ├─ 最終転送：        2026-02-01 18:45   │
│  ├─ 本日転送数：      12枚               │
│  └─ 累計転送数：      1,234枚            │
│                                          │
│ 🎯 クイックアクション                    │
│  ┌──────────┬──────────┬──────────┐     │
│  │ 📂開く   │ ⚙️設定   │ ❌停止   │     │
│  └──────────┴──────────┴──────────┘     │
│                                          │
│ 📜 転送ログ（直近5件）                   │
│  ├─ ✓ VRChat_2026-02-01_18-45-30.png    │
│  ├─ ✓ VRChat_2026-02-01_18-40-15.png    │
│  ├─ ⚠ VRChat_2026-02-01_18-35-00.png    │
│  │   (圧縮: 10.2MB → 5.8MB)             │
│  ├─ ✓ VRChat_2026-02-01_18-30-45.png    │
│  └─ ✓ VRChat_2026-02-01_18-25-20.png    │
│                                          │
│ 🔧 設定クイックメニュー                  │
│  ☐ VRChat起動時に自動起動               │
│  ☑ タスクトレイに最小化                 │
│  ☑ 月別スレッド機能を有効               │
│  ☐ 転送完了時にサウンド再生              │
│                                          │
│ 🌐 Webhook URL：  ●●●●●●●●●●●●●●  │
│                  [接続確認] [設定変更]   │
├──────────────────────────────────────────┤
│  v1.2.0 | ℹ️ ヘルプ | 📋 について       │
└──────────────────────────────────────────┘
```

### 5.2 設定ダイアログ（タブ式）

**タブ 1：基本設定**
- Webhook URL 入力フィールド（マスク表示）
- 接続テストボタン
- 監視フォルダ選択（デフォルト自動検出）

**タブ 2：転送設定**
- 月別スレッド機能 ON/OFF
- 圧縮閾値（MB） - デフォルト 8MB
- 圧縮レベル（品質 vs 速度）
- ファイル名埋め込み ON/OFF

**タブ 3：自動化**
- VRChat 起動連携 ON/OFF
- タスクトレイ最小化 ON/OFF
- 自動アップデート確認 ON/OFF
- 起動時の初期状態（最小化 or 通常）

**タブ 4：通知**
- 転送成功時の通知 ON/OFF
- 転送失敗時の通知 ON/OFF
- サウンド有効 ON/OFF
- Discord DM 通知（オプション）

**タブ 5：詳細設定**
- ログレベル（DEBUG / INFO / WARNING / ERROR）
- ログファイル位置の確認・削除
- DB キャッシュクリア
- 設定リセット

---

## 6. API / Webhook 仕様

### 6.1 Discord Embed フォーマット

```json
{
  "username": "VRChat 撮影転送",
  "avatar_url": "https://example.com/vrchat_icon.png",
  "thread_name": "2026-02",
  "embeds": [
    {
      "title": "📸 VRChat スクリーンショット",
      "description": "VRChat で撮影された写真が転送されました",
      "timestamp": "2026-02-01T18:45:30Z",
      "color": 3066993,
      "fields": [
        {
          "name": "ファイル名",
          "value": "VRChat_2026-02-01_18-45-30.png",
          "inline": false
        },
        {
          "name": "ファイルサイズ",
          "value": "原: 12.5MB → 圧縮: 5.8MB",
          "inline": true
        },
        {
          "name": "圧縮状況",
          "value": "✓ 圧縮済み（4K)",
          "inline": true
        },
        {
          "name": "撮影時刻",
          "value": "2026-02-01 18:45:30",
          "inline": true
        }
      ],
      "image": {
        "url": "attachment://image.png"
      },
      "footer": {
        "text": "VRChat Discord Uploader v1.2.0"
      }
    }
  ]
}
```

### 6.2 エラーハンドリング

| ステータスコード | エラー内容 | 対応 |
|----------------|----------|------|
| 204 | 成功 | ログに記録 |
| 400 | 無効なリクエスト | Embed フォーマット再確認 |
| 401 | Webhook URL 無効 | ユーザーに通知 → 設定画面へ |
| 429 | レート制限 | 指数バックオフで 60 秒後に再試行 |
| 500+ | サーバーエラー | 最大 3 回リトライ（待機時間増加） |

---

## 7. データベーススキーマ

### テーブル：transferred_images

```sql
CREATE TABLE transferred_images (
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
);

CREATE INDEX idx_filename ON transferred_images(filename);
CREATE INDEX idx_transferred_at ON transferred_images(transferred_at);
```

---

## 8. テスト計画

### 8.1 ユニットテスト
- 画像圧縮ロジック（複数サイズ・形式）
- ファイルハッシュ生成・重複検出
- Embed JSON 生成
- 設定暗号化・復号化
- スレッド名生成（月別フォーマット）

### 8.2 統合テスト
- ファイルシステム監視 → Webhook 送信フロー
- Discord API 連携（実 Webhook で）
- 月初のスレッド自動作成
- リトライ機構の動作

### 8.3 E2E テスト
- VRChat 起動時の自動起動確認
- タスクトレイ最小化・復帰
- 設定保存・読み込みの永続性

---

## 9. リリース計画

### Phase 1：MVP（2026年2月）
- コア機能（F001 ～ F006）実装
- 基本的な UI・設定ダイアログ
- テスト・ドキュメント整備

### Phase 2：拡張（2026年3月）
- F101 ～ F107 の推奨機能実装
- 日本語ローカライズ完全化
- パフォーマンス最適化

### Phase 3：安定化（2026年4月）
- バグ修正・ユーザーフィードバック反映
- GitHub Releases での配布開始

---

## 10. ドキュメント成果物

1. **ユーザーマニュアル** - セットアップ、基本操作、FAQ
2. **トラブルシューティングガイド** - ログの見方、よくあるエラー
3. **技術仕様書** - 開発者向け API 仕様、拡張方法
4. **変更履歴（CHANGELOG）** - バージョン間の変更点

---

## 11. 補足・備考

- **VRChat スクリーンショット保存先の自動検出**
  - デフォルト：`C:\Users\{ユーザー名}\Pictures\VRChat`
  - VRChat config.json に `picture_output_folder` が設定されている場合はそちらを優先
  
- **Webhook URL 取得方法**
  - Discord サーバー設定 → ウェブフック → 「新しいウェブフック」作成
  - 初回起動時にヘルプアイコンから詳細手順を表示

- **将来の拡張可能性**
  - Google Drive / OneDrive への自動バックアップ
  - Discord 以外の SNS（Twitter、Bluesky）への同時投稿
  - AI を用いた自動キャプション生成（BLIP など）
  - Web UI（リモート管理用）

---

**署名:** VRChat Discord Uploader Project Team  
**最終更新:** 2026年2月1日
