"""Shared tool functions that agents can use."""

import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("tools")


class FileTool:
    """File read/write operations."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save_json(self, filename: str, data: Any) -> str:
        path = os.path.join(self.base_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved {filename} ({os.path.getsize(path)} bytes)")
        return path

    def load_json(self, filename: str) -> Any:
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def append_log(self, filename: str, entry: dict):
        path = os.path.join(self.base_dir, filename)
        entry["timestamp"] = time.time()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


class TimerTool:
    """Timing and scheduling helpers."""

    @staticmethod
    def elapsed(start_time: float) -> float:
        return round(time.time() - start_time, 3)

    @staticmethod
    def sleep(seconds: float):
        time.sleep(seconds)


class DataTool:
    """Data manipulation helpers."""

    @staticmethod
    def paginate(data: list, page: int = 1, size: int = 20) -> dict:
        start = (page - 1) * size
        end = start + size
        return {
            "page": page,
            "size": size,
            "total": len(data),
            "total_pages": (len(data) + size - 1) // size,
            "data": data[start:end],
        }

    @staticmethod
    def filter_by(data: list, **kwargs) -> list:
        result = data
        for key, value in kwargs.items():
            result = [d for d in result if isinstance(d, dict) and d.get(key) == value]
        return result

    @staticmethod
    def sort_by(data: list, key: str, reverse: bool = False) -> list:
        return sorted(
            [d for d in data if isinstance(d, dict) and key in d],
            key=lambda x: x[key],
            reverse=reverse,
        )
