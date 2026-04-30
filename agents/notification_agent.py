"""Notification agent - handles alerts and notifications delivery."""

import logging
import time
from typing import Any

from core.agent import BaseAgent
from core.task_queue import Task

logger = logging.getLogger("agent.notification")


class NotificationAgent(BaseAgent):
    """Handles sending notifications through various channels."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._notifications_sent = 0
        self._channels = {
            "email": {"enabled": True, "sent": 0},
            "sms": {"enabled": False, "sent": 0},
            "webhook": {"enabled": True, "sent": 0},
            "log": {"enabled": True, "sent": 0},
        }

    def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "send")

        if action == "send":
            return self._send_notification(task)
        elif action == "batch":
            return self._batch_send(task)
        elif action == "configure":
            return self._configure_channels(task)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _send_notification(self, task: Task) -> dict:
        """Send a single notification."""
        channel = task.payload.get("channel", "log")
        subject = task.payload.get("subject", "")
        body = task.payload.get("body", "")
        recipients = task.payload.get("recipients", [])
        priority = task.payload.get("priority", "normal")

        result = self._deliver(channel, subject, body, recipients, priority)
        self._notifications_sent += 1
        self._channels.get(channel, {}).setdefault("sent", 0)
        self._channels[channel]["sent"] += 1

        return {"status": result, "channel": channel, "subject": subject}

    def _batch_send(self, task: Task) -> dict:
        """Send multiple notifications."""
        notifications = task.payload.get("notifications", [])
        results = []

        for notif in notifications:
            channel = notif.get("channel", "log")
            subject = notif.get("subject", "")
            body = notif.get("body", "")
            recipients = notif.get("recipients", [])

            result = self._deliver(channel, subject, body, recipients, notif.get("priority", "normal"))
            results.append({"channel": channel, "subject": subject, "status": result})
            self._notifications_sent += 1

        return {"total": len(notifications), "results": results}

    def _configure_channels(self, task: Task) -> dict:
        """Enable/disable notification channels."""
        config = task.payload.get("channels", {})
        for channel, settings in config.items():
            if channel in self._channels:
                if isinstance(settings, dict):
                    self._channels[channel].update(settings)
                else:
                    self._channels[channel]["enabled"] = bool(settings)

        return {"channels": self._channels.copy()}

    def _deliver(self, channel: str, subject: str, body: str,
                 recipients: list, priority: str) -> str:
        """Simulate delivering through a channel."""
        if not self._channels.get(channel, {}).get("enabled", False):
            return "disabled"

        if channel == "log":
            logger.info(f"NOTIFICATION [{priority}] {subject}: {body}")
            return "sent"
        elif channel == "email":
            return f"email_queued (to: {len(recipients)})"
        elif channel == "sms":
            return f"sms_queued (to: {len(recipients)})"
        elif channel == "webhook":
            return "webhook_posted"
        else:
            return f"sent_via_{channel}"

    def on_message(self, message):
        """Auto-send notifications for certain message types."""
        if message.msg_type.value == "alert":
            alert = message.content.get("alert", {})
            level = alert.get("level", "info")
            self.task_queue.put(Task(
                priority=0 if level == "critical" else 2,
                name="auto_alert_notification",
                agent_type="notification",
                payload={
                    "action": "send",
                    "channel": "log",
                    "subject": f"[{level.upper()}] Alert from {message.sender}",
                    "body": alert.get("message", ""),
                    "priority": level,
                },
            ))

    def get_status(self) -> dict:
        status = super().get_status()
        status["notifications_sent"] = self._notifications_sent
        status["channels"] = {
            ch: {"enabled": c["enabled"], "sent": c.get("sent", 0)}
            for ch, c in self._channels.items()
        }
        return status
