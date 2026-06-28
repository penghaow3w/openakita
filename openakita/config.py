"""全局配置管理"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OpenAkitaConfig:
    api_key: str = ""
    personality: str = "assistant"
    db_path: str = "./data/openakita.db"
    vector_db_path: str = "./data/vectors"
    log_level: str = "INFO"

    # LLM 配置
    llm_provider: str = "openai"       # openai | anthropic | ollama
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""

    # RAG 配置
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 512
    top_k: int = 5

    # RL 配置
    enable_self_optimize: bool = True
    feedback_window: int = 50
    learning_rate: float = 0.1

    # 记忆配置
    memory_ttl_days: int = 90
    enable_persistent_memory: bool = True

    # 技能学习
    enable_skill_learning: bool = True
    auto_fix_errors: bool = True

    # 平台集成 (逗号分隔)
    enabled_platforms: str = "web"

    @classmethod
    def from_env(cls) -> "OpenAkitaConfig":
        return cls(
            api_key=os.getenv("OPENAKITA_API_KEY", ""),
            personality=os.getenv("OPENAKITA_PERSONALITY", "assistant"),
            db_path=os.getenv("OPENAKITA_DB_PATH", "./data/openakita.db"),
            vector_db_path=os.getenv("OPENAKITA_VECTOR_DB_PATH", "./data/vectors"),
            log_level=os.getenv("OPENAKITA_LOG_LEVEL", "INFO"),
            llm_provider=os.getenv("OPENAKITA_LLM_PROVIDER", "openai"),
            llm_model=os.getenv("OPENAKITA_LLM_MODEL", "gpt-4o-mini"),
            llm_base_url=os.getenv("OPENAKITA_LLM_BASE_URL", ""),
            embedding_model=os.getenv("OPENAKITA_EMBEDDING_MODEL", "text-embedding-3-small"),
            chunk_size=int(os.getenv("OPENAKITA_CHUNK_SIZE", "512")),
            top_k=int(os.getenv("OPENAKITA_TOP_K", "5")),
            enable_self_optimize=os.getenv("OPENAKITA_ENABLE_OPTIMIZE", "true").lower() == "true",
            feedback_window=int(os.getenv("OPENAKITA_FEEDBACK_WINDOW", "50")),
            learning_rate=float(os.getenv("OPENAKITA_LEARNING_RATE", "0.1")),
            memory_ttl_days=int(os.getenv("OPENAKITA_MEMORY_TTL_DAYS", "90")),
            enable_persistent_memory=os.getenv("OPENAKITA_PERSISTENT_MEMORY", "true").lower() == "true",
            enable_skill_learning=os.getenv("OPENAKITA_SKILL_LEARNING", "true").lower() == "true",
            auto_fix_errors=os.getenv("OPENAKITA_AUTO_FIX", "true").lower() == "true",
            enabled_platforms=os.getenv("OPENAKITA_PLATFORMS", "web"),
        )