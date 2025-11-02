"""
監査/パフォーマンスログエージェント（デモ）

execution.filled を受け取り、簡易PnLを推定して配信。
"""
from __future__ import annotations

from typing import Optional

from .base import Agent, Message, Publisher


class AuditAgent:
    name = "audit_logger"

    def __init__(self) -> None:
        self.last_fill_price: Optional[float] = None
        self.cum_pnl: float = 0.0

    def on_start(self, bus: Publisher) -> None:
        return

    def on_message(self, message: Message, bus: Publisher) -> None:
        if message.topic != "execution.filled":
            return

        price = float(message.payload["price"])
        side = message.payload["side"]
        size = float(message.payload["size"])

        pnl = 0.0
        if self.last_fill_price is not None:
            if side == "SELL":
                pnl = (price - self.last_fill_price) * size
            else:
                pnl = (self.last_fill_price - price) * size

        self.last_fill_price = price
        self.cum_pnl += pnl

        # ログ配信
        bus.publish(Message(
            topic="audit.pnL",
            payload={"pnl": pnl, "cum_pnl": self.cum_pnl},
        ))

    def on_stop(self) -> None:
        return


