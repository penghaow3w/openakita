"""强化学习反馈系统 - 让 AI 从反馈中自我优化"""
import time
import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FeedbackRecord:
    id: int = 0
    query: str = ""
    response: str = ""
    rating: float = 0.0      # 0.0 ~ 1.0
    feedback_text: str = ""
    created_at: float = 0.0
    category: str = "general"


class FeedbackCollector:
    """反馈收集器"""

    def __init__(self, db_path: str = "./data/openakita.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                rating REAL DEFAULT 0.5,
                feedback_text TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s','now')),
                category TEXT DEFAULT 'general'
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
        """)
        self.conn.commit()

    def add_feedback(self, query: str, response: str, rating: float,
                     feedback_text: str = "", category: str = "general"):
        """添加反馈"""
        self.conn.execute(
            "INSERT INTO feedback (query, response, rating, feedback_text, category) "
            "VALUES (?, ?, ?, ?, ?)",
            (query, response, rating, feedback_text, category),
        )
        self.conn.commit()

    def get_recent_feedback(self, limit: int = 50) -> List[FeedbackRecord]:
        """获取最近的反馈"""
        rows = self.conn.execute(
            "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [FeedbackRecord(*row) for row in rows]

    def get_low_rating_feedback(self, threshold: float = 0.3,
                                limit: int = 20) -> List[FeedbackRecord]:
        """获取低分反馈 (需要改进的部分)"""
        rows = self.conn.execute(
            "SELECT * FROM feedback WHERE rating <= ? ORDER BY rating ASC LIMIT ?",
            (threshold, limit),
        ).fetchall()
        return [FeedbackRecord(*row) for row in rows]


class PolicyOptimizer:
    """策略优化器 - 基于反馈调整行为"""

    def __init__(self, learning_rate: float = 0.1):
        self.lr = learning_rate
        self._adjustments: Dict[str, float] = {}

    def update_from_feedback(self, feedbacks: List[FeedbackRecord]):
        """从反馈中学习并调整策略参数"""
        if not feedbacks:
            return

        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)

        # 计算各分类表现
        category_perf: Dict[str, List[float]] = {}
        for f in feedbacks:
            category_perf.setdefault(f.category, []).append(f.rating)

        for cat, ratings in category_perf.items():
            avg_cat = sum(ratings) / len(ratings)
            current = self._adjustments.get(cat, 0.0)
            # 低分分类增加关注度，高分分类维持
            delta = (0.5 - avg_cat) * self.lr
            self._adjustments[cat] = current + delta

    def get_adjustments(self) -> Dict[str, float]:
        return self._adjustments

    def get_temperature_adjustment(self) -> float:
        """基于平均表现的 temperature 调整"""
        if not self._adjustments:
            return 0.0
        avg_adj = sum(self._adjustments.values()) / len(self._adjustments)
        # 表现差 => 降低 temperature (更保守); 表现好 => 略增
        return -avg_adj * 0.5


class SelfOptimizer:
    """自我优化系统 (RL 核心)"""

    def __init__(self, db_path: str = "./data/openakita.db",
                 learning_rate: float = 0.1):
        self.feedback = FeedbackCollector(db_path)
        self.policy = PolicyOptimizer(learning_rate)
        self.learning_rate = learning_rate

    def record_outcome(self, query: str, response: str, rating: float,
                       feedback_text: str = ""):
        """记录一次交互结果"""
        self.feedback.add_feedback(query, response, rating, feedback_text)

    def optimize(self) -> Dict:
        """执行自我优化"""
        recent = self.feedback.get_recent_feedback(limit=50)
        self.policy.update_from_feedback(recent)
        adjustments = self.policy.get_adjustments()

        # 自动优化建议
        low_rated = self.feedback.get_low_rating_feedback(threshold=0.3, limit=5)
        suggestions = []
        for fb in low_rated:
            suggestions.append({
                "query": fb.query[:100],
                "rating": fb.rating,
                "feedback": fb.feedback_text,
            })

        return {
            "adjustments": adjustments,
            "temperature_adjustment": self.policy.get_temperature_adjustment(),
            "improvement_suggestions": suggestions,
            "total_feedback": len(recent),
        }

    def get_stats(self) -> Dict:
        """获取统计数据"""
        recent = self.feedback.get_recent_feedback(limit=1000)
        if not recent:
            return {"avg_rating": 0, "total": 0, "low_rating_count": 0}
        ratings = [f.rating for f in recent]
        low_count = sum(1 for r in ratings if r <= 0.3)
        return {
            "avg_rating": sum(ratings) / len(ratings),
            "total": len(ratings),
            "low_rating_count": low_count,
        }