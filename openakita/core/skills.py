"""技能系统 - 可学习的技能注册与执行"""
import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Skill:
    name: str
    description: str
    handler: Callable
    category: str = "general"
    version: str = "1.0.0"
    requires: List[str] = field(default_factory=list)


class SkillRegistry:
    """技能注册中心"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._auto_learned: Dict[str, Skill] = {}
        self._discover_builtins()

    def _discover_builtins(self):
        """发现内置技能"""
        builtins = {
            "web_search": Skill(
                name="web_search",
                description="搜索互联网获取实时信息",
                handler=self._web_search,
                category="information",
            ),
            "summarize": Skill(
                name="summarize",
                description="总结文本内容",
                handler=self._summarize,
                category="text_processing",
            ),
            "translate": Skill(
                name="translate",
                description="翻译文本到目标语言",
                handler=self._translate,
                category="text_processing",
            ),
            "calculate": Skill(
                name="calculate",
                description="执行数学计算",
                handler=self._calculate,
                category="utility",
            ),
            "analyze_sentiment": Skill(
                name="analyze_sentiment",
                description="分析文本情感倾向",
                handler=self._analyze_sentiment,
                category="analysis",
            ),
        }
        for name, skill in builtins.items():
            self.register(name, skill)

    def register(self, name: str, skill: Skill, auto_learned: bool = False):
        """注册技能"""
        target = self._auto_learned if auto_learned else self._skills
        target[name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name) or self._auto_learned.get(name)

    def execute(self, name: str, **kwargs) -> Any:
        skill = self.get(name)
        if not skill:
            raise KeyError(f"未知技能: {name}")
        return skill.handler(**kwargs)

    def list_skills(self) -> List[Dict]:
        skills = []
        for name, skill in self._skills.items():
            skills.append({
                "name": name, "description": skill.description,
                "category": skill.category, "version": skill.version,
                "auto_learned": False,
            })
        for name, skill in self._auto_learned.items():
            skills.append({
                "name": name, "description": skill.description,
                "category": skill.category, "version": skill.version,
                "auto_learned": True,
            })
        return skills

    def learn_new_skill(self, name: str, description: str,
                        handler_code: str) -> Skill:
        """自主学习新技能 (动态创建)"""
        try:
            namespace = {}
            exec(handler_code, namespace)
            handler = namespace.get("handler") or namespace.get(
                list(namespace.keys())[0]
            )
            if not callable(handler):
                raise ValueError("技能代码必须包含一个可调用对象")
            skill = Skill(
                name=name, description=description,
                handler=handler, category="auto_learned",
            )
            self.register(name, skill, auto_learned=True)
            return skill
        except Exception as e:
            raise ValueError(f"学习新技能失败: {e}")

    # ---- 内置技能实现 ----
    def _web_search(self, query: str = "", **kwargs) -> str:
        return f"[Web Search] 搜索: {query}"

    def _summarize(self, text: str = "", **kwargs) -> str:
        return f"[Summary] 已总结 {len(text)} 字符文本"

    def _translate(self, text: str = "", target_lang: str = "中文", **kwargs) -> str:
        return f"[Translation] 已翻译到 {target_lang}"

    def _calculate(self, expression: str = "", **kwargs) -> str:
        try:
            safe = expression.replace(" ", "")
            if not all(c in "0123456789+-*/()." for c in safe):
                return "不支持表达式中的非法字符"
            return str(eval(safe))
        except Exception as e:
            return f"计算错误: {e}"

    def _analyze_sentiment(self, text: str = "", **kwargs) -> str:
        positive_words = ["好", "棒", "喜欢", "优秀", "great", "good", "love", "amazing"]
        negative_words = ["差", "坏", "讨厌", "糟糕", "bad", "terrible", "hate", "awful"]
        pos_count = sum(1 for w in positive_words if w in text.lower())
        neg_count = sum(1 for w in negative_words if w in text.lower())
        if pos_count > neg_count:
            return "正面"
        elif neg_count > pos_count:
            return "负面"
        return "中性"