"""Tests for the Telegram CI notification helper (#101).

Loaded straight from ``.github/scripts/telegram_notify.py`` (it is tooling,
not package code) so the exact file the workflow runs is what gets tested.

Message shape (owner-corrected format, third round = environment label):

    <icon> <original GitHub conclusion>
    <title verbatim> (<run URL>) (#<run number of that very run>)
    <empty line>
    <DEV|PROD>: <environment URL, else the run URL>
    [<optional context line>]

Line 2 consistency rule: ``html_url`` and ``run_number`` must come from the
SAME run payload -- GitHub's run URL carries the run *id* while the token
carries the run *number* (they are different values by design), so the only
possible bug class is mixing two runs; ``build_text`` therefore accepts a
single ``run`` mapping and reads both fields from it.

Line 4 rules (round 3): the label is ``DEV`` or ``PROD`` (the old literal
``URL`` label is gone). ``PROD`` is double-gated -- a release build (version
tag ref starting with ``v``) AND a non-empty prod URL secret -- and with
``TELEGRAM_PROD_URL`` deliberately deleted from the repo it is unreachable
today: every build reports ``DEV``. The dev address is a private LAN value:
it may live only in the repository secret and in the Telegram message to the
private chat, never in repo files, ticket/PR text, commit messages or CI
logs, so everything printed must mask it (see the ``main()`` masking test).
"""

import importlib.util
import re
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

# One run payload: id + html_url + run_number always travel together.
RUN = {
    "id": 1234567890,
    "html_url": "https://github.com/example-org/example-repo/actions/runs/1234567890",
    "run_number": 100,
}
NEUTRAL_RUN_URL = RUN["html_url"]
# Fixture values come from the approved fake pools (LAN = 192.168.0.0/24,
# fictional domains) -- never this repo's real infrastructure.
NEUTRAL_DEV_URL = "http://192.168.0.77:7566"
NEUTRAL_PROD_URL = "https://prod.example.com"
_TITLE_BODY = "Telegram-уведомления о завершении прогонов"
SUBJECT = f"ci: {_TITLE_BODY} (#101) (#102)"


def _text(conclusion: str, **kwargs) -> str:
    params = {
        "title": SUBJECT,
        "run": RUN,
        "env_label": "DEV",
        "env_url": NEUTRAL_DEV_URL,
    }
    params.update(kwargs)
    return tn.build_text(conclusion, **params)


def _url_run_id(url: str) -> str:
    match = re.search(r"/runs/([0-9]+)", url)
    return match.group(1) if match else ""


def _printed_number(line2: str) -> str:
    match = re.search(r"\(#([0-9]+)\)\s*$", line2)
    return match.group(1) if match else ""


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
        lines = tn.build_text("success", raw, RUN).splitlines()
        assert tn.escape_html(raw) in lines[1]
    assert tn.build_text("success", "", RUN).splitlines()[1].startswith("<a href=")
    assert tn.build_text("success", None, RUN).splitlines()[1].startswith("<a href=")


# ------------------------------------------------------------- message shape


def test_message_is_four_lines_with_an_empty_third_line():
    lines = _text("success").splitlines()
    assert len(lines) == 4, lines
    assert lines[0] == "\u2705 success"
    assert lines[2] == "", "line 3 must be empty"


def test_line_two_is_title_link_then_run_number_token():
    lines = _text("failure", title=SUBJECT).splitlines()
    line2 = lines[1]
    assert line2.startswith(f'<a href="{NEUTRAL_RUN_URL}">{tn.escape_html(SUBJECT)}</a>')
    # run-number token, GitHub style: (#<run_number>)
    assert line2.endswith(" (#100)")
    # title verbatim: prefix and the subject's own (#N) refs stay untouched
    assert "ci: Telegram" in line2
    assert "(#102)" in line2
    # no big run-id suffix
    assert "(1234567890)" not in line2


def test_number_comes_from_the_same_run_as_the_url():
    # The bug the owner flagged: URL of run A printed with number of run B.
    base = "https://github.com/example-org/example-repo/actions/runs/"
    run_a = {"id": 111, "html_url": f"{base}111", "run_number": 100}
    run_b = {"id": 222, "html_url": f"{base}222", "run_number": 101}
    line_a = tn.build_text("success", "title", run_a).splitlines()[1]
    line_b = tn.build_text("success", "title", run_b).splitlines()[1]

    for run, line in ((run_a, line_a), (run_b, line_b)):
        assert f'href="{run["html_url"]}"' in line
        # the URL carries this run's id ...
        assert _url_run_id(line) == str(run["id"])
        # ... and the token carries THIS run's number -- never the other one
        assert _printed_number(line) == str(run["run_number"])

    # explicit anti-mixing assertions
    assert _printed_number(line_a) == "100" and "runs/111" in line_a
    assert _printed_number(line_b) == "101" and "runs/222" in line_b
    assert _printed_number(line_a) != _printed_number(line_b)


