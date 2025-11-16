"""
認証コードからGoogle Drive APIのトークンを生成するスクリプト
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# 認証コード
code = "4/0Ab32j90E4tdRVfjJ9DrOVBJnojbUbogVcklqgDGDW4ciqX2MkNzmfAGExMtcfS3o8uev-w"

# 認証ファイルを読み込む
CREDENTIALS_PATH = r"C:\Users\purena\.cursor\google-drive-credentials.json"
TOKEN_PATH = r"C:\Users\purena\.cursor\google-drive-token.json"

print("=" * 80)
print("Google Drive トークン生成")
print("=" * 80)
print()

# 認証情報を読み込む
print("認証情報を読み込んでいます...")
with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
    cred = json.load(f)

# installedまたはwebキーから情報を取得
if 'installed' in cred:
    client_info = cred['installed']
elif 'web' in cred:
    client_info = cred['web']
else:
    print("エラー: 認証情報の形式が不正です")
    exit(1)

print("トークンをリクエストしています...")

# トークンエンドポイントにリクエスト
token_url = client_info.get('token_uri', 'https://oauth2.googleapis.com/token')
data = {
    "code": code,
    "client_id": client_info["client_id"],
    "client_secret": client_info["client_secret"],
    "redirect_uri": client_info["redirect_uris"][0],
    "grant_type": "authorization_code"
}

# URLエンコードしてPOSTリクエスト
data_encoded = urllib.parse.urlencode(data).encode('utf-8')
req = urllib.request.Request(token_url, data=data_encoded, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    with urllib.request.urlopen(req) as response:
        token_response = json.loads(response.read().decode('utf-8'))
    
    print("[OK] トークンの取得に成功しました！")
    print()
    
    # トークンデータを準備
    expiry_time = datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600))
    token_data = {
        "access_token": token_response["access_token"],
        "refresh_token": token_response.get("refresh_token"),
        "token_uri": client_info["token_uri"],
        "client_id": client_info["client_id"],
        "client_secret": client_info["client_secret"],
        "scopes": token_response.get("scope", "https://www.googleapis.com/auth/drive").split(),
        "expiry": expiry_time.isoformat() + "Z"
    }
    
    # トークンファイルを保存
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2, ensure_ascii=False)
    
    print("=" * 80)
    print("トークンファイルを作成しました！")
    print("=" * 80)
    print()
    print(f"保存先: {TOKEN_PATH}")
    print()
    print("【トークン情報】")
    print(f"Access Token: {token_response['access_token'][:50]}...")
    if token_response.get("refresh_token"):
        print(f"Refresh Token: {token_response['refresh_token'][:50]}...")
    print(f"有効期限: {expiry_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
    print(f"スコープ: {', '.join(token_data['scopes'])}")
    print()
    print("=" * 80)
    print("[OK] Google Drive APIが使用可能になりました！")
    print("=" * 80)
    
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"[ERROR] エラーが発生しました: {e.code}")
    print(f"詳細: {error_body}")
    exit(1)
except Exception as e:
    print(f"[ERROR] 予期しないエラーが発生しました: {e}")
    exit(1)

