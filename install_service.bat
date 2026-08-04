@echo off
set "TASK_NAME=GraduationProject_AutoSync"
set "SCRIPT_PATH=%~dp0scripts\auto_sync_service.py"

echo Setting up Auto Sync Task in Windows Scheduled Tasks...

schtasks /create /tn "%TASK_NAME%" /tr "pythonw.exe \"%SCRIPT_PATH%\"" /sc onstart /ru "%USERNAME%" /f > nul 2>&1
if %errorlevel% neq 0 (
    schtasks /create /tn "%TASK_NAME%" /tr "python.exe \"%SCRIPT_PATH%\"" /sc onstart /ru "%USERNAME%" /f > nul 2>&1
)

echo Running service now...
schtasks /run /tn "%TASK_NAME%" > nul 2>&1

echo Auto Sync Service installed successfully!

