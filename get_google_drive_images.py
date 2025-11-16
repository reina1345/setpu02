"""
Google Driveから画像ファイル（mimeTypeがimage/）の最新10件を取得するスクリプト
名前・URL・最終更新日を一覧表示します
"""

import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# スコープ: 読み取り専用
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# 認証情報のパス
CREDENTIALS_PATH = r'C:\Users\purena\.cursor\google-drive-credentials.json'
TOKEN_PATH = r'C:\Users\purena\.cursor\google-drive-token.json'


def authenticate():
    """Google Drive APIの認証を行います"""
    creds = None
    
    # 既存のトークンファイルを確認
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # トークンが無効または存在しない場合、再認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"エラー: 認証情報ファイルが見つかりません: {CREDENTIALS_PATH}")
                print("Google Cloud ConsoleからOAuthクライアントIDをダウンロードしてください")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # トークンを保存
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def get_image_files(service, max_results=10):
    """画像ファイルの最新10件を取得します"""
    try:
        # 画像ファイルを検索（mimeTypeがimage/で始まるファイル）
        query = "mimeType contains 'image/' and trashed = false"
        
        # 最終更新日で降順ソート
        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, webContentLink)",
            orderBy="modifiedTime desc",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print('画像ファイルが見つかりませんでした。')
            return []
        
        return items
    
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
    print("Google Drive APIに認証中...")
    creds = authenticate()
    
    if not creds:
        return
    
    print("Google Drive APIサービスを構築中...")
    service = build('drive', 'v3', credentials=creds)
    
    print("\n画像ファイルを検索中...")
    image_files = get_image_files(service, max_results=10)
    
    if not image_files:
        return
    
    print(f"\n{'='*80}")
    print(f"最新の画像ファイル {len(image_files)} 件:")
    print(f"{'='*80}\n")
    
    # テーブル形式で出力
    print(f"{'No.':<4} {'名前':<40} {'最終更新日':<20} {'URL':<60}")
    print(f"{'-'*4} {'-'*40} {'-'*20} {'-'*60}")
    
    for i, file in enumerate(image_files, 1):
        name = file.get('name', '無題')[:38]  # 名前を40文字に制限
        modified = format_date(file.get('modifiedTime', ''))
        # webViewLinkがあればそれを使用、なければwebContentLink
        url = file.get('webViewLink') or file.get('webContentLink', 'URLなし')
        
        print(f"{i:<4} {name:<40} {modified:<20} {url[:58]:<60}")
    
    print(f"\n{'='*80}\n")
    
    # 詳細情報も出力
    print("詳細情報:\n")
    for i, file in enumerate(image_files, 1):
        print(f"{i}. {file.get('name', '無題')}")
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

