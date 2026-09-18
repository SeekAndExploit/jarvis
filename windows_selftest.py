"""Quick check that JARVIS's Windows pieces work on this PC.

Run from the jarvis folder:   .venv\\Scripts\\python windows_selftest.py
Nothing here types into any window or sends anything anywhere except the
voice test (Microsoft Edge TTS) and one test notification.
"""
import asyncio
import os
import shutil
import sys

os.environ.setdefault("PYTHONUTF8", "1")

OK, BAD, SKIP = "  OK  ", " FAIL ", " skip "


def line(status, what, detail=""):
    print(f"[{status}] {what}" + (f" - {detail}" if detail else ""))


async def main():
    print(f"Python {sys.version.split()[0]} on {sys.platform}\n")

    import claude_env
    claude = shutil.which("claude")
    line(OK if claude else BAD, "Claude Code on PATH", claude or
         "add %USERPROFILE%\\.local\\bin to PATH and open a new window")
    if claude:
        line(OK, "claude path survives splitting", str(claude_env.split_command(claude)))

    line(OK if os.path.exists("cert.pem") and os.path.exists("key.pem") else BAD,
         "HTTPS certificate", "run: .venv\\Scripts\\python scripts\\make_cert.py")

    import data_paths
    try:
        data_paths.ensure_tool_token(); data_paths.ensure_tool_token()
        line(OK, "tool token")
    except Exception as e:
        line(BAD, "tool token", str(e))

    import session_watch
    alive = session_watch.pid_alive(os.getpid())
    line(OK if alive else BAD, "process check (must not kill anything)")

    import screen
    try:
        shot = await screen.capture_screen()
        line(OK, "screen capture", f"{shot.width}x{shot.height}, {len(shot.png)//1024} KB")
    except Exception as e:
        line(BAD, "screen capture", str(e))
    try:
        wins = await screen.list_windows()
        front = next((w for w in wins if w.frontmost), None)
        line(OK, "window list", f"{len(wins)} windows"
             + (f", in front: {front.app}" if front else ""))
    except Exception as e:
        line(BAD, "window list", str(e))

    import tts
    try:
        import edge_tts  # noqa: F401
        r = await tts._edge_chunk("Systems online, sir.")
        line(OK if r else BAD, "free Edge voice",
             f"{len(r.audio)//1024} KB of audio" if r else "no audio came back")
    except ImportError:
        line(SKIP, "free Edge voice", "pip install edge-tts")

    import notifier
    ok = await notifier.notify("JARVIS", "Windows self-test notification.")
    line(OK if ok else BAD, "notification", "a toast should have appeared")

    import dialog
    tty = await dialog.tty_for_pid_async(os.getpid())
    line(OK if tty else BAD, "console lookup for key presses", tty or
         "run this from a normal PowerShell window")

    import actions
    line(OK if actions._win_chrome() else SKIP, "Chrome found", actions._win_chrome() or "")
    line(OK if actions._win_vscode() else SKIP, "VS Code found", actions._win_vscode() or
         "will use the default app instead")
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
