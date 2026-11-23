# Benchmarks — model comparison suite (#60)

One task set × one harness (OpenKB) × N models → comparable results.

## Groups (matrix v2 — EN/RU/UK/PL)

Languages: English, русский, українська, polski — native-level prompts (PL
strings verified by a native-level editor pass). Metrics follow community
norms: answer citation = RAGAS *faithfulness*, fact retention = *context
recall* / Summarization Content Units (SCU, Nenkova & Passonneau), expected
values = FActScore-style *atomic facts*. All checks are deterministic —
no LLM judge (privacy by design).

1. **tools** — raw tool-call structure against the model's native API
   (Ollama `/api/chat` or OpenAI-compatible `/v1/chat/completions`):
   14 scenarios, EN/RU/UK/PL, Cyrillic and Polish-diacritics prompts, exact
   filenames with digits, multi-turn follow-up, parallel reads, and no-tool
   false-positive checks. Each tool call is graded as `structured` (real
   `tool_calls` slot), `text-json` (the known small-model failure mode:
   tool JSON in plain content), or `none`.
2. **pipeline** — the real `openkb` CLI on a fixed fixture KB (8 docs, 10
   control facts incl. UK/PL sources): `init` → `add` → 26 questions (5
   facts × EN/RU/UK/PL + UK/PL-specific questions + 1 unanswerable per
   language). Two independent scores per answer: **Cited** (faithfulness —
   the expected page is cited) and **Facts** (answer correctness — the
   expected value is present).
3. **context-recall** — fact retention ("no information lost" in wiki
   generation): each of the 10 control facts must survive `add` and live on
   a real wiki page (not just the index). Shares the pipeline's KB build.

Judge rules (deterministic): NFKC + lowercase; unit synonyms (15 GiB = 15 ГБ
= 15GB), date forms (2026-11-30 = 30 ноября 2026 = 30 listopada 2026), times
(02:00 = 2:00); a fact matches when its tokens sit inside ONE sentence;
word needles match by substring (covers RU/UK/PL/EN word forms and compound
tokens like «щопʼятниці»). Sabotage-proven: inverting the matcher fails the
judge tests.

## Usage

```bash
python benchmarks/model_suite.py \
    --model mimo-v2.6:9b --provider ollama_chat \
    --api-base http://192.168.100.165:11434 --ctx 32768 \
    --label mimo-v2.6-9b-ctx32768 --out docs/local-llm/ollama
```

- `--provider ollama_chat` → `/api/chat` (model tag as-is)
- `--provider openai` → `<api-base>/v1/chat/completions` (llama.cpp llama-server,
  llama-swap facade, any OpenAI-compatible server)

Output: `docs/local-llm/<provider>/<label>/results.json` + `report.md`
(UTC date/time and the OpenKB git SHA pinned — results are only comparable
within one harness version). Reports live per model under `docs/local-llm/`;
the leaderboard table is `docs/local-llm/README.md`.

Harness self-tests: `tests/test_model_suite.py` (mocked transport).
