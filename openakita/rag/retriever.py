"""知识检索系统 (RAG) - 让 AI 拥有外部知识"""
import os
import json
import hashlib
import sqlite3
from typing import List, Dict, Optional, Tuple


class Embedder:
    """简单的嵌入器 - 实际使用时替换为真正的 embedding 模型"""

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name

    def embed(self, text: str) -> List[float]:
        """将文本转为向量 (使用简单 hash 模拟，正式版接入 OpenAI/本地模型)"""
        # 使用 hash 生成固定维度伪向量
        h = hashlib.md5(text.encode()).hexdigest()
        vec = [int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
        # 归一化
        norm = sum(v*v for v in vec) ** 0.5
        return [v/norm for v in vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


class KnowledgeBase:
    """知识库 - 支持文档存储与检索"""

    def __init__(self, db_path: str = "./data/openakita.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.embedder = Embedder()
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                tags TEXT DEFAULT '',
                created_at REAL DEFAULT (strftime('%s','now')),
                access_count INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge(tags);
        """)
        self.conn.commit()

    def add_document(self, title: str, content: str,
                     source: str = "manual", tags: str = ""):
        """添加文档到知识库"""
        self.conn.execute(
            "INSERT INTO knowledge (title, content, source, tags) VALUES (?, ?, ?, ?)",
            (title, content, source, tags),
        )
        self.conn.commit()

    def add_documents_batch(self, documents: List[Dict]):
        """批量添加文档"""
        for doc in documents:
            self.add_document(
                doc.get("title", ""), doc.get("content", ""),
                doc.get("source", "manual"), doc.get("tags", ""),
            )

    def search(self, query: str, top_k: int = 5,
               tag_filter: Optional[str] = None) -> List[Dict]:
        """基于关键词搜索知识"""
        sql = "SELECT * FROM knowledge WHERE content LIKE ?"
        params = [f"%{query}%"]
        if tag_filter:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag_filter}%")
        sql += " ORDER BY access_count DESC LIMIT ?"
        params.append(top_k)

        results = []
        for row in self.conn.execute(sql, params).fetchall():
            self.conn.execute(
                "UPDATE knowledge SET access_count = access_count + 1 WHERE id = ?",
                (row[0],)
            )
            results.append({
                "id": row[0], "title": row[1], "content": row[2],
                "source": row[3], "tags": row[4], "created_at": row[5],
            })
        self.conn.commit()
        return results

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """检索并格式化为上下文文本"""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""
        parts = []
        for r in results:
            parts.append(f"[{r['title']}]({r['source']}): {r['content'][:500]}")
        return "\n\n".join(parts)

    def get_stats(self) -> Dict:
        """知识库统计"""
        count = self.conn.execute(
            "SELECT COUNT(*) FROM knowledge"
        ).fetchone()[0]
        return {"total_documents": count}


class RAGEngine:
    """RAG 引擎 - 整合检索与生成"""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.top_k = 5

    def augment_prompt(self, query: str, user_context: str = "") -> Tuple[str, str]:
        """增强提示词 - 检索相关知识并附加到 prompt"""
        context = self.kb.retrieve_context(query, top_k=self.top_k)
        if user_context:
            context = f"{user_context}\n\n{context}" if context else user_context
        return context, query

    def format_system_context(self, personality_name: str) -> str:
        """格式化系统上下文"""
        context = (
            f"你当前的人格是: {personality_name}\n"
            "你有知识库访问能力，可以检索相关信息来回答问题。\n"
        )
        return context