"""
シンプルなメッセージバス実装（同期型）
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List

from .base import Agent, Message, Publisher


class MessageBus(Publisher):
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Agent]] = defaultdict(list)
        self._started: bool = False

    def subscribe(self, topic: str, agent: Agent) -> None:
        self._subscribers[topic].append(agent)

    def publish(self, message: Message) -> None:
        # 対象トピックの購読者に配信
        for agent in list(self._subscribers.get(message.topic, [])):
            agent.on_message(message, self)

    def start(self, agents: List[Agent]) -> None:
        if self._started:
            return
        self._started = True
        for agent in agents:
            agent.on_start(self)

    def stop(self, agents: List[Agent]) -> None:
        if not self._started:
            return
        for agent in agents:
            agent.on_stop()
        self._started = False


