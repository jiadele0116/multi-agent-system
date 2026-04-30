"""Task queue with priority support."""

import heapq
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass(order=True)
class Task:
    priority: int = field(compare=True)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = field(compare=False, default="")
    description: str = field(compare=False, default="")
    agent_type: str = field(compare=False, default="")
    payload: dict = field(compare=False, default_factory=dict)
    status: TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    assigned_to: str = field(compare=False, default="")
    result: Any = field(compare=False, default=None)
    error: str = field(compare=False, default="")
    created_at: float = field(compare=False, default_factory=time.time)
    started_at: Optional[float] = field(compare=False, default=None)
    completed_at: Optional[float] = field(compare=False, default=None)
    retries: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)


class TaskQueue:
    """Thread-safe priority task queue."""

    def __init__(self, max_retries: int = 3):
        self._lock = threading.Lock()
        self._heap: list[tuple] = []
        self._all_tasks: dict[str, Task] = {}
        self._task_available = threading.Condition(self._lock)
        self._max_retries = max_retries

    def put(self, task: Task):
        """Add a task to the queue."""
        with self._task_available:
            task.max_retries = self._max_retries
            entry = (task.priority, task.created_at, task)
            heapq.heappush(self._heap, entry)
            self._all_tasks[task.task_id] = task
            self._task_available.notify()

    def get(self, agent_type: Optional[str] = None, timeout: float = 1.0) -> Optional[Task]:
        """
        Get the highest priority task.
        If agent_type is specified, only return tasks for that agent type.
        """
        with self._task_available:
            deadline = time.time() + timeout
            while True:
                for i, (priority, created, task) in enumerate(self._heap):
                    if task.status == TaskStatus.PENDING:
                        if agent_type is None or task.agent_type == agent_type:
                            task.status = TaskStatus.ASSIGNED
                            task.assigned_to = agent_type or "any"
                            return task
                # No matching task found, wait
                if time.time() >= deadline:
                    return None
                self._task_available.wait(timeout=0.1)

    def mark_running(self, task_id: str):
        with self._lock:
            task = self._all_tasks.get(task_id)
            if task:
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()

    def mark_completed(self, task_id: str, result: Any = None):
        with self._lock:
            task = self._all_tasks.get(task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = time.time()

    def mark_failed(self, task_id: str, error: str = "") -> bool:
        """
        Mark task as failed. Returns True if task should be retried.
        """
        with self._lock:
            task = self._all_tasks.get(task_id)
            if task:
                task.retries += 1
                task.error = error
                if task.retries < task.max_retries:
                    task.status = TaskStatus.PENDING
                    task.assigned_to = ""
                    return True
                else:
                    task.status = TaskStatus.FAILED
                    task.completed_at = time.time()
                    return False
        return False

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            task = self._all_tasks.get(task_id)
            if task and task.status in (TaskStatus.PENDING, TaskStatus.ASSIGNED):
                task.status = TaskStatus.CANCELLED
                return True
            return False

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._all_tasks.get(task_id)

    def get_stats(self) -> dict:
        with self._lock:
            stats = {s.value: 0 for s in TaskStatus}
            for task in self._all_tasks.values():
                stats[task.status.value] += 1
            stats["total"] = len(self._all_tasks)
            return stats

    def size(self) -> int:
        with self._lock:
            return sum(1 for _, _, t in self._heap if t.status == TaskStatus.PENDING)
