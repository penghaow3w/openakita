# OpenAkita - 自我进化 AI 助手框架

<div align="right">

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](Dockerfile)
</div>

**OpenAkita** 是一个开源的自我进化 AI 助手框架，融合了 **RAG（知识检索）** 和 **RL（强化学习）** 两大核心技术，让 AI 不仅会回答问题，还能从每次交互中学习、进化、自我修复。

---

## 这个代码有什么用？用在哪里？

### 核心能力

| 能力 | 说明 |
|------|------|
| 自我进化 | AI 会记住之前的对话，从反馈中学习，自动修复错误，越用越聪明 |
| 8 种人格 | 一键切换通用助手、管家、Jarvis 工程师、教师、心灵伙伴等角色 |
| 知识库 (RAG) | 上传文档/知识，AI 能检索并基于你的私有知识回答问题 |
| 自我优化 (RL) | 根据用户评分自动调整回答策略，低分反馈会触发改进 |
| 技能学习 | AI 可以学会新技能（搜索、翻译、计算等），且重启后不丢失 |
| 多平台支持 | 同时接入 Web、Discord、Slack、Telegram、企业微信、WhatsApp |

### 适用场景

**1. 个人助手**
- 私人知识管理：把个人文档、笔记导入知识库，AI 帮你检索和问答
- 日程管家：切换到"智能管家"人格，管理日常事务
- 学习伙伴：切换到"知识导师"人格，辅佐学习新知识

**2. 技术团队**
- Jarvis 工程师模式：代码审查、架构设计、DevOps 支持
- 团队知识库：统一管理技术文档，AI 自动检索回答
- 自动化学习：AI 会自动学习团队常用的命令和流程

**3. 客户服务**
- 接入 Slack/Discord/Telegram，7x24 自动客服
- 从历史交互中学习，越用越精准
- 低分反馈自动分析，持续优化服务质量

**4. 教育领域**
- 个性化教学助手，记住每个学生的进度和偏好
- 知识导师人格，耐心解答各类问题
- 可导入教材和讲义作为知识库

**5. 创意写作**
- 写作大师人格，辅助文案创作、故事编写
- 记录用户风格偏好，越写越符合需求

---

## 快速开始

### 方式一：3 分钟部署 (推荐)

```bash
# 1. 克隆
git clone https://github.com/your/openakita.git
cd openakita

# 2. 安装
pip install -r requirements.txt

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 OPENAKITA_API_KEY

# 4. 启动
python -m openakita web
```

打开浏览器访问 **http://localhost:8080**，即可开始对话。

### 方式二：Docker 部署

```bash
docker-compose up -d
```

### 方式三：CLI 模式 (无需 API Key 也可体验)

```bash
python -m openakita chat
```

---

## 配置指南

### 环境变量

所有配置通过 `.env` 文件或环境变量设置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAKITA_API_KEY` | `""` | **必需**，LLM API Key |
| `OPENAKITA_PERSONALITY` | `assistant` | 人格：assistant/butler/jarvis/teacher/counselor/writer/analyst/sage |
| `OPENAKITA_LLM_PROVIDER` | `openai` | LLM 提供商：openai/anthropic/ollama |
| `OPENAKITA_LLM_MODEL` | `gpt-4o-mini` | 模型名 |
| `OPENAKITA_DB_PATH` | `./data/openakita.db` | 数据库路径 |
| `OPENAKITA_PLATFORMS` | `web` | 启用平台：web/discord/slack/telegram/wechat/whatsapp |

### 支持的人格

| 人格 | 标签 | 适用场景 |
|------|------|----------|
| `assistant` | 通用助手 | 日常问答、任务处理 |
| `butler` | 智能管家 | 日程管理、生活服务 |
| `jarvis` | Jarvis 工程师 | 技术开发、系统架构 |
| `teacher` | 知识导师 | 知识讲解、学习辅导 |
| `counselor` | 心灵伙伴 | 情感支持、倾听陪伴 |
| `writer` | 写作大师 | 文案、故事、内容创作 |
| `analyst` | 数据分析师 | 数据处理、可视化洞察 |
| `sage` | 智者 | 深度思考、策略规划 |

运行时切换：输入 `/set jarvis` 或通过 Web 界面下拉菜单切换。

---

## 架构设计

```
openakita/
├── core/                    # 核心系统
│   ├── agent.py            # 自我进化 AI Agent 核心
│   ├── memory.py           # 持久化记忆系统 (SQLite)
│   ├── personality.py      # 8 种人格定义
│   └── skills.py           # 技能注册与执行
│
├── rag/                     # RAG 知识检索系统
│   └── retriever.py        # 知识库 + 检索增强生成
│
├── rl/                      # RL 自我优化系统
│   └── optimizer.py        # 反馈收集 + 策略优化
│
├── learning/                # 自主学习系统
│   └── auto_improve.py     # 技能学习 + 错误修复
│
├── integrations/            # 平台集成
│   └── platforms.py        # Web / Discord / Slack / Telegram / 微信 / WhatsApp
│
├── config.py               # 全局配置
└── main.py                 # 主程序入口
```

### 核心工作流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  1. 记忆检索 (Memory)                │
│     - 搜索相关历史对话               │
│     - 提取用户偏好                   │
├─────────────────────────────────────┤
│  2. 知识检索 (RAG)                   │
│     - 搜索知识库                     │
│     - 增强上下文                     │
├─────────────────────────────────────┤
│  3. 生成回复 (LLM/本地)              │
│     - 注入人格系统提示               │
│     - 调用 LLM API 或本地推理         │
├─────────────────────────────────────┤
│  4. 记录交互 (Memory)                │
│     - 保存到长期记忆                 │
│     - 更新对话历史                   │
├─────────────────────────────────────┤
│  5. 自动学习 (Learning)              │
│     - 识别可学习的技能模式           │
│     - 记录错误以便修复               │
├─────────────────────────────────────┤
│  6. 自我优化 (RL)                    │
│     - 分析反馈评分                   │
│     - 调整策略参数                   │
└─────────────────────────────────────┘
    │
    ▼
用户输出
```