def test_line_two_omits_token_when_number_unavailable():
    lines = tn.build_text(
        "success", "plain subject", {"id": 7, "html_url": "https://x.example/runs/7"}
    ).splitlines()
    assert lines[1] == '<a href="https://x.example/runs/7">plain subject</a>'
    # nothing at all is appended -- a wrong number is worse than none
    assert "(#" not in lines[1]


# --------------------------------------------------- environment label (line 4)


def test_url_line_carries_dev_label_with_dev_url():
    # Owner's shape: "DEV: http://192.168.100.109:7566" -- label, colon,
    # address. The old literal "URL" label is gone entirely.
    lines = _text("success", env_label="DEV", env_url=NEUTRAL_DEV_URL).splitlines()
    assert lines[3] == f"DEV: {NEUTRAL_DEV_URL}"
    assert not lines[3].startswith("URL:")


def test_url_line_falls_back_to_run_url_when_dev_secret_empty():
    for missing in ("", "   "):
        lines = _text("success", env_label="DEV", env_url=missing).splitlines()
        assert lines[3] == f"DEV: {NEUTRAL_RUN_URL}"


def test_url_line_defaults_to_dev_label_when_label_missing():
    # A missing label must never fall back to the old "URL" placeholder.
    lines = tn.build_text("success", "t", RUN, env_url=NEUTRAL_DEV_URL).splitlines()
    assert lines[3] == f"DEV: {NEUTRAL_DEV_URL}"


def test_prod_label_requires_release_ref_and_prod_secret():
    release_ref = "refs/tags/v0.6.0"
    branch_ref = "refs/heads/main"

    # both conditions -> PROD (the only way to get it)
    label, url = tn.resolve_environment(release_ref, NEUTRAL_DEV_URL, NEUTRAL_PROD_URL)
    assert (label, url) == ("PROD", NEUTRAL_PROD_URL)

    # release build but no prod secret -> DEV with the dev URL
    assert tn.resolve_environment(release_ref, NEUTRAL_DEV_URL, "") == (
        "DEV",
        NEUTRAL_DEV_URL,
    )

    # prod secret present but not a release build -> still DEV
    assert tn.resolve_environment(branch_ref, NEUTRAL_DEV_URL, NEUTRAL_PROD_URL) == (
        "DEV",
        NEUTRAL_DEV_URL,
    )

    # neither -> DEV
    assert tn.resolve_environment(branch_ref, NEUTRAL_DEV_URL, "") == (
        "DEV",
        NEUTRAL_DEV_URL,
    )


def test_prod_is_impossible_without_the_prod_secret():
    # There is no v0.6.0 release and TELEGRAM_PROD_URL was deleted: with an
    # empty prod secret NO ref can ever select PROD.
    refs = [
        "refs/tags/v0.6.0",
        "v0.6.0",
        "refs/tags/v1.0.0",
        "refs/heads/main",
        "refs/heads/fix/ci-notify-env-line",
        "refs/pull/105/merge",
        "",
    ]
    for ref in refs:
        label, url = tn.resolve_environment(ref, NEUTRAL_DEV_URL, "")
        assert label == "DEV", ref
        assert url == NEUTRAL_DEV_URL, ref
        built = tn.build_text("success", "t", RUN, env_label=label, env_url=url)
        assert built.splitlines()[3].startswith("DEV: "), ref


def test_release_ref_detection_is_version_tags_only():
    release = ["refs/tags/v0.6.0", "refs/tags/v1", "v0.6.0", "v1.0.0-rc1"]
    not_release = [
        "refs/heads/main",
        "refs/tags/0.6.0",
        "refs/tags/rc1",
        "refs/tags/v",
        "refs/tags/versioning",
        "refs/heads/v2-experiment",
        "",
    ]
    for ref in release:
        assert tn.is_release_ref(ref), ref
    for ref in not_release:
        assert not tn.is_release_ref(ref), ref


def test_dev_secret_empty_falls_back_to_run_url_through_resolve():
    label, url = tn.resolve_environment("refs/heads/main", "", "", NEUTRAL_RUN_URL)
    assert (label, url) == ("DEV", NEUTRAL_RUN_URL)


def test_context_line_is_appended_after_the_url_line():
    assert len(_text("success").splitlines()) == 4
    lines = _text("success", context="PROD : https://example.com").splitlines()
    assert len(lines) == 5
    assert lines[3].startswith("DEV: ")
    assert lines[4] == "PROD : https://example.com"


