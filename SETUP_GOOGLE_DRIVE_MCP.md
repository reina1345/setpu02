# Google Drive MCPサーバーのセットアップ手順

## 1. Google Cloud Projectの作成とAPI有効化

### Google Cloud Consoleでの設定

1. **Google Cloud Consoleにアクセス**
   - https://console.cloud.google.com/ にアクセス
   - Googleアカウントでログイン

2. **新しいプロジェクトを作成**
   - 上部のプロジェクト選択ドロップダウンをクリック
   - **新しいプロジェクト** をクリック
   - プロジェクト名を入力（例: "Cursor MCP Google Drive"）
   - **作成** をクリック

3. **Google Drive APIを有効化**
   - 左メニューから **APIとサービス** → **ライブラリ** をクリック
   - "Google Drive API" を検索
   - **Google Drive API** を選択
   - **有効にする** をクリック

4. **OAuth同意画面を設定**
   - **APIとサービス** → **OAuth同意画面** をクリック
   - ユーザータイプで **外部** を選択（個人利用の場合）
   - **作成** をクリック
   - 必須項目を入力:
     - アプリ名: "Cursor MCP"
     - ユーザーサポートメール: あなたのメールアドレス
     - デベロッパーの連絡先情報: あなたのメールアドレス
   - **保存して次へ** をクリック
   - スコープの画面で **保存して次へ** をクリック
   - テストユーザーに自分のメールアドレスを追加
   - **保存して次へ** をクリック

5. **OAuth 2.0クライアントIDを作成**
   - **APIとサービス** → **認証情報** をクリック
   - **+ 認証情報を作成** → **OAuth クライアント ID** を選択
   - アプリケーションの種類: **デスクトップアプリ** を選択
   - 名前: "Cursor MCP Client" など
   - **作成** をクリック
   - **認証情報をダウンロード** (JSON) をクリック
   - ダウンロードしたファイルを `credentials.json` として保存

## 2. MCP設定ファイルの更新

### グローバル設定（推奨）

`C:\Users\[ユーザー名]\.cursor\mcp.json` を編集:

```json
{
  "mcpServers": {
    "google-drive": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-google-drive"
      ],
      "env": {
        "GOOGLE_DRIVE_CREDENTIALS_PATH": "C:\\Users\\[ユーザー名]\\.cursor\\google-drive-credentials.json"
      }
    }
  }
}
```

### プロジェクト単位の設定

`.vscode/mcp.json` を編集:

```json
{
  "mcpServers": {
    "google-drive": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-google-drive"
      ],
      "env": {
        "GOOGLE_DRIVE_CREDENTIALS_PATH": "C:\\Users\\[ユーザー名]\\.cursor\\google-drive-credentials.json"
      }
    }
  }
}
```

## 3. credentials.jsonの配置

1. ダウンロードした `credentials.json` を以下の場所に配置:
   ```
   C:\Users\[ユーザー名]\.cursor\google-drive-credentials.json
   ```

2. ファイルパスの権限を確認してください

## 4. 初回認証の実行

1. **Cursorを再起動**

2. **初回使用時に認証が必要**
   - MCPサーバーが起動すると、ブラウザが自動的に開きます
   - Googleアカウントでログイン
   - アクセス許可を求められたら **許可** をクリック
   - 認証が完了すると、`token.json` が自動的に作成されます

## 5. 使用方法

MCPサーバーが有効になると、以下のような操作が可能になります:

- **ファイルの検索**: Google Drive内のファイルを検索
- **ファイルの読み取り**: ドキュメント、スプレッドシート、テキストファイルの内容を取得
- **ファイルの作成**: 新しいドキュメントやファイルを作成
- **ファイルの更新**: 既存ファイルの内容を編集
- **フォルダの管理**: フォルダの作成、ファイルの移動
- **共有設定**: ファイルの共有とアクセス権限の管理

### 使用例

Cursorのチャットで以下のようなリクエストが可能です:

```
- "Google Driveで最近編集したドキュメントを表示して"
- "プロジェクト名のフォルダ内のファイル一覧を取得"
- "特定のスプレッドシートのデータを読み込んで"
- "新しいドキュメントを作成して、この内容を書き込んで"
```

## トラブルシューティング

### エラー: "Invalid credentials"

**原因**: credentials.jsonが正しく配置されていない、または形式が間違っている

**解決方法**:
1. credentials.jsonが正しい場所に配置されているか確認
2. ファイルパスに日本語やスペースが含まれていないか確認
3. JSONファイルの形式が正しいか確認

### エラー: "Access denied"

**原因**: OAuth同意画面でアクセスが許可されていない

**解決方法**:
1. Google Cloud Consoleで OAuth同意画面の設定を確認
2. テストユーザーに自分のメールアドレスが追加されているか確認
3. token.jsonを削除して再認証

### 認証ブラウザが開かない

**原因**: ファイアウォールやセキュリティソフトが通信をブロックしている

**解決方法**:
1. ファイアウォール設定を確認
2. 手動でブラウザを開いて認証URLにアクセス
3. Cursorを管理者権限で実行

### MCPサーバーが起動しない

**原因**: Node.jsがインストールされていない、またはnpxコマンドが利用できない

**解決方法**:
1. Node.jsをインストール（https://nodejs.org/）
2. ターミナルで `node --version` と `npm --version` を実行して確認
3. Cursorを再起動

## セキュリティ注意事項

⚠️ **重要**: 
- `credentials.json` と `token.json` は機密情報です
- これらのファイルを持つ人は、あなたのGoogle Driveにアクセスできます
- これらのファイルは絶対にGitリポジトリにコミットしないでください
- プロジェクトに設定する場合は、必ず `.gitignore` に追加してください
- token.jsonが漏洩した場合は、Google Cloud ConsoleでクライアントIDを無効化してください

### .gitignore への追加

```gitignore
# Google Drive MCP
google-drive-credentials.json
token.json
.vscode/mcp.json
.cursor/mcp.json
```

## 参考リンク

- Google Drive API公式ドキュメント: https://developers.google.com/drive
- Google Cloud Console: https://console.cloud.google.com/
- MCP公式ドキュメント: https://modelcontextprotocol.io/


