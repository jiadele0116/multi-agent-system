"""Monitoring agent - watches system metrics and sends alerts."""

import logging
import random
import time
from typing import Any

from core.agent import BaseAgent
from core.message_bus import MessageType
from core.task_queue import Task

logger = logging.getLogger("agent.monitor")

ALERT_THRESHOLDS = {
    "cpu_usage": 85,
    "memory_usage": 90,
    "error_rate": 5,
    "response_time": 2000,
    "queue_size": 100,
}


class MonitorAgent(BaseAgent):
    """Monitors system health, metrics, and triggers alerts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._alert_count = 0
        self._alerts_sent: list[dict] = []

    def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "check")

        if action == "check":
            return self._check_health(task)
        elif action == "alert":
            return self._send_alert(task)
        elif action == "metrics":
            return self._collect_metrics(task)
        elif action == "threshold":
            return self._update_threshold(task)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _check_health(self, task: Task) -> dict:
        """Simulate health checks across services."""
        services = task.payload.get("services", ["api", "database", "cache", "queue"])
        results = {}

        for service in services:
            health = self._simulate_check(service)
            results[service] = health

            if health["status"] == "critical":
                self._trigger_alert("critical", f"{service} is critical: {health.get('message', '')}")
            elif health["status"] == "warning":
                self._trigger_alert("warning", f"{service} degraded: {health.get('message', '')}")

        return {"timestamp": time.time(), "services": results}

    def _send_alert(self, task: Task) -> dict:
        """Send a specific alert."""
        level = task.payload.get("level", "info")
        message = task.payload.get("message", "No details")
        channel = task.payload.get("channel", "default")

        return self._trigger_alert(level, message, channel)

    def _collect_metrics(self, task: Task) -> dict:
        """Collect system metrics."""
        metrics = {
            "cpu_usage": round(random.uniform(20, 95), 1),
            "memory_usage": round(random.uniform(40, 95), 1),
            "disk_usage": round(random.uniform(30, 80), 1),
            "active_connections": random.randint(10, 500),
            "requests_per_second": random.randint(50, 2000),
            "error_rate": round(random.uniform(0, 8), 2),
            "avg_response_time_ms": random.randint(50, 3000),
            "queue_size": self.task_queue.size(),
        }

        # Check thresholds
        alerts = []
        for metric, threshold in ALERT_THRESHOLDS.items():
            if metric in metrics and metrics[metric] > threshold:
                alerts.append({
                    "metric": metric,
                    "value": metrics[metric],
                    "threshold": threshold,
                })

        if alerts:
            logger.warning(f"Threshold alerts: {alerts}")

        return {"metrics": metrics, "alerts": alerts, "timestamp": time.time()}

    def _update_threshold(self, task: Task) -> dict:
        """Update alert thresholds."""
        updates = task.payload.get("thresholds", {})
        for key, value in updates.items():
            if key in ALERT_THRESHOLDS:
                ALERT_THRESHOLDS[key] = value

        return {"updated": updates, "current_thresholds": ALERT_THRESHOLDS.copy()}

    def _simulate_check(self, service: str) -> dict:
        r = random.random()
        if r < 0.7:
            return {"status": "healthy", "uptime": random.randint(1, 365)}
        elif r < 0.9:
            return {"status": "warning", "message": "Elevated latency detected"}
        else:
            return {"status": "critical", "message": "Service unreachable"}

    def _trigger_alert(self, level: str, message: str, channel: str = "default") -> dict:
        self._alert_count += 1
        alert = {
            "id": self._alert_count,
            "level": level,
            "message": message,
            "channel": channel,
            "timestamp": time.time(),
        }
        self._alerts_sent.append(alert)

        # Broadcast alert to all agents
        self.broadcast(
            {"alert": alert},
            msg_type=MessageType.ALERT,
        )

        logger.warning(f"ALERT [{level}]: {message}")
        return alert

    def on_message(self, message):
        """React to alerts from other agents."""
        if message.msg_type.value == "alert":
            logger.info(f"[{self.agent_id}] Received alert: {message.content}")

    def get_status(self) -> dict:
        status = super().get_status()
        status["alerts_sent"] = self._alert_count
        return status
