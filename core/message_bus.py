"""Message bus for inter-agent communication."""

import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"
    BROADCAST = "broadcast"


@dataclass
class Message:
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    msg_type: MessageType = MessageType.BROADCAST
    sender: str = ""
    receiver: str = ""  # empty = broadcast
    content: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # higher = more urgent


class MessageBus:
    """Thread-safe message bus for agent communication."""

    def __init__(self):
        self._lock = threading.Lock()
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)
        self._message_history: list[Message] = []
        self._max_history = 1000

    def subscribe(self, agent_id: str, callback: Callable[[Message], None]):
        """Register an agent to receive messages."""
        with self._lock:
            self._subscriptions[agent_id].append(callback)

    def unsubscribe(self, agent_id: str, callback: Callable[[Message], None]):
        with self._lock:
            if callback in self._subscriptions[agent_id]:
                self._subscriptions[agent_id].remove(callback)

    def send(self, message: Message):
        """Send a message to one or all agents."""
        with self._lock:
            message.timestamp = time.time()
            self._message_history.append(message)
            if len(self._message_history) > self._max_history:
                self._message_history = self._message_history[-self._max_history:]

            target = message.receiver
            if target:
                for cb in self._subscriptions.get(target, []):
                    threading.Thread(target=cb, args=(message,), daemon=True).start()
            else:
                for agent_id, callbacks in self._subscriptions.items():
                    if agent_id != message.sender:
                        for cb in callbacks:
                            threading.Thread(target=cb, args=(message,), daemon=True).start()

    def send_direct(self, sender: str, receiver: str, content: dict,
                    msg_type: MessageType = MessageType.TASK, priority: int = 0) -> Message:
        """Convenience: send a direct message."""
        msg = Message(
            msg_type=msg_type, sender=sender, receiver=receiver,
            content=content, priority=priority,
        )
        self.send(msg)
        return msg

    def send_broadcast(self, sender: str, content: dict,
                       msg_type: MessageType = MessageType.BROADCAST) -> Message:
        """Convenience: broadcast a message."""
        msg = Message(
            msg_type=msg_type, sender=sender, content=content,
        )
        self.send(msg)
        return msg

    def get_history(self, agent_id: Optional[str] = None, limit: int = 50) -> list[Message]:
        with self._lock:
            msgs = self._message_history
            if agent_id:
                msgs = [m for m in msgs if m.receiver == agent_id or m.sender == agent_id or not m.receiver]
            return msgs[-limit:]

    def clear(self):
        with self._lock:
            self._message_history.clear()
