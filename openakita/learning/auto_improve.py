"""自主学习系统 - 让 AI 持续进化"""
import sqlite3
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from ..core.skills import SkillRegistry, Skill
from ..core.memory import PersistentMemory


@dataclass
class LearningRecord:
    id: int = 0
    skill_name: str = ""
    source: str = ""          # auto_discover | user_teach | error_fix
    code: str = ""
    description: str = ""
    success_count: int = 0
    fail_count: int = 0
    created_at: float = 0.0


class SkillLearner:
    """技能学习者 - 从交互中自动学习新技能"""

    def __init__(self, skill_registry: SkillRegistry,
                 memory: PersistentMemory,
                 db_path: str = "./data/openakita.db"):
        self.skills = skill_registry
        self.memory = memory
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS learned_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL UNIQUE,
                source TEXT DEFAULT 'auto',
                code TEXT DEFAULT '',
                description TEXT DEFAULT '',
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s','now'))
            );
        """)
        self.conn.commit()

    def learn_from_interaction(self, query: str, response: str) -> Optional[str]:
        """从交互中识别可学习的模式"""
        patterns = {
            "search": ["搜索", "查找", "找一下", "search", "find"],
            "calculate": ["计算", "算一下", "加", "减", "乘", "除"],
            "translate": ["翻译", "translate", "翻成"],
            "summarize": ["总结", "概括", "summarize"],
        }

        for skill_name, keywords in patterns.items():
            if any(k in query.lower() for k in keywords):
                if not self.skills.get(skill_name):
                    return skill_name
        return None

    def record_learning(self, skill_name: str, source: str,
                        code: str = "", description: str = ""):
        """记录一次技能学习"""
        self.conn.execute("""
            INSERT INTO learned_skills (skill_name, source, code, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(skill_name) DO UPDATE SET
                source = excluded.source,
                code = excluded.code,
                description = excluded.description
        """, (skill_name, source, code, description))
        self.conn.commit()

    def record_execution(self, skill_name: str, success: bool):
        """记录技能执行结果"""
        col = "success_count" if success else "fail_count"
        self.conn.execute(
            f"UPDATE learned_skills SET {col} = {col} + 1 "
            "WHERE skill_name = ?", (skill_name,)
        )
        self.conn.commit()

    def get_learned_skills(self) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT * FROM learned_skills ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "id": r[0], "name": r[1], "source": r[2],
                "description": r[4], "success_count": r[5],
                "fail_count": r[6],
            }
            for r in rows
        ]

    def get_stats(self) -> Dict:
        row = self.conn.execute(
            "SELECT COUNT(*), SUM(success_count), SUM(fail_count) "
            "FROM learned_skills"
        ).fetchone()
        return {
            "total_learned": row[0] or 0,
            "total_success": row[1] or 0,
            "total_fails": row[2] or 0,
        }


class ErrorFixer:
    """自动错误修复系统"""

    def __init__(self, memory: PersistentMemory,
                 skill_registry: SkillRegistry):
        self.memory = memory
        self.skills = skill_registry

    def record_error(self, context: str, error: str):
        """记录错误以便后续分析和修复"""
        self.memory.save(
            key=f"error_{int(time.time())}",
            content=f"Context: {context}\nError: {error}",
            memory_type="error",
            tags="error,auto_fix",
        )

    def suggest_fix(self, error: str) -> Optional[str]:
        """基于历史模式建议修复"""
        known_fixes = {
            "not found": "检查路径或名称是否正确",
            "timeout": "建议增加超时时间或检查网络连接",
            "permission": "检查文件权限或 API Key 权限",
            "invalid": "验证输入参数格式是否正确",
            "connection": "检查网络连接和 API 端点配置",
        }
        for key, fix in known_fixes.items():
            if key in error.lower():
                return fix
        return None


class AutoImprover:
    """自我改进系统 - 整合学习、修复、优化"""

    def __init__(self, skill_registry: SkillRegistry,
                 memory: PersistentMemory,
                 db_path: str = "./data/openakita.db"):
        self.learner = SkillLearner(skill_registry, memory, db_path)
        self.fixer = ErrorFixer(memory, skill_registry)
        self.memory = memory

    def process_interaction(self, query: str, response: str,
                            error: Optional[str] = None) -> Dict:
        """处理一次交互，自动学习与改进"""
        results = {"learned": False, "fixed": False, "suggestion": None}

        # 1. 从交互中学习
        learned_skill = self.learner.learn_from_interaction(query, response)
        if learned_skill:
            self.learner.record_learning(learned_skill, "auto")
            results["learned"] = True
            results["learned_skill"] = learned_skill

        # 2. 错误修复
        if error:
            self.fixer.record_error(f"Query: {query}", error)
            fix = self.fixer.suggest_fix(error)
            if fix:
                results["fixed"] = True
                results["suggestion"] = fix

        return results

    def get_improvement_report(self) -> Dict:
        """生成改进报告"""
        return {
            "skills": self.learner.get_stats(),
            "learned_skills": self.learner.get_learned_skills(),
            "recent_errors": [
                {
                    "key": m.key,
                    "content": m.content[:200],
                    "created_at": m.created_at,
                }
                for m in self.memory.search("error", memory_type="error", limit=5)
            ],
        }