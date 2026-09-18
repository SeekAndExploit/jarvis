JARVIS on Windows (unofficial - upstream supports macOS only)

1. Right-click setup-jarvis.ps1 > Run with PowerShell   (one time)
   - installs Python / Node / Claude Code if missing, all dependencies,
     and asks for your Fish Audio API key.
2. Open a terminal, run:  claude   and log in once (uses your Claude subscription).
3. Double-click start-jarvis.bat
   - Chrome opens http://localhost:5173 -> click the page once, allow the mic, talk.
   - Dashboard: http://localhost:5173/dashboard.html
   - Stop: close the two "JARVIS" console windows.

Notes
- Must be Google Chrome (speech recognition uses Chrome's Web Speech API).
- Without a Fish Audio key he replies as text only.
- Doesn't work on Windows: controlling Terminal windows, desktop notifications,
  screenshots (those are macOS AppleScript features).
- Patched for Windows: data_paths.py (POSIX-only file calls).
- cert.pem/key.pem are a self-signed localhost certificate, already generated.
  To make your own: openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
- Builds JARVIS starts run Claude Code with --dangerously-skip-permissions.
