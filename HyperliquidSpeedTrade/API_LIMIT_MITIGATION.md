# 📌 API制限に対する対応策

## ❌ できないこと（Hyperliquid側の制限）

以下の制限は**Hyperliquid側のサーバーで設定されている**ため、こちらでは変更できません：

1. **APIレートリミット値**
   - 「12回/分」「6回/分」などの制限値
   - Hyperliquid側のサーバー設定

2. **HTTP 429エラーの発生条件**
   - どの頻度でエラーが発生するか
   - Hyperliquid側のレートリミッターの設定

3. **最小注文額（$10）**
   - 取引所のポリシー
   - Hyperliquid側のルール

4. **WebSocket接続数の制限**
   - 1アカウント1接続などの制限
   - Hyperliquid側のインフラ設定

---

## ✅ できること（対策の実装）

こちらで実装できる対策は以下の通りです：

### 1. レートリミット回避のための頻度制限

**現在の実装**:
```python
# main.py:296
time.sleep(5)  # ポジション更新を5秒ごとに制限

# main.py:300
include_orders=(update_count % 2 == 0)  # 未約定注文を10秒ごとに制限
```

**効果**:
- API呼び出し頻度を制限値以下に抑制
- HTTP 429エラーの発生を回避

---

### 2. HTTP 429エラーの検出と警告

**現在の実装**:
```python
# hyperliquid_api.py:271-273
if '429' in error_str:
    print("[警告] APIレートリミット: リクエストが多すぎます。15秒待機してください。")
```

**効果**:
- エラー発生時にユーザーに警告
- 手動で待機時間を調整可能

**改善の余地**:
- ⚠️ 自動リトライが未実装（手動対応が必要）

---

### 3. 更新頻度の調整（設定変更可能）

**実装場所**:
- `main.py:296` - ポジション更新間隔
- `main.py:300` - 未約定注文取得間隔
- `config.py:51` - WebSocket再接続遅延

**変更方法**:
```python
# より安全な設定（頻度を下げる）
time.sleep(10)  # 5秒 → 10秒に変更

# より頻繁な更新（リスクあり）
time.sleep(3)  # 5秒 → 3秒に変更（HTTP 429のリスク増加）
```

---

### 4. 自動リトライロジック（未実装）

**現在の状態**: ❌ 未実装

**実装可能な改善**:
```python
def get_open_orders_with_retry(self, max_retries=3, delay=15):
    """自動リトライ機能付きで未約定注文を取得"""
    for attempt in range(max_retries):
        try:
            return self.get_open_orders()
        except Exception as e:
            if '429' in str(e):
                if attempt < max_retries - 1:
                    print(f"[自動リトライ] {delay}秒後に再試行します（{attempt+1}/{max_retries}）")
                    time.sleep(delay)
                    continue
            raise
    return []
```

**効果**:
- HTTP 429エラー時に自動で待機して再試行
- ユーザー操作が不要

---

### 5. クライアント側レートリミッター（未実装）

**現在の状態**: ❌ 未実装

**実装可能な改善**:
```python
from collections import deque
import time

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls  # 例: 12
        self.period = period  # 例: 60秒
        self.calls = deque()
    
    def wait_if_needed(self):
        now = time.time()
        # 古い呼び出しを削除
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        
        # 制限に達している場合は待機
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.calls.append(time.time())

# 使用例
rate_limiter = RateLimiter(max_calls=12, period=60)  # 60秒に12回まで

def get_positions(self):
    rate_limiter.wait_if_needed()  # 自動で待機
    # ... API呼び出し ...
```

**効果**:
- クライアント側でレートリミットを強制
- HTTP 429エラーの発生を事前に防止

---

## 📊 現在の実装状況

| 対策 | 実装状況 | 効果 |
|------|---------|------|
| **頻度制限** | ✅ 実装済み | レートリミット回避 |
| **エラー検出** | ✅ 実装済み | 警告表示 |
| **自動リトライ** | ❌ 未実装 | 改善の余地あり |
| **クライアント側レートリミッター** | ❌ 未実装 | 改善の余地あり |

---

## 🎯 推奨される改善

### 優先度: 高

1. **自動リトライロジックの実装**
   - HTTP 429エラー時に自動で待機して再試行
   - ユーザー操作が不要になる

2. **クライアント側レートリミッターの実装**
   - 事前にレートリミットを回避
   - HTTP 429エラーの発生を減らす

### 優先度: 中

3. **設定ファイルでの調整可能化**
   - 更新頻度を設定ファイルで変更可能に
   - 環境に応じて最適化

### 優先度: 低

4. **リトライ回数・待機時間の設定可能化**
   - ユーザーが調整可能に

---

## 📝 まとめ

### ❌ できないこと
- **Hyperliquid側のAPI制限値の変更**
- **レートリミットそのものの解除**
- **最小注文額の変更**

### ✅ できること（現在実装済み）
- **頻度制限による回避**（5秒/10秒間隔）
- **エラー検出と警告表示**

### ✅ できること（改善の余地）
- **自動リトライロジック**
- **クライアント側レートリミッター**
- **設定ファイルでの調整可能化**

---

**結論**: API制限そのものは変更できませんが、**レートリミットを回避するための対策**は実装できます。現在は基本的な対策は実装済みですが、自動リトライやクライアント側レートリミッターを追加することで、より堅牢な実装になります。

