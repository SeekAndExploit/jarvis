"""
JARVIS Notifier -- macOS notification fallback.

When JARVIS needs the user's attention but no browser tab is connected to
speak through, this posts a native macOS notification instead. See
actions.py for the project's usual pattern of driving `osascript`; this
module differs from it deliberately (see below) because the text here is
attacker-influenced.

Notification titles/messages surface a Claude Code session's title or its
last message -- text that originates in someone else's transcript, not
text JARVIS wrote itself. actions.py's `applescript_escape()` handles this
by escaping quotes/backslashes before interpolating into the script
*source*. That is fine for its callers, but here we take a stronger
approach: the script never contains the untrusted text at all. It is
written once as a fixed `on run argv` handler and read from stdin, and the
title/message/subtitle are passed as trailing argv strings, which
osascript hands to the script as plain data -- never parsed as AppleScript
source. There is no escaping step to get wrong because there is nothing to
escape: a value containing `" & do shell script "..." & "` is just a
string with those characters in it.
"""

import asyncio
import logging
import shutil
import sys

log = logging.getLogger("jarvis.notifier")

# A notification is a glance, not an essay -- keep it short. These bound
# what we pass to Notification Center regardless of how long the source
# text (a session title, a transcript line) actually is.
_TITLE_MAX = 120
_SUBTITLE_MAX = 120
_MESSAGE_MAX = 300

# osascript is usually near-instant; a wedged one must not hang the caller.
_TIMEOUT_SECONDS = 5.0

# Fixed script, no untrusted text ever enters this string. Title, message,
# and subtitle arrive purely via argv (see module docstring).
_NOTIFY_SCRIPT = """\
on run argv
    set theTitle to item 1 of argv
    set theMessage to item 2 of argv
    set theSubtitle to item 3 of argv
    if theSubtitle is "" then
        display notification theMessage with title theTitle
    else
        display notification theMessage with title theTitle subtitle theSubtitle
    end if
end run
"""


def _truncate(text: str, limit: int) -> str:
    """Bound text length for a glanceable notification, marking any cut."""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"  # ellipsis


def available() -> bool:
    """Whether posting a notification is plausible right now.

    Cheap and side-effect free: macOS platform + `osascript` on PATH. This
    is a precondition check, not a delivery guarantee -- Notification
    Center settings, Focus/Do Not Disturb, or per-app permissions can still
    silently drop the notification even when this returns True.
    """
    return sys.platform == "darwin" and shutil.which("osascript") is not None


async def notify(title: str, message: str, *, subtitle: str = "") -> bool:
    """Post a macOS notification. Returns whether it was handed off successfully.

    This is a fallback path for when nobody is listening on the voice
    channel, so it must never raise: any failure (no macOS, no osascript,
    non-zero exit, timeout, spawn error) is logged as a warning and
    reported back as False. The `osascript` call runs as a subprocess so it
    never blocks the event loop, and is bounded by _TIMEOUT_SECONDS so a
    wedged process cannot hang the caller.
    """
    try:
        if not available():
            log.warning("notifier: notifications unavailable on this platform")
            return False

        safe_title = _truncate(str(title or ""), _TITLE_MAX)
        safe_message = _truncate(str(message or ""), _MESSAGE_MAX)
        safe_subtitle = _truncate(str(subtitle or ""), _SUBTITLE_MAX)

        try:
            proc = await asyncio.create_subprocess_exec(
                "osascript", "-", safe_title, safe_message, safe_subtitle,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as e:
            log.warning(f"notifier: failed to spawn osascript: {e}")
            return False

        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(_NOTIFY_SCRIPT.encode("utf-8")),
                timeout=_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            log.warning("notifier: osascript timed out, killing it")
            try:
                proc.kill()
                await proc.communicate()
            except Exception:
                pass
            return False

        if proc.returncode != 0:
            log.warning(
                f"notifier: osascript exited {proc.returncode}: "
                f"{stderr.decode(errors='replace').strip()}"
            )
            return False

        return True
    except Exception as e:
        # Belt and suspenders: this path must never raise into the caller.
        log.warning(f"notifier: unexpected error posting notification: {e}")
        return False


# ── Windows patch ──────────────────────────────────────────────────────────
# A Windows toast via PowerShell + WinRT (built into Windows 10/11). Same rule
# as the macOS path: the script is fixed, and the untrusted title/message
# reach it only as environment variables -- data, never PowerShell source.

import os as _os

_WIN_TOAST_PS = r"""
$ErrorActionPreference = 'Stop'
[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
$title = $env:JARVIS_TOAST_TITLE
$body = $env:JARVIS_TOAST_MESSAGE
if ($env:JARVIS_TOAST_SUBTITLE) { $body = $env:JARVIS_TOAST_SUBTITLE + "`n" + $body }
$tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$t = $tpl.GetElementsByTagName('text')
[void]$t.Item(0).AppendChild($tpl.CreateTextNode($title))
[void]$t.Item(1).AppendChild($tpl.CreateTextNode($body))
$toast = [Windows.UI.Notifications.ToastNotification]::new($tpl)
$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
"""


def _win_available() -> bool:
    return shutil.which("powershell") is not None


async def _win_notify(title: str, message: str, *, subtitle: str = "") -> bool:
    try:
        if not _win_available():
            return False
        env = dict(_os.environ)
        env["JARVIS_TOAST_TITLE"] = _truncate(str(title or ""), _TITLE_MAX)
        env["JARVIS_TOAST_MESSAGE"] = _truncate(str(message or ""), _MESSAGE_MAX)
        env["JARVIS_TOAST_SUBTITLE"] = _truncate(str(subtitle or ""), _SUBTITLE_MAX)
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", "-",
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, env=env)
        except OSError as e:
            log.warning(f"notifier: failed to spawn powershell: {e}")
            return False
        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(_WIN_TOAST_PS.encode("utf-8")),
                timeout=_TIMEOUT_SECONDS + 5)
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.communicate()
            except Exception:
                pass
            return False
        if proc.returncode != 0:
            log.warning(f"notifier: toast failed: "
                        f"{stderr.decode(errors='replace').strip()[:200]}")
            return False
        return True
    except Exception as e:
        log.warning(f"notifier: unexpected error posting notification: {e}")
        return False


if sys.platform == "win32":
    available = _win_available      # noqa: F811
    notify = _win_notify            # noqa: F811