---

## 命令行使用

```bash
# CLI 交互模式
python -m openakita chat

# Web 界面
python -m openakita web

# 查看状态
python -m openakita status

# 列出所有人格
python -m openakita personalities

# 交互式学习
python -m openakita learn
```

### CLI 内置命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/quit` | 退出 |
| `/personality` | 列出所有人格 |
| `/set <name>` | 切换人格，如 `/set jarvis` |
| `/status` | 查看 AI 状态 |
| `/stats` | 查看详细统计 |
| `/skills` | 列出所有技能 |
| `/learn <name>` | 交互式学习新技能 |
| `/forget` | 遗忘旧记忆 |
| `/feedback <0-10>` | 对上一条回复评分 |

---

## 代码实际用途详解

### 1. 持久化记忆系统 (`core/memory.py`)

AI 关掉聊天后不会忘记你。所有重要信息存入 SQLite：
- 你的名字、偏好、习惯
- 之前的聊天内容
- 自动提取的重要事实

```python
# 示例：AI 会记住你的偏好
你: 我喜欢简洁的回答
AI: 好的，我记住了，以后我会给你简洁的回答。

# 重启后再次对话
你: 我的偏好是什么？
AI: 我记得你喜欢简洁的回答风格。
```

### 2. RAG 知识检索 (`rag/retriever.py`)

让 AI 基于你的私有知识回答问题，而不是"凭空编造"：

```python
# 添加知识
agent.add_knowledge(
    title="项目架构说明",
    content="OpenAkita 采用模块化架构...",
    tags="tech,architecture"
)

# 提问时自动检索相关知识
你: 项目架构是怎样的？
AI: (自动检索知识库后回答) OpenAkita 采用模块化架构...
```

### 3. RL 自我优化 (`rl/optimizer.py`)

AI 根据你的反馈自动调整：
- 如果回答太啰嗦，给它低分，下次它会更简洁
- 如果回答不够专业，给它低分，下次会更严谨
- 长期跟踪各分类表现，持续改进

### 4. 技能学习 (`learning/auto_improve.py`)

AI 可以动态学习新技能，无需重启：

```python
# 教 AI 一个新技能
agent.learn_skill(
    name="weather",
    description="查询天气",
    code="""
def handler(city: str = "") -> str:
    return f"[Weather] {city} 的天气是晴天，25°C"
"""
)
```

### 5. 多平台集成 (`integrations/platforms.py`)

同一套 AI 核心，接入不同平台共享记忆：

```python
# Web 界面 (默认)
python -m openakita web

# Discord/Slack/Telegram Bot - 只需提供 Token
from openakita.integrations.platforms import DiscordIntegration
discord_bot = DiscordIntegration(agent, token="your-token")
```

---

## 示例场景

### 场景：搭建一个团队技术助手

```bash
# 1. 启动 Jarvis 人格
export OPENAKITA_PERSONALITY=jarvis
export OPENAKITA_API_KEY=sk-xxx

# 2. 启动 Web 界面
python -m openakita web
```

```python
# 3. 在代码中导入团队知识库
from openakita import OpenAkitaAgent
from openakita.config import OpenAkitaConfig

config = OpenAkitaConfig.from_env()
agent = OpenAkitaAgent(config)

# 导入技术文档
agent.add_knowledge("API 规范", "所有 API 使用 RESTful 风格...", tags="api")
agent.add_knowledge("部署流程", "生产环境使用 Docker Compose...", tags="devops")

# 现在团队成员可以直接问技术问题
# AI 会基于知识库 + 记忆 + 持续学习来回答
```

---

## 项目结构

```
openakita/
├── openakita/               # 核心 Python 包
│   ├── __init__.py
│   ├── __main__.py         # CLI 入口
│   ├── config.py           # 配置管理
│   ├── main.py             # 主程序
│   ├── core/               # 核心系统
│   │   ├── agent.py        # Agent 核心
│   │   ├── memory.py       # 记忆系统
│   │   ├── personality.py  # 人格系统
│   │   └── skills.py       # 技能系统
│   ├── rag/                # 知识检索
│   │   └── retriever.py    # RAG 引擎
│   ├── rl/                 # 自我优化
│   │   └── optimizer.py    # RL 引擎
│   ├── learning/           # 学习系统
│   │   └── auto_improve.py # 自动学习与修复
│   └── integrations/       # 平台集成
│       └── platforms.py    # 6 种平台适配器
│
├── requirements.txt        # Python 依赖
├── .env.example            # 配置模板
├── Dockerfile              # Docker 构建
├── docker-compose.yml      # Docker 编排
├── quickstart.sh           # Linux/Mac 快速启动
├── start.bat               # Windows 快速启动
└── README.md               # 本文件
```

---

## 技术栈

- **Python 3.9+** - 核心语言
- **SQLite** - 持久化存储 (记忆、知识库、反馈)
- **Flask** - Web 界面
- **OpenAI API / Anthropic / Ollama** - LLM 提供商支持
- **Docker** - 容器化部署

---

## License

MIT License

---

> OpenAkita — 让你的 AI 越用越聪明