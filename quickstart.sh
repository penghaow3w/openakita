#!/bin/bash
# OpenAkita 快速启动脚本 (Linux/Mac)
set -e

echo "========================================"
echo "  OpenAkita - 自我进化 AI 助手"
echo "  3 分钟快速部署"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python，请先安装 Python 3.9+"
    exit 1
fi

# 安装依赖
echo "[1/3] 安装依赖..."
pip3 install -r requirements.txt

# 检查 .env
if [ ! -f .env ]; then
    echo "[2/3] 创建配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件填入你的 API Key"
else
    echo "[2/3] 配置文件已存在，跳过"
fi

# 启动
echo "[3/3] 启动 OpenAkita..."
echo ""
echo "选择模式:"
echo "  web  - Web 界面 (默认 http://localhost:8080)"
echo "  chat - CLI 交互模式"
echo ""

read -p "启动模式 (web/chat, 默认 web): " mode
mode=${mode:-web}

python3 -m openakita $mode