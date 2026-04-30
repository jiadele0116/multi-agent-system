"""Multi-Agent Operations Automation System - Main Entry Point."""

import logging
import sys
import time

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SYSTEM_CONFIG, WORKFLOWS
from core.logging_config import setup_logging
from core.coordinator import Coordinator
from core.task_queue import TaskPriority
from dashboard.text_ui import interactive_dashboard

# Import agents
from agents.data_agent import DataAgent
from agents.content_agent import ContentAgent
from agents.monitor_agent import MonitorAgent
from agents.report_agent import ReportAgent
from agents.scheduler_agent import SchedulerAgent
from agents.notification_agent import NotificationAgent

logger = logging.getLogger("main")


def create_system(config: dict) -> Coordinator:
    """Create and configure the multi-agent system."""
    coordinator = Coordinator(config)

    agent_configs = config.get("agents", {})

    # Create agents based on config
    agent_id_map = {}

    for agent_type, type_config in agent_configs.items():
        instances = type_config.get("instances", 1)
        for i in range(instances):
            agent_id = f"{agent_type}_{i}"
            agent_id_map[agent_id] = agent_type

            agent = _create_agent(agent_id, agent_type, coordinator)
            coordinator.register_agent(agent)

    return coordinator


def _create_agent(agent_id: str, agent_type: str, coordinator: Coordinator):
    """Factory function to create agents by type."""
    agents = {
        "data": DataAgent,
        "content": ContentAgent,
        "monitor": MonitorAgent,
        "report": ReportAgent,
        "scheduler": SchedulerAgent,
        "notification": NotificationAgent,
    }
    cls = agents.get(agent_type, DataAgent)
    return cls(
        agent_id=agent_id,
        agent_type=agent_type,
        message_bus=coordinator.message_bus,
        task_queue=coordinator.task_queue,
    )


def run_demo(coordinator: Coordinator):
    """Run a demo workflow."""
    logger.info("=" * 60)
    logger.info("Starting demo workflow execution...")
    logger.info("=" * 60)

    # 1. Submit daily report workflow
    logger.info("\n--- Workflow: Daily Report ---")
    coordinator.submit_tasks_batch(WORKFLOWS["daily_report"])

    # 2. Submit content campaign
    logger.info("\n--- Workflow: Content Campaign ---")
    coordinator.submit_tasks_batch(WORKFLOWS["content_campaign"])

    # 3. Submit system health check
    logger.info("\n--- Workflow: System Health ---")
    coordinator.submit_tasks_batch(WORKFLOWS["system_health"])

    # 4. Submit ad-hoc tasks
    logger.info("\n--- Ad-hoc Tasks ---")
    coordinator.submit_task(
        name="quick_data_analysis",
        agent_type="data",
        payload={"action": "aggregate", "group_by": "category", "agg_field": "value"},
        priority=TaskPriority.NORMAL,
    )

    coordinator.submit_task(
        name="send_notification",
        agent_type="notification",
        payload={
            "action": "send",
            "channel": "log",
            "subject": "System Update",
            "body": "All systems operational",
        },
        priority=TaskPriority.NORMAL,
    )

    # 5. Schedule recurring monitoring
    coordinator.submit_task(
        name="setup_monitoring",
        agent_type="scheduler",
        payload={
            "action": "schedule",
            "name": "health_check_5min",
            "agent_type": "monitor",
            "interval": 30,  # every 30s for demo
            "payload": {"action": "metrics"},
        },
        priority=TaskPriority.NORMAL,
    )

    logger.info(f"\nAll tasks submitted. Queue size: {coordinator.task_queue.size()}")


def print_final_report(coordinator: Coordinator):
    """Print a summary report."""
    status = coordinator.get_system_status()
    queue_stats = status.get("queue", {})

    print("\n" + "=" * 60)
    print("  SYSTEM EXECUTION REPORT".center(60))
    print("=" * 60)

    print(f"\n  Total tasks: {queue_stats.get('total', 0)}")
    print(f"  Completed:   {queue_stats.get('completed', 0)}")
    print(f"  Failed:      {queue_stats.get('failed', 0)}")
    print(f"  Pending:     {queue_stats.get('pending', 0)}")

    print("\n  Agent Performance:")
    print(f"  {'Agent':<20} {'State':<10} {'Done':<6} {'Failed':<6} {'Uptime':<10}")
    print("  " + "-" * 52)

    for agent_id, info in status.get("agents", {}).items():
        uptime = info.get("uptime", 0)
        print(f"  {agent_id:<20} {info.get('state', ''):<10} "
              f"{info.get('tasks_completed', 0):<6} "
              f"{info.get('tasks_failed', 0):<6} "
              f"{uptime:.1f}s")

    print("\n" + "=" * 60)


def run_interactive(coordinator: Coordinator):
    """Run interactive dashboard mode."""
    print("Starting interactive dashboard. Press Ctrl+C to stop.\n")
    time.sleep(2)
    interactive_dashboard(coordinator)


def main():
    """Main entry point."""
    # Parse args
    mode = "demo"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    # Setup logging
    setup_logging(log_level=SYSTEM_CONFIG.get("log_level", "INFO"))

    # Create system
    coordinator = create_system(SYSTEM_CONFIG)
    coordinator.start()

    try:
        if mode == "demo":
            run_demo(coordinator)
            # Wait for tasks to process
            logger.info("\nWaiting for task execution to complete...")
            for _ in range(30):  # max 30s
                stats = coordinator.task_queue.get_stats()
                if stats.get("pending", 1) == 0:
                    break
                time.sleep(1)

            print_final_report(coordinator)

        elif mode == "interactive":
            run_interactive(coordinator)

        elif mode == "workflow":
            workflow_name = sys.argv[2] if len(sys.argv) > 2 else "daily_report"
            if workflow_name in WORKFLOWS:
                coordinator.submit_tasks_batch(WORKFLOWS[workflow_name])
                logger.info(f"Workflow '{workflow_name}' submitted")
            else:
                logger.error(f"Unknown workflow: {workflow_name}")
                sys.exit(1)

            for _ in range(30):
                stats = coordinator.task_queue.get_stats()
                if stats.get("pending", 1) == 0:
                    break
                time.sleep(1)

            print_final_report(coordinator)

        else:
            print("Usage:")
            print("  python main.py demo          - Run demo workflows")
            print("  python main.py interactive    - Start interactive dashboard")
            print("  python main.py workflow NAME  - Run specific workflow")
            print(f"\nAvailable workflows: {list(WORKFLOWS.keys())}")

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    finally:
        coordinator.stop()


if __name__ == "__main__":
    main()
