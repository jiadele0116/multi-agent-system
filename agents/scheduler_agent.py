"""Scheduler agent - manages recurring and timed tasks."""

import logging
import time
from typing import Any, Optional

from core.agent import BaseAgent
from core.task_queue import Task, TaskPriority

logger = logging.getLogger("agent.scheduler")


class ScheduledTask:
    """Represents a scheduled/recurring task."""

    def __init__(self, name: str, agent_type: str, payload: dict,
                 cron_expr: str = "", interval: int = 0, priority: int = 2):
        self.name = name
        self.agent_type = agent_type
        self.payload = payload
        self.cron_expr = cron_expr
        self.interval = interval  # seconds
        self.priority = priority
        self.created_at = time.time()
        self.last_run = 0.0
        self.run_count = 0
        self.enabled = True

    def is_due(self, current_time: float) -> bool:
        if not self.enabled:
            return False
        if self.interval > 0:
            return current_time - self.last_run >= self.interval
        return False

    def mark_executed(self):
        self.last_run = time.time()
        self.run_count += 1


class SchedulerAgent(BaseAgent):
    """Manages scheduled and recurring tasks."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._schedules: dict[str, ScheduledTask] = {}

    def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "schedule")

        if action == "schedule":
            return self._schedule_task(task)
        elif action == "cancel":
            return self._cancel_schedule(task)
        elif action == "list":
            return self._list_schedules()
        elif action == "cron_run":
            return self._process_due_tasks()
        else:
            raise ValueError(f"Unknown action: {action}")

    def on_idle(self):
        """Check for due tasks when idle."""
        self._process_due_tasks()

    def _schedule_task(self, task: Task) -> dict:
        """Register a new scheduled task."""
        name = task.payload.get("name", f"task_{len(self._schedules)}")
        agent_type = task.payload.get("agent_type", "data")
        payload = task.payload.get("payload", {})
        interval = task.payload.get("interval", 3600)  # default 1 hour
        cron_expr = task.payload.get("cron", "")

        scheduled = ScheduledTask(
            name=name,
            agent_type=agent_type,
            payload=payload,
            interval=interval,
            cron_expr=cron_expr,
            priority=task.payload.get("priority", TaskPriority.NORMAL.value),
        )
        self._schedules[name] = scheduled

        logger.info(f"Scheduled task '{name}' every {interval}s for {agent_type}")
        return {"name": name, "status": "scheduled", "interval": interval}

    def _cancel_schedule(self, task: Task) -> dict:
        """Cancel a scheduled task."""
        name = task.payload.get("name", "")
        if name in self._schedules:
            self._schedules[name].enabled = False
            return {"name": name, "status": "cancelled"}
        return {"name": name, "status": "not_found"}

    def _list_schedules(self) -> dict:
        """List all scheduled tasks."""
        schedules = {}
        for name, s in self._schedules.items():
            schedules[name] = {
                "agent_type": s.agent_type,
                "interval": s.interval,
                "enabled": s.enabled,
                "run_count": s.run_count,
                "last_run": s.last_run,
            }
        return {"schedules": schedules, "total": len(schedules)}

    def _process_due_tasks(self) -> dict:
        """Submit tasks that are due."""
        now = time.time()
        submitted = []

        for name, schedule in self._schedules.items():
            if schedule.is_due(now):
                self.task_queue.put(Task(
                    priority=schedule.priority,
                    name=f"[scheduled] {name}",
                    agent_type=schedule.agent_type,
                    payload=schedule.payload,
                    description=f"Auto-executed from schedule '{name}'",
                ))
                schedule.mark_executed()
                submitted.append(name)

        if submitted:
            logger.info(f"Scheduler submitted {len(submitted)} tasks: {submitted}")

        return {"submitted": submitted, "active_schedules": sum(1 for s in self._schedules.values() if s.enabled)}

    def get_status(self) -> dict:
        status = super().get_status()
        status["active_schedules"] = sum(1 for s in self._schedules.values() if s.enabled)
        status["total_schedules"] = len(self._schedules)
        return status
