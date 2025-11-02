"""
エージェント基盤インターフェース

各エージェントは MessageBus 経由でメッセージを受信し、
必要に応じて新たなメッセージを発行する。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class Message:
    topic: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None


class Publisher(Protocol):
    def publish(self, message: Message) -> None:  # pragma: no cover
        ...


class Agent(Protocol):
    name: str

    def on_start(self, bus: Publisher) -> None:  # pragma: no cover
        ...

    def on_message(self, message: Message, bus: Publisher) -> None:  # pragma: no cover
        ...

    def on_stop(self) -> None:  # pragma: no cover
        ...


