"""Telegram notification for a completed GitHub Actions run (#101).

Reads the conclusion of a finished workflow run and posts one HTML-formatted
message to the owner's Telegram group/topic. Every completed run notifies --
including ``skipped`` and ``neutral`` -- with a status icon plus the ORIGINAL
GitHub conclusion text (see ``STATUS_MAP``).

Message shape (owner-corrected format, supersedes the earlier one):

    <icon> <original GitHub conclusion>            e.g.  "✅ success"
    <title> (<run URL>) (#ticket)
    <empty line>
    URL: <PROD_URL from secrets.TELEGRAM_PROD_URL, else the run URL>
    [<optional context line>]

Line 2 rules: the title goes VERBATIM exactly as GitHub provides it (commit
subject or the ``title`` input -- no prefix stripping, no rewriting); the run
number is NOT shown (it lives inside the URL); "(#ticket)" is appended from
the Fixes/Refs ref in the commit body, else the first "(#N)" in the subject,
else nothing.

Secrets: ``TELEGRAM_BOT_TOKEN`` (auth) and ``TELEGRAM_PROD_URL`` (line 4) are
repository secrets -- never printed, logged, committed or put in the repo.
Printed output (dry-run payload, message preview) always masks the PROD URL.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

TELEGRAM_API = "https://api.telegram.org"
GITHUB_API = "https://api.github.com"

# Trailer honoured in the head commit message for an extra context line, e.g.
#   CI-Context: PROD : https://example.com
CONTEXT_TRAILER = "ci-context"

# Ticket from the commit body: "Fixes #123" / "Refs: #123".
BODY_REF_RE = re.compile(r"(?i)\b(?:fixes|refs)\s*:?\s*#([0-9]+)")
# Fallback: first "(#N)" in the subject.
SUBJECT_TICKET_RE = re.compile(r"\(#([0-9]+)\)")

REDACTED = "<PROD_URL masked: real infra identifiers never appear in logs>"

# Conclusion -> text glyph, mirroring GitHub's own status octicons (Telegram
# cannot render SVG icons, so the closest Unicode equivalent of each octicon is
# used). Mapping approved by the owner as FINAL (see #101 / PR #102):
#   success check-circle-fill -> ✅   failure x-circle-fill     -> ❌
#   cancelled stop-fill       -> ⏹️   skipped skip-fill         -> ⏭️
#   timed_out clock           -> ⏰   action_required attention -> ⚠️
#   neutral grey dot-fill     -> ⚪   stale refresh-ish         -> ♻️
#   startup_failure x-circle  -> 💥
# Line 1 always shows the ORIGINAL GitHub wording of the conclusion next to
# the glyph -- no human translation. Unknown conclusions fall back to
# UNKNOWN_GLYPH (a new conclusion must never crash the notifier).
STATUS_MAP: dict[str, str] = {
    "success": "\u2705",  # check-circle-fill
    "failure": "\u274c",  # x-circle-fill
    "cancelled": "\u23f9\ufe0f",  # stop-fill / circle-slash
    "skipped": "\u23ed\ufe0f",  # skip-fill
    "neutral": "\u26aa",  # grey/white dot-fill
    "timed_out": "\u23f0",  # clock
    "action_required": "\u26a0\ufe0f",  # yellow attention
    "stale": "\u267b\ufe0f",  # refresh (stale) mark
    "startup_failure": "\U0001f4a5",  # x-circle / boom
}
UNKNOWN_GLYPH = "\u2753"  # anything GitHub adds later


def status_line(conclusion: str | None) -> str:
    """``"failure"`` -> ``"❌ failure"``; unknown text keeps its own wording."""
    text = (conclusion or "").strip() or "unknown"
    emoji = STATUS_MAP.get(text.lower(), UNKNOWN_GLYPH)
    return f"{emoji} {text}"


def escape_html(text: str) -> str:
    """Escape user-controlled text for Telegram's HTML parse mode."""
    return html.escape(text or "", quote=True)


def first_line(text: str | None) -> str:
    """First non-empty line of a commit message (the run title)."""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def extract_ticket(message: str | None) -> str:
    """``"#101"`` from the commit body (Fixes/Refs), subject "(#N)", or ''."""
    body_match = BODY_REF_RE.search(message or "")
    if body_match:
        return f"#{body_match.group(1)}"
    subject_match = SUBJECT_TICKET_RE.search(first_line(message))
    if subject_match:
        return f"#{subject_match.group(1)}"
    return ""


def context_from_commit(message: str | None) -> str:
    """Value of the ``CI-Context:`` trailer in a commit message, or ''."""
    for line in (message or "").splitlines():
        key, sep, value = line.strip().partition(":")
        if sep and key.strip().lower() == CONTEXT_TRAILER:
            return value.strip()
    return ""


def redact(text: str, secret_value: str) -> str:
    """Mask the internal PROD URL in anything that gets printed or logged."""
    value = (secret_value or "").strip()
    if not value:
        return text
    return text.replace(value, REDACTED)


def build_text(
    conclusion: str | None,
    title: str,
    run_url: str,
    ticket: str = "",
    prod_url: str = "",
    context: str = "",
) -> str:
    """Compose the 4 (+optional 5) line HTML message of the corrected format.

    ``title`` is used VERBATIM (commit subject or the ``title`` input) --
    no prefix stripping, no rewriting (owner correction to #101).
    """
    link = f'<a href="{escape_html(run_url)}">{escape_html(title)}</a>'
    line2 = link + (f" ({escape_html(ticket)})" if ticket.strip() else "")
    target = (prod_url or "").strip() or run_url
    lines = [
        status_line(conclusion),
        line2,
        "",
        f"URL: {escape_html(target)}",
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
    prod_url = env.get("TELEGRAM_PROD_URL", "").strip()
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
        env.get("TITLE", "").strip()
        or first_line(commit_message)
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
    ticket = extract_ticket(commit_message)
    context = resolve_context(env.get("DISPATCH_CONTEXT", ""), commit_message)

    if not chat_id:
        raise SystemExit("TELEGRAM_CHAT_ID is not set")
    if not token and not dry_run:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set -- add it as a repository secret "
            "(gh secret set TELEGRAM_BOT_TOKEN)"
        )

    text = build_text(conclusion, title, run_url, ticket=ticket, prod_url=prod_url, context=context)
    payload = build_payload(chat_id, thread_id, text)

    # Logs are public in this repo: always mask the internal PROD URL.
    print("message preview (PROD URL masked):")
    print(redact(text, prod_url))

    if dry_run:
        safe_payload = dict(payload, text=redact(payload["text"], prod_url))
        print(json.dumps(safe_payload, ensure_ascii=False, indent=2))
        print("dry-run: payload printed, nothing sent")
        return 0

    body = send(payload, token)
    # The message_id is the evidence that the notification actually arrived.
    print(f"message_id={body['result'].get('message_id')} chat={chat_id} thread={thread_id or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
