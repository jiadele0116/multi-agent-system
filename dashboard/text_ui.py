"""CLI dashboard for real-time system monitoring."""

import os
import sys
import time


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def render_dashboard(status: dict) -> str:
    """Render a text-based dashboard."""
    lines = []
    width = 80

    lines.append("=" * width)
    lines.append("  MULTI-AGENT OPERATIONS SYSTEM".center(width))
    lines.append("=" * width)
    lines.append("")

    # System overview
    running = status.get("running", False)
    queue_stats = status.get("queue", {})
    lines.append(f"  Status: {'RUNNING' if running else 'STOPPED'}")
    lines.append(f"  Queue: {queue_stats.get('pending', 0)} pending | "
                 f"{queue_stats.get('completed', 0)} done | "
                 f"{queue_stats.get('failed', 0)} failed")
    lines.append("")

    # Agent status
    lines.append("-" * width)
    lines.append(f"  {'Agent':<25} {'Type':<15} {'State':<10} {'Done':<6} {'Failed':<6}")
    lines.append("-" * width)

    for agent_id, info in status.get("agents", {}).items():
        lines.append(
            f"  {agent_id:<25} {info.get('agent_type', ''):<15} "
            f"{info.get('state', ''):<10} {info.get('tasks_completed', 0):<6} "
            f"{info.get('tasks_failed', 0):<6}"
        )

    lines.append("-" * width)
    lines.append("")
    lines.append(f"  Total tasks: {queue_stats.get('total', 0)}")
    lines.append(f"  Queue pending: {status.get('queue_pending', 0)}")
    lines.append("")

    return "\n".join(lines)


def interactive_dashboard(coordinator):
    """Run an interactive dashboard loop."""
    try:
        while True:
            status = coordinator.get_system_status()
            clear_screen()
            print(render_dashboard(status))
            time.sleep(2)
    except KeyboardInterrupt:
        pass
