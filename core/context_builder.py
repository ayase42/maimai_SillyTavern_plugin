"""
上下文构建模块
负责构建对话历史上下文
"""
from typing import Dict, Any, List, Optional, Callable
from .utils import collapse_text
from .scene_db import SceneDB


class ContextBuilder:
    """上下文构建器"""

    def __init__(self, db: SceneDB, get_config: Callable):
        self.db = db
        self.get_config = get_config

    def build_context_block(self, session_id: Optional[str], context_type: str = "reply") -> str:
        """
        构建最近对话上下文片段，供提示词使用

        Args:
            session_id: 会话ID
            context_type: 上下文类型，"planner"或"reply"

        Returns:
            格式化的历史上下文字符串
        """
        if not session_id:
            return ""

        try:
            if context_type == "planner":
                config_key = "scene.planner_context_messages"
                default_limit = 3  # Planner需要更多上下文来判断场景连续性
            else:
                config_key = "scene.reply_context_messages"
                default_limit = 10

            limit = self.get_config(config_key, default_limit)
            limit = int(limit)
        except (TypeError, ValueError):
            limit = default_limit if context_type == "reply" else 1

        limit = max(0, min(limit, 50))
        if limit == 0:
            return ""

        history = self.db.get_recent_history(session_id, limit) if self.db else []

        if not history:
            return "【最近场景对话】暂无历史记录"

        return self._build_dialogue_context(history)

    def _build_dialogue_context(self, history: List[Dict]) -> str:
        """构建对话形式的上下文，交替展示用户和Bot的内容"""
        total = len(history)
        lines: List[str] = [f"【最近场景对话】（共{total}轮）"]

        for record in history:
            user_msg = record.get("user_message") or ""
            # 优先使用干净的场景描述，避免格式化边框污染上下文
            scene_desc = record.get("scene_description") or ""
            location = record.get("location") or ""
            clothing = record.get("clothing") or ""

            if user_msg:
                lines.append(f"用户：{user_msg}")

            # 构建干净的Bot回复（无边框噪音）
            if scene_desc:
                bot_context = f"[{location}][{clothing}] {scene_desc}" if location and clothing else scene_desc
                lines.append(f"Bot：{bot_context}")

        return "\n".join(lines)
