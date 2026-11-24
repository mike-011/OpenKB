# Telegram CI notifications (#101)

Every completed GitHub Actions run posts one message to the owner's Telegram
group + topic — **for any conclusion**, never silently. Implemented by
[`.github/workflows/telegram-notify.yml`](../.github/workflows/telegram-notify.yml)
+ [`../.github/scripts/telegram_notify.py`](../.github/scripts/telegram_notify.py);
behaviour is pinned down by `tests/test_telegram_notify.py`.

## Message format

`parse_mode=HTML` (user-controlled text is escaped — commit titles can contain
`<`, `&`, quotes; an unescaped `<` would make Telegram reject the whole message).

```text
<emoji> <original GitHub conclusion>
<title as a link to the run> (<run_id>/<run_attempt>)
URL: <run link>
[<optional context line>]
```

Real shape (example values, `example-org/example-repo` is not this repo):

```text
🟢 success
Merge pull request #86 from example/branch (https://github.com/example-org/example-repo/actions/runs/1234567890) (1234567890)
URL: https://github.com/example-org/example-repo/actions/runs/1234567890
PROD : https://example.com
```

- Line 1: status emoji + the **original GitHub wording** of the conclusion
  (`success`, `timed_out`, …) — not a translation.
- Line 2: run/commit title as an HTML `<a href>` link to the run URL (the
  Markdown link form `[title](url)` adapted to the chosen parse mode), then the
  run reference `(run_id)` — `(run_id/run_attempt)` when the run was retried.
- Line 3: literal `URL: ` + the run link. Always present.
- Optional 4th line: an extra context string (deployment URL etc.), *in
  addition* to the URL line. Sources, first match wins:
  1. `context` input on `workflow_dispatch`;
  2. a `CI-Context:` trailer in the head commit message, e.g.
     `CI-Context: PROD : https://example.com`.

## Status mapping (all GitHub Actions conclusions)

| `conclusion`       | Emoji  | Meaning                          |
| ------------------- | ------ | -------------------------------- |
| `success`           | 🟢     | all jobs green                   |
| `failure`           | 🔴     | at least one job failed          |
| `cancelled`         | 🔵     | run cancelled (superseded/manual)|
| `skipped`           | ⚪     | run skipped — still notified     |
| `neutral`           | ⬜     | finished without a verdict       |
| `timed_out`         | 🟠     | a job exceeded its timeout       |
| `action_required`   | 🟡     | needs attention (approval/brand) |
| `stale`             | 🩶     | marked stale by GitHub           |
| `startup_failure`   | ⛔     | runner failed to start the run   |
| *(anything else)*   | ❓     | fallback — raw text kept, no crash |

The mapping lives in `STATUS_MAP` in `.github/scripts/telegram_notify.py`; the
table above and the PR body document the same list. Unknown conclusions fall
back to ❓ with their original text, so a future GitHub addition can never break
or suppress a notification.

## Triggers

- `workflow_run` → `types: [completed]` for the repo's product workflows
  (`CI`, `Publish to PyPI`). Any conclusion fires it.
- `workflow_dispatch` for smoke tests and mapping checks:
  - `fake_conclusion` — send with a faked conclusion (failure path);
  - `title` — override line 2 text;
  - `context` — extra context line;
  - `dry_run` — print the payload instead of sending (no Telegram traffic).

The notify workflow does **not** list itself as a `workflow_run` source —
otherwise each notification would trigger the next one forever.

## Configuration

- Bot: `@sysadminodua_bot`. Token is **only** in the repository secret
  `TELEGRAM_BOT_TOKEN` (`gh secret set TELEGRAM_BOT_TOKEN`); it is never
  committed, logged, echoed or placed in the payload body.
- Target `chat_id` / `message_thread_id` are set in the workflow's `env` block
  (values taken from the owner's topic link; example placeholders elsewhere in
  this doc: `-1001234567890`, thread `111`).
- The job runs with `permissions: contents: read, actions: read` — it only
  checks out the repo and reads run metadata.

## Verifying

```bash
# real send (message_id in the run log = proof of arrival)
gh workflow run "Telegram notify" --ref ci/telegram-notifications \
  -f fake_conclusion=success -f title="Telegram notify smoke test (#101)"

# failure path / payload only, no Telegram traffic
gh workflow run "Telegram notify" --ref ci/telegram-notifications \
  -f fake_conclusion=timed_out -f dry_run=true

# unit-style: every conclusion builds a message without crashing
uv run --no-sync pytest tests/test_telegram_notify.py
```
