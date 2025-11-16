"""
Google Driveで「北海道旅行」フォルダ内のラーメン関連写真を再帰的に検索するスクリプト
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


def get_subfolders(service, parent_folder_id):
    """サブフォルダを取得"""
    try:
        query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, parents)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        return results.get('files', [])
    
    except HttpError as error:
        print(f'エラーが発生しました: {error}')
        return []


def get_all_subfolders_recursive(service, folder_id, folder_name="", level=0):
    """再帰的にすべてのサブフォルダを取得"""
    all_folders = [(folder_id, folder_name, level)]
    
    subfolders = get_subfolders(service, folder_id)
    
    for subfolder in subfolders:
        sub_id = subfolder.get('id')
        sub_name = subfolder.get('name')
        
        # 再帰的にサブフォルダを取得
        sub_results = get_all_subfolders_recursive(service, sub_id, sub_name, level + 1)
        all_folders.extend(sub_results)
    
    return all_folders


def search_images_in_folder(service, folder_id):
    """指定フォルダ内のすべての画像を取得"""
    try:
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, mimeType, modifiedTime, webViewLink, webContentLink, parents)",
            orderBy="modifiedTime desc",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        return results.get('files', [])
    
    except HttpError as error:
        print(f'エラーが発生しました: {error}')
        return []


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
    print("北海道旅行フォルダからラーメン写真を検索（サブフォルダ含む）")
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
    print("\n「北海道旅行」を含むフォルダを検索中...")
    folders = search_folder(service, '北海道旅行')
    
    if not folders:
        print("「北海道旅行」を含むフォルダが見つかりませんでした。")
        print("\n「北海道」を含むフォルダを検索します...")
        folders = search_folder(service, '北海道')
    
    if not folders:
        print("該当するフォルダが見つかりませんでした。")
        return
    
    print(f"\n見つかったフォルダ: {len(folders)}件")
    for i, folder in enumerate(folders, 1):
        print(f"  {i}. {folder.get('name')} (ID: {folder.get('id')})")
    
    # すべてのサブフォルダを取得
    print("\n" + "=" * 80)
    print("サブフォルダを検索中...")
    print("=" * 80)
    
    all_folders_to_search = []
    for folder in folders:
        folder_id = folder.get('id')
        folder_name = folder.get('name')
        
        print(f"\n[{folder_name}] のサブフォルダを検索中...")
        subfolders = get_all_subfolders_recursive(service, folder_id, folder_name, 0)
        
        print(f"  見つかったフォルダ数（サブフォルダ含む）: {len(subfolders)}件")
        
        # サブフォルダの詳細を表示
        for sub_id, sub_name, level in subfolders:
            indent = "  " * (level + 1)
            if sub_name:
                print(f"{indent}└─ {sub_name}")
            else:
                print(f"{indent}└─ (ルート)")
        
        all_folders_to_search.extend(subfolders)
    
    # 各フォルダ内でラーメン写真を検索
    print("\n" + "=" * 80)
    print("すべてのフォルダ内の画像を検索中...")
    print("=" * 80)
    
    all_images = []
    
    for folder_id, folder_name, level in all_folders_to_search:
        display_name = folder_name if folder_name else "(ルート)"
        
        images = search_images_in_folder(service, folder_id)
        
        if images:
            print(f"\n[{display_name}] {len(images)}件の画像")
            all_images.extend([(display_name, img) for img in images])
    
    if not all_images:
        print("\n画像が見つかりませんでした。")
        return
    
    # ラーメン関連の写真をフィルタリング
    ramen_photos = []
    for folder_name, img in all_images:
        img_name = img.get('name', '').lower()
        if 'ラーメン' in img_name or 'ramen' in img_name or 'らーめん' in img_name:
            ramen_photos.append((folder_name, img))
    
    print("\n" + "=" * 80)
    print(f"全画像: {len(all_images)}件")
    print(f"ラーメン関連（ファイル名に含む）: {len(ramen_photos)}件")
    print("=" * 80)
    
    # ラーメン関連の写真を表示
    if ramen_photos:
        print("\n【ラーメン関連の写真】")
        print(f"{'No.':<4} {'フォルダ':<30} {'ファイル名':<40} {'最終更新'}")
        print(f"{'-'*4} {'-'*30} {'-'*40} {'-'*20}")
        
        for i, (folder_name, file) in enumerate(ramen_photos, 1):
            name = file.get('name', '無題')[:38]
            modified = format_date(file.get('modifiedTime', ''))
            folder_short = folder_name[:28]
            print(f"{i:<4} {folder_short:<30} {name:<40} {modified}")
        
        # 詳細情報
        print("\n" + "=" * 80)
        print("詳細情報:")
        print("=" * 80)
        print()
        
        for i, (folder_name, file) in enumerate(ramen_photos, 1):
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
    else:
        print("\nファイル名に「ラーメン」を含む写真は見つかりませんでした。")
        print("\nすべての画像（最初の20件）:")
        print(f"{'No.':<4} {'フォルダ':<30} {'ファイル名':<40}")
        print(f"{'-'*4} {'-'*30} {'-'*40}")
        
        for i, (folder_name, file) in enumerate(all_images[:20], 1):
            name = file.get('name', '無題')[:38]
            folder_short = folder_name[:28]
            print(f"{i:<4} {folder_short:<30} {name:<40}")


if __name__ == '__main__':
    main()

