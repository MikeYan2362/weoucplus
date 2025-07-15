@echo off
chcp 65001 >nul
echo ===========================================
echo    WePlus 开发者后台管理系统
echo ===========================================
echo.
echo 🚀 正在启动管理后台...
echo 📍 访问地址: http://localhost:9000
echo 👤 默认账号: admin
echo 🔑 默认密码: admin123
echo.
echo 按 Ctrl+C 停止服务
echo ===========================================
echo.

cd /d "%~dp0"
python app.py

pause 