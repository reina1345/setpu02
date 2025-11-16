"""
Google Drive OAuth認証URLを生成するスクリプト
"""
import json
import urllib.parse

# 認証情報ファイルのパス
CREDENTIALS_PATH = r'C:\Users\purena\.cursor\google-drive-credentials.json'

# 必要なスコープ
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

def generate_auth_url():
    """OAuth認証URLを生成します"""
    
    # 認証情報を読み込む
    with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
        credentials = json.load(f)
    
    # installedまたはwebキーから情報を取得
    if 'installed' in credentials:
        client_info = credentials['installed']
    elif 'web' in credentials:
        client_info = credentials['web']
    else:
        print("エラー: 認証情報の形式が不正です")
        return
    
    client_id = client_info['client_id']
    redirect_uri = client_info['redirect_uris'][0]
    auth_uri = client_info.get('auth_uri', 'https://accounts.google.com/o/oauth2/v2/auth')
    
    # 認証URLのパラメータを構築
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'  # 毎回同意画面を表示
    }
    
    # URLを構築
    auth_url = f"{auth_uri}?{urllib.parse.urlencode(params)}"
    
    print("=" * 80)
    print("Google Drive OAuth認証URL")
    print("=" * 80)
    print()
    print("以下のURLをブラウザで開いて、Googleアカウントで認証してください：")
    print()
    print(auth_url)
    print()
    print("=" * 80)
    print()
    print("認証後、リダイレクトURLに含まれる「code=」の後の値をコピーしてください。")
    print()
    print("【認証情報】")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print()
    print("=" * 80)
    
    return auth_url

if __name__ == '__main__':
    generate_auth_url()
