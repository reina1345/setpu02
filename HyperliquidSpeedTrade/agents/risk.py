"""
リスク管理エージェント（デモ）

機能:
- 1トレードの名目額上限
- 連続損失による一時停止（サーキットブレーカー）
"""
from __future__ import annotations

import time
from typing import Optional

from .base import Agent, Message, Publisher


class RiskAgent:
    name = "risk_manager"

    def __init__(
        self,
        max_notional_per_trade_usd: float = 200.0,
        max_consecutive_losses: int = 3,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self.max_notional = max_notional_per_trade_usd
        self.max_consecutive_losses = max_consecutive_losses
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_losses = 0
        self.blocked_until_ts: Optional[float] = None

    def on_start(self, bus: Publisher) -> None:
        return

    def on_message(self, message: Message, bus: Publisher) -> None:
        if message.topic == "strategy.signal":
            if self.blocked_until_ts and time.time() < self.blocked_until_ts:
                # ブロック中は破棄
                bus.publish(Message(
                    topic="risk.blocked",
                    payload={"reason": "cooldown", "until": self.blocked_until_ts},
                ))
                return

            symbol = message.payload["symbol"]
            price = float(message.payload["price"])
            size = float(message.payload["size"])
            notional = price * size

            if notional > self.max_notional:
                size = self.max_notional / max(price, 1e-9)

            bus.publish(Message(
                topic="risk.approved",
                payload={
                    "symbol": symbol,
                    "side": message.payload["side"],
                    "size": size,
                    "price": price,
                },
            ))

        elif message.topic == "audit.pnL":
            # 実行結果の疑似PnLに基づき連敗カウント
            pnl = float(message.payload.get("pnl", 0.0))
            if pnl < 0:
                self.consecutive_losses += 1
                if self.consecutive_losses >= self.max_consecutive_losses:
                    self.blocked_until_ts = time.time() + self.cooldown_seconds
                    self.consecutive_losses = 0
                    bus.publish(Message(
                        topic="risk.blocked",
                        payload={"reason": "loss_streak", "until": self.blocked_until_ts},
                    ))
            else:
                self.consecutive_losses = 0

    def on_stop(self) -> None:
        return


