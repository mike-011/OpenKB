# Benchmarks — model comparison suite (#60)

One task set × one harness (OpenKB) × N models → comparable results.

## Groups

1. **tools** — raw tool-call structure against the model's native API
   (Ollama `/api/chat` or OpenAI-compatible `/v1/chat/completions`):
   10 scenarios, EN/RU, Cyrillic arguments, exact filenames with digits,
   multi-turn follow-up, parallel reads, and a no-tool false-positive check.
   Each tool call is graded as `structured` (real `tool_calls` slot),
   `text-json` (the known small-model failure mode: tool JSON in plain
   content), or `none`.
2. **pipeline** — the real `openkb` CLI on a fixed fixture KB:
   `init` → `add` → 5 grounded RU questions (answer must cite the fixture
   page) + 1 unanswerable (fabrication check).

## Usage

```bash
python benchmarks/model_suite.py \
    --model mimo-v2.6:9b --provider ollama_chat \
    --api-base http://192.168.0.203:11434 --ctx 32768 \
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
