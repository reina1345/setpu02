import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# 認証コード
code = "4/0Ab32j90ZJ-gtpNlM8fDhgrDRZe1vhGZTY8JPFqTGePEupROH-pBbmpGyjtSnTGxN3bS8xQ"

# 認証ファイルを読み込む
with open(r"C:\Users\purena\.cursor\google-drive-credentials.json", "r", encoding="utf-8") as f:
    cred = json.load(f)

# トークンエンドポイントにリクエスト
token_url = "https://oauth2.googleapis.com/token"
data = {
    "code": code,
    "client_id": cred["installed"]["client_id"],
    "client_secret": cred["installed"]["client_secret"],
    "redirect_uri": cred["installed"]["redirect_uris"][0],
    "grant_type": "authorization_code"
}

# URLエンコードしてPOSTリクエスト
data_encoded = urllib.parse.urlencode(data).encode('utf-8')
req = urllib.request.Request(token_url, data=data_encoded, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

with urllib.request.urlopen(req) as response:
    token_response = json.loads(response.read().decode('utf-8'))

# トークンデータを準備
expiry_time = datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600))
token_data = {
    "access_token": token_response["access_token"],
    "refresh_token": token_response.get("refresh_token"),
    "token_uri": cred["installed"]["token_uri"],
    "client_id": cred["installed"]["client_id"],
    "client_secret": cred["installed"]["client_secret"],
    "scope": token_response.get("scope", "https://www.googleapis.com/auth/drive.readonly"),
    "expiry": expiry_time.strftime("%Y-%m-%dT%H:%M:%SZ")
}

# トークンファイルを保存
token_file_path = r"C:\Users\purena\.cursor\google-drive-token.json"
with open(token_file_path, "w", encoding="utf-8") as f:
    json.dump(token_data, f, indent=2, ensure_ascii=False)

print("トークンファイルを作成しました！")
print(f"保存先: {token_file_path}")

