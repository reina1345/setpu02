"""
実行エージェント（ドライラン）

risk.approved を受け取り、実行ログを発行するだけ（約定シミュレーション）。
"""
from __future__ import annotations

import random
from typing import Optional

from .base import Agent, Message, Publisher


class DryRunExecutionAgent:
    name = "execution_dryrun"

    def __init__(self) -> None:
        self.position: float = 0.0  # HYPEの口数（+ロング/-ショート）
        self.avg_price: Optional[float] = None

    def on_start(self, bus: Publisher) -> None:
        return

    def on_message(self, message: Message, bus: Publisher) -> None:
        if message.topic != "risk.approved":
            return

        symbol = message.payload["symbol"]
        side = message.payload["side"]  # BUY/SELL
        size = float(message.payload["size"])
        price = float(message.payload["price"])

        slip_bp = random.uniform(-2.0, 2.0)  # ±2bp
        exec_price = price * (1.0 + slip_bp / 10000.0)

        delta = size if side == "BUY" else -size
        new_pos = self.position + delta

        if self.position == 0.0 or (self.position > 0) == (new_pos > 0):
            # 同方向への追加：加重平均
            if self.avg_price is None:
                self.avg_price = exec_price
            else:
                total_notional = abs(self.position) * self.avg_price + abs(delta) * exec_price
                total_size = abs(self.position) + abs(delta)
                self.avg_price = total_notional / max(total_size, 1e-9)
            self.position = new_pos
        else:
            # 反対売買：部分決済
            if abs(delta) >= abs(self.position):
                # 反転またはフラット
                self.position = new_pos
                self.avg_price = exec_price if self.position != 0 else None
            else:
                self.position = new_pos
                # 平均価格は変えない（残ポジションに対して）

        bus.publish(Message(
            topic="execution.filled",
            payload={
                "symbol": symbol,
                "side": side,
                "size": size,
                "price": exec_price,
                "position": self.position,
                "avg_price": self.avg_price,
            },
        ))

    def on_stop(self) -> None:
        return


