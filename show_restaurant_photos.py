"""
北海道旅行 飲食店フォルダ内のすべての写真を表示
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
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        
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


def search_images_in_folder(service, folder_id):
    """指定フォルダ内のすべての画像を取得"""
    try:
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, mimeType, modifiedTime, createdTime, size, webViewLink, webContentLink, thumbnailLink)",
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


def format_size(size_bytes):
    """バイトサイズを読みやすい形式に変換"""
    try:
        size = int(size_bytes)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    except:
        return "不明"


def main():
    """メイン処理"""
    print("=" * 80)
    print("北海道旅行 飲食店フォルダ内の写真一覧")
    print("=" * 80)
    print()
    
    # 認証
    print("Google Drive APIに認証中...")
    creds = authenticate()
    if not creds:
        print("認証に失敗しました")
        return
    
    service = build('drive', 'v3', credentials=creds)
    
    # 飲食店フォルダを検索
    print("\n「飲食店」フォルダを検索中...")
    folders = search_folder(service, '飲食店')
    
    if not folders:
        print("「飲食店」フォルダが見つかりませんでした。")
        return
    
    print(f"\n見つかった「飲食店」フォルダ: {len(folders)}件")
    
    # すべての飲食店フォルダから画像を取得
    all_images = []
    
    for folder in folders:
        folder_id = folder.get('id')
        folder_name = folder.get('name')
        
        print(f"\n[{folder_name}] (ID: {folder_id})")
        images = search_images_in_folder(service, folder_id)
        
        print(f"  画像数: {len(images)}件")
        
        if images:
            all_images.extend(images)
    
    if not all_images:
        print("\n画像が見つかりませんでした。")
        return
    
    # 画像一覧を表示
    print("\n" + "=" * 80)
    print(f"飲食店フォルダ内の写真: {len(all_images)}件")
    print("=" * 80)
    print()
    
    print(f"{'No.':<4} {'ファイル名':<45} {'撮影日時':<20} {'サイズ'}")
    print(f"{'-'*4} {'-'*45} {'-'*20} {'-'*10}")
    
    for i, img in enumerate(all_images, 1):
        name = img.get('name', '無題')[:43]
        created = format_date(img.get('createdTime', ''))
        size = format_size(img.get('size', '0'))
        print(f"{i:<4} {name:<45} {created:<20} {size}")
    
    # 詳細情報
    print("\n" + "=" * 80)
    print("詳細情報（URLとサムネイル付き）:")
    print("=" * 80)
    print()
    
    for i, img in enumerate(all_images, 1):
        print(f"{i}. {img.get('name', '無題')}")
        print(f"   ファイルID: {img.get('id', '')}")
        print(f"   タイプ: {img.get('mimeType', '')}")
        print(f"   サイズ: {format_size(img.get('size', '0'))}")
        print(f"   撮影日: {format_date(img.get('createdTime', ''))}")
        print(f"   最終更新: {format_date(img.get('modifiedTime', ''))}")
        
        if img.get('webViewLink'):
            print(f"   [閲覧URL] {img.get('webViewLink')}")
        if img.get('webContentLink'):
            print(f"   [ダウンロードURL] {img.get('webContentLink')}")
        if img.get('thumbnailLink'):
            print(f"   [サムネイルURL] {img.get('thumbnailLink')}")
        
        print()
    
    print("=" * 80)
    print("これらの写真の中からラーメンの写真を探すには:")
    print("- 上記のURLをブラウザで開いて確認してください")
    print("- または、撮影日時から該当する写真を特定してください")
    print("=" * 80)


if __name__ == '__main__':
    main()

