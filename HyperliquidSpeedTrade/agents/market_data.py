"""
市場データアダプタ（デモ用）

HYPE の疑似ティックを生成して配信する。
必要に応じて Hyperliquid の実データに差し替え可能。
"""
from __future__ import annotations

import math
import random
import time
from typing import Optional

from .base import Agent, Message, Publisher


class DemoMarketDataAgent:
    name = "market_data_demo"

    def __init__(self, symbol: str = "HYPE", base_price: float = 1.0, interval_ms: int = 250) -> None:
        self.symbol = symbol.upper()
        self.base_price = base_price
        self.interval_ms = interval_ms
        self._running = False
        self._t: float = 0.0
        self._last_ts: Optional[float] = None

    def on_start(self, bus: Publisher) -> None:
        self._running = True
        # デモではブロッキングにせず、呼び出し側ループから tick() を呼ぶ想定

    def on_message(self, message: Message, bus: Publisher) -> None:
        # 市場データは購読のみ（ここでは受信不要）
        return

    def on_stop(self) -> None:
        self._running = False

    def tick(self, bus: Publisher) -> None:
        if not self._running:
            return

        now = time.time()
        if self._last_ts and (now - self._last_ts) * 1000.0 < self.interval_ms:
            return
        self._last_ts = now

        # 疑似価格生成（サイン波 + ホワイトノイズ + ドリフト）
        self._t += 0.15
        drift = 0.0005
        price = max(0.0001, (self.base_price * (1.0 + drift * self._t)) * (1.0 + 0.01 * math.sin(self._t)) )
        price *= (1.0 + random.uniform(-0.0025, 0.0025))

        message = Message(
            topic="market.tick",
            payload={
                "symbol": self.symbol,
                "price": float(price),
                "ts": now,
            },
        )
        bus.publish(message)


