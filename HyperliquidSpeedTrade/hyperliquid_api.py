"""
Hyperliquid API接続モジュール
価格取得、注文送信、ポジション管理を行います
"""
import json
import asyncio
import time
import websockets
from typing import Optional, Dict, List, Callable
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account import Account
from config import Config
from rate_limiter import get_rate_limiter, RequestPriority

class HyperliquidAPI:
    """Hyperliquid APIクライアントクラス"""
    
    def __init__(self):
        """初期化"""
        self.config = Config()
        self.info = None
        self.exchange = None
        self.account = None
        self.address = None
        self._price_callback = None
        self._is_connected = False
        # レートリミッターを初期化
        self.rate_limiter = get_rate_limiter(
            max_calls=Config.RATE_LIMIT_MAX_CALLS,
            period=Config.RATE_LIMIT_PERIOD,
            priority_bypass=Config.RATE_LIMIT_PRIORITY_BYPASS
        )
        
    def _with_retry(self, op_name: str, fn: Callable, *, max_retries: int = 5, base_delay: float = 0.25, 
                    priority: RequestPriority = RequestPriority.NORMAL, use_rate_limiter: bool = True):
        """レート制限や一時的失敗に対する指数バックオフ付きリトライ
        - 429/ネットワーク系/OSErrorは再試行
        - それ以外は即時例外
        - レートリミッターによる事前制限も実施
        
        Args:
            op_name: 操作名（ログ用）
            fn: 実行する関数
            max_retries: 最大リトライ回数
            base_delay: 基本待機時間（秒）
            priority: リクエストの優先度
            use_rate_limiter: レートリミッターを使用するか
        """
        # レートリミッターによる事前制限
        if use_rate_limiter:
            wait_time = self.rate_limiter.wait_if_needed(priority)
            if wait_time > 0:
                print(f"[RATE_LIMIT] {op_name}: レートリミット待機 {wait_time:.2f}秒")
        
        attempt = 0
        while True:
            try:
                return fn()
            except Exception as e:
                msg = str(e)
                # HTTP 429エラーは特別に処理（より長い待機時間）
                is_429 = '429' in msg or 'Rate limit' in msg or 'rate limit' in msg
                retryable = is_429 or ('Rate' in msg) or isinstance(e, OSError)
                
                if not retryable or attempt >= max_retries:
                    raise
                
                # HTTP 429の場合は長めに待機（15秒+指数バックオフ）
                if is_429:
                    wait = 15.0 + min(base_delay * (2 ** attempt), 10.0)
                    print(f"[429_RETRY] {op_name}: HTTP 429エラー検出。{wait:.2f}秒待機後再試行 ({attempt+1}/{max_retries})")
                else:
                    wait = min(base_delay * (2 ** attempt), 5.0)
                    print(f"[RETRY] {op_name}: {attempt+1}/{max_retries} 待機 {wait:.2f}s (理由: {type(e).__name__})")
                
                attempt += 1
                time.sleep(wait)

    def initialize(self) -> bool:
        """APIクライアントを初期化"""
        try:
            # 設定の検証
            errors = Config.validate()
            if errors:
                for error in errors:
                    print(f"設定エラー: {error}")
                return False
            
            # アカウント設定
            self.account = Account.from_key(Config.PRIVATE_KEY)
            self.address = self.account.address
            
            # Infoクライアント（読み取り専用）
            if Config.USE_TESTNET:
                self.info = Info(constants.TESTNET_API_URL, skip_ws=True)
            else:
                self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            
            # Exchangeクライアント（取引用）
            if Config.USE_TESTNET:
                self.exchange = Exchange(
                    self.account,
                    constants.TESTNET_API_URL,
                    account_address=self.address
                )
            else:
                self.exchange = Exchange(
                    self.account,
                    constants.MAINNET_API_URL,
                    account_address=self.address
                )
            
            self._is_connected = True
            print(f"Hyperliquid API初期化成功 (アドレス: {self.address})")
            print(f"ネットワーク: {'テストネット' if Config.USE_TESTNET else 'メインネット'}")
            
            return True
            
        except Exception as e:
            print(f"API初期化エラー: {e}")
            self._is_connected = False
            return False
    
    def is_connected(self) -> bool:
        """接続状態を返す"""
        return self._is_connected
    
    def get_price(self, symbol: str = "BTC") -> Optional[float]:
        """現在価格を取得"""
        try:
            # 全マーケット情報を取得（リトライ、通常優先度）
            all_mids = self._with_retry("all_mids", lambda: self.info.all_mids(), 
                                       priority=RequestPriority.NORMAL)
            
            # シンボルの価格を検索
            if symbol in all_mids:
                return float(all_mids[symbol])
            
            print(f"シンボル {symbol} が見つかりません")
            return None
            
        except Exception as e:
            print(f"価格取得エラー: {e}")
            return None
    
    def get_symbols_by_volume(self) -> List[str]:
        """出来高順に通貨ペアリストを取得（全通貨対応）"""
        try:
            # メタ情報と資産コンテキストを取得（リトライ、通常優先度）
            meta_and_asset_ctxs = self._with_retry("meta_and_asset_ctxs", lambda: self.info.meta_and_asset_ctxs(),
                                                   priority=RequestPriority.NORMAL)
            
            if not meta_and_asset_ctxs or len(meta_and_asset_ctxs) < 2:
                print("出来高情報の取得に失敗しました。デフォルトのリストを使用します。")
                return Config.AVAILABLE_SYMBOLS
            
            # meta情報（通貨名リスト）を取得
            meta = meta_and_asset_ctxs[0]
            # asset_ctxs（資産コンテキスト）から出来高情報を取得
            asset_ctxs = meta_and_asset_ctxs[1]
            
            # metaから通貨リスト（universe）を取得
            if isinstance(meta, dict) and 'universe' in meta:
                universe = meta['universe']
            else:
                print("[WARNING] meta構造が不正です。デフォルトリストを使用します。")
                return Config.AVAILABLE_SYMBOLS
            
            # 通貨ペアと出来高のリストを作成
            volume_list = []
            
            # universeとasset_ctxsを組み合わせ
            for universe_item, ctx in zip(universe, asset_ctxs):
                # universeから通貨名を取得
                symbol = universe_item.get('name', '')
                # 24時間出来高を取得（dayNtlVlm）
                volume = float(ctx.get('dayNtlVlm', 0))
                
                if symbol:
                    volume_list.append((symbol, volume))
            
            # 出来高が大きい順にソート
            volume_list.sort(key=lambda x: x[1], reverse=True)
            
            # 通貨ペアのみのリストを返す
            sorted_symbols = [symbol for symbol, volume in volume_list]
            
            print(f"[INFO] 出来高順通貨ペア（上位10つ）:")
            for i, (symbol, volume) in enumerate(volume_list[:10], 1):
                print(f"  {i}. {symbol}: ${volume:,.0f}")
            
            print(f"[INFO] 合計 {len(sorted_symbols)} 個の通貨ペアを取得しました")
            
            # 結果が空の場合はデフォルトを使用
            if not sorted_symbols:
                print("[WARNING] APIから通貨ペアを取得できませんでした。デフォルトリストを使用します。")
                return Config.AVAILABLE_SYMBOLS
            
            return sorted_symbols
            
        except Exception as e:
            print(f"出来高情報取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return Config.AVAILABLE_SYMBOLS
    
    def get_account_state(self) -> Optional[Dict]:
        """アカウント状態を取得（通常優先度）"""
        try:
            user_state = self._with_retry("user_state", lambda: self.info.user_state(self.address),
                                         priority=RequestPriority.NORMAL)
            return user_state
        except Exception as e:
            print(f"アカウント状態取得エラー: {e}")
            return None
    
    def get_account_leverage(self) -> Optional[float]:
        """アカウント全体のレバレッジを取得"""
        try:
            user_state = self._with_retry("user_state", lambda: self.info.user_state(self.address),
                                         priority=RequestPriority.NORMAL)
            if not user_state:
                return None
            
            # クロスマージン情報を取得
            margin_summary = user_state.get('marginSummary', {})
            account_value = float(margin_summary.get('accountValue', 0))
            total_ntl_pos = float(margin_summary.get('totalNtlPos', 0))
            
            if account_value > 0:
                leverage = total_ntl_pos / account_value
                return leverage
            
            return 0.0
            
        except Exception as e:
            print(f"レバレッジ取得エラー: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """アカウント情報（Equity、Spot、Perps）を取得"""
        try:
            user_state = self._with_retry("user_state", lambda: self.info.user_state(self.address),
                                         priority=RequestPriority.NORMAL)
            if not user_state:
                return None
            
            margin_summary = user_state.get('marginSummary', {})
            
            # Perps証拠金（accountValueはPerps証拠金の総額）
            account_value = float(margin_summary.get('accountValue', 0))
            
            # Spot残高（HyperliquidではSpot取引は別システムなので通常0）
            # 将来的にSpot残高APIがあれば追加
            spot_value = 0.0
            
            # Total Equity（Spot + Perps）
            total_equity = spot_value + account_value
            
            return {
                'equity': total_equity,
                'spot': spot_value,
                'perps': account_value
            }
            
        except Exception as e:
            print(f"アカウント情報取得エラー: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """現在のポジションを取得"""
        try:
            user_state = self.get_account_state()
            if user_state and 'assetPositions' in user_state:
                positions = []
                for pos in user_state['assetPositions']:
                    position_data = pos.get('position', {})
                    if float(position_data.get('szi', 0)) != 0:  # ポジションがある場合のみ
                        positions.append({
                            'coin': position_data.get('coin', ''),
                            'size': float(position_data.get('szi', 0)),
                            'entry_price': float(position_data.get('entryPx', 0)),
                            'unrealized_pnl': float(position_data.get('unrealizedPnl', 0)),
                            'leverage': position_data.get('leverage', {}),
                        })
                return positions
            return []
        except Exception as e:
            print(f"ポジション取得エラー: {e}")
            return []
    
    def get_open_orders(self) -> List[Dict]:
        """未約定注文（オープンオーダー）を取得"""
        try:
            open_orders_response = self._with_retry("open_orders", lambda: self.info.open_orders(self.address),
                                                    priority=RequestPriority.LOW)  # 低優先度（定期更新用）
            
            if not open_orders_response:
                return []
            
            orders = []
            for order in open_orders_response:
                # 注文情報を整形
                coin = order.get('coin', '')
                side = order.get('side', '')
                limit_px = float(order.get('limitPx', 0))
                sz = float(order.get('sz', 0))
                oid = order.get('oid', 0)
                timestamp = order.get('timestamp', 0)
                
                orders.append({
                    'coin': coin,
                    'side': side,  # 'B' (buy) or 'A' (ask/sell)
                    'is_buy': side == 'B',
                    'limit_price': limit_px,
                    'size': sz,
                    'order_id': oid,
                    'timestamp': timestamp
                })
            
            if orders:
                print(f"[INFO] {len(orders)}個の未約定注文を取得")
            
            return orders
            
        except Exception as e:
            error_str = str(e)
            # HTTP 429 (Rate Limiting) エラーを検出
            if '429' in error_str:
                print("[警告] APIレートリミット: リクエストが多すぎます。15秒待機してください。")
            else:
                print(f"未約定注文取得エラー: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """指定した注文をキャンセル"""
        try:
            print(f"[キャンセル] {symbol} 注文ID={order_id}")
            
            # 注文をキャンセル（高優先度）
            cancel_result = self._with_retry(
                "cancel",
                lambda: self.exchange.cancel(name=symbol, oid=order_id),
                priority=RequestPriority.HIGH,
                max_retries=3
            )
            
            # レスポンスを解析
            if isinstance(cancel_result, dict):
                if 'status' in cancel_result:
                    status = cancel_result.get('status', '')
                    if status == 'ok':
                        return {
                            'success': True,
                            'message': f"注文をキャンセルしました: {symbol} (ID: {order_id})"
                        }
                    elif status == 'err':
                        error_msg = cancel_result.get('response', 'Unknown error')
                        return {
                            'success': False,
                            'error': error_msg,
                            'message': f"キャンセルエラー: {error_msg}"
                        }
                
                # responseの中のstatusesをチェック
                response = cancel_result.get('response', {})
                if isinstance(response, dict) and 'data' in response:
                    data = response.get('data', {})
                    statuses = data.get('statuses', [])
                    if statuses and len(statuses) > 0:
                        first_status = statuses[0]
                        
                        # エラーチェック
                        if 'error' in first_status:
                            error_msg = first_status['error']
                            return {
                                'success': False,
                                'error': error_msg,
                                'message': f"キャンセルエラー: {error_msg}"
                            }
                        
                        # 成功チェック
                        if first_status == 'success' or 'success' in str(first_status).lower():
                            return {
                                'success': True,
                                'message': f"注文をキャンセルしました: {symbol} (ID: {order_id})"
                            }
            
            # デフォルトで成功と見なす（Hyperliquid APIは成功時に詳細を返さない場合がある）
            return {
                'success': True,
                'message': f"注文キャンセル送信: {symbol} (ID: {order_id})"
            }
            
        except Exception as e:
            error_msg = f"キャンセルエラー: {e}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def place_limit_order(self, symbol: str, is_buy: bool, size: float, limit_price: float) -> Dict:
        """指値注文を送信（高優先度）"""
        try:
            action = '買い' if is_buy else '売り'
            print(f"[指値注文] {symbol} {action} サイズ={size} 価格=${limit_price}")
            
            # 指値注文を送信（高優先度、レートリミッターはバイパス可能）
            order_result = self._with_retry(
                "limit_order",
                lambda: self.exchange.order(
                    name=symbol,
                    is_buy=is_buy,
                    sz=size,
                    limit_px=limit_price,
                    order_type={"limit": {"tif": "Gtc"}}
                ),
                priority=RequestPriority.HIGH,
                max_retries=3  # 注文は少ないリトライ回数で
            )
            
            # レスポンスを解析
            if isinstance(order_result, dict):
                if 'error' in order_result or 'status' in order_result:
                    status = order_result.get('status', '')
                    if status == 'err' or 'error' in order_result:
                        error_msg = order_result.get('response', order_result.get('error', 'Unknown error'))
                        return {
                            'success': False,
                            'error': error_msg,
                            'message': f"指値注文エラー: {error_msg}"
                        }
                
                # responseの中のstatusesをチェック
                response = order_result.get('response', {})
                if isinstance(response, dict) and 'data' in response:
                    data = response.get('data', {})
                    statuses = data.get('statuses', [])
                    if statuses and len(statuses) > 0:
                        first_status = statuses[0]
                        
                        # エラーチェック
                        if 'error' in first_status:
                            error_msg = first_status['error']
                            
                            # エラーの詳細説明を追加
                            detail = ""
                            if "open interest is at cap" in error_msg.lower():
                                detail = f"\n[原因] {symbol}のオープンインタレストが上限に達しています\n[対策] 別の通貨ペアを試すか、時間をおいて再試行してください"
                            elif "minimum value" in error_msg.lower():
                                detail = f"\n[原因] 注文額が$10未満です\n[対策] サイズを増やすか、価格の高い通貨を選んでください"
                            elif "insufficient margin" in error_msg.lower():
                                detail = f"\n[原因] 証拠金不足です\n[対策] ポジションを減らすか、レバレッジを下げてください"
                            
                            return {
                                'success': False,
                                'error': error_msg,
                                'message': f"指値注文エラー: {error_msg}{detail}"
                            }
                        
                        # 注文受付チェック
                        if 'resting' in first_status:
                            # 指値注文が待機中（通常のケース）
                            resting_info = first_status['resting']
                            oid = resting_info.get('oid', 'unknown')
                            
                            message = f"指値注文が発注されました: {symbol} {'買い' if is_buy else '売り'} " \
                                     f"{size} @ ${limit_price:.4f} (注文ID: {oid})"
                            
                            return {
                                'success': True,
                                'result': order_result,
                                'message': message,
                                'order_id': oid
                            }
                        
                        # 指値注文が即座に約定した場合
                        if 'filled' in first_status:
                            filled_info = first_status['filled']
                            filled_size = float(filled_info.get('totalSz', size))
                            filled_price = float(filled_info.get('avgPx', limit_price))
                            
                            message = f"指値注文が即座に約定しました: {symbol} {'買い' if is_buy else '売り'} " \
                                     f"{filled_size} @ ${filled_price:.4f}"
                            
                            return {
                                'success': True,
                                'result': order_result,
                                'message': message,
                                'filled_price': filled_price
                            }
            
            # ここに到達した場合は情報不足
            return {
                'success': False,
                'error': 'No order info',
                'message': f"指値注文失敗: 注文情報が確認できません ({order_result})"
            }
            
        except Exception as e:
            error_msg = f"指値注文エラー: {e}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def place_market_order(self, symbol: str, is_buy: bool, size: float) -> Dict:
        """成行注文を送信（高優先度）"""
        try:
            action = '買い' if is_buy else '売り'
            print(f"[注文] {symbol} {action} サイズ={size}")
            
            # 成行注文を送信（高優先度、レートリミッターはバイパス可能）
            order_result = self._with_retry(
                "market_open",
                lambda: self.exchange.market_open(
                    name=symbol,
                    is_buy=is_buy,
                    sz=size,
                    slippage=0.05
                ),
                priority=RequestPriority.HIGH,
                max_retries=3  # 注文は少ないリトライ回数で
            )
            
            # デバッグログ（詳細）
            # print(f"[API応答] {order_result}")
            # if isinstance(order_result, dict):
            #     print(f"[API応答キー] {order_result.keys()}")
            
            # 注文結果を検証
            if not order_result:
                return {
                    'success': False,
                    'error': 'Empty response',
                    'message': '注文結果が空です'
                }
            
            # レスポンスの構造を確認
            if isinstance(order_result, dict):
                # エラーレスポンスをチェック
                if 'error' in order_result or 'status' in order_result:
                    status = order_result.get('status', '')
                    if status == 'err' or 'error' in order_result:
                        error_msg = order_result.get('response', order_result.get('error', 'Unknown error'))
                        return {
                            'success': False,
                            'error': error_msg,
                            'message': f"注文エラー: {error_msg}"
                        }
                    elif status == 'ok':
                        # 成功
                        return {
                            'success': True,
                            'result': order_result,
                            'message': f"注文が約定しました: {symbol} {'買い' if is_buy else '売り'} {size}"
                        }
                
                # responseの中のstatusesをチェック
                response = order_result.get('response', {})
                if isinstance(response, dict) and 'data' in response:
                    data = response.get('data', {})
                    statuses = data.get('statuses', [])
                    if statuses and len(statuses) > 0:
                        first_status = statuses[0]
                        
                        # エラーチェック（最優先）
                        if 'error' in first_status:
                            error_msg = first_status['error']
                            
                            # エラーの詳細説明を追加
                            detail = ""
                            if "open interest is at cap" in error_msg.lower():
                                detail = f"\n[原因] {symbol}のオープンインタレストが上限に達しています\n[対策] 別の通貨ペアを試すか、時間をおいて再試行してください"
                            elif "minimum value" in error_msg.lower():
                                detail = f"\n[原因] 注文額が最低額（$10）未満です\n[対策] サイズを増やしてください"
                            elif "insufficient margin" in error_msg.lower():
                                detail = f"\n[原因] 証拠金不足です\n[対策] ポジションを決済するか、サイズを減らしてください"
                            elif "trading is halted" in error_msg.lower():
                                detail = f"\n[原因] {symbol}の取引が停止中です\n[対策] 別の通貨ペアを試してください"
                            
                            print(f"[エラー] {error_msg}{detail}")
                            
                            return {
                                'success': False,
                                'error': error_msg,
                                'message': f"注文エラー: {error_msg}{detail}"
                            }
                        
                        # 約定チェック
                        if 'filled' in first_status:
                            filled_info = first_status['filled']
                            filled_size = float(filled_info.get('totalSz', size))
                            filled_price = float(filled_info.get('avgPx', 0))
                            
                            # サイズが異なる場合は警告
                            if abs(filled_size - size) > 0.0001:
                                message = f"注文約定: {symbol} {'買い' if is_buy else '売り'} " \
                                         f"要求={size} → 実際={filled_size} (価格: ${filled_price:.4f})"
                                print(f"[警告] サイズ調整: 要求={size} → 実際={filled_size}")
                            else:
                                message = f"注文が約定しました: {symbol} {'買い' if is_buy else '売り'} " \
                                         f"{filled_size} @ ${filled_price:.4f}"
                            
                            print(f"[約定成功] {symbol} {action} サイズ={filled_size} 価格=${filled_price:.4f}")
                            
                            return {
                                'success': True,
                                'result': order_result,
                                'message': message,
                                'filled_size': filled_size,
                                'requested_size': size
                            }
            
            # ここに到達した場合は失敗とみなす（約定情報がない）
            return {
                'success': False,
                'error': 'No filled info',
                'message': f"注文失敗: 約定情報が確認できません ({order_result})"
            }
            
        except Exception as e:
            error_msg = f"注文エラー: {e}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def close_position(self, symbol: str) -> Dict:
        """ポジションを決済（全量）"""
        try:
            # 現在のポジションを取得
            positions = self.get_positions()
            position = None
            
            for pos in positions:
                if pos['coin'] == symbol:
                    position = pos
                    break
            
            if not position:
                return {
                    'success': False,
                    'message': f"{symbol}のポジションが見つかりません"
                }
            
            # ポジションサイズと方向を取得
            size = abs(position['size'])
            is_buy = position['size'] < 0  # ショートポジションの場合は買いで決済
            
            # 決済注文を送信
            result = self.place_market_order(symbol, is_buy, size)
            
            if result['success']:
                result['message'] = f"{symbol}のポジションを決済しました（全量: {size}）"
            
            return result
            
        except Exception as e:
            error_msg = f"決済エラー: {e}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def close_position_partial(self, symbol: str, close_size: float) -> Dict:
        """ポジションを一部決済"""
        try:
            # 現在のポジションを取得
            positions = self.get_positions()
            position = None
            
            for pos in positions:
                if pos['coin'] == symbol:
                    position = pos
                    break
            
            if not position:
                return {
                    'success': False,
                    'message': f"{symbol}のポジションが見つかりません"
                }
            
            # ポジションサイズと方向を取得
            current_size = abs(position['size'])
            is_buy = position['size'] < 0  # ショートポジションの場合は買いで決済
            
            # サイズチェック
            if close_size > current_size:
                return {
                    'success': False,
                    'message': f"決済サイズ({close_size})が現在のポジション({current_size})を超えています"
                }
            
            # 決済注文を送信
            result = self.place_market_order(symbol, is_buy, close_size)
            
            if result['success']:
                remaining = current_size - close_size
                result['message'] = f"{symbol}の一部決済完了（決済: {close_size}, 残り: {remaining:.4f}）"
            
            return result
            
        except Exception as e:
            error_msg = f"一部決済エラー: {e}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def close_all_positions(self) -> Dict:
        """すべてのポジションを一括決済（並列処理で高速化）"""
        import concurrent.futures
        
        try:
            positions = self.get_positions()
            
            if not positions:
                return {
                    'success': False,
                    'message': "決済するポジションがありません"
                }
            
            print(f"全決済開始: {len(positions)}個のポジション（並列処理）")
            
            success_count = 0
            failed_count = 0
            errors = []
            
            # 並列処理で全ポジションを同時に決済
            def close_single_position(position):
                symbol = position['coin']
                size = abs(position['size'])
                is_buy = position['size'] < 0
                
                print(f"決済中: {symbol} {'買い' if is_buy else '売り'} {size}")
                
                result = self.place_market_order(symbol, is_buy, size)
                
                if result['success']:
                    print(f"[OK] {symbol} 決済成功")
                else:
                    print(f"[NG] {symbol} 決済失敗: {result.get('error', 'Unknown')}")
                
                return (symbol, result)
            
            # ThreadPoolExecutorで並列実行（最大10スレッド）
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(close_single_position, pos) for pos in positions]
                
                for future in concurrent.futures.as_completed(futures):
                    symbol, result = future.result()
                    if result['success']:
                        success_count += 1
                    else:
                        failed_count += 1
                        errors.append(f"{symbol}: {result.get('error', 'Unknown error')}")
            
            if failed_count == 0:
                return {
                    'success': True,
                    'message': f"全ポジション決済完了 ({success_count}個)"
                }
            elif success_count == 0:
                return {
                    'success': False,
                    'message': f"全ポジション決済失敗\n{', '.join(errors)}"
                }
            else:
                return {
                    'success': True,
                    'message': f"一部決済完了 (成功: {success_count}, 失敗: {failed_count})"
                }
        
        except Exception as e:
            error_msg = f"全決済エラー: {e}"
            print(error_msg)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    async def start_websocket(self, symbols: List[str], callback: Callable):
        """WebSocketで価格をリアルタイム取得"""
        self._price_callback = callback
        ws_url = Config.get_ws_url()
        reconnect_count = 0
        
        while True:
            try:
                async with websockets.connect(ws_url) as websocket:
                    # 購読メッセージを送信
                    subscribe_msg = {
                        "method": "subscribe",
                        "subscription": {
                            "type": "allMids"
                        }
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    print("WebSocket接続成功")
                    reconnect_count = 0  # 接続成功時にカウントをリセット
                    
                    # メッセージを受信
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            if data.get('channel') == 'allMids' and 'data' in data:
                                mids = data['data'].get('mids', {})
                                
                                # コールバックを呼び出し
                                if self._price_callback and mids:
                                    self._price_callback(mids)
                        except json.JSONDecodeError:
                            print("警告: WebSocketメッセージのJSON解析に失敗しました")
                            continue
                
            except websockets.exceptions.ConnectionClosedError:
                reconnect_count += 1
                print(f"WebSocket接続が切断されました（試行 {reconnect_count}回目）")
            except websockets.exceptions.ConnectionClosedOK:
                print("WebSocket接続が正常に終了しました")
                break
            except websockets.exceptions.InvalidStatusCode as e:
                reconnect_count += 1
                print(f"WebSocket接続エラー: 無効なステータスコード（{e.status_code}）")
            except OSError as e:
                reconnect_count += 1
                print(f"ネットワークエラー: 接続できません")
            except Exception as e:
                reconnect_count += 1
                print(f"WebSocket予期しないエラー: {type(e).__name__}")
                # デバッグモードの場合のみ詳細を表示
                # print(f"詳細: {e}")  # 本番環境では無効化
            
            # 再接続の待機
            if reconnect_count <= 3:
                wait_time = Config.WS_RECONNECT_DELAY
            elif reconnect_count <= 10:
                wait_time = Config.WS_RECONNECT_DELAY * 2
            else:
                wait_time = Config.WS_RECONNECT_DELAY * 5
            
            print(f"{wait_time}秒後に再接続します...")
            await asyncio.sleep(wait_time)
    
    def start_price_stream(self, symbols: List[str], callback: Callable):
        """価格ストリームを開始（別スレッドで実行）"""
        import threading
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_websocket(symbols, callback))
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

