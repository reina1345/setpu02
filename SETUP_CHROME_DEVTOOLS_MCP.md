# Chrome DevTools MCPサーバーのセットアップ手順

## 概要

Chrome DevTools MCPサーバーを使用すると、PuppeteerやChrome DevTools Protocolを通じて、Webブラウザの自動化、スクレイピング、テストなどが可能になります。

## 前提条件

- Node.js (v18以上推奨)
- Chrome または Chromium ブラウザ

## 1. 必要なパッケージの確認

Chrome DevTools MCPは、通常 Puppeteer MCPサーバーとして提供されています。

## 2. MCP設定ファイルの更新

### グローバル設定（推奨）

`C:\Users\[ユーザー名]\.cursor\mcp.json` を編集:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
```

### プロジェクト単位の設定

`.vscode/mcp.json` を編集:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
```

### 高度な設定（カスタムChrome設定）

特定のChromeバージョンや設定を使用する場合:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ],
      "env": {
        "PUPPETEER_EXECUTABLE_PATH": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
      }
    }
  }
}
```

## 3. 複数のMCPサーバーを統合

既存のNotion、GitHub設定と統合する場合:

### グローバル設定の例

`C:\Users\[ユーザー名]\.cursor\mcp.json`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-notion"
      ],
      "env": {
        "NOTION_API_KEY": "secret_xxxxxxxxxxxxxxxxxxxx"
      }
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx"
      }
    },
    "google-drive": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-google-drive"
      ],
      "env": {
        "GOOGLE_DRIVE_CREDENTIALS_PATH": "C:\\Users\\[ユーザー名]\\.cursor\\google-drive-credentials.json"
      }
    },
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
```

## 4. Cursorの再起動

設定を有効にするため、Cursorを完全に再起動してください。

## 5. 使用方法

MCPサーバーが有効になると、以下のような操作が可能になります:

### Webスクレイピング
- **ページの取得**: Webページのコンテンツを取得
- **スクリーンショット**: ページのスクリーンショットを撮影
- **PDFエクスポート**: WebページをPDFとして保存

### ブラウザ自動化
- **フォーム入力**: 入力フォームに自動的にデータを入力
- **クリック操作**: ボタンやリンクのクリックを自動化
- **ナビゲーション**: ページ間の移動を自動化

### テスト
- **E2Eテスト**: エンドツーエンドテストの実行
- **要素の検証**: DOM要素の存在や内容を確認
- **パフォーマンステスト**: ページ読み込み時間などを測定

### 使用例

Cursorのチャットで以下のようなリクエストが可能です:

```
- "https://example.com にアクセスして、タイトルを取得して"
- "指定したWebサイトのスクリーンショットを撮って"
- "ログインフォームに自動入力してログインして"
- "複数のページから特定の情報を収集して"
- "このWebページのすべてのリンクをリストアップして"
```

## 6. セキュリティとパフォーマンスの設定

### ヘッドレスモードの設定

より高速な実行のために、環境変数でヘッドレスモードを設定できます:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ],
      "env": {
        "PUPPETEER_HEADLESS": "true"
      }
    }
  }
}
```

### タイムアウト設定

長時間実行される操作のためのタイムアウト設定:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ],
      "env": {
        "PUPPETEER_TIMEOUT": "60000"
      }
    }
  }
}
```

## トラブルシューティング

### エラー: "Chrome not found"

**原因**: Chromeがインストールされていない、またはパスが見つからない

**解決方法**:
1. Google Chromeをインストール（https://www.google.com/chrome/）
2. カスタムChromeパスを設定:
   ```json
   "env": {
     "PUPPETEER_EXECUTABLE_PATH": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
   }
   ```
3. または Chromiumをインストール

### エラー: "Navigation timeout"

**原因**: ページの読み込みに時間がかかりすぎている

**解決方法**:
1. タイムアウト値を増やす
2. ネットワーク接続を確認
3. ページのURLが正しいか確認

### Chromeが終了しない

**原因**: プロセスが正常に終了していない

**解決方法**:
1. タスクマネージャーでChromeプロセスを手動で終了
2. Cursorを再起動
3. システムを再起動（必要に応じて）

### MCPサーバーが起動しない

**原因**: Node.jsがインストールされていない、または依存関係の問題

**解決方法**:
1. Node.jsをインストール（https://nodejs.org/）
2. ターミナルで以下を実行:
   ```bash
   node --version
   npm --version
   ```
3. キャッシュをクリア:
   ```bash
   npm cache clean --force
   ```
4. Cursorを再起動

### スクリーンショットが撮れない

**原因**: ディスプレイ設定やヘッドレスモードの問題

**解決方法**:
1. ヘッドレスモードを無効化してテスト
2. ファイル保存先のパスを確認
3. 書き込み権限があるか確認

## セキュリティ注意事項

⚠️ **重要**: 

### スクレイピング使用時の注意
- Webサイトの利用規約を確認してください
- robots.txtを尊重してください
- 過度なリクエストでサーバーに負荷をかけないでください
- 個人情報の取り扱いには十分注意してください

### 認証情報の扱い
- ログイン情報をスクリプトに直接書き込まないでください
- 環境変数や安全なストレージを使用してください
- スクリーンショットに機密情報が含まれないよう注意してください

### リソース管理
- ブラウザインスタンスは適切に閉じてください
- メモリリークに注意してください
- 不要なタブやページは閉じてください

## 高度な使用例

### 複数ページの処理

```javascript
// Cursorチャットで以下のようにリクエスト可能:
"以下のURLリストから各ページのタイトルとメタディスクリプションを取得して、
CSVファイルとして保存して"
```

### ログイン後のスクレイピング

```javascript
// Cursorチャットで:
"指定したWebサイトにログインして、
ダッシュボードのデータを取得してください"
```

### 定期的なデータ収集

```javascript
// Cursorチャットで:
"特定のページを監視して、変更があったら通知してください"
```

## パフォーマンス最適化

### リソースの制限

不要なリソースの読み込みをブロック:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ],
      "env": {
        "PUPPETEER_BLOCK_RESOURCES": "image,stylesheet,font"
      }
    }
  }
}
```

### 並列処理

複数のページを並列で処理する場合は、リソース使用量に注意してください。

## 参考リンク

- Puppeteer公式ドキュメント: https://pptr.dev/
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- MCP公式ドキュメント: https://modelcontextprotocol.io/
- Puppeteer GitHub: https://github.com/puppeteer/puppeteer

## ライセンスと制約

Puppeteerは Apache-2.0 ライセンスのオープンソースソフトウェアです。
商用利用も可能ですが、各Webサイトの利用規約は別途確認が必要です。


