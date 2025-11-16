"""
Hyperliquid Speed Trade - メインアプリケーション
MT4スピード注文のようなUIでHyperliquidの取引を行います
"""
import sys
import threading
import time
from hyperliquid_api import HyperliquidAPI
from gui import SpeedTradeGUI
from config import Config

class SpeedTradeApp:
    """メインアプリケーションクラス"""
    
    def __init__(self):
        """初期化"""
        self.api = HyperliquidAPI()
        self.gui = SpeedTradeGUI()
        self.is_running = True
        
    def initialize(self):
        """アプリケーションを初期化"""
        print("=== Hyperliquid Speed Trade ===")
        print("初期化中...")
        
        # API初期化
        if not self.api.initialize():
            print("APIの初期化に失敗しました")
            print("\n.envファイルを確認してください:")
            print("1. .env.exampleを.envにコピー")
            print("2. PRIVATE_KEYを設定")
            return False
        
        # 出来高順に通貨ペアリストを取得
        print("出来高情報を取得中...")
        sorted_symbols = self.api.get_symbols_by_volume()
        
        # GUI作成（出来高順のリストを渡す）
        self.gui.create_window(sorted_symbols)
        
        # コールバック設定
        self.gui.set_buy_callback(self.on_buy_order)
        self.gui.set_sell_callback(self.on_sell_order)
        self.gui.on_limit_buy_callback = self.on_limit_buy_order  # 指値買い
        self.gui.on_limit_sell_callback = self.on_limit_sell_order  # 指値売り
        self.gui.set_close_callback(self.on_close_position)
        self.gui.on_symbol_change_callback = self.on_symbol_change
        self.gui.on_cancel_order_callback = self.on_cancel_order  # 注文キャンセル
        
        # 価格ストリーム開始（全ての通貨ペアを購読）
        # 取得した通貨ペアリスト（上位100個まで）を購読してWebSocketの負荷を軽減
        subscribe_symbols = sorted_symbols[:100] if len(sorted_symbols) > 100 else sorted_symbols
        print(f"価格ストリーム開始: {len(subscribe_symbols)}個の通貨ペアを購読")
        self.api.start_price_stream(subscribe_symbols, self.on_price_update)
        
        # ポジション更新スレッド開始
        self.start_position_updater()
        
        print("初期化完了！")
        self.gui.show_status("接続済み - 取引準備完了")
        
        # 初期接続状態を設定
        self.gui.update_api_status(self.api.is_connected())
        
        return True
    
    def on_price_update(self, prices: dict):
        """価格が更新された時のコールバック"""
        # GUIスレッドで価格を更新（クロージャ問題を回避）
        if self.gui.root:
            # pricesのコピーを作成して安全に渡す
            prices_copy = dict(prices)
            self.gui.root.after(0, lambda p=prices_copy: self.gui.update_price(p))
    
    def on_symbol_change(self, symbol: str):
        """通貨ペアが変更された時のコールバック"""
        print(f"通貨ペアを {symbol} に変更しました")
        self.gui.show_status(f"{symbol}-USD に切り替えました")
    
    def on_buy_order(self, symbol: str, size: float):
        """買い注文のコールバック"""
        self.gui.show_status(f"買い注文を送信中: {symbol} {size}...")
        self.gui.add_log(f"買い注文送信: {symbol} サイズ={size}")
        
        # 別スレッドで実行
        def execute():
            result = self.api.place_market_order(symbol, True, size)
            
            # GUIスレッドで結果を表示（クロージャ問題を回避）
            if self.gui.root:
                success = result['success']
                message = result['message']
                
                if success:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_success(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[OK] {msg}"))
                    # 成行注文後はポジションのみ更新（未約定注文は不要）
                    self.gui.root.after(1000, lambda: self.update_positions(include_orders=False))
                else:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_error(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[NG] {msg}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def on_limit_buy_order(self, symbol: str, size: float, limit_price: float):
        """指値買い注文のコールバック"""
        self.gui.show_status(f"指値買い注文を送信中: {symbol} {size} @ ${limit_price}...")
        self.gui.add_log(f"指値買い注文送信: {symbol} サイズ={size} 価格=${limit_price}")
        
        # 別スレッドで実行
        def execute():
            result = self.api.place_limit_order(symbol, True, size, limit_price)
            
            # GUIスレッドで結果を表示（クロージャ問題を回避）
            if self.gui.root:
                success = result['success']
                message = result['message']
                
                if success:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_success(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[OK] {msg}"))
                    # 指値注文後は未約定注文リストも含めて更新
                    self.gui.root.after(1000, lambda: self.update_positions(include_orders=True))
                else:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_error(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[NG] {msg}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def on_limit_sell_order(self, symbol: str, size: float, limit_price: float):
        """指値売り注文のコールバック"""
        self.gui.show_status(f"指値売り注文を送信中: {symbol} {size} @ ${limit_price}...")
        self.gui.add_log(f"指値売り注文送信: {symbol} サイズ={size} 価格=${limit_price}")
        
        # 別スレッドで実行
        def execute():
            result = self.api.place_limit_order(symbol, False, size, limit_price)
            
            # GUIスレッドで結果を表示（クロージャ問題を回避）
            if self.gui.root:
                success = result['success']
                message = result['message']
                
                if success:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_success(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[OK] {msg}"))
                    # 指値注文後は未約定注文リストも含めて更新
                    self.gui.root.after(1000, lambda: self.update_positions(include_orders=True))
                else:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_error(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[NG] {msg}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def on_sell_order(self, symbol: str, size: float):
        """売り注文のコールバック"""
        self.gui.show_status(f"売り注文を送信中: {symbol} {size}...")
        self.gui.add_log(f"売り注文送信: {symbol} サイズ={size}")
        
        # 別スレッドで実行
        def execute():
            result = self.api.place_market_order(symbol, False, size)
            
            # GUIスレッドで結果を表示（クロージャ問題を回避）
            if self.gui.root:
                success = result['success']
                message = result['message']
                
                if success:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_success(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[OK] {msg}"))
                    # 成行注文後はポジションのみ更新（未約定注文は不要）
                    self.gui.root.after(1000, lambda: self.update_positions(include_orders=False))
                else:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_error(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[NG] {msg}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def on_close_position(self, symbol: str = None, size: float = None):
        """ポジション決済のコールバック（symbol=Noneで全決済、size=Noneで全量決済）"""
        if symbol is None:
            self.gui.show_status("全ポジション決済中...")
            self.gui.add_log("全決済開始（並列処理）")
        else:
            if size is None:
                self.gui.show_status(f"ポジション決済中: {symbol} (全量)...")
                self.gui.add_log(f"決済開始: {symbol} (全量)")
            else:
                self.gui.show_status(f"ポジション決済中: {symbol} {size}...")
                self.gui.add_log(f"決済開始: {symbol} サイズ={size}")
        
        # 別スレッドで実行
        def execute():
            if symbol is None:
                # 全決済
                result = self.api.close_all_positions()
            elif size is None:
                # 個別全決済
                result = self.api.close_position(symbol)
            else:
                # 一部決済
                result = self.api.close_position_partial(symbol, size)
            
            # GUIスレッドで結果を表示（クロージャ問題を回避）
            if self.gui.root:
                success = result['success']
                message = result['message']
                
                if success:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_success(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[OK] {msg}"))
                    # 決済後はポジションを複数回更新（APIの遅延に対応、未約定注文は不要）
                    self.gui.root.after(50, lambda: self.update_positions(include_orders=False))   # 即座に更新
                    self.gui.root.after(300, lambda: self.update_positions(include_orders=False))  # 0.3秒後に再更新
                    self.gui.root.after(800, lambda: self.update_positions(include_orders=False))  # 0.8秒後に再更新
                else:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_error(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[NG] {msg}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def on_cancel_order(self, symbol: str, order_id: int):
        """注文キャンセルのコールバック"""
        self.gui.show_status(f"注文をキャンセル中: {symbol} (ID: {order_id})...")
        self.gui.add_log(f"キャンセル送信: {symbol} 注文ID={order_id}")
        
        # 別スレッドで実行
        def execute():
            result = self.api.cancel_order(symbol, order_id)
            
            # GUIスレッドで結果を表示（クロージャ問題を回避）
            if self.gui.root:
                success = result['success']
                message = result['message']
                
                if success:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_success(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[OK] {msg}"))
                    # キャンセル後は未約定注文リストを即座に更新
                    self.gui.root.after(1000, lambda: self.update_positions(include_orders=True))
                else:
                    self.gui.root.after(0, lambda msg=message: self.gui.show_error(msg))
                    self.gui.root.after(0, lambda msg=message: self.gui.add_log(f"[NG] {msg}"))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def update_positions(self, include_orders=True):
        """ポジション情報と未約定注文を更新
        
        Args:
            include_orders: 未約定注文も取得するか（デフォルト: True）
        """
        def execute():
            positions = self.api.get_positions()
            
            # 未約定注文を取得（include_ordersがTrueの場合のみ）
            if include_orders:
                open_orders = self.api.get_open_orders()
            else:
                open_orders = []
            
            # アカウントレバレッジを取得
            leverage = self.api.get_account_leverage()
            
            # アカウント情報を取得
            account_info = self.api.get_account_info()
            
            # GUIスレッドで更新（クロージャ問題を回避）
            if self.gui.root:
                # positionsのコピーを作成して安全に渡す
                positions_copy = list(positions)
                self.gui.root.after(0, lambda p=positions_copy: self.gui.update_positions(p))
                
                # 未約定注文を更新（データがある場合のみ）
                if include_orders:
                    orders_copy = list(open_orders)
                    self.gui.root.after(0, lambda o=orders_copy: self.gui.update_open_orders(o))
                
                # レバレッジを更新
                if leverage is not None:
                    self.gui.root.after(0, lambda lev=leverage: self.gui.update_account_leverage(lev))
                
                # アカウント情報を更新
                if account_info:
                    self.gui.root.after(0, lambda info=account_info: self.gui.update_account_info(
                        equity=info['equity'],
                        spot=info['spot'],
                        perps=info['perps']
                    ))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def start_position_updater(self):
        """ポジション自動更新を開始"""
        def updater():
            update_count = 0
            while self.is_running:
                time.sleep(5)  # 5秒ごとに更新
                if self.api.is_connected():
                    update_count += 1
                    # 未約定注文は10秒ごと（2回に1回）に更新して負荷を減らす
                    self.update_positions(include_orders=(update_count % 2 == 0))
                    
                    # 接続状態とレートリミット状態を更新
                    if self.gui.root:
                        # API接続状態
                        self.gui.root.after(0, lambda: self.gui.update_api_status(self.api.is_connected()))
                        
                        # レートリミット状態
                        try:
                            from rate_limiter import get_rate_limiter
                            limiter = get_rate_limiter()
                            current = limiter.get_current_calls()
                            max_calls = limiter.max_calls
                            self.gui.root.after(0, lambda c=current, m=max_calls: self.gui.update_rate_limit_status(c, m))
                        except Exception:
                            pass  # エラー時は無視
        
        thread = threading.Thread(target=updater, daemon=True)
        thread.start()
    
    def run(self):
        """アプリケーションを実行"""
        if not self.initialize():
            return 1
        
        try:
            # GUIを起動
            self.gui.run()
        except KeyboardInterrupt:
            print("\n終了しています...")
        finally:
            self.is_running = False
        
        return 0

def main():
    """メイン関数"""
    app = SpeedTradeApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()

