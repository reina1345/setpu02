# GitHub MCPサーバーのセットアップ手順

## 1. GitHubパーソナルアクセストークンの取得

1. GitHubにログインしてください
2. 右上のプロフィールアイコン → **Settings** をクリック
3. 左サイドバーの最下部の **Developer settings** をクリック
4. **Personal access tokens** → **Tokens (classic)** をクリック
5. **Generate new token** → **Generate new token (classic)** をクリック
6. トークンに名前を付けて（例: "Cursor MCP"）、以下のスコープを選択:
   - `repo` - すべてのリポジトリへのフルアクセス
   - `read:org` - 組織の読み取り
   - `read:user` - ユーザー情報の読み取り
7. **Generate token** をクリック
8. 生成されたトークンをコピーしてください（後で表示できません）

## 2. 設定ファイルの更新

`.vscode/mcp.json` ファイルを開いて、取得したトークンで置き換えてください:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

## 3. Cursorの設定

1. Cursorを再起動してください
2. Cursorの設定でMCPサーバーが有効になっていることを確認してください
   - **Settings** → **Features** → **MCP** を確認

## 4. 使用方法

MCPサーバーが有効になると、以下のようなコマンドが利用可能になります:
- リポジトリの情報を取得
- イシューやプルリクエストの管理
- コードレビューの自動化
- リポジトリのクローンや操作

## トラブルシューティング

### MCPサーバーが見つからない場合
- Node.jsがインストールされていることを確認してください
- `npm` コマンドが利用可能か確認してください

### 認証エラーが発生する場合
- トークンが正しく設定されているか確認してください
- トークンの有効期限を確認してください
- 必要なスコープが付与されているか確認してください

## セキュリティ注意事項

⚠️ **重要**: 
- このトークンは機密情報です
- `.vscode/mcp.json` は `.gitignore` に追加するか、GitHubにプッシュしないでください
- トークンが漏洩した場合は、すぐにGitHubで無効化してください




