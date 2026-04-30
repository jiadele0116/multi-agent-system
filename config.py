"""System configuration."""

SYSTEM_CONFIG = {
    "max_retries": 3,
    "monitor_interval": 30,
    "log_level": "INFO",
    "agents": {
        "data": {"instances": 1},
        "content": {"instances": 1},
        "monitor": {"instances": 1},
        "report": {"instances": 1},
        "scheduler": {"instances": 1},
        "notification": {"instances": 1},
    },
}


# Pre-defined workflows for common operations
WORKFLOWS = {
    "daily_report": [
        {
            "name": "collect_daily_data",
            "agent_type": "data",
            "payload": {"action": "collect", "source": "daily_events", "count": 200},
            "priority": 2,
        },
        {
            "name": "analyze_daily_data",
            "agent_type": "data",
            "payload": {"action": "analyze", "metric": "revenue"},
            "priority": 2,
        },
        {
            "name": "monitor_health_check",
            "agent_type": "monitor",
            "payload": {"action": "check", "services": ["api", "database", "cache"]},
            "priority": 1,
        },
        {
            "name": "generate_daily_report",
            "agent_type": "report",
            "payload": {
                "action": "generate",
                "report_type": "daily",
                "metrics": {"total_events": 200},
            },
            "priority": 2,
        },
        {
            "name": "notify_report_ready",
            "agent_type": "notification",
            "payload": {
                "action": "send",
                "channel": "log",
                "subject": "Daily Report Ready",
                "body": "The daily operations report has been generated.",
            },
            "priority": 2,
        },
    ],
    "content_campaign": [
        {
            "name": "generate_social_posts",
            "agent_type": "content",
            "payload": {
                "action": "generate",
                "type": "social_media",
                "params": {
                    "product": "小米15 Ultra",
                    "benefit": "徕卡光学，影像新境界",
                    "feature": "一英寸大底传感器",
                },
                "count": 3,
            },
            "priority": 2,
        },
        {
            "name": "review_content",
            "agent_type": "content",
            "payload": {
                "action": "review",
                "content": "Sample content",
                "banned_words": [],
            },
            "priority": 2,
        },
        {
            "name": "schedule_posts",
            "agent_type": "scheduler",
            "payload": {
                "action": "schedule",
                "name": "social_media_campaign",
                "agent_type": "content",
                "interval": 7200,
                "payload": {
                    "action": "generate",
                    "type": "social_media",
                    "params": {"product": "新品", "benefit": "品质生活"},
                },
            },
            "priority": 2,
        },
    ],
    "system_health": [
        {
            "name": "collect_metrics",
            "agent_type": "monitor",
            "payload": {"action": "metrics"},
            "priority": 0,
        },
        {
            "name": "analyze_metrics",
            "agent_type": "data",
            "payload": {"action": "analyze", "metric": "cpu_usage"},
            "priority": 1,
        },
        {
            "name": "health_report",
            "agent_type": "report",
            "payload": {
                "action": "generate",
                "report_type": "incident",
            },
            "priority": 1,
        },
    ],
}
