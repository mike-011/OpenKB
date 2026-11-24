"""Tests for the Telegram CI notification helper (#101).

Loaded straight from ``.github/scripts/telegram_notify.py`` (it is tooling,
not package code) so the exact file the workflow runs is what gets tested.

Message shape (owner-corrected format, supersedes the earlier one):

    <icon> <original GitHub conclusion>
    <title without conventional prefix> (<run URL>) (#ticket)
    <empty line>
    URL: <PROD_URL or run URL>
    [<optional context line>]
"""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "telegram_notify.py"
_spec = importlib.util.spec_from_file_location("telegram_notify", _SCRIPT)
assert _spec is not None and _spec.loader is not None
tn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tn)

# Every conclusion GitHub Actions can report (spec list).
ALL_CONCLUSIONS = [
    "success",
    "failure",
    "cancelled",
    "skipped",
    "neutral",
    "timed_out",
    "action_required",
    "stale",
    "startup_failure",
]

# The owner approved this exact icon map as FINAL (#101) -- lock it down.
APPROVED_ICONS = {
    "success": "\u2705",
    "failure": "\u274c",
    "cancelled": "\u23f9\ufe0f",
    "skipped": "\u23ed\ufe0f",
    "timed_out": "\u23f0",
    "action_required": "\u26a0\ufe0f",
    "neutral": "\u26aa",
    "stale": "\u267b\ufe0f",
    "startup_failure": "\U0001f4a5",
}

NEUTRAL_RUN_URL = "https://github.com/example-org/example-repo/actions/runs/1234567890"
NEUTRAL_PROD_URL = "https://prod.example.com"
_TITLE_BODY = "Telegram-уведомления о завершении прогонов"
SUBJECT = f"ci: {_TITLE_BODY} (#101) (#102)"


def _text(conclusion: str, **kwargs) -> str:
    params = {
        "title": SUBJECT,
        "run_url": NEUTRAL_RUN_URL,
        "ticket": "#101",
        "prod_url": NEUTRAL_PROD_URL,
    }
    params.update(kwargs)
    return tn.build_text(conclusion, **params)


# ---------------------------------------------------------------- icon line


def test_every_conclusion_maps_to_an_icon():
    for conclusion in ALL_CONCLUSIONS:
        assert conclusion in tn.STATUS_MAP, f"no icon for {conclusion}"
        assert tn.STATUS_MAP[conclusion]


def test_icon_map_matches_owner_approved_mapping():
    assert tn.STATUS_MAP == APPROVED_ICONS
    for conclusion, icon in APPROVED_ICONS.items():
        assert tn.status_line(conclusion) == f"{icon} {conclusion}"


def test_status_line_keeps_original_github_wording():
    for conclusion in ALL_CONCLUSIONS:
        line = tn.status_line(conclusion)
        assert line.startswith(tn.STATUS_MAP[conclusion])
        # raw conclusion, untranslated (owner's format correction)
        assert line.split(" ", 1)[1] == conclusion


def test_unknown_conclusion_uses_fallback_and_never_crashes():
    assert tn.status_line("something_brand_new") == f"{tn.UNKNOWN_GLYPH} something_brand_new"
    assert tn.status_line("") == f"{tn.UNKNOWN_GLYPH} unknown"
    assert tn.status_line(None) == f"{tn.UNKNOWN_GLYPH} unknown"


# ------------------------------------------------------------------- title


def test_title_is_verbatim_no_prefix_stripping():
    # Owner correction: the "ci: " prefix was stripped ACCIDENTALLY before;
    # the title goes exactly as GitHub provides it -- never rewritten.
    for raw in (
        "ci: Telegram notify",
        "fix(web): connector cards",
        "feat(api)!: breaking change",
        "Merge pull request #86 from example/branch",
        SUBJECT,
    ):
        lines = tn.build_text("success", raw, NEUTRAL_RUN_URL, ticket="#1").splitlines()
        assert tn.escape_html(raw) in lines[1]
    assert tn.build_text("success", "", NEUTRAL_RUN_URL).splitlines()[1].startswith("<a href=")
    assert tn.build_text("success", None, NEUTRAL_RUN_URL).splitlines()[1].startswith("<a href=")


# --------------------------------------------------------- ticket extraction


def test_extract_ticket_prefers_commit_body_refs():
    assert tn.extract_ticket("ci: whatever (#9)\n\nRefs #101\n") == "#101"
    assert tn.extract_ticket("fix: whatever\n\nFixes #42\n") == "#42"
    assert tn.extract_ticket("fix: whatever\n\nfixes: #42\n") == "#42"


def test_extract_ticket_falls_back_to_subject_then_nothing():
    assert tn.extract_ticket("ci: thing (#101) (#102)\n") == "#101"
    assert tn.extract_ticket("Merge pull request #86 from example/branch\n") == ""
    assert tn.extract_ticket("") == ""
    assert tn.extract_ticket(None) == ""


# ------------------------------------------------------------- message shape


def test_message_is_four_lines_with_an_empty_third_line():
    lines = _text("success").splitlines()
    assert len(lines) == 4, lines
    assert lines[0] == "\u2705 success"
    assert lines[2] == "", "line 3 must be empty"


