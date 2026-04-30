"""Report generation agent - creates operational reports."""

import json
import logging
import time
from typing import Any

from core.agent import BaseAgent
from core.task_queue import Task

logger = logging.getLogger("agent.report")


class ReportAgent(BaseAgent):
    """Generates various operational reports from collected data."""

    def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "generate")

        if action == "generate":
            return self._generate_report(task)
        elif action == "summary":
            return self._generate_summary(task)
        elif action == "compare":
            return self._compare_report(task)
        elif action == "export":
            return self._export(task)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _generate_report(self, task: Task) -> dict:
        """Generate a full report from input data."""
        report_type = task.payload.get("report_type", "daily")
        data = task.payload.get("data", {})
        metrics = task.payload.get("metrics", {})
        alerts = task.payload.get("alerts", [])

        report = {
            "type": report_type,
            "generated_at": time.time(),
            "generated_by": self.agent_id,
        }

        if report_type == "daily":
            report["sections"] = self._build_daily_report(data, metrics, alerts)
        elif report_type == "weekly":
            report["sections"] = self._build_weekly_report(data, metrics)
        elif report_type == "incident":
            report["sections"] = self._build_incident_report(data, alerts)
        else:
            report["sections"] = {"summary": "No data available"}

        logger.info(f"Generated {report_type} report")
        return report

    def _generate_summary(self, task: Task) -> dict:
        """Generate a brief summary."""
        data = task.payload.get("data", {})
        key_points = task.payload.get("key_points", 5)

        summary = {
            "total_records": len(data) if isinstance(data, list) else 1,
            "generated_at": time.time(),
        }

        if isinstance(data, list) and data:
            numeric_fields = {}
            for d in data:
                if isinstance(d, dict):
                    for k, v in d.items():
                        if isinstance(v, (int, float)):
                            numeric_fields.setdefault(k, []).append(v)

            for field, values in numeric_fields.items():
                summary[field] = {
                    "avg": round(sum(values) / len(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                }

        return summary

    def _compare_report(self, task: Task) -> dict:
        """Compare two datasets."""
        dataset_a = task.payload.get("dataset_a", [])
        dataset_b = task.payload.get("dataset_b", [])
        comparison_fields = task.payload.get("fields", [])

        results = {}
        for field in comparison_fields:
            values_a = [d.get(field, 0) for d in dataset_a if isinstance(d, dict)]
            values_b = [d.get(field, 0) for d in dataset_b if isinstance(d, dict)]

            avg_a = sum(values_a) / len(values_a) if values_a else 0
            avg_b = sum(values_b) / len(values_b) if values_b else 0
            change = ((avg_b - avg_a) / avg_a * 100) if avg_a else 0

            results[field] = {
                "before": round(avg_a, 2),
                "after": round(avg_b, 2),
                "change_pct": round(change, 2),
                "direction": "up" if change > 0 else ("down" if change < 0 else "unchanged"),
            }

        return {"comparison": results, "generated_at": time.time()}

    def _export(self, task: Task) -> dict:
        """Export report to specified format."""
        data = task.payload.get("data", {})
        format_type = task.payload.get("format", "json")
        filename = task.payload.get("filename", "report")

        if format_type == "json":
            content = json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type == "csv":
            content = self._to_csv(data)
        elif format_type == "markdown":
            content = self._to_markdown(data)
        else:
            content = json.dumps(data, indent=2, ensure_ascii=False)

        return {
            "filename": f"{filename}.{format_type}",
            "format": format_type,
            "size_bytes": len(content),
            "content_preview": content[:200],
        }

    def _build_daily_report(self, data, metrics, alerts) -> dict:
        return {
            "overview": f"Daily report with {metrics.get('total_events', 0)} events",
            "metrics": metrics,
            "top_alerts": alerts[:5] if alerts else [],
            "data_summary": str(data)[:500] if data else "No data",
        }

    def _build_weekly_report(self, data, metrics) -> dict:
        return {
            "overview": f"Weekly summary",
            "key_metrics": metrics,
            "trends": "Trend analysis based on weekly data",
        }

    def _build_incident_report(self, data, alerts) -> dict:
        return {
            "incident_count": len(alerts),
            "severity_breakdown": self._count_severity(alerts),
            "recommendations": ["Review alert patterns", "Update thresholds if needed"],
        }

    def _count_severity(self, alerts) -> dict:
        counts = {}
        for a in alerts:
            level = a.get("level", "unknown")
            counts[level] = counts.get(level, 0) + 1
        return counts

    def _to_csv(self, data) -> str:
        if not isinstance(data, list) or not data:
            return "No data"
        if not isinstance(data[0], dict):
            return "Data must be list of dicts for CSV export"

        headers = list(data[0].keys())
        lines = [",".join(str(h) for h in headers)]
        for row in data:
            lines.append(",".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)

    def _to_markdown(self, data) -> str:
        if isinstance(data, dict):
            lines = ["# Report\n"]
            for k, v in data.items():
                lines.append(f"## {k}\n{v}\n")
            return "\n".join(lines)
        return str(data)
