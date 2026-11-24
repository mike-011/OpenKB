"""Telegram notification for a completed GitHub Actions run (#101).

Reads the conclusion of a finished workflow run and posts one HTML-formatted
message to the owner's Telegram group/topic. Every completed run notifies --
including ``skipped`` and ``neutral`` -- with a status emoji plus a
human-readable Russian phrase (see ``STATUS_MAP``).

Message shape (3 lines, an optional 4th context line):

    <emoji> <original GitHub conclusion text>   e.g.  "🟢 success"
    <title as link to the run> (<run_id>/<run_attempt>)
    URL: <run link>
    [<context>]

The bot token comes from the ``TELEGRAM_BOT_TOKEN`` repository secret. It is
never printed, logged, committed or included in any payload body.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.request

TELEGRAM_API = "https://api.telegram.org"
GITHUB_API = "https://api.github.com"

# Trailer honoured in the head commit message for an extra context line, e.g.
#   CI-Context: PROD : https://example.com
CONTEXT_TRAILER = "ci-context"

# Conclusion -> status emoji. Covers every conclusion GitHub Actions can
# report; anything unknown falls back to UNKNOWN_EMOJI (a new conclusion must
# never crash the notifier). Line 1 always shows the ORIGINAL GitHub wording
# of the conclusion next to the emoji -- no human translation.
STATUS_MAP: dict[str, str] = {
    "success": "\U0001f7e2",  # green circle
    "failure": "\U0001f534",  # red circle
    "cancelled": "\U0001f535",  # blue circle
    "skipped": "⚪",  # white circle
    "neutral": "⬜",  # white square
    "timed_out": "\U0001f7e0",  # orange circle
    "action_required": "\U0001f7e1",  # yellow circle (needs attention)
    "stale": ("\U0001fa76"),  # grey heart
    "startup_failure": "⛔",  # no entry / blocked
}
UNKNOWN_EMOJI = "❓"  # anything GitHub adds later


def status_line(conclusion: str | None) -> str:
    """``"failure"`` -> ``"🔴 failure"``; unknown text keeps its own wording."""
    text = (conclusion or "").strip() or "unknown"
    emoji = STATUS_MAP.get(text.lower(), UNKNOWN_EMOJI)
    return f"{emoji} {text}"


def escape_html(text: str) -> str:
    """Escape user-controlled text for Telegram's HTML parse mode."""
    return html.escape(text or "", quote=True)


def first_line(text: str | None) -> str:
    """First non-empty line of a commit subject (the run title)."""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def context_from_commit(message: str | None) -> str:
    """Value of the ``CI-Context:`` trailer in a commit message, or ''."""
    for line in (message or "").splitlines():
        key, sep, value = line.strip().partition(":")
        if sep and key.strip().lower() == CONTEXT_TRAILER:
            return value.strip()
    return ""


def run_ref(run_id: str | int | None, attempt: str | int | None = 1) -> str:
    """``run_id/run_attempt`` identifier shown in parentheses on line 2."""
    ident = str(run_id or "").strip() or "0"
    try:
        attempt_n = int(attempt or 1)
    except (TypeError, ValueError):
        attempt_n = 1
    return ident if attempt_n <= 1 else f"{ident}/{attempt_n}"


def build_text(
    conclusion: str | None,
    title: str,
    run_url: str,
    ref: str,
    context: str = "",
) -> str:
    """Compose the 3 (+optional 4) line HTML message."""
    link = f'<a href="{escape_html(run_url)}">{escape_html(title)}</a>'
    lines = [
        status_line(conclusion),
        f"{link} ({escape_html(ref)})",
        f"URL: {escape_html(run_url)}",
    ]
    if context:
        lines.append(escape_html(context))
    return "\n".join(lines)


def build_payload(chat_id: str, thread_id: str, text: str) -> dict:
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if thread_id:
        payload["message_thread_id"] = int(thread_id)
    return payload


def send(payload: dict, token: str) -> dict:
    """POST to Telegram sendMessage; return the response JSON (has message_id)."""
    request = urllib.request.Request(
        f"{TELEGRAM_API}/bot{token}/sendMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Never echo the request URL: it contains the bot token.
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise SystemExit(f"sendMessage failed: HTTP {exc.code} {detail}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"sendMessage failed: {exc.reason}") from None
    if not body.get("ok"):
        raise SystemExit(f"sendMessage rejected: {str(body)[:300]}")
    return body


def fetch_run(repo: str, run_id: str, token: str) -> dict:
    """Fetch run details (title, url, conclusion) from the GitHub API."""
    request = urllib.request.Request(
        f"{GITHUB_API}/repos/{repo}/actions/runs/{run_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        kind = exc.__class__.__name__
        print(f"::warning::could not fetch run details ({kind}); using event payload")
        return {}


def resolve_context(explicit: str, commit_message: str) -> str:
    """Dispatch input wins, then the CI-Context commit trailer."""
    explicit = (explicit or "").strip()
    return explicit or context_from_commit(commit_message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Send a Telegram CI notification")
    parser.add_argument("--dry-run", action="store_true", help="print payload, do not send")
    args = parser.parse_args(argv)

    env = os.environ
    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
    thread_id = env.get("TELEGRAM_THREAD_ID", "").strip()
    repo = env.get("GITHUB_REPOSITORY", "").strip()
    github_token = env.get("GITHUB_TOKEN", "").strip()
    run_id = env.get("RUN_ID", "").strip()
    dry_run = args.dry_run or env.get("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}

    run: dict = {}
    if run_id and repo and github_token:
        run = fetch_run(repo, run_id, github_token)

    head_commit = (run.get("head_commit") or {}) if isinstance(run.get("head_commit"), dict) else {}
    commit_message = head_commit.get("message") or env.get("HEAD_MESSAGE", "")
    commit_message = commit_message or ""

    conclusion = (
        env.get("DISPATCH_CONCLUSION", "").strip()
        or run.get("conclusion")
        or env.get("CONCLUSION", "").strip()
        or "neutral"
    )
    title = (
        first_line(commit_message)
        or env.get("TITLE", "").strip()
        or run.get("display_title")
        or env.get("DISPLAY_TITLE", "").strip()
        or run.get("name")
        or "GitHub Actions"
    )
    run_url = (
        run.get("html_url")
        or env.get("RUN_URL", "").strip()
        or (f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else "")
    )
    attempt = run.get("run_attempt") or env.get("RUN_ATTEMPT", "") or 1
    ident = str(run.get("id") or run_id or env.get("RUN_NUMBER", "") or "0")
    context = resolve_context(env.get("DISPATCH_CONTEXT", ""), commit_message)

    if not chat_id:
        raise SystemExit("TELEGRAM_CHAT_ID is not set")
    if not token and not dry_run:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set -- add it as a repository secret "
            "(gh secret set TELEGRAM_BOT_TOKEN)"
        )

    text = build_text(conclusion, title, run_url, run_ref(ident, attempt), context)
    payload = build_payload(chat_id, thread_id, text)

    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("dry-run: payload printed, nothing sent")
        return 0

    body = send(payload, token)
    # The message_id is the evidence that the notification actually arrived.
    print(f"message_id={body['result'].get('message_id')} chat={chat_id} thread={thread_id or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
