"""利用可能な通貨ペアを確認するスクリプト"""
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
meta = info.meta()

print("=== Hyperliquid テストネットで利用可能な通貨ペア ===\n")
for asset in meta['universe']:
    print(f"  {asset['name']}")
    
print(f"\n合計: {len(meta['universe'])} 通貨ペア")

