# Golden Principles

Opinionated, mechanical rules that keep this agent-generated codebase legible
and consistent for future agent runs. Enforced by CI where possible; the rest
are honored by convention and checked in review. When a rule proves valuable,
promote it into a lint (see `tests/test_file_size.py` for the pattern).

## Data hygiene (secrets & personal infra) — hard rule (#77)
Real IPs, DNS names, hostnames, logins, passwords, tokens and any
infrastructure identifiers must NEVER land in this repo (it is public).
Every example/fixture/doc value that looks like infrastructure comes from
approved fake pools instead — and must not be a calque of real infra:
- LAN addresses: random addresses from `192.168.0.0/24`
- DNS examples: public resolvers (`8.8.8.8`, `1.1.1.1`)
- person names: mixes of footballers / Harry Potter characters
- site addresses: fictional domains (`noname099.xyz`, `denegv2030.net`)
Bench report output masks LAN endpoints automatically
(`benchmarks.model_suite.mask_endpoint`). Examples in tests must use pool
values too.

## Public repo, private planning board
The repository is public; the project board
(github.com/users/mike-011/projects/6) is PRIVATE planning tooling — outside
contributors cannot see it. Issues are the public source of truth: any ticket
asking for outside help (label `help wanted`) must be self-contained —
problem, files, acceptance and how-to-help all live in the issue body, never
only in board fields or internal chat.

## Boundaries
- **Validate data shapes at boundaries.** Parse/validate inputs (frontmatter via
  `openkb/frontmatter.py`, config via `openkb/config.py`) at the edge. Never build
  on guessed shapes.

## Reuse
- **Prefer shared utilities over hand-rolled helpers** so invariants stay
  centralized. Check `openkb/` for an existing helper before writing a new one.

## I/O and state
- **All wiki file writes go through `openkb/locks.py` / `openkb/mutation.py`**
  (atomic, crash-safe). No ad-hoc writes to the wiki tree.
- **Log through `openkb/log.py`**, not bare `print`, for anything diagnostic.

## Size and shape
<a id="file-size"></a>
- **Keep modules focused and under 800 lines** (enforced by
  `tests/test_file_size.py`). Split large modules into focused units by
  responsibility. Existing over-limit files are grandfathered (with reasons)
  in the test's `_GRANDFATHERED` set and additionally tracked in
  `docs/internal/tech-debt.md` *(maintainer-local, not in git)*.

## Change discipline
<a id="change-discipline"></a>
- **Every change ships all five: ticket → tests → docs → commit → evidence.**
  1. **Ticket** — an issue describing the problem and acceptance criteria,
     opened BEFORE the code; branch and commits reference it
     (`Fixes #N` / `Refs #N`). No ticket → no change.
  2. **Tests** — automated tests for the new/expected behavior. A bug fix
     needs a regression test proven to FAIL without the fix (run it against
     the old behavior first). Never delete or weaken a test for a green run.
  3. **Docs** — update `docs/`, README, config examples, and test counts
     whenever behavior or interfaces change.
  4. **Commit** — conventional message (`feat(agent):`, `fix(cli):`,
     `test(agent):`, `docs:`, `style:`), one logical change per commit, the
     ticket referenced in the body.
  5. **Evidence** — CI run link(s) and test counts from a real run, pasted
     into the PR (checklist: `.github/pull_request_template.md`). A claim
     without run output is not evidence.
- **Branch naming**: `type/short-description`; branches that switch or tune
  an LLM model carry the model suffix (e.g. `feat/openkb-mimo-v2.6-flash`).
- **Production first**: anything touching production (deployed KBs, configs,
  model endpoints) needs explicit owner approval before execution.

## Docs
- **`AGENTS.md` is a map, not a manual.** Keep it short; deep/local docs live
  under `docs/` (public) and `docs/internal/` (maintainer-local, not in git).
