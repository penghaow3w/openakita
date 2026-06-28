"""持久化记忆系统 - 跨会话记忆"""
import json
import sqlite3
import time
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class MemoryItem:
    id: int = 0
    key: str = ""
    content: str = ""
    memory_type: str = "fact"    # fact | preference | skill | feedback | error
    tags: str = ""
    created_at: float = 0.0
    access_count: int = 0
    importance: float = 1.0


class PersistentMemory:
    """持久化记忆系统，确保 agent 不会"失忆""""

    def __init__(self, db_path: str = "./data/openakita.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'fact',
                tags TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s','now')),
                access_count INTEGER DEFAULT 0,
                importance REAL DEFAULT 1.0
            );
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
        """)
        self.conn.commit()

    def save(self, key: str, content: str, memory_type: str = "fact",
             tags: str = "", importance: float = 1.0):
        """保存一条记忆"""
        self.conn.execute("""
            INSERT INTO memories (key, content, memory_type, tags, importance)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                content = excluded.content,
                access_count = access_count + 1,
                importance = MAX(importance, excluded.importance)
        """, (key, content, memory_type, tags, importance))
        self.conn.commit()

    def recall(self, key: str) -> Optional[MemoryItem]:
        """回忆一条记忆"""
        row = self.conn.execute(
            "SELECT * FROM memories WHERE key = ?", (key,)
        ).fetchone()
        if row:
            self.conn.execute(
                "UPDATE memories SET access_count = access_count + 1 WHERE id = ?",
                (row[0],)
            )
            self.conn.commit()
            return MemoryItem(*row)
        return None

    def search(self, query: str, memory_type: Optional[str] = None,
               limit: int = 10) -> List[MemoryItem]:
        """搜索记忆 (基于关键词)"""
        sql = "SELECT * FROM memories WHERE content LIKE ?"
        params = [f"%{query}%"]
        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)
        sql += " ORDER BY importance DESC, access_count DESC LIMIT ?"
        params.append(limit)
        return [MemoryItem(*row) for row in self.conn.execute(sql, params).fetchall()]

    def recall_recent(self, limit: int = 20) -> List[MemoryItem]:
        """回忆最近的记忆"""
        rows = self.conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [MemoryItem(*row) for row in rows]

    def forget(self, older_than_days: int = 90):
        """遗忘旧的低重要性记忆"""
        cutoff = time.time() - older_than_days * 86400
        self.conn.execute(
            "DELETE FROM memories WHERE created_at < ? AND importance < 2.0",
            (cutoff,)
        )
        self.conn.commit()

    def get_all_memories(self) -> List[MemoryItem]:
        rows = self.conn.execute(
            "SELECT * FROM memories ORDER BY importance DESC, access_count DESC"
        ).fetchall()
        return [MemoryItem(*row) for row in rows]