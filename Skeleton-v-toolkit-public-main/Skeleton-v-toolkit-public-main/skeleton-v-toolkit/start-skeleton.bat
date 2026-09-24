@echo off
::
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

::
cd /d "C:\Users\31220\Desktop\skeleton-v-toolkit"

::
py "skeleton v.py"

pause