def test_every_conclusion_builds_a_message_without_crashing():
    for conclusion in ALL_CONCLUSIONS:
        lines = _text(conclusion).splitlines()
        assert len(lines) == 4
        assert lines[0] == f"{tn.STATUS_MAP[conclusion]} {conclusion}"
        assert lines[2] == ""
        assert lines[3].startswith("DEV: ")


def test_empty_and_none_conclusion_are_handled():
    lines = tn.build_text(None, "t", RUN, env_url="").splitlines()
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
    run = {
        "id": 1,
        "html_url": "https://github.com/example-org/example-repo/actions/runs/1?a=1&b=2",
        "run_number": 5,
    }
    lines = _text("success", run=run, env_url="").splitlines()
    assert "a=1&amp;b=2" in lines[3]
    assert lines[3].startswith("DEV: ")
    href = '<a href="https://github.com/example-org/example-repo/actions/runs/1?a=1&amp;b=2">'
    assert href in lines[1]


def test_preview_redacts_the_environment_urls():
    assert tn.redact(NEUTRAL_DEV_URL, NEUTRAL_DEV_URL) == tn.REDACTED
    assert tn.redact("keep this", NEUTRAL_DEV_URL) == "keep this"
    assert tn.redact("x", "") == "x"
    # both secret values are masked in one pass
    both = f"DEV: {NEUTRAL_DEV_URL} / PROD: {NEUTRAL_PROD_URL}"
    masked = tn.redact(both, NEUTRAL_DEV_URL, NEUTRAL_PROD_URL)
    assert NEUTRAL_DEV_URL not in masked
    assert NEUTRAL_PROD_URL not in masked
    assert masked.count(tn.REDACTED) == 2


# --------------------------------------------------- log masking guarantee


def test_printed_output_masks_env_url_while_payload_carries_it(monkeypatch, capsys):
    """The whole security contract of the environment URL, in one test.

    The dev address is a private LAN value: it may exist only in the repo
    secret and in the Telegram message text sent to the private chat. Run
    ``main()`` with a fake ``send`` that captures the outgoing payload and
    assert (a) the payload text CARRIES ``DEV: <env URL>`` and (b) stdout --
    what CI logs show -- does NOT contain the address, only the mask.
    """
    env_url = NEUTRAL_DEV_URL
    sent: list[dict] = []

    def fake_send(payload: dict, token: str) -> dict:
        sent.append(payload)
        return {"result": {"message_id": 42}}

    monkeypatch.setattr(tn, "send", fake_send)
    for name in ("GITHUB_TOKEN", "DRY_RUN", "TELEGRAM_PROD_URL", "DISPATCH_CONTEXT", "TITLE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "000000:fake-token-for-tests")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001234567890")
    monkeypatch.setenv("TELEGRAM_THREAD_ID", "111")
    monkeypatch.setenv("TELEGRAM_DEV_URL", env_url)
    monkeypatch.setenv("BUILD_REF", "refs/heads/main")
    monkeypatch.setenv("RUN_ID", "1234567890")
    monkeypatch.setenv("RUN_URL", NEUTRAL_RUN_URL)
    monkeypatch.setenv("RUN_NUMBER", "100")
    monkeypatch.setenv("DISPATCH_CONCLUSION", "success")
    monkeypatch.setenv("TITLE", "masking smoke test (#101)")

    assert tn.main([]) == 0
    out = capsys.readouterr().out

    # (a) the Telegram payload carries the labelled environment URL
    assert len(sent) == 1
    payload_text = sent[0]["text"]
    assert f"DEV: {env_url}" in payload_text

    # (b) nothing printed to stdout / CI logs shows the address
    assert env_url not in out
    assert tn.REDACTED in out
    assert f"DEV: {tn.REDACTED}" in out


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


def test_run_source_from_env_never_mixes_runs():
    # Both fields are taken from ONE event payload (workflow_run) or ONE
    # dispatch run -- never url from one and number from another.
    env = {
        "RUN_URL": "https://github.com/example-org/example-repo/actions/runs/111",
        "RUN_NUMBER": "100",
        "RUN_ID": "111",
    }
    source = tn.run_source_from_env(env, "example-org/example-repo")
    assert source == {
        "html_url": env["RUN_URL"],
        "run_number": env["RUN_NUMBER"],
        "id": env["RUN_ID"],
    }
    line = tn.build_text("success", "t", source).splitlines()[1]
    assert _url_run_id(line) == "111" and _printed_number(line) == "100"

    # dispatch fallback: no RUN_URL -> the URL is built from THIS run's id and
    # the number is this run's own number
    dispatch = tn.run_source_from_env(
        {"RUN_NUMBER": "101", "RUN_ID": "222"}, "example-org/example-repo"
    )
    assert dispatch["html_url"].endswith("/runs/222")
    line = tn.build_text("success", "t", dispatch).splitlines()[1]
    assert _url_run_id(line) == "222" and _printed_number(line) == "101"
