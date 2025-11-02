"""
簡易スキャルピング戦略エージェント

ルール（デモ用）:
- 移動平均(短期/長期)のゴールデンクロスで買い、デッドクロスで売り
- 同一方向のシグナルは抑制（連打防止）
"""
from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from .base import Agent, Message, Publisher


class ScalperAgent:
    name = "strategy_scalper"

    def __init__(self, symbol: str = "HYPE", short: int = 5, long: int = 20, size: float = 10.0) -> None:
        self.symbol = symbol.upper()
        self.short = short
        self.long = long
        self.size = size  # 名目サイズ（実行エージェントで口数換算）
        self.prices: Deque[float] = deque(maxlen=max(self.short, self.long))
        self.prev_signal: Optional[str] = None  # "BUY" | "SELL" | None

    def on_start(self, bus: Publisher) -> None:
        # 市場データ購読
        # 購読はバス側で管理しているので、ここでは説明用のコメントのみ
        return

    def on_message(self, message: Message, bus: Publisher) -> None:
        if message.topic != "market.tick":
            return
        if message.payload.get("symbol") != self.symbol:
            return

        price = float(message.payload["price"])
        self.prices.append(price)

        if len(self.prices) < max(self.short, self.long):
            return

        short_ma = sum(list(self.prices)[-self.short:]) / self.short
        long_ma = sum(list(self.prices)[-self.long:]) / self.long

        signal: Optional[str] = None
        if short_ma > long_ma and self.prev_signal != "BUY":
            signal = "BUY"
        elif short_ma < long_ma and self.prev_signal != "SELL":
            signal = "SELL"

        if signal:
            self.prev_signal = signal
            bus.publish(Message(
                topic="strategy.signal",
                payload={
                    "symbol": self.symbol,
                    "side": signal,
                    "size": self.size,
                    "price": price,
                },
            ))

    def on_stop(self) -> None:
        return


