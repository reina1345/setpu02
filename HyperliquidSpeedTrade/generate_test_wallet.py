"""
テスト用ウォレットを生成するスクリプト
警告: これはテストネット専用です。本番環境では絶対に使用しないでください。
"""
import os
import secrets

# 秘密鍵を生成（32バイト = 256ビット）
private_key_bytes = secrets.token_bytes(32)
private_key_hex = '0x' + private_key_bytes.hex()

# eth_keysを使用してアドレスを計算（ckzgなしでも動作）
try:
    from eth_keys import keys
    pk = keys.PrivateKey(private_key_bytes)
    address = pk.public_key.to_checksum_address()
    
    print("=" * 60)
    print("新しいテスト用ウォレットを生成しました")
    print("=" * 60)
    print()
    print(f"アドレス: {address}")
    print(f"秘密鍵: {private_key_hex}")
    print()
    print("⚠️ 重要:")
    print("1. この秘密鍵はテストネット専用です")
    print("2. 本番環境では絶対に使用しないでください")
    print("3. この秘密鍵を.envファイルのPRIVATE_KEYに設定してください")
    print("4. テストネット資金を取得してください:")
    print("   https://app.hyperliquid-testnet.xyz/")
    print()
    print("🔧 .envファイルを編集:")
    print(f'   PRIVATE_KEY={private_key_hex}')
    print()
    print("=" * 60)
    
except ImportError as e:
    print("=" * 60)
    print("⚠️ eth_keysのインポートエラー")
    print("=" * 60)
    print()
    print("生成された秘密鍵:")
    print(f"{private_key_hex}")
    print()
    print("注意: アドレスを計算できませんでしたが、")
    print("秘密鍵は有効です。アプリ起動時にアドレスが表示されます。")
    print()
    print("🔧 .envファイルを編集:")
    print(f'   PRIVATE_KEY={private_key_hex}')
    print()
    print("=" * 60)

