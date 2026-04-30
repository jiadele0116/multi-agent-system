"""Data analysis agent - processes and analyzes operational data."""

import logging
import random
import time
from typing import Any

from core.agent import BaseAgent
from core.task_queue import Task

logger = logging.getLogger("agent.data")


class DataAgent(BaseAgent):
    """Handles data collection, cleaning, and analysis tasks."""

    def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "analyze")

        if action == "analyze":
            return self._analyze(task)
        elif action == "collect":
            return self._collect(task)
        elif action == "clean":
            return self._clean(task)
        elif action == "aggregate":
            return self._aggregate(task)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _analyze(self, task: Task) -> dict:
        data = task.payload.get("data", [])
        metric = task.payload.get("metric", "revenue")

        if not data:
            data = self._generate_sample_data(metric, size=100)

        values = [d.get(metric, 0) for d in data if isinstance(d, dict)]
        if not values:
            values = data if isinstance(data[0], (int, float)) else [0]

        result = {
            "count": len(values),
            "sum": round(sum(values), 2),
            "mean": round(sum(values) / len(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "metric": metric,
        }

        # Simple trend detection
        if len(values) > 1:
            diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
            positive = sum(1 for d in diffs if d > 0)
            result["trend"] = "up" if positive > len(diffs) * 0.6 else ("down" if positive < len(diffs) * 0.4 else "stable")
            result["volatility"] = round(sum(abs(d) for d in diffs) / len(diffs), 2)

        logger.info(f"Analysis complete: {result['count']} records, trend={result.get('trend', 'N/A')}")
        return result

    def _collect(self, task: Task) -> dict:
        source = task.payload.get("source", "default")
        count = task.payload.get("count", 50)
        logger.info(f"Collecting {count} records from {source}")

        # Simulated data collection
        data = []
        for i in range(count):
            data.append({
                "id": i + 1,
                "source": source,
                "timestamp": time.time() - random.randint(0, 86400 * 7),
                "value": round(random.uniform(10, 1000), 2),
                "category": random.choice(["A", "B", "C", "D"]),
            })

        return {"source": source, "records_collected": len(data), "sample": data[:5]}

    def _clean(self, task: Task) -> dict:
        data = task.payload.get("data", [])
        rules = task.payload.get("rules", ["remove_nulls", "deduplicate"])

        original_count = len(data)

        if "remove_nulls" in rules:
            data = [d for d in data if d is not None and d != {}]

        if "deduplicate" in rules:
            seen = set()
            deduped = []
            for d in data:
                key = str(d)
                if key not in seen:
                    seen.add(key)
                    deduped.append(d)
            data = deduped

        removed = original_count - len(data)
        return {"original_count": original_count, "clean_count": len(data), "removed": removed}

    def _aggregate(self, task: Task) -> dict:
        data = task.payload.get("data", [])
        group_by = task.payload.get("group_by", "category")
        agg_field = task.payload.get("agg_field", "value")
        agg_func = task.payload.get("agg_func", "sum")

        groups: dict[str, list] = {}
        for d in data:
            if isinstance(d, dict):
                key = d.get(group_by, "unknown")
                val = d.get(agg_field, 0)
                groups.setdefault(key, []).append(val)

        result = {}
        for key, values in groups.items():
            if agg_func == "sum":
                result[key] = round(sum(values), 2)
            elif agg_func == "mean":
                result[key] = round(sum(values) / len(values), 2)
            elif agg_func == "count":
                result[key] = len(values)
            else:
                result[key] = round(sum(values), 2)

        return {"grouped_by": group_by, "agg_func": agg_func, "result": result}

    def _generate_sample_data(self, metric: str, size: int) -> list[dict]:
        base = random.uniform(100, 500)
        data = []
        for i in range(size):
            data.append({
                metric: round(base + random.gauss(0, base * 0.2), 2),
                "date": f"2026-04-{(i % 30) + 1:02d}",
                "category": random.choice(["A", "B", "C"]),
            })
        return data
