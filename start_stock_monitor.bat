@echo off

REM 启动股票行情监控系统

REM 直接指定工作目录
cd /d "D:\12.股票\stock_quote_tae"

REM 启动Flask应用
start "Flask App" python app.py

REM 等待2秒，确保Flask应用已经启动
ping 127.0.0.1 -n 3 > nul

REM 启动后台服务
start "Background Service" python background_service.py

echo Stock monitoring system started
pause