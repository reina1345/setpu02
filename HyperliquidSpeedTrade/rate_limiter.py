"""
レートリミッターモジュール
API呼び出し頻度を制限し、HTTP 429エラーを回避します
"""
import time
from collections import deque
from threading import Lock
from typing import Optional
from enum import Enum


class RequestPriority(Enum):
    """リクエストの優先度"""
    HIGH = 1  # 注文送信など、即座に実行が必要
    NORMAL = 2  # 通常の読み取り操作
    LOW = 3  # 定期更新など、待機可能


class RateLimiter:
    """トークンバケットアルゴリズムを使用したレートリミッター
    
    60秒あたりmax_calls回までリクエストを許可します。
    優先度に応じて待機時間を調整します。
    """
    
    def __init__(self, max_calls: int = 12, period: int = 60, priority_bypass: bool = True):
        """
        Args:
            max_calls: 期間内に許可される最大呼び出し数（デフォルト: 12）
            period: 期間（秒）（デフォルト: 60）
            priority_bypass: 高優先度リクエストは制限をバイパスするか（デフォルト: True）
        """
        self.max_calls = max_calls
        self.period = period
        self.priority_bypass = priority_bypass
        self.calls = deque()  # タイムスタンプのキュー
        self.lock = Lock()  # スレッドセーフのためのロック
        
    def wait_if_needed(self, priority: RequestPriority = RequestPriority.NORMAL) -> float:
        """
        必要に応じて待機してからリクエストを許可
        
        Args:
            priority: リクエストの優先度
            
        Returns:
            float: 待機時間（秒）。待機しなかった場合は0
        """
        with self.lock:
            now = time.time()
            
            # 高優先度リクエストはバイパス可能
            if priority == RequestPriority.HIGH and self.priority_bypass:
                # ただし、制限を超えそうな場合は短い待機を推奨
                self._cleanup_old_calls(now)
                if len(self.calls) >= self.max_calls:
                    # 最古の呼び出しが期間を過ぎるまで待機（最大でも数秒）
                    oldest_call = self.calls[0]
                    wait_time = self.period - (now - oldest_call)
                    if wait_time > 0 and wait_time < 5:
                        # 5秒以内なら待機（それ以上は待たない）
                        time.sleep(wait_time)
                        now = time.time()
            
            # 古い呼び出しを削除（期間外になったもの）
            self._cleanup_old_calls(now)
            
            # 制限に達している場合は待機
            wait_time = 0.0
            if len(self.calls) >= self.max_calls:
                # 最古の呼び出しが期間を過ぎるまで待機
                oldest_call = self.calls[0]
                wait_time = self.period - (now - oldest_call)
                
                if wait_time > 0:
                    # 優先度に応じて待機時間を調整
                    if priority == RequestPriority.HIGH:
                        # 高優先度は待機しない（既にバイパス処理済み）
                        pass
                    elif priority == RequestPriority.LOW:
                        # 低優先度は少し余裕を持って待機
                        wait_time = max(wait_time, 1.0)
                    
                    time.sleep(wait_time)
                    now = time.time()
                    # 再度クリーンアップ（待機中に古い呼び出しが追加された可能性）
                    self._cleanup_old_calls(now)
            
            # 呼び出しを記録
            self.calls.append(now)
            
            return wait_time
    
    def _cleanup_old_calls(self, now: float):
        """期間外になった古い呼び出しを削除"""
        cutoff_time = now - self.period
        while self.calls and self.calls[0] < cutoff_time:
            self.calls.popleft()
    
    def get_current_calls(self) -> int:
        """現在の期間内の呼び出し数を取得"""
        with self.lock:
            self._cleanup_old_calls(time.time())
            return len(self.calls)
    
    def get_remaining_calls(self) -> int:
        """残りの呼び出し可能数を取得"""
        return max(0, self.max_calls - self.get_current_calls())
    
    def reset(self):
        """呼び出し履歴をリセット"""
        with self.lock:
            self.calls.clear()


# グローバルインスタンス（モジュールレベル）
# 各API操作で共有される
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_calls: int = 12, period: int = 60, priority_bypass: bool = True) -> RateLimiter:
    """
    グローバルレートリミッターを取得（シングルトン）
    
    Args:
        max_calls: 期間内に許可される最大呼び出し数
        period: 期間（秒）
        priority_bypass: 高優先度リクエストは制限をバイパスするか
        
    Returns:
        RateLimiter: グローバルレートリミッターインスタンス
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(max_calls, period, priority_bypass)
    return _global_rate_limiter


def set_rate_limiter(limiter: RateLimiter):
    """グローバルレートリミッターを設定（テスト用）"""
    global _global_rate_limiter
    _global_rate_limiter = limiter

