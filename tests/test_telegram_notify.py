"""Tests for the Telegram CI notification helper (#101).

Loaded straight from ``.github/scripts/telegram_notify.py`` (it is tooling,
not package code) so the exact file the workflow runs is what gets tested.
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

NEUTRAL_URL = "https://github.com/example-org/example-repo/actions/runs/1234567890"


def _text(conclusion: str, **kwargs) -> str:
    params = {
        "title": "Merge pull request #86 from example/branch",
        "run_url": NEUTRAL_URL,
        "ref": "1234567890",
    }
    params.update(kwargs)
    return tn.build_text(conclusion, **params)


def test_every_conclusion_maps_to_an_emoji():
    for conclusion in ALL_CONCLUSIONS:
        assert conclusion in tn.STATUS_MAP, f"no emoji for {conclusion}"
        assert tn.STATUS_MAP[conclusion]


def test_status_line_keeps_original_github_wording():
    for conclusion in ALL_CONCLUSIONS:
        line = tn.status_line(conclusion)
        assert line.startswith(tn.STATUS_MAP[conclusion])
        # raw conclusion, untranslated (owner's format correction)
        assert line.endswith(conclusion)
        assert line.split(" ", 1)[1] == conclusion


def test_every_conclusion_builds_a_message_without_crashing():
    for conclusion in ALL_CONCLUSIONS:
        text = _text(conclusion)
        lines = text.splitlines()
        assert len(lines) == 3
        assert lines[0] == f"{tn.STATUS_MAP[conclusion]} {conclusion}"
        assert lines[2].startswith("URL: ")


def test_unknown_conclusion_uses_fallback_and_never_crashes():
    text = _text("something_brand_new")
    assert text.splitlines()[0] == f"{tn.UNKNOWN_EMOJI} something_brand_new"


def test_empty_and_none_conclusion_are_handled():
    assert tn.status_line("") == f"{tn.UNKNOWN_EMOJI} unknown"
    assert tn.status_line(None) == f"{tn.UNKNOWN_EMOJI} unknown"
    assert tn.build_text(None, "t", NEUTRAL_URL, "1").count("\n") == 2


def test_line_two_is_a_link_to_the_run_plus_run_reference():
    text = _text("success")
    line2 = text.splitlines()[1]
    assert f'<a href="{NEUTRAL_URL}">' in line2
    assert "Merge pull request #86 from example/branch</a>" in line2
    assert line2.endswith("(1234567890)")


def test_run_ref_includes_attempt_on_retries():
    assert tn.run_ref(42, 1) == "42"
    assert tn.run_ref(42, 2) == "42/2"
    assert tn.run_ref(None, None) == "0"


def test_user_controlled_text_is_html_escaped():
    nasty = 'CI "fix" <script>alert(1)</script> & burn'
    text = _text("failure", title=nasty)
    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    assert "&amp;" in text
    # line 1 stays outside the link: raw emoji + raw status
    assert text.splitlines()[0] == "🔴 failure"


def test_url_line_is_escaped_for_html_parse_mode():
    url = "https://github.com/example-org/example-repo/actions/runs/1?a=1&b=2"
    text = _text("success", run_url=url)
    assert "URL: " in text.splitlines()[2]
    assert "a=1&amp;b=2" in text.splitlines()[2]
    href = '<a href="https://github.com/example-org/example-repo/actions/runs/1?a=1&amp;b=2">'
    assert href in text


def test_context_line_is_optional():
    default = _text("success")
    assert len(default.splitlines()) == 3
    with_ctx = _text("success", context="PROD : https://example.com")
    lines = with_ctx.splitlines()
    assert len(lines) == 4
    assert lines[3] == "PROD : https://example.com"
    # URL line is always present, context is additive
    assert lines[2].startswith("URL: ")


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
