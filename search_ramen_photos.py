"""
Google Driveで「北海道旅行飲食店」フォルダ内のラーメン関連写真を検索するスクリプト
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# スコープ: 読み取り専用
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# 認証情報のパス
CREDENTIALS_PATH = r'C:\Users\purena\.cursor\google-drive-credentials.json'
TOKEN_PATH = r'C:\Users\purena\.cursor\google-drive-token.json'


def authenticate():
    """Google Drive APIの認証を行います"""
    creds = None
    
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
    
    return creds


def search_folder(service, folder_name):
    """フォルダ名でフォルダを検索"""
    try:
        query = f"name contains '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=20,
            fields="files(id, name, parents, modifiedTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        folders = results.get('files', [])
        return folders
    
    except HttpError as error:
        print(f'エラーが発生しました: {error}')
        return []


def search_images_in_folder(service, folder_id, keyword):
    """指定フォルダ内で画像を検索"""
    try:
        # フォルダ内の画像ファイルで、名前にキーワードを含むものを検索
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime, webViewLink, webContentLink, parents)",
            orderBy="modifiedTime desc",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        all_files = results.get('files', [])
        
        # キーワードでフィルタリング（ファイル名に含まれるか確認）
        filtered_files = [
            f for f in all_files 
            if keyword.lower() in f.get('name', '').lower()
        ]
        
        return filtered_files, all_files
    
    except HttpError as error:
        print(f'エラーが発生しました: {error}')
        return [], []


def format_date(date_str):
    """ISO形式の日付を読みやすい形式に変換"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y年%m月%d日 %H:%M:%S')
    except:
        return date_str


def main():
    """メイン処理"""
    print("=" * 80)
    print("北海道旅行飲食店フォルダからラーメン写真を検索")
    print("=" * 80)
    print()
    
    # 認証
    print("Google Drive APIに認証中...")
    creds = authenticate()
    if not creds:
        print("認証に失敗しました")
        return
    
    service = build('drive', 'v3', credentials=creds)
    
    # フォルダを検索
    print("\n「北海道旅行飲食店」フォルダを検索中...")
    folders = search_folder(service, '北海道旅行飲食店')
    
    if not folders:
        print("「北海道旅行飲食店」フォルダが見つかりませんでした。")
        print("\n代わりに「北海道」を含むフォルダを検索します...")
        folders = search_folder(service, '北海道')
    
    if not folders:
        print("該当するフォルダが見つかりませんでした。")
        return
    
    print(f"\n見つかったフォルダ: {len(folders)}件")
    for i, folder in enumerate(folders, 1):
        print(f"  {i}. {folder.get('name')} (ID: {folder.get('id')})")
    
    # 各フォルダ内でラーメン写真を検索
    print("\n" + "=" * 80)
    print("ラーメンに関連する写真を検索中...")
    print("=" * 80)
    
    all_ramen_photos = []
    
    for folder in folders:
        folder_name = folder.get('name')
        folder_id = folder.get('id')
        
        print(f"\n[{folder_name}] フォルダを検索中...")
        
        ramen_files, all_files = search_images_in_folder(service, folder_id, 'ラーメン')
        
        # ファイル名に「ラーメン」が含まれていない場合、「ramen」でも検索
        if not ramen_files:
            ramen_files_en, _ = search_images_in_folder(service, folder_id, 'ramen')
            ramen_files.extend(ramen_files_en)
        
        print(f"  フォルダ内の画像: {len(all_files)}件")
        print(f"  ラーメン関連: {len(ramen_files)}件")
        
        all_ramen_photos.extend([(folder_name, f) for f in ramen_files])
    
    # 結果を表示
    if not all_ramen_photos:
        print("\n" + "=" * 80)
        print("ラーメンに関連する写真が見つかりませんでした。")
        print("=" * 80)
        print("\nヒント: ファイル名に「ラーメン」または「ramen」が含まれている写真を検索しています。")
        print("該当するファイルがない場合は、フォルダ内のすべての画像を確認してください。")
        return
    
    print("\n" + "=" * 80)
    print(f"ラーメン関連の写真: {len(all_ramen_photos)}件")
    print("=" * 80)
    print()
    
    # テーブル形式で表示
    print(f"{'No.':<4} {'フォルダ':<30} {'ファイル名':<40} {'最終更新'}")
    print(f"{'-'*4} {'-'*30} {'-'*40} {'-'*20}")
    
    for i, (folder_name, file) in enumerate(all_ramen_photos, 1):
        name = file.get('name', '無題')[:38]
        modified = format_date(file.get('modifiedTime', ''))
        folder_short = folder_name[:28]
        print(f"{i:<4} {folder_short:<30} {name:<40} {modified}")
    
    # 詳細情報
    print("\n" + "=" * 80)
    print("詳細情報:")
    print("=" * 80)
    print()
    
    for i, (folder_name, file) in enumerate(all_ramen_photos, 1):
        print(f"{i}. {file.get('name', '無題')}")
        print(f"   フォルダ: {folder_name}")
        print(f"   ID: {file.get('id', '')}")
        print(f"   タイプ: {file.get('mimeType', '')}")
        print(f"   最終更新: {format_date(file.get('modifiedTime', ''))}")
        if file.get('webViewLink'):
            print(f"   閲覧URL: {file.get('webViewLink')}")
        if file.get('webContentLink'):
            print(f"   ダウンロードURL: {file.get('webContentLink')}")
        print()


if __name__ == '__main__':
    main()

