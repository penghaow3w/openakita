@echo off
REM OpenAkita 快速启动脚本 (Windows)
echo ========================================
echo    OpenAkita - 自我进化 AI 助手
echo    3 分钟快速部署
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt

REM 检查 .env
if not exist .env (
    echo [2/3] 创建配置文件...
    copy .env.example .env
    echo 请编辑 .env 文件填入你的 API Key
) else (
    echo [2/3] 配置文件已存在，跳过
)

REM 启动
echo [3/3] 启动 OpenAkita...
echo.
echo 选择模式:
echo   web  - Web 界面 (默认 http://localhost:8080)
echo   chat - CLI 交互模式
echo.

set /p mode="启动模式 (web/chat, 默认 web): "
if "%mode%"=="" set mode=web

python -m openakita %mode%

pause