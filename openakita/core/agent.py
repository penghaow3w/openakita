"""OpenAkita 核心 Agent - 融合 RAG + RL + 自动学习的自我进化 AI"""
import time
from typing import Dict, List, Optional, Callable

from .memory import PersistentMemory
from .personality import Personality, get_personality, list_personalities
from .skills import SkillRegistry

from ..rag.retriever import KnowledgeBase, RAGEngine
from ..rl.optimizer import SelfOptimizer
from ..learning.auto_improve import AutoImprover
from ..config import OpenAkitaConfig


class OpenAkitaAgent:
    """自我进化 AI Agent 核心"""

    def __init__(self, config: OpenAkitaConfig):
        self.config = config
        self.db_path = config.db_path

        # 核心系统
        self.memory = PersistentMemory(config.db_path)
        self.skills = SkillRegistry()
        self.knowledge_base = KnowledgeBase(config.db_path)
        self.rag = RAGEngine(self.knowledge_base)

        # 自我进化系统
        self.optimizer = SelfOptimizer(config.db_path, config.learning_rate)
        self.improver = AutoImprover(self.skills, self.memory, config.db_path)

        # 人格系统
        self._personality: Personality = get_personality(config.personality)

        # 对话历史
        self._history: List[Dict] = []
        self._max_history = 20

    @property
    def personality(self) -> Personality:
        return self._personality

    def set_personality(self, name: str):
        """切换人格"""
        self._personality = get_personality(name)
        self.config.personality = name
        self.memory.save(
            key="preferred_personality",
            content=name,
            memory_type="preference",
            importance=3.0,
        )

    def chat(self, message: str) -> str:
        """处理用户消息并返回回复"""
        # 1. 检索相关记忆
        memories = self._get_relevant_memories(message)

        # 2. 检索相关知识
        context = self.rag.augment_prompt(message)
        knowledge_context = context[0] if context else ""

        # 3. 构建系统提示
        system_prompt = self._build_system_prompt(memories, knowledge_context)

        # 4. 生成回复 (使用 LLM 或本地模式)
        response = self._generate_response(system_prompt, message)

        # 5. 记录交互
        self._record_interaction(message, response)

        # 6. 自动学习
        if self.config.enable_skill_learning:
            try:
                result = self.improver.process_interaction(message, response)
                if result.get("learned"):
                    print(f"[学习] 检测到新技能需求: {result.get('learned_skill')}")
            except Exception:
                pass

        # 7. 自动优化
        if self.config.enable_self_optimize:
            try:
                self.optimizer.optimize()
            except Exception:
                pass

        return response

    def _get_relevant_memories(self, query: str) -> List[Dict]:
        """获取相关记忆"""
        results = self.memory.search(query, limit=5)
        return [
            {"key": m.key, "content": m.content, "type": m.memory_type}
            for m in results
        ]

    def _build_system_prompt(self, memories: List[Dict],
                              knowledge_context: str = "") -> str:
        """构建系统提示"""
        personality = self._personality

        # 基础系统提示
        prompt = personality.system_prompt

        # 附加能力说明
        prompt += (
            "\n\n## 能力说明\n"
            f"- 人格: {personality.label}\n"
            f"- 响应风格: {personality.response_style}\n"
        )

        # 记忆注入
        if memories:
            prompt += "\n## 相关记忆 (跨会话)\n"
            for m in memories[:3]:
                prompt += f"- {m['content'][:200]}\n"

        # 知识注入
        if knowledge_context:
            prompt += f"\n## 知识库参考\n{knowledge_context}\n"

        # 技能列表
        skills = self.skills.list_skills()
        if skills:
            prompt += "\n## 可用技能\n"
            for s in skills:
                prompt += f"- {s['name']}: {s['description']}\n"

        # 自我进化说明
        prompt += (
            "\n## 自我进化\n"
            "- 你会从每次对话中学习，持续提升能力\n"
            "- 你会记住用户的偏好和重要信息\n"
            "- 你会自动修复错误并学习新技能\n"
        )

        return prompt

    def _generate_response(self, system_prompt: str, message: str) -> str:
        """生成回复"""
        personality = self._personality

        # 构建完整 prompt
        full_prompt = f"{system_prompt}\n\n用户: {message}\n\n{personality.label}:"

        # 添加对话历史
        history_text = ""
        for h in self._history[-5:]:
            role = "用户" if h["role"] == "user" else personality.label
            history_text += f"{role}: {h['content']}\n"
        if history_text:
            full_prompt = f"{system_prompt}\n\n## 对话历史\n{history_text}\n\n用户: {message}\n\n{personality.label}:"

        # 尝试使用 LLM API
        response = self._call_llm(full_prompt)

        if response:
            return response

        # 本地 fallback：使用内置技能
        return self._local_response(message)

    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用 LLM API"""
        provider = self.config.llm_provider
        api_key = self.config.api_key

        if not api_key:
            return None

        try:
            if provider == "openai":
                return self._call_openai(prompt)
            elif provider == "ollama":
                return self._call_ollama(prompt)
            elif provider == "anthropic":
                return self._call_anthropic(prompt)
        except Exception as e:
            print(f"[LLM 调用失败] {e}")
            return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        """调用 OpenAI API"""
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
            base_url = self.config.llm_base_url or "https://api.openai.com/v1"
            data = {
                "model": self.config.llm_model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": prompt.split("用户: ")[-1].split("\n")[0]},
                ],
                "temperature": self._personality.temperature,
                "max_tokens": self._personality.max_tokens,
            }
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers=headers, json=data, timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用本地 Ollama"""
        try:
            import requests
            data = {
                "model": self.config.llm_model,
                "prompt": prompt,
                "stream": False,
            }
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json=data, timeout=60,
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception:
            pass
        return None

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """调用 Anthropic Claude"""
        try:
            import requests
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            data = {
                "model": self.config.llm_model or "claude-3-haiku-20240307",
                "max_tokens": self._personality.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers, json=data, timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["content"][0]["text"]
        except Exception:
            pass
        return None

    def _local_response(self, message: str) -> str:
        """本地模式回复 (不依赖 LLM API)"""
        # 检查是否有匹配的技能
        for skill in self.skills.list_skills():
            name = skill["name"]
            if name == "web_search" and any(
                k in message for k in ["搜索", "查找", "search", "find"]
            ):
                return self.skills.execute(name, query=message)
            if name == "calculate" and any(
                k in message for k in ["计算", "加", "减", "乘", "除"]
            ):
                return self.skills.execute(name, expression=message)
            if name == "translate" and "翻译" in message:
                return self.skills.execute(name, text=message)
            if name == "analyze_sentiment":
                result = self.skills.execute(name, text=message)
                return f"[情感分析] 这条消息的情感倾向是: {result}"

        # 默认回复 - 注入人格风格
        return self._default_reply(message)

    def _default_reply(self, message: str) -> str:
        """默认回复 - 体现人格特征"""
        label = self._personality.label
        style = self._personality.response_style

        # 不同风格的回复模板
        style_prefixes = {
            "friendly": f"[{label}] 收到你的消息！",
            "formal": f"[{label}] 已收到您的消息。",
            "professional": f"[{label}] 收到: ",
            "casual": f"[{label}] 嗯哼~ ",
            "creative": f"[{label}] ✨ ",
        }
        prefix = style_prefixes.get(style, f"[{label}] ")

        # 检查记忆中有无相关信息
        memories = self.memory.search(message, limit=3)
        memory_hint = ""
        if memories:
            memory_hint = f"\n(我记得你之前提过: {memories[0].content[:80]})"

        return (
            f"{prefix}我收到了你的问题。{memory_hint}"
            f"\n\n提示: 连接 LLM API 后我会给出更智能的回答。"
            f"\n设置环境变量 OPENAKITA_API_KEY 即可激活 AI 能力。"
        )

    def _record_interaction(self, message: str, response: str):
        """记录交互到历史和记忆"""
        # 添加到历史
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "assistant", "content": response})
        if len(self._history) > self._max_history * 2:
            self._history = self._history[-self._max_history * 2:]

        # 保存到长期记忆 (重要信息)
        if len(message) > 5:
            self.memory.save(
                key=f"qa_{int(time.time())}",
                content=f"Q: {message[:200]}\nA: {response[:200]}",
                memory_type="fact",
                tags="interaction",
                importance=1.0,
            )

    def provide_feedback(self, query: str, response: str,
                         rating: float, feedback_text: str = ""):
        """提供反馈以帮助 AI 改进"""
        self.optimizer.record_outcome(query, response, rating, feedback_text)

    def learn_skill(self, name: str, description: str, code: str):
        """手动教会 AI 一个新技能"""
        try:
            self.skills.learn_new_skill(name, description, code)
            self.improver.learner.record_learning(name, "user_teach", code, description)
            self.memory.save(
                key=f"skill_{name}",
                content=f"Learned skill: {name} - {description}",
                memory_type="skill",
            )
            return True
        except Exception as e:
            return False

    def add_knowledge(self, title: str, content: str,
                      source: str = "manual", tags: str = ""):
        """添加知识到知识库"""
        self.knowledge_base.add_document(title, content, source, tags)

    def get_stats(self) -> Dict:
        """获取完整统计信息"""
        # 学习统计
        learning_stats = self.improver.get_improvement_report()

        # RL 统计
        rl_stats = self.optimizer.get_stats()

        # 记忆统计
        all_memories = self.memory.get_all_memories()
        memory_count = len(all_memories)

        return {
            "personality": self._personality.label,
            "personality_name": self._personality.name,
            "memory_count": memory_count,
            "skill_count": len(self.skills.list_skills()),
            "learned_skills_count": len(learning_stats.get("learned_skills", [])),
            "feedback_count": rl_stats.get("total", 0),
            "avg_rating": rl_stats.get("avg_rating", 0),
            "knowledge_count": self.knowledge_base.get_stats().get("total_documents", 0),
        }

    def get_status_report(self) -> str:
        """生成状态报告"""
        stats = self.get_stats()
        lines = [
            "=" * 40,
            "OpenAkita 自我进化 AI - 状态报告",
            "=" * 40,
            f"人格: {stats['personality']} ({stats['personality_name']})",
            f"记忆: {stats['memory_count']} 条",
            f"技能: {stats['skill_count']} 项 (自学: {stats['learned_skills_count']} 项)",
            f"反馈: {stats['feedback_count']} 条 | 平均评分: {stats.get('avg_rating', 0):.2f}",
            f"知识库: {stats['knowledge_count']} 篇文档",
            "-" * 40,
        ]

        # 优化建议
        if stats.get("avg_rating", 1.0) < 0.5:
            lines.append("建议: 需要改进回答质量，考虑降低 temperature 或增加知识库。")

        return "\n".join(lines)