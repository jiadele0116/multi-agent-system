"""Central coordinator that manages agents and orchestrates tasks."""

import logging
import threading
import time
from typing import Any, Optional

from core.agent import BaseAgent
from core.message_bus import Message, MessageBus, MessageType
from core.task_queue import Task, TaskPriority, TaskQueue, TaskStatus

logger = logging.getLogger("coordinator")


class Coordinator:
    """Central orchestrator for the multi-agent system."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.message_bus = MessageBus()
        self.task_queue = TaskQueue(max_retries=self.config.get("max_retries", 3))
        self.agents: dict[str, BaseAgent] = {}
        self._running = False
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._agent_configs: dict[str, dict] = self.config.get("agents", {})

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the coordinator."""
        with self._lock:
            self.agents[agent.agent_id] = agent
            logger.info(f"Registered agent: {agent.agent_id} (type={agent.agent_type})")

    def remove_agent(self, agent_id: str):
        """Remove an agent from the coordinator."""
        with self._lock:
            if agent_id in self.agents:
                agent = self.agents.pop(agent_id)
                agent.stop()
                logger.info(f"Removed agent: {agent_id}")

    def submit_task(self, name: str, agent_type: str, payload: dict,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    description: str = "") -> Task:
        """Submit a new task to the queue."""
        task = Task(
            priority=priority.value,
            name=name,
            agent_type=agent_type,
            payload=payload,
            description=description,
        )
        self.task_queue.put(task)
        logger.info(f"Task submitted: {task.name} (type={agent_type}, priority={priority.name})")
        return task

    def submit_tasks_batch(self, tasks: list[dict]) -> list[Task]:
        """Submit multiple tasks at once."""
        created = []
        for t in tasks:
            task = self.submit_task(
                name=t["name"],
                agent_type=t["agent_type"],
                payload=t.get("payload", {}),
                priority=TaskPriority(t.get("priority", TaskPriority.NORMAL.value)),
                description=t.get("description", ""),
            )
            created.append(task)
        return created

    def start(self):
        """Start all agents and the monitoring loop."""
        self._running = True
        for agent in self.agents.values():
            agent.start()

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Coordinator started with {len(self.agents)} agents")

    def stop(self):
        """Stop all agents and the coordinator."""
        self._running = False
        for agent in list(self.agents.values()):
            agent.stop()
        logger.info("Coordinator stopped")

    def _monitor_loop(self):
        """Periodically check agent health and system status."""
        interval = self.config.get("monitor_interval", 30)
        while self._running:
            try:
                self._check_agent_health()
                self._log_system_status()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

    def _check_agent_health(self):
        """Check if any agents have died unexpectedly."""
        with self._lock:
            for agent_id, agent in self.agents.items():
                if not agent.is_running and agent._state != "stopped":
                    logger.warning(f"Agent {agent_id} appears to have died, restarting...")
                    try:
                        agent.start()
                    except Exception as e:
                        logger.error(f"Failed to restart agent {agent_id}: {e}")

    def _log_system_status(self):
        """Log current system status."""
        stats = self.task_queue.get_stats()
        agent_states = {a.agent_id: a._state for a in self.agents.values()}
        logger.info(f"System status: {stats} | Agent states: {agent_states}")

    def get_system_status(self) -> dict:
        """Get full system status."""
        return {
            "running": self._running,
            "agents": {aid: a.get_status() for aid, a in self.agents.items()},
            "queue": self.task_queue.get_stats(),
            "queue_pending": self.task_queue.size(),
        }

    def get_agents_by_type(self, agent_type: str) -> list[BaseAgent]:
        """Get all agents of a specific type."""
        with self._lock:
            return [a for a in self.agents.values() if a.agent_type == agent_type]