def test_line_two_title_link_ticket_without_run_number():
    lines = _text("failure", title=SUBJECT, ticket="#101").splitlines()
    line2 = lines[1]
    assert line2.startswith(f'<a href="{NEUTRAL_RUN_URL}">{tn.escape_html(SUBJECT)}</a>')
    assert line2.endswith(" (#101)")
    # title is verbatim: prefix and its own (#N) refs stay untouched
    assert "ci: Telegram" in line2
    assert "(#102)" in line2
    # the run number must NOT be appended any more (it lives inside the URL)
    assert "(1234567890)" not in line2


def test_line_two_without_ticket_omits_the_ref():
    # No ticket -> nothing is appended after the link (the title itself may
    # still contain "(#N)" text, since the title is verbatim).
    lines = _text("success", ticket="", title="plain subject").splitlines()
    assert lines[1] == f'<a href="{NEUTRAL_RUN_URL}">plain subject</a>'
    lines = _text("success", ticket="").splitlines()
    assert lines[1].endswith("</a>")
    assert "(#101) (#102)</a>" in lines[1]


def test_url_line_uses_prod_url():
    lines = _text("success", prod_url="https://prod.example.com/path").splitlines()
    assert lines[3] == "URL: https://prod.example.com/path"


def test_url_line_falls_back_to_run_url_when_prod_url_missing():
    for missing in ("", "   "):
        lines = _text("success", prod_url=missing).splitlines()
        assert lines[3] == f"URL: {NEUTRAL_RUN_URL}"


def test_context_line_is_appended_after_the_url_line():
    assert len(_text("success").splitlines()) == 4
    lines = _text("success", context="PROD : https://example.com").splitlines()
    assert len(lines) == 5
    assert lines[3].startswith("URL: ")
    assert lines[4] == "PROD : https://example.com"


def test_every_conclusion_builds_a_message_without_crashing():
    for conclusion in ALL_CONCLUSIONS:
        lines = _text(conclusion).splitlines()
        assert len(lines) == 4
        assert lines[0] == f"{tn.STATUS_MAP[conclusion]} {conclusion}"
        assert lines[2] == ""
        assert lines[3].startswith("URL: ")


def test_empty_and_none_conclusion_are_handled():
    lines = tn.build_text(None, "t", NEUTRAL_RUN_URL, ticket="", prod_url="").splitlines()
    assert len(lines) == 4
    assert lines[0] == f"{tn.UNKNOWN_GLYPH} unknown"


# ----------------------------------------------------------------- escaping


def test_user_controlled_text_is_html_escaped():
    nasty = 'CI "fix" <script>alert(1)</script> & burn'
    text = _text("failure", title=nasty)
    line2 = text.splitlines()[1]
    assert "<script>" not in line2
    assert "&lt;script&gt;" in line2
    assert "&amp;" in line2
    assert text.splitlines()[0] == "\u274c failure"


def test_url_line_is_escaped_for_html_parse_mode():
    url = "https://github.com/example-org/example-repo/actions/runs/1?a=1&b=2"
    lines = _text("success", run_url=url, prod_url="").splitlines()
    assert "a=1&amp;b=2" in lines[3]
    href = '<a href="https://github.com/example-org/example-repo/actions/runs/1?a=1&amp;b=2">'
    assert href in lines[1]


def test_preview_redacts_the_prod_url():
    assert tn.redact(NEUTRAL_PROD_URL, NEUTRAL_PROD_URL) == tn.REDACTED
    assert tn.redact("keep this", NEUTRAL_PROD_URL) == "keep this"
    assert tn.redact("x", "") == "x"


# ----------------------------------------------------------- commit metadata


def test_context_from_commit_trailer():
    message = "fix: thing\n\nRefs #1\nCI-Context: PROD : https://example.com\n"
    assert tn.context_from_commit(message) == "PROD : https://example.com"
    assert tn.context_from_commit("fix: thing\n") == ""
    assert tn.context_from_commit(None) == ""


def test_resolve_context_prefers_explicit_input():
    assert tn.resolve_context("from input", "CI-Context: from trailer") == "from input"
    assert tn.resolve_context("", "CI-Context: from trailer") == "from trailer"
    assert tn.resolve_context("  ", "no trailer") == ""


def test_build_payload_targets_thread_without_token():
    payload = tn.build_payload("-1001234567890", "111", "text")
    assert payload["chat_id"] == "-1001234567890"
    assert payload["message_thread_id"] == 111
    assert payload["parse_mode"] == "HTML"
    # token never belongs in the payload body
    assert all("token" not in str(v).lower() for v in payload.values())


def test_build_payload_without_thread():
    payload = tn.build_payload("-1001234567890", "", "text")
    assert "message_thread_id" not in payload


def test_first_line_picks_commit_subject():
    subject = "Merge pull request #86 from example/branch"
    assert tn.first_line(f"{subject}\n\nbody") == subject
    assert tn.first_line("\n\n body ") == "body"
    assert tn.first_line(None) == ""
