@echo off
REM ====================================================================
REM Windows 计划任务配置脚本
REM ====================================================================

echo 创建 Windows 计划任务...

REM 获取当前目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM 创建计划任务（每天20:00执行）
schtasks /create ^
  /tn "量化交易系统-每日报告" ^
  /tr "python %PROJECT_DIR%\main.py --mode full" ^
  /sc daily ^
  /st 20:00 ^
  /f

echo.
echo ✅ 计划任务创建成功！
echo.
echo 任务名称: 量化交易系统-每日报告
echo 执行时间: 每天 20:00
echo.
echo 管理任务:
echo   查看: 打开"任务计划程序"应用
echo   删除: schtasks /delete /tn "量化交易系统-每日报告" /f
echo.

pause