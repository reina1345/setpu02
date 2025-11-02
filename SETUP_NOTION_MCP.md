# Notion MCPサーバーのセットアップ手順

## 1. Notion統合（Integration）の作成

1. **Notionの統合ページにアクセス**
   - https://www.notion.so/my-integrations にアクセス
   - Notionアカウントでログイン

2. **新しい統合を作成**
   - **+ New integration** をクリック
   - 統合の名前を入力（例: "Cursor MCP"）
   - 関連するワークスペースを選択
   - **Submit** をクリック

3. **統合トークンをコピー**
   - 作成された統合ページで **Internal Integration Token** が表示されます
   - **Show** をクリックしてトークンを表示
   - トークンをコピー（形式: `secret_xxxxxxxxxxxxxxxxxxxx`）

4. **統合の機能を設定**
   - **Capabilities** セクションで以下を有効化:
     - ✅ Read content
     - ✅ Update content
     - ✅ Insert content
   - **Save** をクリック

## 2. NotionページやデータベースにMCPアクセスを許可

統合を作成しただけでは、Notionのページにアクセスできません。各ページまたはデータベースに対して、明示的にアクセス権限を付与する必要があります。

### 方法1: 個別のページに権限を付与

1. Notionで統合を使いたいページを開く
2. 右上の **•••** (More) メニューをクリック
3. **Add connections** をクリック
4. 作成した統合（例: "Cursor MCP"）を選択
5. **Confirm** をクリック

### 方法2: ワークスペース全体に権限を付与

1. Notionのワークスペース設定を開く
2. **Settings & members** → **Connections** をクリック
3. 作成した統合を選択
4. アクセスを許可するページを選択

## 3. MCP設定ファイルの更新

### グローバル設定（全プロジェクト共通）

`C:\Users\[ユーザー名]\.cursor\mcp.json` を編集:

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
    }
  }
}
```

### プロジェクト単位の設定

`.vscode/mcp.json` を編集（プロジェクトごとに異なる設定が必要な場合）:

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
    }
  }
}
```

## 4. Cursorの再起動

設定を有効にするため、Cursorを再起動してください。

## 5. 使用方法

MCPサーバーが有効になると、以下のような操作が可能になります:

- **ページの読み取り**: Notionページの内容を取得
- **ページの作成**: 新しいNotionページを作成
- **ページの更新**: 既存のページの内容を編集
- **データベースの操作**: Notionデータベースのクエリと操作
- **ブロックの追加**: ページにテキスト、画像、コードブロックなどを追加

## トラブルシューティング

### エラー: "Unauthorized"

**原因**: APIトークンが無効、または対象ページに統合のアクセス権限が付与されていない

**解決方法**:
1. APIトークンが正しく設定されているか確認
2. 対象のNotionページに統合を接続（**Add connections**）
3. 統合が有効であることを確認

### エラー: "Object not found"

**原因**: ページIDが間違っているか、統合がページにアクセスできない

**解決方法**:
1. ページURLからページIDを確認
2. ページに統合のアクセス権限を付与

### MCPサーバーが起動しない

**原因**: Node.jsがインストールされていない、またはnpxコマンドが利用できない

**解決方法**:
1. Node.jsをインストール（https://nodejs.org/）
2. ターミナルで `node --version` と `npm --version` を実行して確認
3. Cursorを再起動

## セキュリティ注意事項

⚠️ **重要**: 
- Notion APIトークンは機密情報です
- トークンを持つ人は、許可されたNotionページにアクセスできます
- グローバル設定ファイル（`~/.cursor/mcp.json`）は通常リポジトリに含まれません
- プロジェクト設定（`.vscode/mcp.json`）を使う場合は、必ず `.gitignore` に追加してください
- トークンが漏洩した場合は、すぐにNotionの統合ページで無効化してください

## 参考リンク

- Notion API公式ドキュメント: https://developers.notion.com/
- Notion統合の作成: https://www.notion.so/my-integrations
- MCP公式ドキュメント: https://modelcontextprotocol.io/




