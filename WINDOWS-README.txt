JARVIS on Windows (unofficial port - upstream supports macOS only)

SETUP (one time)
1. Right-click setup-jarvis.ps1 > Run with PowerShell
   - checks/installs Python, Node.js, Claude Code, all packages,
     makes the HTTPS certificate, asks for a Fish Audio key (optional).
2. Open a NEW PowerShell, run:  claude   log in, then /exit
3. Optional check:  .venv\Scripts\python windows_selftest.py

RUN
- Double-click start-jarvis.bat
- Chrome opens http://localhost:5173 -> click the page once, allow the mic, talk.
- Dashboard: http://localhost:5173/dashboard.html
- Stop: close the two "JARVIS" windows.

VOICE
- Fish Audio key in .env = the movie JARVIS voice (needs credit on fish.audio).
- No key / no credit = free Microsoft Edge voice. Force it with TTS_ENGINE=edge
  in .env; pick another with EDGE_VOICE=en-GB-ThomasNeural (el-GR-NestorasNeural = Greek).

WHAT WORKS ON WINDOWS
- Talking, brain, memory, dashboard, builds/runs, session watching
- "What's on my screen?" / "What windows are open?"  (PowerShell capture)
- Opening a terminal (PowerShell), Chrome/Firefox, VS Code
- Notifications (Windows toast) when no browser tab is open
- Answering a Claude Code permission prompt by voice (Return / Escape / 1-9),
  sent straight to that session's console, never to whatever window is in front

KNOWN LIMITS
- Must be Google Chrome (speech recognition is Chrome's Web Speech API).
- Steering messages into other Claude sessions depends on Claude Code exposing
  an inbox on Windows; if it doesn't, JARVIS says so instead of sending.
- Builds JARVIS starts run Claude Code with --dangerously-skip-permissions.

WINDOWS FIXES IN THIS FORK
data_paths, usage_scan, brain/run_executor/claude_env (paths), session_watch
(liveness check used to KILL processes on Windows), server (C:\ project paths),
jarvis_mcp (bypass system proxy), screen, actions, notifier, dialog,
session_steer, preflight, tts (free Edge voice).
