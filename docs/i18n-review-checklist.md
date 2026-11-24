# i18n review checklist (PL / UK) — standing task

The interface strings of the Workbench live in `frontend/src/locales/`. The
Polish and Ukrainian translations were machine-assisted and need a native
speaker's review. This doc is the self-contained task (moved from issue #75 —
the planning board is private, so everything lives here or in issues).

## Scope
- Files: `frontend/src/locales/` — all PL and UK string tables.
- English strings are the reference (same keys).

## What to check
1. **Naturalness / grammar** — flag calques from English; idiomatic phrasing wins.
2. **Terminology (IT / LLM context)** — consistent terms for: knowledge base,
   compile, source, query, chat, model, release, build.
3. **Consistency** — the same concept uses the same word across all strings.

## How to contribute
- Comment on this file's PR or open a PR with concrete edits.
- Preferred format per finding: `key → suggested string` (language, PL or UK).
- Even partial reviews (one locale, one section) are welcome.

Thank you — this is the last standing help-wanted task of the fork.
