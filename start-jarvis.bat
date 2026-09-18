@echo off
rem Starts JARVIS on Windows: backend + frontend in two windows, then opens Chrome.
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
start "JARVIS server" cmd /k ".venv\Scripts\python.exe server.py --host 127.0.0.1"
start "JARVIS frontend" cmd /k "cd frontend && npm run dev"
timeout /t 6 /nobreak >nul
start chrome http://localhost:5173
