"""Telegram notification for a completed GitHub Actions run (#101).

Reads the conclusion of a finished workflow run and posts one HTML-formatted
message to the owner's Telegram group/topic. Every completed run notifies --
including ``skipped`` and ``neutral`` -- with a status icon plus the ORIGINAL
GitHub conclusion text (see ``STATUS_MAP``).

Message shape (owner-final format, fourth round = PR-suffix strip + PR block):

    <icon> <original GitHub conclusion>            e.g.  "✅ success"
    <title minus trailing GitHub PR-suffix tokens> (<run URL>) (#<run number>)
    <empty line>
    PR #<n1>
    PR #<n2>
    <empty line>
    <DEV|PROD>: <environment URL, else the run URL>
    [<optional context line>]

When NO pull request is associated with the run's commits, the PR block and
its separating empty line are BOTH omitted -- the message keeps the earlier
shape: title line, empty line, env line (then the optional context line).

Env line = the environment label, a colon and the address (the old literal
``URL`` label is gone). Two labels exist: ``DEV`` for dev builds and ``PROD``
for release builds (``PROD: http://ip.ad.dr.es:7566`` shape). ``PROD`` is
double-gated by ``resolve_environment`` -- BOTH a release build (version tag
ref starting with ``v``) AND a non-empty prod URL secret are required -- so
with ``TELEGRAM_PROD_URL`` deliberately absent from the repo no run can select
it yet: every build reports ``DEV`` with ``secrets.TELEGRAM_DEV_URL``, and an
empty dev secret falls back to the run URL.

Line 2 rules: the title goes VERBATIM exactly as GitHub provides it (commit
subject or the ``title`` input) with ONE named exception -- GitHub's
squash-merge suffix, a trailing " (#<digits>)" token at the END of the title
is removed repeatedly until none remain (``strip_pr_suffix``): no other
prefix or substring is ever touched, and never by a fixed character count.
The trailing token of line 2 itself is " (#<run number>)" in GitHub's own
style, and that number must be the run number OF THE VERY RUN the URL points
to -- ``html_url`` and ``run_number`` are always read from one payload
(``run_source_from_env`` / the fetched run object), never mixed across runs.
Unknown number -> token omitted rather than guessed.

PR block rules: one ``PR #N`` line (hash, decimal, no link, no punctuation)
per pull request associated with the run's commits -- GitHub API
``GET /repos/{repo}/commits/{sha}/pulls`` (``Accept: application/vnd.github+json``)
for each commit of the run: the payload's ``commits`` when present, else the
run's ``head_sha`` commit (``collect_commit_shas``). Numbers are deduped and
sorted ascending (``fetch_pr_numbers``), and a failed lookup degrades to no
block rather than crashing a notification. The block always ends with a
second empty line before the env line.

Secrets: ``TELEGRAM_BOT_TOKEN`` (auth), ``TELEGRAM_DEV_URL`` (env line, dev
address) and ``TELEGRAM_PROD_URL`` (env line, release address -- name kept for
the gate, no such secret exists yet) are repository secrets -- never printed,
logged, committed or put in the repo. The environment URL is a private LAN
address: it may exist ONLY in the secret value and in the Telegram message
text sent to the private chat, never in repo files, issue/PR bodies or
comments, commit messages or CI logs. Every printed byte (preview, dry-run
payload) therefore masks it via ``redact`` -- see
``test_printed_output_masks_env_url_while_payload_carries_it``.
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
from collections.abc import Mapping, Sequence

TELEGRAM_API = "https://api.telegram.org"
GITHUB_API = "https://api.github.com"

# Trailer honoured in the head commit message for an extra context line, e.g.
#   CI-Context: PROD : https://example.com
CONTEXT_TRAILER = "ci-context"

# GitHub's squash-merge suffix: a trailing " (#<digits>)" token at the END of
# the title (round 4) -- a NAMED pattern, removed repeatedly until none
# remain. Nothing else is stripped: no other prefix/substring, never a fixed
# character count.
PR_SUFFIX_RE = re.compile(r" \(#\d+\)$")

# Media type for the PR-association lookup /repos/{repo}/commits/{sha}/pulls.
PULLS_ACCEPT = "application/vnd.github+json"

REDACTED = "<ENV URL masked: real infra identifiers never appear in logs>"

# Env-line environment labels. DEV = every build; PROD = release builds only,
# and only when a prod URL secret exists (see resolve_environment).
DEV_LABEL = "DEV"
PROD_LABEL = "PROD"

# A release build = the ref is a version tag: "refs/tags/v0.6.0" (Actions'
# GITHUB_REF form) or the bare tag name "v0.6.0". Everything else -- branches,
# pull refs, non-version tags -- is a dev build.
RELEASE_REF_RE = re.compile(r"^(?:refs/tags/)?v\d")

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


def strip_pr_suffix(title: str | None) -> str:
    """Drop GitHub's trailing squash-merge PR-suffix tokens from ``title``.

    ``"fix(test): something (#107)"`` -> ``"fix(test): something"``; the strip
    repeats until no trailing ``" (#<digits>)"`` token remains
    (``"foo (#107) (#108)"`` -> ``"foo"``). Everything else -- prefixes,
    interior tokens, non-digit tokens, length -- is untouched: this is a
    named pattern, never a fixed character count (round-4 owner rule).
    """
    text = title or ""
    while True:
        stripped = PR_SUFFIX_RE.sub("", text)
        if stripped == text:
            return stripped
        text = stripped


def context_from_commit(message: str | None) -> str:
    """Value of the ``CI-Context:`` trailer in a commit message, or ''."""
    for line in (message or "").splitlines():
        key, sep, value = line.strip().partition(":")
        if sep and key.strip().lower() == CONTEXT_TRAILER:
            return value.strip()
    return ""


def is_release_ref(ref: str | None) -> bool:
    """True only for a version tag ref (``refs/tags/v…`` / bare ``v…``)."""
    return bool(RELEASE_REF_RE.match((ref or "").strip()))


def resolve_environment(
    ref: str,
    dev_url: str,
    prod_url: str,
    run_url: str = "",
) -> tuple[str, str]:
    """Env-line ``(label, address)`` for this build.

    ``PROD`` requires BOTH conditions at once: a release build (version tag
    ref) AND a non-empty prod URL secret. No prod secret exists yet (the old
    ``TELEGRAM_PROD_URL`` was deliberately deleted, there is no v0.6.0), so
    the PROD branch is currently impossible to reach -- every build resolves
    to ``DEV``. With an empty dev secret the address falls back to the run
    URL rather than printing nothing.
    """
    prod = (prod_url or "").strip()
    if prod and is_release_ref(ref):
        return PROD_LABEL, prod
    return DEV_LABEL, (dev_url or "").strip() or (run_url or "").strip()


def redact(text: str, *secret_values: str) -> str:
    """Mask every environment URL in anything that gets printed or logged."""
    for secret_value in secret_values:
        value = (secret_value or "").strip()
        if value:
            text = text.replace(value, REDACTED)
    return text


def run_source_from_env(env: Mapping[str, str], repo: str) -> dict:
    """Build the single run mapping used for line 2 from ONE event source.

    ``html_url`` and ``run_number`` always come from the same payload (the
    ``workflow_run`` event fields, or this dispatch run's own id/number) --
    mixing a URL of one run with the number of another is the bug this
    function exists to make impossible.
    """
    run_id = str(env.get("RUN_ID", "") or "").strip()
    run_url = str(env.get("RUN_URL", "") or "").strip()
    if not run_url and repo and run_id:
        run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    return {
        "html_url": run_url,
        "run_number": str(env.get("RUN_NUMBER", "") or "").strip(),
        "id": run_id,
    }


def build_text(
    conclusion: str | None,
    title: str,
    run: dict | None = None,
    env_label: str = "",
    env_url: str = "",
    context: str = "",
    prs: Sequence[int] | None = None,
) -> str:
    """Compose the owner-final HTML message (round 4).

    ``title`` is used VERBATIM (commit subject or the ``title`` input) with
    ONE named exception -- ``strip_pr_suffix`` removes GitHub's trailing
    squash-merge suffix, ``" (#<digits>)"`` tokens at the END, until none
    remain; nothing else about it changes (owner correction to #101).

    Line 2 = ``<title minus the suffix> (<run URL>) (#<run number>)``: both
    run fields are read from the SAME ``run`` mapping (see
    ``run_source_from_env``) so a URL of one run can never be paired with the
    number of another. GitHub's run URL carries the run *id*, the token
    carries the run *number*. If the number is unknown the token is omitted --
    a wrong number is worse than none.

    PR block = one ``PR #N`` line per entry of ``prs`` (deduped, ascending),
    preceded by the format's empty line and followed by a SECOND empty line.
    When ``prs`` is empty the whole block -- including that separating empty
    line -- vanishes, so line 2 is followed directly by the env line.

    Env line = ``<DEV|PROD>: <address>`` -- the label comes from
    ``resolve_environment`` (never the old literal ``URL``; a missing label
    still defaults to ``DEV``), the address from ``env_url`` with the run URL
    as fallback when the secret is empty.
    """
    run = run or {}
    run_url = str(run.get("html_url") or "")
    number = str(run.get("run_number") or "").strip()
    link = f'<a href="{escape_html(run_url)}">{escape_html(strip_pr_suffix(title))}</a>'
    line2 = link + (f" (#{escape_html(number)})" if number.isdigit() else "")
    label = (env_label or "").strip() or DEV_LABEL
    target = (env_url or "").strip() or run_url
    lines = [status_line(conclusion), line2, ""]
    # PR block (round 4): normalized here too (deduped, ascending) so the
    # printed order never depends on the API's response order.
    block = sorted({int(pr) for pr in prs or ()})
    if block:
        lines.extend(f"PR #{pr}" for pr in block)
        lines.append("")
    lines.append(f"{label}: {escape_html(target)}")
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


def collect_commit_shas(run: Mapping, env: Mapping[str, str]) -> list[str]:
    """Commits whose pull requests the PR block must list (deduped, in order).

    The run payload's ``commits`` when present (workflow_run), else the run's
    ``head_sha`` commit -- falling back to the ``HEAD_SHA`` env the workflow
    passes for the trigger run's head commit (round-4 rule).
    """
    shas: list[str] = []
    commits = run.get("commits")
    if isinstance(commits, list):
        for commit in commits:
            sha = ""
            if isinstance(commit, dict):
                sha = str(commit.get("sha") or "").strip()
            if sha:
                shas.append(sha)
    if not shas:
        sha = str(run.get("head_sha") or env.get("HEAD_SHA") or "").strip()
        if sha:
            shas.append(sha)
    ordered: list[str] = []
    seen: set[str] = set()
    for sha in shas:
        if sha not in seen:
            seen.add(sha)
            ordered.append(sha)
    return ordered


def github_json(path: str, token: str) -> object:
    """GET a GitHub API path; return the parsed JSON or ``[]`` on any failure.

    A failed lookup must never crash or suppress a notification: warn with the
    error KIND only (auth travels in the header, never the URL) and let the
    caller degrade.
    """
    request = urllib.request.Request(
        f"{GITHUB_API}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": PULLS_ACCEPT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        print(f"::warning::GitHub lookup failed ({exc.__class__.__name__}); continuing without it")
        return []


def fetch_pr_numbers(repo: str, shas: Sequence[str], token: str) -> list[int]:
    """PR numbers linked to ``shas`` via ``GET /repos/{repo}/commits/{sha}/pulls``.

    One lookup per commit of the run, deduped by number, sorted ascending --
    exactly the order the PR block prints (round-4 rule).
    """
    numbers: set[int] = set()
    for sha in shas:
        data = github_json(f"/repos/{repo}/commits/{sha}/pulls", token)
        if not isinstance(data, list):
            continue
        for pull in data:
            if not isinstance(pull, dict):
                continue
            number = pull.get("number")
            if isinstance(number, int):
                numbers.add(number)
            elif isinstance(number, str) and number.isdigit():
                numbers.add(int(number))
    return sorted(numbers)


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
    dev_url = env.get("TELEGRAM_DEV_URL", "").strip()
    prod_url = env.get("TELEGRAM_PROD_URL", "").strip()
    # Release detection: the triggering build's ref (tag) when available,
    # else this workflow run's own ref. Only a version tag counts -- see
    # is_release_ref.
    build_ref = env.get("BUILD_REF", "").strip() or env.get("GITHUB_REF", "").strip()
    repo = env.get("GITHUB_REPOSITORY", "").strip()
    github_token = env.get("GITHUB_TOKEN", "").strip()
    run_id = env.get("RUN_ID", "").strip()
    dry_run = args.dry_run or env.get("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}

    # One source for url+number: the API object of THIS run when available,
    # otherwise the event payload fields (both from the same event).
    run: dict = {}
    if run_id and repo and github_token:
        run = fetch_run(repo, run_id, github_token)
    if not run.get("html_url"):
        run = run_source_from_env(env, repo)

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
    context = resolve_context(env.get("DISPATCH_CONTEXT", ""), commit_message)
    if not str(run.get("run_number") or "").strip():
        print("::warning::run_number unavailable; line 2 will omit the (#N) token")

    # PR block (round 4): pull requests of the run's commits -- the payload's
    # commits when present, else head_sha -- via commits/{sha}/pulls. Without
    # a token there is no authenticated lookup: skip it and simply send no PR
    # block (never guess numbers).
    shas = collect_commit_shas(run, env)
    pr_numbers: list[int] = []
    if shas and repo and github_token:
        pr_numbers = fetch_pr_numbers(repo, shas, github_token)
    elif shas:
        print("::notice::no GITHUB_TOKEN; PR block omitted")

    if not chat_id:
        raise SystemExit("TELEGRAM_CHAT_ID is not set")
    if not token and not dry_run:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set -- add it as a repository secret "
            "(gh secret set TELEGRAM_BOT_TOKEN)"
        )

    # Label + address for the env line, from ONE decision point (double gate).
    run_url = str(run.get("html_url") or "")
    env_label, env_address = resolve_environment(build_ref, dev_url, prod_url, run_url)
    text = build_text(
        conclusion,
        title,
        run,
        env_label=env_label,
        env_url=env_address,
        context=context,
        prs=pr_numbers,
    )
    payload = build_payload(chat_id, thread_id, text)

    # Logs are public in this repo: never let the environment URL reach them.
    print("message preview (environment URL masked):")
    print(redact(text, dev_url, prod_url))

    if dry_run:
        safe_payload = dict(payload, text=redact(payload["text"], dev_url, prod_url))
        print(json.dumps(safe_payload, ensure_ascii=False, indent=2))
        print("dry-run: payload printed, nothing sent")
        return 0

    body = send(payload, token)
    # The message_id is the evidence that the notification actually arrived.
    print(f"message_id={body['result'].get('message_id')} chat={chat_id} thread={thread_id or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
