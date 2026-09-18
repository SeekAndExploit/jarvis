@echo off
rem Starts JARVIS on Windows: backend + frontend in two windows, then opens Chrome.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo JARVIS isn't set up yet. Right-click setup-jarvis.ps1 and choose "Run with PowerShell".
  pause
  exit /b 1
)
if not exist "cert.pem" ".venv\Scripts\python.exe" scripts\make_cert.py
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
start "JARVIS server" cmd /k ".venv\Scripts\python.exe server.py --host 127.0.0.1"
start "JARVIS frontend" cmd /k "cd frontend && npm run dev"
timeout /t 6 /nobreak >nul
start chrome http://localhost:5173
