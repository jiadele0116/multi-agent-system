"""Content generation agent - creates marketing copy, social media posts, etc."""

import logging
import random
import time
from typing import Any

from core.agent import BaseAgent
from core.task_queue import Task

logger = logging.getLogger("agent.content")

TEMPLATES = {
    "social_media": [
        "🎯 {product} - {benefit}！立即体验 {feature} 的无限可能。#小米 #科技改变生活",
        "📱 全新 {product} 已上线！{benefit} 让生活更简单。了解更多 → {link}",
        "✨ {product} 带来全新体验：{feature}，让每一天都不同寻常！",
    ],
    "email": [
        "尊敬的{user}，\n\n我们很高兴向您推荐 {product}。\n核心优势：{benefit}\n\n如有任何问题，请随时联系我们。\n\n此致\n运营团队",
    ],
    "notification": [
        "【运营通知】{product} 已更新，新增 {feature}，{benefit}。",
    ],
    "blog": [
        "# {product} 深度评测\n\n## 亮点\n- {benefit}\n- {feature}\n\n## 总结\n{product} 是今年最值得关注的产品之一。",
    ],
}


class ContentAgent(BaseAgent):
    """Generates marketing content, social media posts, and notifications."""

    def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "generate")

        if action == "generate":
            return self._generate(task)
        elif action == "review":
            return self._review(task)
        elif action == "schedule":
            return self._schedule(task)
        elif action == "translate":
            return self._translate(task)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _generate(self, task: Task) -> dict:
        content_type = task.payload.get("type", "social_media")
        params = task.payload.get("params", {})

        templates = TEMPLATES.get(content_type, TEMPLATES["social_media"])
        template = random.choice(templates)

        content = template.format(
            product=params.get("product", "新品"),
            benefit=params.get("benefit", "提升效率"),
            feature=params.get("feature", "智能功能"),
            user=params.get("user", "用户"),
            link=params.get("link", "https://example.com"),
        )

        result = {
            "type": content_type,
            "content": content,
            "generated_at": time.time(),
            "params": params,
        }

        # If multiple copies needed
        count = task.payload.get("count", 1)
        if count > 1:
            variations = []
            for _ in range(count - 1):
                t = random.choice(templates)
                variations.append(t.format(
                    product=params.get("product", "新品"),
                    benefit=params.get("benefit", "提升效率"),
                    feature=params.get("feature", "智能功能"),
                    user=params.get("user", "用户"),
                    link=params.get("link", "https://example.com"),
                ))
            result["variations"] = variations

        logger.info(f"Generated {content_type} content (count={count})")
        return result

    def _review(self, task: Task) -> dict:
        content = task.payload.get("content", "")
        rules = task.payload.get("rules", ["length", "keywords"])

        issues = []
        if "length" in rules and len(content) > 500:
            issues.append("Content exceeds 500 characters")
        if "keywords" in rules:
            banned = task.payload.get("banned_words", [])
            for word in banned:
                if word in content:
                    issues.append(f"Contains banned word: {word}")

        score = 100 - len(issues) * 25
        return {"content": content, "score": max(0, score), "issues": issues, "passed": len(issues) == 0}

    def _schedule(self, task: Task) -> dict:
        content = task.payload.get("content", "")
        schedule_time = task.payload.get("schedule_time", "")
        channel = task.payload.get("channel", "all")

        return {
            "content": content,
            "scheduled_for": schedule_time,
            "channel": channel,
            "status": "scheduled",
        }

    def _translate(self, task: Task) -> dict:
        content = task.payload.get("content", "")
        target_lang = task.payload.get("target_lang", "en")

        # Simulated translation dictionary
        translations = {
            "提升效率": {"en": "Boost efficiency", "ja": "効率を向上", "ko": "효율성 향상"},
            "智能功能": {"en": "Smart features", "ja": "スマート機能", "ko": "스마트 기능"},
            "新品": {"en": "New product", "ja": "新製品", "ko": "신제품"},
        }

        translated = content
        for cn, langs in translations.items():
            if cn in translated:
                translated = translated.replace(cn, langs.get(target_lang, cn))

        return {"original": content, "translated": translated, "target_lang": target_lang}
