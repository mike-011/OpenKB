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
<icon> <original GitHub conclusion>
<title verbatim> (<run URL>) (#<run number>)
<empty line>
<DEV|PROD>: <environment URL from secrets, else the run URL>
[<optional context line>]
```

Real shape (example values, `example-org/example-repo`, `prod.example.com`
and `192.168.0.77` are NOT this repo — the real dev address is a secret and
never appears in files, logs or comments):

```text
✅ success
ci: Telegram notifications for every CI run (#101) (https://github.com/example-org/example-repo/actions/runs/1234567890) (#100)

DEV: http://192.168.0.77:7566
PROD : https://example.com
```

(Here the URL path holds the run *id* `1234567890` while the token shows the
run *number* `100` — GitHub assigns them independently; what matters is that
both come from the same run payload.)

- Line 1: status icon + the **original GitHub wording** of the conclusion
  (`success`, `timed_out`, …) — not a translation.
- Line 2: run title as an HTML `<a href>` link to the run URL (the Markdown
  link form `[title](url)` adapted to the chosen parse mode), then
  ` (#<run number>)` in GitHub's own style. Rules:
  - the title is **verbatim** exactly as GitHub provides it (commit subject or
    the `title` input) — no prefix stripping, no rewriting (owner correction);
  - the number is the run number **of the very run the URL points to**:
    `html_url` and `run_number` are always read from ONE payload
    (`workflow_run` event fields for trigger runs, the dispatch run's own
    id/number for tests) — `run_source_from_env()` / the fetched run object
    make cross-run mixing impossible. The token is omitted rather than guessed
    if the number is unknown;
  - no ticket token and no run-id suffix: an earlier `(#ticket)` slot in the
    owner's mock was actually the run-number slot showing a mismatched value
    ("link goes to run #100 but the message shows #101") — fixed by the
    same-source rule above.
- Line 3: **empty**.
- Line 4: **environment label** + `: ` + the address — the literal `URL`
  label from earlier rounds is gone. Two labels exist:
  - `DEV: <secrets.TELEGRAM_DEV_URL>` — every build (dev builds are the only
    kind that exist today); if that secret is empty, the run URL is used
    instead;
  - `PROD: <secrets.TELEGRAM_PROD_URL>` — release builds **only**, and only
    when BOTH conditions hold: the build ref is a version tag
    (`refs/tags/v…` / bare `v…`) **and** the prod URL secret exists. The prod
    secret was deliberately deleted (there is no v0.6.0 release yet), so the
    PROD branch is currently impossible to trigger — every run prints `DEV`.
    Gate lives in `resolve_environment()` / `is_release_ref()`.
  The addresses are private: never read into the repo, never printed —
  logs and dry-run output mask them as `<ENV URL masked …>`
  (`test_printed_output_masks_env_url_while_payload_carries_it` asserts that
  the printed output masks the address while the Telegram payload carries it).
- Optional line 5: an extra context string (deployment URL etc.), appended
  after the URL line. Sources, first match wins:
  1. `context` input on `workflow_dispatch`;
  2. a `CI-Context:` trailer in the head commit message, e.g.
     `CI-Context: PROD : https://example.com`.

## Status mapping (all GitHub Actions conclusions)

| `conclusion`       | Icon  | Octicon it mirrors               |
| ------------------- | ----- | -------------------------------- |
| `success`           | ✅    | check-circle-fill                |
| `failure`           | ❌    | x-circle-fill                    |
| `cancelled`         | ⏹️    | stop-fill / circle-slash         |
| `skipped`           | ⏭️    | skip-fill (grey slashed circle)  |
| `neutral`           | ⚪    | grey dot-fill                    |
| `timed_out`         | ⏰    | clock                            |
| `action_required`   | ⚠️    | yellow attention                 |
| `stale`             | ♻️    | refresh (stale)                  |
| `startup_failure`   | 💥    | x-circle / boom                  |
| *(anything else)*   | ❓    | fallback — raw text kept, no crash |

The owner approved this exact glyph set as FINAL: line 1 is always
`<icon> <original GitHub conclusion text>` (e.g. `✅ success`), never a
translated phrase.

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
- Line-4 target: repository secrets `TELEGRAM_DEV_URL` (dev address, set) and
  `TELEGRAM_PROD_URL` (release address — **not set**, deliberately deleted
  until a release exists). The workflow references only `secrets.<NAME>`;
  empty dev secret ⇒ run URL fallback, empty prod secret ⇒ PROD unreachable.
- Where the environment address may live — each surface, explicitly:
  1. **Repository secret value** — write-only via the API; the only stored
     copy.
  2. **Telegram message text** — sent to the private group/topic only.
  3. Nowhere else: **not** in repo files, **not** in issue/PR bodies or
     comments, **not** in commit messages, **not** in CI logs. Logs are
     public, so every printed byte (preview, dry-run JSON, warnings) passes
     through `redact()`, which masks the dev and prod values as
     `<ENV URL masked …>`; the unit test
     `test_printed_output_masks_env_url_while_payload_carries_it` pins the
     split (payload carries it, stdout masks it).
- Target `chat_id` / `message_thread_id` are set in the workflow's `env` block
  (values taken from the owner's topic link; example placeholders elsewhere in
  this doc: `-1001234567890`, thread `111`).
- The job runs with `permissions: contents: read, actions: read` — it only
  checks out the repo and reads run metadata.

## Verifying

```bash
# real send (message_id in the run log = proof of arrival)
gh workflow run "Telegram notify" --ref main \
  -f fake_conclusion=success -f title="Telegram notify smoke test (#101)"

# failure path / payload only, no Telegram traffic (env URL masked in log)
gh workflow run "Telegram notify" --ref main \
  -f fake_conclusion=timed_out -f dry_run=true

# unit-style: label gates, masking guarantee, every conclusion builds a
# message without crashing
uv run --no-sync pytest tests/test_telegram_notify.py
```

Log check for the masking guarantee: in any run's log the preview line must
show `DEV: <ENV URL masked …>` — the address itself never appears in the log
text, while the delivered Telegram message shows `DEV: <address>`.
