import urllib.request
import json
import base64

# ソースファイルのリストを取得
try:
    url = 'https://api.github.com/repos/Longtran2404/mcp-google-drive/contents/src'
    response = urllib.request.urlopen(url)
    files = json.loads(response.read().decode('utf-8'))
    print('Source files:')
    for f in files:
        if f['type'] == 'file':
            print(f"  {f['name']}")
    print()
except Exception as e:
    print(f"Error getting file list: {e}")

# index.tsを取得
try:
    url = 'https://api.github.com/repos/Longtran2404/mcp-google-drive/contents/src/index.ts'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode('utf-8'))
    content = base64.b64decode(data['content']).decode('utf-8')
    print("=== src/index.ts (first 6000 chars) ===")
    print(content[:6000])
except Exception as e:
    print(f"Error getting index.ts: {e}")

# auth.tsやauth関連のファイルを探す
try:
    url = 'https://api.github.com/repos/Longtran2404/mcp-google-drive/contents/src'
    response = urllib.request.urlopen(url)
    files = json.loads(response.read().decode('utf-8'))
    auth_files = [f for f in files if 'auth' in f['name'].lower() and f['type'] == 'file']
    if auth_files:
        print("\n=== Auth-related files ===")
        for f in auth_files:
            print(f"\n--- {f['name']} ---")
            file_url = f['download_url']
            file_response = urllib.request.urlopen(file_url)
            file_content = file_response.read().decode('utf-8')
            print(file_content[:4000])
except Exception as e:
    print(f"Error getting auth files: {e}")


