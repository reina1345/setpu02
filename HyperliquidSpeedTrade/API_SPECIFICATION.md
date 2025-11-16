# 📚 HyperliquidAPI 仕様書

**最終更新**: 2025年1月  
**バージョン**: 1.0

---

## 📋 目次

1. [クラス概要](#クラス概要)
2. [初期化・接続管理](#初期化接続管理)
3. [価格取得](#価格取得)
4. [通貨ペア情報](#通貨ペア情報)
5. [アカウント情報](#アカウント情報)
6. [ポジション管理](#ポジション管理)
7. [注文管理](#注文管理)
8. [WebSocketストリーム](#websocketストリーム)
9. [エラーハンドリング](#エラーハンドリング)
10. [戻り値の形式](#戻り値の形式)

---

## 🏗️ クラス概要

```python
class HyperliquidAPI:
    """Hyperliquid APIクライアントクラス"""
```

Hyperliquid取引所のAPIと通信するためのラッパークラス。以下の機能を提供：
- 価格情報の取得
- 注文の送信（成行・指値）
- ポジション管理
- アカウント情報の取得
- リアルタイム価格ストリーム

---

## 🔧 初期化・接続管理

### `__init__()`
**概要**: クラスの初期化

**引数**: なし

**戻り値**: なし

**使用例**:
```python
api = HyperliquidAPI()
```

---

### `initialize() -> bool`
**概要**: APIクライアントを初期化し、接続を確立

**引数**: なし

**戻り値**: 
- `True`: 初期化成功
- `False`: 初期化失敗

**処理内容**:
1. 設定の検証（`Config.validate()`）
2. アカウントの設定（秘密鍵からアカウント生成）
3. Infoクライアントの初期化（読み取り専用）
4. Exchangeクライアントの初期化（取引用）

**エラー**: 例外発生時は`False`を返し、エラーメッセージを出力

**使用例**:
```python
if api.initialize():
    print("初期化成功")
else:
    print("初期化失敗")
```

---

### `is_connected() -> bool`
**概要**: 接続状態を確認

**引数**: なし

**戻り値**: 
- `True`: 接続中
- `False`: 未接続

**使用例**:
```python
if api.is_connected():
    positions = api.get_positions()
```

---

## 💰 価格取得

### `get_price(symbol: str = "BTC") -> Optional[float]`
**概要**: 指定した通貨ペアの現在価格を取得

**引数**:
- `symbol` (str): 通貨ペア（例: "BTC", "ETH"）。デフォルトは"BTC"

**戻り値**:
- `float`: 価格（成功時）
- `None`: エラー時または通貨ペアが見つからない場合

**使用例**:
```python
btc_price = api.get_price("BTC")
if btc_price:
    print(f"BTC価格: ${btc_price}")
```

**注意**: 
- 全マーケット情報を取得してから検索するため、頻繁な呼び出しは避ける
- リアルタイム価格は`start_price_stream()`を使用することを推奨

---

## 📊 通貨ペア情報

### `get_symbols_by_volume() -> List[str]`
**概要**: 24時間出来高順にソートされた通貨ペアリストを取得

**引数**: なし

**戻り値**: 
- `List[str]`: 出来高順にソートされた通貨ペアのリスト
- エラー時は`Config.AVAILABLE_SYMBOLS`（デフォルトリスト）を返す

**処理内容**:
1. `meta_and_asset_ctxs`から全通貨ペア情報を取得
2. `meta['universe']`から通貨名を取得
3. `asset_ctxs`から24時間出来高（`dayNtlVlm`）を取得
4. 出来高が大きい順にソート
5. 上位10通貨の情報をコンソールに出力

**戻り値の例**:
```python
['BTC', 'VIRTUAL', 'ASTER', 'BNB', 'DOOD', ...]  # 出来高順
```

**使用例**:
```python
symbols = api.get_symbols_by_volume()
print(f"取得した通貨ペア数: {len(symbols)}")
# 出力例: [INFO] 出来高順通貨ペア（上位10つ）:
#          1. BTC: $4,070,892
#          2. VIRTUAL: $2,122,599
#          ...
```

**注意**: 
- API呼び出し失敗時はデフォルトリストを返す
- 通常は197個程度の通貨ペアを取得

---

## 👤 アカウント情報

### `get_account_state() -> Optional[Dict]`
**概要**: アカウントの完全な状態を取得

**引数**: なし

**戻り値**: 
- `Dict`: アカウント状態の辞書（`user_state`の生データ）
- `None`: エラー時

**使用例**:
```python
state = api.get_account_state()
if state:
    positions = state.get('assetPositions', [])
```

**注意**: 低レベルAPI。通常は`get_account_info()`や`get_positions()`を使用推奨

---

### `get_account_leverage() -> Optional[float]`
**概要**: アカウント全体のレバレッジを計算

**引数**: なし

**戻り値**: 
- `float`: レバレッジ（例: 2.5 = 2.5倍）
- `0.0`: レバレッジが0の場合
- `None`: エラー時

**計算式**:
```python
leverage = total_ntl_pos / account_value
```

**使用例**:
```python
leverage = api.get_account_leverage()
if leverage is not None:
    print(f"現在のレバレッジ: {leverage}x")
```

---

### `get_account_info() -> Optional[Dict]`
**概要**: アカウント情報（Equity、Spot、Perps）を取得

**引数**: なし

**戻り値**: 
```python
{
    'equity': float,   # Total Equity（Spot + Perps）
    'spot': float,     # Spot残高（現在は常に0.0）
    'perps': float     # Perps証拠金（accountValue）
}
```
または `None`（エラー時）

**使用例**:
```python
info = api.get_account_info()
if info:
    print(f"Equity: ${info['equity']}")
    print(f"Perps: ${info['perps']}")
```

**注意**: 
- Spot残高は現在常に0.0（HyperliquidではSpot取引は別システム）
- 将来的にSpot残高APIが追加されれば対応予定

---

## 📈 ポジション管理

### `get_positions() -> List[Dict]`
**概要**: 現在のポジション一覧を取得

**引数**: なし

**戻り値**: 
```python
[
    {
        'coin': str,              # 通貨ペア（例: "BTC"）
        'size': float,            # ポジションサイズ（正=ロング、負=ショート）
        'entry_price': float,     # エントリー価格
        'unrealized_pnl': float, # 未実現損益
        'leverage': dict          # レバレッジ情報
    },
    ...
]
```

**ポジションサイズの意味**:
- `size > 0`: ロングポジション
- `size < 0`: ショートポジション
- `size == 0`: ポジションなし（リストに含まれない）

**使用例**:
```python
positions = api.get_positions()
for pos in positions:
    side = "ロング" if pos['size'] > 0 else "ショート"
    print(f"{pos['coin']}: {side} {abs(pos['size'])} @ ${pos['entry_price']}")
```

**更新頻度**: 5秒ごとに自動更新（`main.py`で設定）

---

### `close_position(symbol: str) -> Dict`
**概要**: 指定した通貨ペアのポジションを全量決済

**引数**:
- `symbol` (str): 決済する通貨ペア（例: "BTC"）

**戻り値**: [標準的な戻り値形式](#戻り値の形式)を参照

**処理内容**:
1. 現在のポジションを取得
2. 指定シンボルのポジションを検索
3. ポジションサイズと方向を取得
4. 成行注文で決済（ショートは買い、ロングは売りで決済）

**使用例**:
```python
result = api.close_position("BTC")
if result['success']:
    print(result['message'])
```

**エラーケース**:
- ポジションが見つからない場合: `success=False`

---

### `close_position_partial(symbol: str, close_size: float) -> Dict`
**概要**: 指定した通貨ペアのポジションを一部決済

**引数**:
- `symbol` (str): 決済する通貨ペア
- `close_size` (float): 決済するサイズ

**戻り値**: [標準的な戻り値形式](#戻り値の形式)を参照

**処理内容**:
1. 現在のポジションを取得
2. 指定シンボルのポジションを検索
3. サイズを検証（ポジションサイズを超えないか）
4. 成行注文で一部決済

**使用例**:
```python
result = api.close_position_partial("BTC", 0.5)
if result['success']:
    print(result['message'])  # 例: "BTCの一部決済完了（決済: 0.5, 残り: 0.3）"
```

**エラーケース**:
- ポジションが見つからない場合
- 決済サイズがポジションサイズを超える場合

**注意**: 決済額は最低$10以上である必要がある

---

### `close_all_positions() -> Dict`
**概要**: すべてのポジションを一括決済（並列処理で高速化）

**引数**: なし

**戻り値**: [標準的な戻り値形式](#戻り値の形式)を参照

**処理内容**:
1. すべてのポジションを取得
2. `ThreadPoolExecutor`を使用して並列に決済（最大10スレッド）
3. 成功・失敗数をカウント

**戻り値の例**:
```python
# すべて成功
{
    'success': True,
    'message': '全ポジション決済完了 (5個)'
}

# 一部失敗
{
    'success': True,
    'message': '一部決済完了 (成功: 4, 失敗: 1)'
}

# すべて失敗
{
    'success': False,
    'message': '全ポジション決済失敗\nBTC: insufficient margin'
}
```

**使用例**:
```python
result = api.close_all_positions()
print(result['message'])
```

**注意**: 
- 並列処理のため高速だが、APIレートリミットに注意
- 各決済は独立して実行されるため、一部が失敗しても他の決済は継続

---

## 📝 注文管理

### `place_market_order(symbol: str, is_buy: bool, size: float) -> Dict`
**概要**: 成行注文を送信（即座に約定）

**引数**:
- `symbol` (str): 通貨ペア（例: "BTC"）
- `is_buy` (bool): `True`=買い、`False`=売り
- `size` (float): 注文サイズ

**戻り値**: [標準的な戻り値形式](#戻り値の形式)を参照

**成功時の戻り値**:
```python
{
    'success': True,
    'result': dict,              # APIレスポンスの生データ
    'message': str,             # 約定メッセージ
    'filled_size': float,       # 実際に約定したサイズ
    'requested_size': float     # 要求したサイズ
}
```

**エラー時の戻り値**:
```python
{
    'success': False,
    'error': str,               # エラーメッセージ
    'message': str              # 詳細なエラーメッセージ（原因・対策含む）
}
```

**処理内容**:
1. 成行注文を送信（スリッページ許容5%）
2. APIレスポンスを解析
3. 約定情報を確認（`filled`ステータス）
4. サイズが異なる場合は警告

**使用例**:
```python
result = api.place_market_order("BTC", True, 0.01)
if result['success']:
    print(f"約定: {result['filled_size']} @ ${result.get('filled_price', 0)}")
else:
    print(f"エラー: {result['error']}")
```

**エラーケース**:
- オープンインタレスト上限到達
- 最低注文額（$10）未満
- 証拠金不足
- 取引停止中

**注意**: 
- 成行注文は即座に約定するため、未約定注文リストには表示されない
- サイズが調整される場合がある（`filled_size != requested_size`）

---

### `place_limit_order(symbol: str, is_buy: bool, size: float, limit_price: float) -> Dict`
**概要**: 指値注文を送信（Good Till Cancel = キャンセルされるまで有効）

**引数**:
- `symbol` (str): 通貨ペア
- `is_buy` (bool): `True`=買い、`False`=売り
- `size` (float): 注文サイズ
- `limit_price` (float): 指値価格

**戻り値**: [標準的な戻り値形式](#戻り値の形式)を参照

**成功時の戻り値（待機中）**:
```python
{
    'success': True,
    'result': dict,              # APIレスポンスの生データ
    'message': str,              # 発注メッセージ
    'order_id': int              # 注文ID（キャンセル時に使用）
}
```

**成功時の戻り値（即座に約定）**:
```python
{
    'success': True,
    'result': dict,
    'message': str,              # 約定メッセージ
    'filled_price': float        # 約定価格
}
```

**エラー時の戻り値**:
```python
{
    'success': False,
    'error': str,                # エラーメッセージ
    'message': str               # 詳細なエラーメッセージ（原因・対策含む）
}
```

**処理内容**:
1. 指値注文を送信（Time In Force = "Gtc"）
2. APIレスポンスを解析
3. `resting`（待機中）または`filled`（即座に約定）を確認

**ステータスの意味**:
- `resting`: 注文がオーダーブックに登録され、待機中
- `filled`: 指値価格で即座に約定

**使用例**:
```python
result = api.place_limit_order("BTC", True, 0.01, 50000.0)
if result['success']:
    if 'order_id' in result:
        print(f"注文発注: ID={result['order_id']}")
    else:
        print(f"即座に約定: ${result['filled_price']}")
```

**エラーケース**: `place_market_order`と同じ

**注意**: 
- 指値注文は未約定注文リストに表示される（`resting`の場合）
- 即座に約定した場合（`filled`）は未約定注文リストには表示されない

---

### `get_open_orders() -> List[Dict]`
**概要**: 未約定注文（オープンオーダー）の一覧を取得

**引数**: なし

**戻り値**: 
```python
[
    {
        'coin': str,           # 通貨ペア
        'side': str,           # 'B' (buy) or 'A' (ask/sell)
        'is_buy': bool,        # True=買い、False=売り
        'limit_price': float,  # 指値価格
        'size': float,         # 注文サイズ
        'order_id': int,       # 注文ID（キャンセル時に使用）
        'timestamp': int       # タイムスタンプ
    },
    ...
]
```

**使用例**:
```python
orders = api.get_open_orders()
for order in orders:
    side = "買い" if order['is_buy'] else "売り"
    print(f"{order['coin']} {side} {order['size']} @ ${order['limit_price']} (ID: {order['order_id']})")
```

**エラーケース**:
- HTTP 429 (Rate Limiting): 警告メッセージを出力し、空リストを返す
- その他のエラー: エラーメッセージを出力し、空リストを返す

**注意**: 
- 更新頻度は10秒ごと（APIレートリミット対策）
- 成行注文は含まれない（即座に約定するため）

---

### `cancel_order(symbol: str, order_id: int) -> Dict`
**概要**: 指定した注文をキャンセル

**引数**:
- `symbol` (str): 通貨ペア
- `order_id` (int): キャンセルする注文のID

**戻り値**: [標準的な戻り値形式](#戻り値の形式)を参照

**成功時の戻り値**:
```python
{
    'success': True,
    'message': str  # 例: "注文をキャンセルしました: BTC (ID: 12345)"
}
```

**エラー時の戻り値**:
```python
{
    'success': False,
    'error': str,    # エラーメッセージ
    'message': str   # 詳細なエラーメッセージ
}
```

**使用例**:
```python
result = api.cancel_order("BTC", 12345)
if result['success']:
    print(result['message'])
```

**注意**: 
- 注文IDは`get_open_orders()`で取得
- キャンセル後、1秒待ってから`get_open_orders()`を呼び出すことを推奨

---

## 🔴 WebSocketストリーム

### `start_price_stream(symbols: List[str], callback: Callable)`
**概要**: リアルタイム価格ストリームを開始（別スレッドで実行）

**引数**:
- `symbols` (List[str]): 購読する通貨ペアのリスト（実際には`allMids`を購読するため、すべての通貨ペアの価格が取得される）
- `callback` (Callable): 価格更新時に呼び出されるコールバック関数

**戻り値**: なし

**コールバック関数の形式**:
```python
def on_price_update(prices: dict):
    """
    Args:
        prices: {symbol: price} の辞書
            例: {'BTC': 50000.0, 'ETH': 3000.0, ...}
    """
    for symbol, price in prices.items():
        print(f"{symbol}: ${price}")
```

**処理内容**:
1. 別スレッドで非同期WebSocket接続を開始
2. `allMids`チャンネルを購読
3. 価格更新時にコールバック関数を呼び出し
4. 接続が切れた場合は自動再接続

**使用例**:
```python
def price_callback(prices):
    if 'BTC' in prices:
        print(f"BTC価格更新: ${prices['BTC']}")

api.start_price_stream(['BTC', 'ETH'], price_callback)
```

**再接続ロジック**:
- 3回まで: 5秒待機
- 4〜10回: 10秒待機
- 11回以降: 25秒待機

**エラーケース**:
- `ConnectionClosedError`: 接続が切断された
- `ConnectionClosedOK`: 正常に終了
- `InvalidStatusCode`: 無効なステータスコード
- `OSError`: ネットワークエラー

**注意**: 
- デーモンスレッドで実行されるため、メインプロセスが終了すると自動停止
- すべての通貨ペアの価格が取得される（`allMids`を購読）

---

## ⚠️ エラーハンドリング

### エラーレスポンスの形式

すべてのメソッドは統一されたエラーレスポンス形式を使用：

```python
{
    'success': False,
    'error': str,      # エラーメッセージ（英語）
    'message': str     # 詳細なエラーメッセージ（日本語、原因・対策含む）
}
```

### よくあるエラーと対策

| エラーメッセージ | 原因 | 対策 |
|----------------|------|------|
| `open interest is at cap` | オープンインタレスト上限到達 | 別の通貨ペアを試すか、時間をおいて再試行 |
| `minimum value` | 注文額が$10未満 | サイズを増やすか、価格の高い通貨を選ぶ |
| `insufficient margin` | 証拠金不足 | ポジションを決済するか、サイズを減らす |
| `trading is halted` | 取引停止中 | 別の通貨ペアを試す |
| HTTP 429 | APIレートリミット | 15秒待機してから再試行 |

### レートリミット対策

- **ポジション更新**: 5秒ごと
- **未約定注文取得**: 10秒ごと（5秒ごとの更新の2回に1回）
- **エラー時の待機**: HTTP 429エラー検出時に警告を表示

---

## 📦 戻り値の形式

### 成功時の標準形式

```python
{
    'success': True,
    'result': dict,        # APIレスポンスの生データ（オプション）
    'message': str        # 成功メッセージ（日本語）
}
```

### 注文固有のフィールド

**成行注文**:
```python
{
    'success': True,
    'filled_size': float,      # 実際に約定したサイズ
    'requested_size': float    # 要求したサイズ
}
```

**指値注文（待機中）**:
```python
{
    'success': True,
    'order_id': int           # 注文ID
}
```

**指値注文（即座に約定）**:
```python
{
    'success': True,
    'filled_price': float      # 約定価格
}
```

---

## 🔗 使用例（統合）

```python
from hyperliquid_api import HyperliquidAPI

# 初期化
api = HyperliquidAPI()
if not api.initialize():
    print("初期化失敗")
    exit(1)

# 価格ストリーム開始
def on_price_update(prices):
    if 'BTC' in prices:
        print(f"BTC: ${prices['BTC']}")

api.start_price_stream(['BTC'], on_price_update)

# 成行注文
result = api.place_market_order("BTC", True, 0.01)
if result['success']:
    print(f"約定: {result['message']}")

# 指値注文
result = api.place_limit_order("BTC", True, 0.01, 50000.0)
if result['success']:
    if 'order_id' in result:
        order_id = result['order_id']
        print(f"注文発注: ID={order_id}")
        
        # 後でキャンセル
        cancel_result = api.cancel_order("BTC", order_id)
        if cancel_result['success']:
            print("キャンセル成功")

# ポジション確認
positions = api.get_positions()
for pos in positions:
    print(f"{pos['coin']}: {pos['size']} @ ${pos['entry_price']}")

# 一部決済
if positions:
    result = api.close_position_partial(positions[0]['coin'], 0.5)
    print(result['message'])

# 全決済
result = api.close_all_positions()
print(result['message'])

# アカウント情報
info = api.get_account_info()
if info:
    print(f"Equity: ${info['equity']}")

leverage = api.get_account_leverage()
if leverage is not None:
    print(f"Leverage: {leverage}x")
```

---

## 📝 注意事項

1. **APIレートリミット**: 
   - 頻繁なAPI呼び出しは避ける
   - 未約定注文取得は10秒ごとに制限

2. **最小注文額**: 
   - すべての注文は$10以上である必要がある

3. **スレッドセーフ**: 
   - メソッドはスレッドセーフではない
   - 複数スレッドから呼び出す場合はロックが必要

4. **エラーハンドリング**: 
   - すべてのメソッドは例外をキャッチして処理
   - エラー時は`None`または空リストを返す

5. **WebSocket接続**: 
   - 切断時は自動再接続
   - コールバック関数は別スレッドから呼び出される

---

**仕様書バージョン**: 1.0  
**最終更新**: 2025年1月

