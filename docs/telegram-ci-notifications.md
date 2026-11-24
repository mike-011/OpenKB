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
<title verbatim> (<run URL>) (#ticket)
<empty line>
URL: <PROD_URL from secrets.TELEGRAM_PROD_URL, else the run URL>
[<optional context line>]
```

Real shape (example values, `example-org/example-repo` and `prod.example.com`
are NOT this repo — the real PROD address is a secret and never appears in
files, logs or comments):

```text
✅ success
ci: Telegram notifications for every CI run (#101) (https://github.com/example-org/example-repo/actions/runs/1234567890) (#101)

URL: https://prod.example.com
PROD : https://example.com
```

- Line 1: status icon + the **original GitHub wording** of the conclusion
  (`success`, `timed_out`, …) — not a translation.
- Line 2: run title as an HTML `<a href>` link to the run URL (the Markdown
  link form `[title](url)` adapted to the chosen parse mode), then
  ` (#ticket)`. Rules:
  - the title is **verbatim** exactly as GitHub provides it (commit subject or
    the `title` input) — no prefix stripping, no rewriting (owner correction);
  - the run number is NOT appended — it already lives inside the URL;
  - `#ticket` comes from the `Fixes`/`Refs` ref in the commit body, else the
    first `(#N)` in the subject, else nothing.
- Line 3: **empty**.
- Line 4: literal `URL: ` + `<PROD_URL>` from the repository secret
  `TELEGRAM_PROD_URL`; if that secret is empty, the run URL is used instead.
  The value is never read into the repo, never printed — logs and dry-run
  output mask it as `<PROD_URL masked …>`.
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
- Line-4 target: repository secret `TELEGRAM_PROD_URL` (internal address —
  data-hygiene rule: never written to any repo file, log or issue comment; the
  workflow only references `secrets.TELEGRAM_PROD_URL`, and the script masks
  the value in everything it prints). Empty secret ⇒ run URL fallback.
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

# failure path / payload only, no Telegram traffic (PROD URL masked in log)
gh workflow run "Telegram notify" --ref main \
  -f fake_conclusion=timed_out -f dry_run=true

# unit-style: every conclusion builds a message without crashing
uv run --no-sync pytest tests/test_telegram_notify.py
```
