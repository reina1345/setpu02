"""
マルチエージェント デモランナー（HYPE）

使い方:
  python agents_demo.py
"""
from __future__ import annotations

import time

from agents.base import Message
from agents.bus import MessageBus
from agents.market_data import DemoMarketDataAgent
from agents.strategy_scalper import ScalperAgent
from agents.risk import RiskAgent
from agents.execution import DryRunExecutionAgent
from agents.audit import AuditAgent


def main() -> None:
    bus = MessageBus()

    market = DemoMarketDataAgent(symbol="HYPE", base_price=1.0, interval_ms=200)
    strat = ScalperAgent(symbol="HYPE", short=5, long=20, size=50.0)
    risk = RiskAgent(max_notional_per_trade_usd=150.0, max_consecutive_losses=3, cooldown_seconds=10)
    exec_agent = DryRunExecutionAgent()
    audit = AuditAgent()

    agents = [market, strat, risk, exec_agent, audit]

    # サブスクライブ設定
    bus.subscribe("market.tick", strat)
    bus.subscribe("strategy.signal", risk)
    bus.subscribe("risk.approved", exec_agent)
    bus.subscribe("execution.filled", audit)
    bus.subscribe("audit.pnL", risk)

    # ログ用の簡易サブスクライバ（匿名）
    class Logger:
        name = "logger"
        def on_start(self, b):
            pass
        def on_message(self, m, b):
            if m.topic == "strategy.signal":
                print(f"[SIGNAL] {m.payload}")
            elif m.topic == "risk.approved":
                print(f"[RISK]   {m.payload}")
            elif m.topic == "execution.filled":
                print(f"[FILL]   {m.payload}")
            elif m.topic == "risk.blocked":
                print(f"[BLOCK]  {m.payload}")
            elif m.topic == "audit.pnL":
                print(f"[PNL]    {m.payload}")
        def on_stop(self):
            pass

    logger = Logger()
    bus.subscribe("strategy.signal", logger)
    bus.subscribe("risk.approved", logger)
    bus.subscribe("execution.filled", logger)
    bus.subscribe("risk.blocked", logger)
    bus.subscribe("audit.pnL", logger)

    bus.start(agents + [logger])

    print("--- Agents demo running for HYPE (Ctrl+C to stop) ---")
    try:
        while True:
            market.tick(bus)
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        bus.stop(agents + [logger])


if __name__ == "__main__":
    main()


