"""OpenAkita 主程序入口"""
import os
import sys
import time
import json
from typing import Dict, Optional

from .config import OpenAkitaConfig
from .core.agent import OpenAkitaAgent
from .core.personality import get_personality, list_personalities
from .integrations.platforms import WebIntegration


class OpenAkita:
    """OpenAkita 应用主类"""

    def __init__(self, config: Optional[OpenAkitaConfig] = None):
        self.config = config or OpenAkitaConfig.from_env()
        self.agent = OpenAkitaAgent(self.config)

        # 加载 .env 文件
        self._load_env()

    def _load_env(self):
        """加载 .env 文件"""
        try:
            dotenv_path = os.path.join(os.getcwd(), ".env")
            if os.path.exists(dotenv_path):
                with open(dotenv_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
                # 重新加载配置
                self.config = OpenAkitaConfig.from_env()
                self.agent = OpenAkitaAgent(self.config)
        except Exception:
            pass

    def run(self):
        """运行程序 (CLI 模式)"""
        if len(sys.argv) > 1:
            cmd = sys.argv[1]
            if cmd == "web":
                return self.run_web()
            elif cmd == "chat":
                return self._run_cli()
            elif cmd == "status":
                return self._show_status()
            elif cmd == "personalities":
                return self._list_personalities()
            elif cmd == "learn":
                return self._run_learn()
            elif cmd == "--help" or cmd == "-h":
                return self._show_help()
            else:
                print(f"未知命令: {cmd}")
                self._show_help()
        else:
            self._run_cli()

    def _run_cli(self):
        """CLI 交互模式"""
        self._print_banner()
        print(f"人格: {self.agent.personality.label}")
        print("输入 /help 查看命令, /quit 退出")
        print("-" * 50)

        while True:
            try:
                msg = input("\n你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not msg:
                continue

            if msg.startswith("/"):
                self._handle_command(msg)
                continue

            # 处理消息
            start = time.time()
            response = self.agent.chat(msg)
            elapsed = time.time() - start
            print(f"\n{self.agent.personality.label}: {response}")
            print(f"\n[耗时: {elapsed:.2f}s]")

    def _handle_command(self, cmd: str):
        """处理 CLI 命令"""
        cmd = cmd.lower().strip()

        if cmd in ("/quit", "/exit", "/q"):
            print("再见！")
            sys.exit(0)

        elif cmd == "/help":
            print("""
命令列表:
  /help           - 显示帮助
  /quit           - 退出
  /personality    - 列出所有人格
  /set <name>     - 切换人格 (如 /set jarvis)
  /status         - 查看 AI 状态
  /stats          - 查看详细统计
  /skills         - 列出所有技能
  /learn <name>   - 学习新技能 (交互式)
  /forget         - 遗忘旧记忆
  /feedback <n>   - 对上个回答评分 (0-10)
            """)

        elif cmd == "/personality":
            for p in list_personalities():
                print(f"  {p['name']:15s} - {p['label']}: {p['description']}")

        elif cmd.startswith("/set "):
            name = cmd[5:].strip()
            if get_personality(name).name != "assistant" or name == "assistant":
                self.agent.set_personality(name)
                print(f"已切换人格为: {self.agent.personality.label}")
            else:
                print(f"未知人格: {name}")

        elif cmd == "/status":
            print(self.agent.get_status_report())

        elif cmd == "/stats":
            stats = self.agent.get_stats()
            print(json.dumps(stats, ensure_ascii=False, indent=2))

        elif cmd == "/skills":
            skills = self.agent.skills.list_skills()
            print(f"共有 {len(skills)} 项技能:")
            for s in skills:
                learned = " [自学]" if s.get("auto_learned") else ""
                print(f"  - {s['name']}: {s['description']}{learned}")

        elif cmd.startswith("/learn "):
            name = cmd[7:].strip()
            if not name:
                print("请输入技能名称")
                return
            print(f"准备学习新技能: {name}")
            desc = input("技能描述: ").strip()
            print("请输入 Python 代码 (handler 函数):")
            print("示例:\ndef handler(param: str = \"\") -> str:\n    return f\"处理: {param}\"")
            lines = []
            try:
                while True:
                    line = input()
                    if line == "---":
                        break
                    lines.append(line)
            except EOFError:
                pass
            code = "\n".join(lines)
            if name and code:
                success = self.agent.learn_skill(name, desc, code)
                print("学习成功!" if success else "学习失败")

        elif cmd == "/forget":
            self.agent.memory.forget(older_than_days=1)
            print("已遗忘旧记忆")

        elif cmd.startswith("/feedback "):
            try:
                rating = int(cmd[10:].strip()) / 10.0
                rating = max(0.0, min(1.0, rating))
                if self.agent._history:
                    last_q = self.agent._history[-2]["content"]
                    last_a = self.agent._history[-1]["content"]
                    self.agent.provide_feedback(last_q, last_a, rating)
                    print(f"已记录评分: {rating:.1f}")
            except (IndexError, ValueError):
                print("格式: /feedback <0-10>")

        else:
            print(f"未知命令: {cmd}")

    def run_web(self, host: str = "0.0.0.0", port: int = 8080):
        """启动 Web 界面"""
        web = WebIntegration(self.agent, host=host, port=port)
        web.start(debug=False)

    def _show_status(self):
        """显示状态"""
        print(self.agent.get_status_report())

    def _list_personalities(self):
        """列出人格"""
        for p in list_personalities():
            print(f"  {p['name']:15s} - {p['label']}: {p['description']}")

    def _run_learn(self):
        """交互式学习"""
        print("OpenAkita 交互式学习模式")
        print("输入问题和期望的回答，AI 将从中学习。")
        print("输入 /done 结束学习。")

        examples = []
        while True:
            q = input("\n问题 (或 /done): ").strip()
            if q == "/done":
                break
            a = input("期望回答: ").strip()
            if q and a:
                examples.append((q, a))
                self.agent.memory.save(
                    key=f"learn_example_{int(time.time())}",
                    content=f"Q: {q}\nA: {a}",
                    memory_type="skill",
                    tags="learning_example",
                )
                print("已学习此示例！")
        print(f"学习了 {len(examples)} 个示例。")

    def _print_banner(self):
        """打印启动 Banner"""
        banner = """
    ╔══════════════════════════════════════╗
    ║        OpenAkita                     ║
    ║    自我进化 AI 助手框架              ║
    ║                                     ║
    ║  RAG + RL + 自动学习 + 多平台       ║
    ╚══════════════════════════════════════╝
        """
        print(banner)

    def _show_help(self):
        """显示帮助"""
        self._print_banner()
        print("用法: python -m openakita [命令]")
        print()
        print("命令:")
        print("  (无参数)     启动 CLI 交互模式")
        print("  chat         启动 CLI 交互模式")
        print("  web          启动 Web 界面 (默认 http://0.0.0.0:8080)")
        print("  status       查看 AI 状态")
        print("  personalities 列出所有人格")
        print("  learn        交互式学习模式")
        print()
        print("环境变量:")
        print("  OPENAKITA_API_KEY       - LLM API Key")
        print("  OPENAKITA_PERSONALITY   - 人格 (默认: assistant)")
        print("  OPENAKITA_LLM_PROVIDER  - LLM 提供商 (openai/ollama/anthropic)")
        print("  OPENAKITA_LLM_MODEL     - 模型名称")
        print("  OPENAKITA_PLATFORMS     - 启用平台 (web/discord/slack/...)")
        print()
        print("示例:")
        print("  python -m openakita")
        print("  python -m openakita web")
        print("  OPENAKITA_API_KEY=sk-xxx python -m openakita")