"""Web 界面集成 (Flask)"""
import json
from typing import Optional
from ..core.agent import OpenAkitaAgent


class WebIntegration:
    """Web Chat 集成"""

    def __init__(self, agent: OpenAkitaAgent, host: str = "0.0.0.0",
                 port: int = 8080):
        self.agent = agent
        self.host = host
        self.port = port
        self._app = None

    def create_app(self):
        """创建 Flask Web 应用"""
        try:
            from flask import Flask, request, jsonify, render_template_string
            import secrets

            app = Flask(__name__)
            secret = secrets.token_hex(16)
            app.secret_key = secret

            HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenAkita - 自我进化 AI 助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #0f0f1a; color: #e0e0e0; height: 100vh; display: flex; }
        .sidebar { width: 260px; background: #1a1a2e; padding: 20px; display: flex;
                   flex-direction: column; border-right: 1px solid #2a2a4a; }
        .sidebar h1 { font-size: 18px; color: #6c63ff; margin-bottom: 20px; }
        .sidebar .status { font-size: 12px; color: #888; margin-bottom: 20px; }
        .sidebar .status .dot { display: inline-block; width: 8px; height: 8px;
                                background: #4caf50; border-radius: 50%; margin-right: 6px; }
        .personality-select { width: 100%; padding: 8px; background: #252542;
                              border: 1px solid #3a3a5a; color: #e0e0e0;
                              border-radius: 6px; margin-bottom: 16px; }
        .personality-desc { font-size: 12px; color: #888; margin-bottom: 16px;
                            padding: 8px; background: #252542; border-radius: 6px; }
        .stats { font-size: 12px; color: #666; margin-top: auto; }
        .stats div { margin-bottom: 4px; }
        .main { flex: 1; display: flex; flex-direction: column; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; }
        .message { margin-bottom: 16px; max-width: 80%; }
        .message.user { margin-left: auto; }
        .message .bubble { padding: 12px 16px; border-radius: 12px; white-space: pre-wrap; }
        .message.user .bubble { background: #6c63ff; color: white;
                                border-bottom-right-radius: 4px; }
        .message.assistant .bubble { background: #252542; color: #e0e0e0;
                                     border-bottom-left-radius: 4px; }
        .message .time { font-size: 11px; color: #666; margin-top: 4px; }
        .message.user .time { text-align: right; }
        .input-area { padding: 16px 20px; background: #1a1a2e; border-top: 1px solid #2a2a4a; }
        .input-row { display: flex; gap: 10px; }
        .input-row input { flex: 1; padding: 12px; background: #252542; border: 1px solid #3a3a5a;
                           color: #e0e0e0; border-radius: 8px; font-size: 14px; }
        .input-row input:focus { outline: none; border-color: #6c63ff; }
        .input-row button { padding: 12px 24px; background: #6c63ff; color: white;
                            border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .input-row button:hover { background: #5a52e0; }
        .typing { color: #888; font-size: 13px; padding: 8px 16px; }
        .personality-info { margin-bottom: 8px; }
        .personality-info .label { font-size: 11px; color: #6c63ff;
                                   background: #252542; padding: 2px 8px; border-radius: 4px; }
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .message { max-width: 90%; }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>OpenAkita</h1>
        <div class="status"><span class="dot"></span>运行中</div>
        <label style="font-size:12px;color:#888;margin-bottom:4px;">人格切换</label>
        <select class="personality-select" id="personality" onchange="switchPersonality(this.value)">
            {% for p in personalities %}
            <option value="{{ p.name }}" {% if p.name == current %}selected{% endif %}>
                {{ p.label }}
            </option>
            {% endfor %}
        </select>
        <div class="personality-desc" id="personality-desc">{{ description }}</div>
        <div class="stats">
            <div>记忆: {{ memory_count }} 条</div>
            <div>技能: {{ skill_count }} 项</div>
            <div>反馈: {{ feedback_count }} 条</div>
        </div>
    </div>
    <div class="main">
        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="bubble">你好！我是 OpenAkita，你的自我进化 AI 助手。有什么可以帮你的？</div>
                <div class="time">刚刚</div>
            </div>
        </div>
        <div class="input-area">
            <div class="input-row">
                <input type="text" id="input" placeholder="输入你的问题..." autofocus
                       onkeydown="if(event.key==='Enter') send()">
                <button onclick="send()">发送</button>
            </div>
        </div>
    </div>
    <script>
        const personalities = {{ personalities|tojson }};
        function switchPersonality(name) {
            const p = personalities.find(x => x.name === name);
            document.getElementById('personality-desc').textContent =
                p ? p.description : '';
            fetch('/personality', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({personality: name})
            });
        }
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value.trim();
            if (!msg) return;
            input.value = '';
            const msgsDiv = document.getElementById('messages');
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.innerHTML = '<div class="bubble">' + escapeHtml(msg) +
                '</div><div class="time">刚刚</div>';
            msgsDiv.appendChild(userDiv);

            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing';
            typingDiv.textContent = '思考中...';
            msgsDiv.appendChild(typingDiv);
            msgsDiv.scrollTop = msgsDiv.scrollHeight;

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                typingDiv.remove();
                const aiDiv = document.createElement('div');
                aiDiv.className = 'message assistant';
                aiDiv.innerHTML = '<div class="bubble">' + escapeHtml(data.response) +
                    '</div><div class="time">' + new Date().toLocaleTimeString() + '</div>';
                msgsDiv.appendChild(aiDiv);
            } catch(e) {
                typingDiv.remove();
                const errDiv = document.createElement('div');
                errDiv.className = 'message assistant';
                errDiv.innerHTML = '<div class="bubble">抱歉，发生了错误，请重试。</div>';
                msgsDiv.appendChild(errDiv);
            }
            msgsDiv.scrollTop = msgsDiv.scrollHeight;
        }
        function escapeHtml(text) {
            const d = document.createElement('div');
            d.textContent = text;
            return d.innerHTML;
        }
    </script>
</body>
</html>"""

            @app.route("/")
            def index():
                from ..core.personality import get_personality, list_personalities
                current = self.agent.config.personality
                p = get_personality(current)
                stats = self.agent.get_stats()
                return render_template_string(
                    HTML_TEMPLATE,
                    personalities=list_personalities(),
                    current=current,
                    description=p.description,
                    memory_count=stats.get("memory_count", 0),
                    skill_count=stats.get("skill_count", 0),
                    feedback_count=stats.get("feedback_count", 0),
                )

            @app.route("/chat", methods=["POST"])
            def chat():
                data = request.get_json(force=True)
                msg = data.get("message", "")
                if not msg:
                    return jsonify({"response": "请输入消息"})
                response = self.agent.chat(msg)
                return jsonify({"response": response})

            @app.route("/personality", methods=["POST"])
            def change_personality():
                data = request.get_json(force=True)
                name = data.get("personality", "assistant")
                self.agent.set_personality(name)
                return jsonify({"status": "ok"})

            self._app = app
            return app
        except ImportError:
            print("Flask 未安装，Web 集成不可用。请运行: pip install flask")
            return None

    def start(self, debug: bool = False):
        """启动 Web 服务器"""
        if not self._app:
            self.create_app()
        if self._app:
            print(f"🌐 OpenAkita Web 界面启动: http://{self.host}:{self.port}")
            self._app.run(host=self.host, port=self.port, debug=debug)


class DiscordIntegration:
    """Discord Bot 集成"""

    def __init__(self, agent: "OpenAkitaAgent", token: str = ""):
        self.agent = agent
        self.token = token

    async def handle_message(self, message):
        content = message.content
        response = self.agent.chat(content)
        await message.channel.send(response)


class SlackIntegration:
    """Slack Bot 集成"""

    def __init__(self, agent: "OpenAkitaAgent", token: str = "", signing_secret: str = ""):
        self.agent = agent

    def handle_event(self, event):
        if "text" in event:
            return self.agent.chat(event["text"])
        return ""


class TelegramIntegration:
    """Telegram Bot 集成"""

    def __init__(self, agent: "OpenAkitaAgent", token: str = ""):
        self.agent = agent
        self.token = token

    def handle_update(self, update):
        if hasattr(update, "message") and update.message.text:
            return self.agent.chat(update.message.text)
        return ""


class WeChatIntegration:
    """企业微信 Bot 集成"""

    def __init__(self, agent: "OpenAkitaAgent", webhook_url: str = ""):
        self.agent = agent
        self.webhook_url = webhook_url

    def handle_message(self, content: str) -> str:
        return self.agent.chat(content)


class WhatsAppIntegration:
    """WhatsApp Business API 集成"""

    def __init__(self, agent: "OpenAkitaAgent", phone_number_id: str = "",
                 token: str = ""):
        self.agent = agent
        self.phone_number_id = phone_number_id
        self.token = token

    def handle_message(self, text: str) -> str:
        return self.agent.chat(text)