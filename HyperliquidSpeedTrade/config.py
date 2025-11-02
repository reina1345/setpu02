"""
設定管理モジュール
環境変数から設定を読み込み、アプリケーション全体で使用します
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

class Config:
    """アプリケーション設定クラス"""
    
    # ネットワーク設定
    USE_TESTNET = os.getenv('USE_TESTNET', 'True').lower() == 'true'
    
    # API設定
    PRIVATE_KEY = os.getenv('PRIVATE_KEY', '')
    
    # デフォルト取引設定
    DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'BTC')
    
    # 利用可能な通貨ペア（Hyperliquidで実際に取引可能な通貨）
    AVAILABLE_SYMBOLS = [
        'BTC', 'ETH', 'SOL', 'ARB', 'AVAX', 'ATOM', 
        'DOGE', 'MATIC', 'OP', 'BNB', 'ADA', 'APT',
        'AAVE', 'MKR', 'SNX', 'SUSHI', 'COMP', 'WIF',
        'JUP', 'TIA', 'INJ', 'SUI', 'PENDLE', 'FET',
        'NEAR', 'FIL', 'RUNE', 'IMX', 'ETC', 'RENDER'
    ]
    
    # DEFAULT_SIZEの安全な型変換
    try:
        DEFAULT_SIZE = float(os.getenv('DEFAULT_SIZE', '0.001'))
        if DEFAULT_SIZE <= 0:
            print("警告: DEFAULT_SIZEは正の数である必要があります。デフォルト値0.001を使用します。")
            DEFAULT_SIZE = 0.001
    except (ValueError, TypeError):
        print("警告: DEFAULT_SIZEの値が不正です。デフォルト値0.001を使用します。")
        DEFAULT_SIZE = 0.001
    
    # GUI設定
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    THEME = "dark-blue"
    
    # 注文確認ダイアログ（True=表示する、False=表示しない）
    # 既定: テストネット=False / 本番=True （環境変数で上書き可）
    _confirm_default = 'False' if USE_TESTNET else 'True'
    CONFIRM_ORDERS = os.getenv('CONFIRM_ORDERS', _confirm_default).lower() == 'true'

    # リスク関連の既定値（環境別）。環境変数で上書き可能
    # 成行スリッページ上限（例: テスト=5%、本番=1%）
    try:
        SLIPPAGE_MAX = float(os.getenv('SLIPPAGE_MAX', '0.05' if USE_TESTNET else '0.01'))
        if SLIPPAGE_MAX <= 0:
            print("警告: SLIPPAGE_MAXは正の数である必要があります。既定値を使用します。")
            SLIPPAGE_MAX = 0.05 if USE_TESTNET else 0.01
    except (ValueError, TypeError):
        print("警告: SLIPPAGE_MAXの値が不正です。既定値を使用します。")
        SLIPPAGE_MAX = 0.05 if USE_TESTNET else 0.01

    # 1注文あたりの最大サイズ（資産サイズ単位）
    try:
        MAX_SIZE_PER_ORDER = float(os.getenv('MAX_SIZE_PER_ORDER', '5' if USE_TESTNET else '1'))
        if MAX_SIZE_PER_ORDER <= 0:
            print("警告: MAX_SIZE_PER_ORDERは正の数である必要があります。既定値を使用します。")
            MAX_SIZE_PER_ORDER = 5 if USE_TESTNET else 1
    except (ValueError, TypeError):
        print("警告: MAX_SIZE_PER_ORDERの値が不正です。既定値を使用します。")
        MAX_SIZE_PER_ORDER = 5 if USE_TESTNET else 1

    # 1注文あたりの最大名目金額（USD想定）
    try:
        MAX_NOTIONAL_PER_ORDER = float(os.getenv('MAX_NOTIONAL_PER_ORDER', '50000' if USE_TESTNET else '10000'))
        if MAX_NOTIONAL_PER_ORDER <= 0:
            print("警告: MAX_NOTIONAL_PER_ORDERは正の数である必要があります。既定値を使用します。")
            MAX_NOTIONAL_PER_ORDER = 50000 if USE_TESTNET else 10000
    except (ValueError, TypeError):
        print("警告: MAX_NOTIONAL_PER_ORDERの値が不正です。既定値を使用します。")
        MAX_NOTIONAL_PER_ORDER = 50000 if USE_TESTNET else 10000
    
    # WebSocket設定
    WS_RECONNECT_DELAY = 5  # 秒
    
    # レートリミット設定
    RATE_LIMIT_MAX_CALLS = int(os.getenv('RATE_LIMIT_MAX_CALLS', '12'))  # 60秒あたりの最大呼び出し数
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '60'))  # 期間（秒）
    RATE_LIMIT_PRIORITY_BYPASS = os.getenv('RATE_LIMIT_PRIORITY_BYPASS', 'True').lower() == 'true'  # 高優先度バイパス
    
    # API URL
    @staticmethod
    def get_api_url():
        """API URLを取得"""
        if Config.USE_TESTNET:
            return "https://api.hyperliquid-testnet.xyz"
        return "https://api.hyperliquid.xyz"
    
    @staticmethod
    def get_ws_url():
        """WebSocket URLを取得"""
        if Config.USE_TESTNET:
            return "wss://api.hyperliquid-testnet.xyz/ws"
        return "wss://api.hyperliquid.xyz/ws"
    
    @staticmethod
    def validate():
        """設定の妥当性をチェック"""
        errors = []
        
        # 秘密鍵の検証
        if not Config.PRIVATE_KEY:
            errors.append("PRIVATE_KEYが設定されていません")
        elif not Config.PRIVATE_KEY.startswith('0x'):
            errors.append("PRIVATE_KEYは0xで始まる必要があります")
        elif len(Config.PRIVATE_KEY) != 66:  # 0x + 64文字の16進数
            errors.append(f"PRIVATE_KEYの長さが不正です（現在: {len(Config.PRIVATE_KEY)}文字、必要: 66文字）")
        else:
            # 16進数として有効かチェック
            try:
                int(Config.PRIVATE_KEY, 16)
            except ValueError:
                errors.append("PRIVATE_KEYは有効な16進数である必要があります")
        
        # サイズの検証（既にクラス変数で処理済みだが念のため）
        if Config.DEFAULT_SIZE <= 0:
            errors.append("DEFAULT_SIZEは正の数である必要があります")
        
        return errors

