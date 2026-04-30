"""Base Agent class that all agents inherit from."""

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from core.message_bus import Message, MessageBus, MessageType
from core.task_queue import Task, TaskQueue, TaskStatus

logger = logging.getLogger("agent")


class BaseAgent(ABC):
    """Abstract base for all agents in the system."""

    def __init__(self, agent_id: str, agent_type: str, message_bus: MessageBus,
                 task_queue: TaskQueue, config: Optional[dict] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.message_bus = message_bus
        self.task_queue = task_queue
        self.config = config or {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._state = "idle"  # idle, busy, waiting, error
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._started_at = 0.0

        # Subscribe to messages
        self.message_bus.subscribe(self.agent_id, self._on_message)

    def start(self):
        """Start the agent in a background thread."""
        self._running = True
        self._started_at = time.time()
        self._state = "waiting"
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name=self.agent_id)
        self._thread.start()
        logger.info(f"[{self.agent_id}] Agent started")

    def stop(self):
        """Stop the agent gracefully."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._state = "stopped"
        logger.info(f"[{self.agent_id}] Agent stopped (completed={self._tasks_completed}, failed={self._tasks_failed})")

    def _run_loop(self):
        """Main agent loop."""
        self.on_start()
        while self._running:
            try:
                task = self.task_queue.get(agent_type=self.agent_type, timeout=0.5)
                if task is None:
                    self.on_idle()
                    continue

                self._state = "busy"
                self.task_queue.mark_running(task.task_id)
                logger.info(f"[{self.agent_id}] Processing task: {task.name} ({task.task_id})")

                try:
                    result = self.execute(task)
                    self.task_queue.mark_completed(task.task_id, result)
                    self._tasks_completed += 1
                    self.on_task_completed(task, result)
                except Exception as e:
                    should_retry = self.task_queue.mark_failed(task.task_id, str(e))
                    self._tasks_failed += 1
                    self.on_task_failed(task, e)
                    if not should_retry:
                        logger.error(f"[{self.agent_id}] Task {task.task_id} failed permanently: {e}")
                    else:
                        logger.warning(f"[{self.agent_id}] Task {task.task_id} failed, will retry ({task.retries}/{task.max_retries})")

                self._state = "waiting"
            except Exception as e:
                logger.error(f"[{self.agent_id}] Unexpected error in run loop: {e}")
                self._state = "error"

        self.on_stop()

    def _on_message(self, message: Message):
        """Handle incoming messages."""
        self.on_message(message)

    def send_message(self, receiver: str, content: dict,
                     msg_type: MessageType = MessageType.TASK, priority: int = 0):
        """Send a message to another agent."""
        self.message_bus.send_direct(self.agent_id, receiver, content, msg_type, priority)

    def broadcast(self, content: dict, msg_type: MessageType = MessageType.BROADCAST):
        """Broadcast a message to all agents."""
        self.message_bus.send_broadcast(self.agent_id, content, msg_type)

    # --- Override points ---

    def on_start(self):
        """Called when agent starts."""
        pass

    def on_stop(self):
        """Called when agent stops."""
        pass

    def on_idle(self):
        """Called when no tasks are available."""
        pass

    @abstractmethod
    def execute(self, task: Task) -> Any:
        """Execute a task and return the result."""
        ...

    def on_task_completed(self, task: Task, result: Any):
        """Called after a task completes successfully."""
        pass

    def on_task_failed(self, task: Task, error: Exception):
        """Called when a task fails."""
        pass

    def on_message(self, message: Message):
        """Called when a message is received."""
        pass

    def get_status(self) -> dict:
        """Return agent status info."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self._state,
            "running": self._running,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "uptime": time.time() - self._started_at if self._started_at else 0,
        }

    @property
    def is_running(self) -> bool:
        return self._running
